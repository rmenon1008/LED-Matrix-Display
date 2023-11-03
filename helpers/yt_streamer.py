import cv2
import yt_dlp
import time
import multiprocessing as mp
import queue
from .image_processing import center_crop as center_crop_img, crop_percentages

class YtStreamer:
    def __init__(self, yt_url, desired_width, size=None, crop=None):
        self.yt_url = yt_url
        self.desired_width = desired_width
        self.size = size
        self.crop = crop
        
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(yt_url, download=False, process=False)
            formats = info['formats']

            for format in formats:
                if 'height' in format:
                    if format['height'] == desired_width:
                        break
                else:
                    continue
            else:
                raise ValueError("No format with desired width found")

            self.stream_url = format['url']
            self.fps = format['fps']

            self.start_time = time.perf_counter()
            self.frames_displayed = 0

            self.frame_queue = mp.Queue(maxsize=int(3*self.fps))
            self.thread = mp.Process(target=self._read_frames)
            self.thread.start()
            print("Created frame queue")

    def kill(self):
        self.killed = True
        self.thread.terminate()
        self.thread.join()
        self.closed = True

    def _read_frames(self):
        while True:
            print("Setting up stream")
            cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            while True:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        print("Video stream ended unexpectedly")
                        cap.release()
                        break
                    if self.crop is not None:
                        frame = crop_percentages(frame, self.crop)
                    if self.size is not None:
                        frame = center_crop_img(frame, self.size[0] / self.size[1])
                        frame = cv2.resize(frame, self.size)
                    self.frame_queue.put(frame)
                except Exception as e:
                    cap.release()
                    break
                
                time.sleep(1/60)

            # Wait 5 seconds before trying to reconnect
            time.sleep(5)

            self.start_time = time.perf_counter()
            self.frames_displayed = 0
            while not self.frame_queue.empty():
                self.frame_queue.get()

    def next_frame(self):
        # If we're behind schedule, skip frames
        while self.frames_displayed < int((time.perf_counter() - self.start_time) * self.fps):
            self.frame_queue.get()
            self.frames_displayed += 1
        # If we're ahead of schedule, wait
        while self.frames_displayed >= int((time.perf_counter() - self.start_time) * self.fps):
            pass
        self.frames_displayed += 1

        frame = self.frame_queue.get()
        return frame


class YtFrameDownloader:
    def __init__(self, yt_url, desired_width):
        self.yt_url = yt_url
        self.desired_width = desired_width

        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(yt_url, download=False, process=False)
            formats = info['formats']

            for format in formats:
                if 'height' in format:
                    if format['height'] == desired_width:
                        break
                else:
                    continue
            else:
                raise ValueError("No format with desired width found")

            self.stream_url = format['url']
            if format['fps'] != 30:
                raise ValueError("Video must be 30fps")

    def get_frames(self, size=None, max_duration=None, cvt_color=False, center_crop=False):
        cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if center_crop:
                frame = center_crop_img(frame, size[0] / size[1])
            if size is not None:
                frame = cv2.resize(frame, size)
            if max_duration is not None and len(frames) > max_duration * 30:
                break
            if cvt_color:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            frames.append(frame)
        return frames