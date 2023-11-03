import cv2
import yt_dlp
import time
import threading
import queue
from .image_processing import center_crop as center_crop_image

class YtStreamer:
    def __init__(self, yt_url, desired_width, auto_restart=True, auto_start=True):
        self.yt_url = yt_url
        self.desired_width = desired_width
        self.auto_restart = auto_restart
        self._set_up(yt_url, desired_width)

        self.unexpected_end = False
        self.killed = False
        self.closed = False
        pass

    def kill(self):
        self.killed = True
        self.cap.release()

    def _set_up(self, yt_url, desired_width):
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

            self.frame_queue = queue.Queue(maxsize=3*self.fps)
            self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            self.thread = threading.Thread(target=self._read_frames)
            self.thread.start()
            print("Created frame queue")

    def _read_frames(self):
        while True:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("Video stream ended unexpectedly")
                    self.unexpected_end = True
                    self.cap.release()
                    self.closed = True
                    break
                self.frame_queue.put(frame)
            except Exception as e:
                self.unexpected_end = True
                self.cap.release()
                self.closed = True
                break

    def next_frame(self):
        # Check if we need to restart the stream
        if self.unexpected_end and self.auto_restart:
            print("Restarting stream")
            while not self.frame_queue.empty():
                try:
                    print("Attempting to set up again")
                    self._set_up(self.yt_url, self.desired_width)
                    self.unexpected_end = False
                except Exception as e:
                    print(e)
                    time.sleep(5)

        # If we're behind schedule, skip frames
        while self.frames_displayed < int((time.perf_counter() - self.start_time) * self.fps):
            self.frame_queue.get()
            self.frames_displayed += 1
        # If we're ahead of schedule, wait
        while self.frames_displayed >= int((time.perf_counter() - self.start_time) * self.fps):
            pass
        self.frames_displayed += 1
        return self.frame_queue.get()


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
                frame = center_crop_image(frame, size[0] / size[1])
            if size is not None:
                frame = cv2.resize(frame, size)
            if max_duration is not None and len(frames) > max_duration * 30:
                break
            if cvt_color:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            frames.append(frame)
        return frames