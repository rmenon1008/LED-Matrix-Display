import cv2
import yt_dlp
import time
import threading
import queue

class YtStreamer:
    def __init__(self, yt_url, desired_width):
        self.yt_url = yt_url
        self.desired_width = desired_width
        self._set_up(yt_url, desired_width)

        self.unexpected_end = False
        self.killed = False
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

            self.frame_queue = queue.Queue(maxsize=2*self.fps)
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
                    break
                self.frame_queue.put(frame)
            except Exception as e:
                self.unexpected_end = True
                break

    def next_frame(self):
        # Check if we need to restart the stream
        if self.unexpected_end:
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

