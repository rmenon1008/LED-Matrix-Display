import time
import threading
import json
import multiprocessing as mp
import requests

import yt_dlp
import websocket
import numpy as np
import cv2

import helpers.text as text
import helpers.image_processing as imp
from helpers.yt_streamer import YtStreamer, YtFrameDownloader
import fonts.fonts as fonts


# color = (254, 254, 254, 255)
# outline = (1, 1, 1, 200)

def colors_from_global_settings(global_settings):
    color = (254, 254, 254, 255)
    if global_settings and "foreground_opacity" in global_settings:
        color = (*color[:3], global_settings["foreground_opacity"])
    outline_color = (1, 1, 1, 210)
    if global_settings and "background_opacity" in global_settings:
        outline_color = (*outline_color[:3], global_settings["background_opacity"])

    return color, outline_color

class App:
    def __init__(self):
        self.frame_queue = mp.Queue(maxsize=1)
        self.frame = np.zeros((48, 96, 4), dtype=np.uint8)
        self.process = mp.Process(target=self._run)

    def _start(self):
        self.process.start()

    def get_colors(self):
        return None, None

    def _run(self):
        pass

    def get_frame(self):
        if not self.frame_queue.empty():
            self.frame = self.frame_queue.get()
        return self.frame

class Time(App):
    def __init__(
            self,
            use_12_hr=True,
            show_seconds=False,
            show_am_pm=False,
            small_font=False,
            pos="tr",
            padding=(1, 1, 1, 1),
            _global_settings=None
        ):
        super().__init__()
        if use_12_hr:
            self.time_format = "%-I:%M"
        else:
            self.time_format = "%-H:%M"
        if show_seconds:
            self.time_format += ":%S"
        if show_am_pm and use_12_hr:
            self.time_format += " %p"

        self.color, self.outline_color = colors_from_global_settings(_global_settings)

        self.refresh_rate = 5
        if show_seconds:
            self.refresh_rate = 0.5

        self.font = fonts.SIX_TALL
        if small_font:
            self.font = fonts.FOUR_TALL
        
        self.pos = pos
        self.padding = padding

        self._start()

    

    def _run(self):
        while True:
            time_str = time.strftime(self.time_format)
            time_pixels = text.render_string(
                time_str,
                text_font=self.font,
                container_size=(96, 48),
                container_padding=self.padding,
                container_pos=self.pos,
                color=self.color,
                outline_color=self.outline_color
            )
            self.frame_queue.put(time_pixels)
            time.sleep(self.refresh_rate)

class Weather(App):
    PIRATE_API_KEY = "R8DbhW2ey6vfKHLy"

    def __init__(
            self,
            location_lat_lon,
            use_celsius=False,
            use_feels_like=False,
            show_icon=True,
            small_font=True,
            pos="tl",
            padding=(1, 1, 1, 1),
            _global_settings=None
        ):
        super().__init__()
        self.location_lat_lon = location_lat_lon
        self.use_feels_like = use_feels_like
        self.use_celsius = use_celsius
        self.show_icon = show_icon
        self.small_font = small_font
        self.pos = pos
        self.padding = padding

        self.color, self.outline_color = colors_from_global_settings(_global_settings)

        self._start()

    def _run(self):
        while True:
            # Get weather data
            try:
                request = f"https://api.pirateweather.net/forecast/{self.PIRATE_API_KEY}/{self.location_lat_lon[0]},{self.location_lat_lon[1]}?units={'si' if self.use_celsius else 'us'}"
                response = requests.get(request)
                data = response.json()
            except:
                time.sleep(5)
                continue

            # Render weather data
            temp = round(data["currently"]["temperature" if self.use_feels_like else "apparentTemperature"])
            if self.show_icon:
                icon = data["currently"]["icon"].replace("-", "_").upper()
                weather_string = f"![{icon}] {temp}°"
            else:
                weather_string = f"{temp}°"

            font = fonts.SIX_TALL
            if self.small_font:
                font = fonts.FOUR_TALL                

            weather_pixels = text.render_string(
                weather_string,
                text_font=font,
                container_size=(96, 48),
                container_padding=self.padding,
                container_pos=self.pos,
                color=self.color,
                outline_color=self.outline_color
            )
            self.frame_queue.put(weather_pixels)

            time.sleep(5 * 60)

class YtStream(App):
    def __init__(
            self,
            url,
            desired_quality=144,
            crop=None,
            size=(96, 48),
            image_adjustments=None,
            _global_settings=None
        ):
        super().__init__()
        self.url = url
        self.desired_quality = desired_quality
        print(f"Starting stream for {url} at {desired_quality}p")
        self.crop = crop
        self.size = size
        self.image_adjustments = image_adjustments
        self._start()

    def get_colors(self):
        return imp.get_fg_bg_colors(self.frame)

    def _run(self):
        self.streamer = YtStreamer(self.url, self.desired_quality, crop=self.crop, size=self.size)
        while True:
            frame = self.streamer.next_frame()
            if self.image_adjustments:
                frame = imp.image_adjustment(frame, **self.image_adjustments)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            while self.frame_queue.full():
                self.frame_queue.get()
            self.frame_queue.put_nowait(frame)

            time.sleep(1/60)

def _run_ws_download(video_queue, desired_quality, size, max_duration):
    def on_message(ws, message):
        try:
            obj = json.loads(message[message.index("["):])
            video_id = obj[1]["video"]["id"]
        except:
            return
        
        ws.send("2")
        if video_queue.full():
            print("Video queue full, skipping video")
            return
        
        try:
            yt = YtFrameDownloader(video_id, desired_quality)
        except:
            return
        frames = yt.get_frames(size=size, max_duration=max_duration, cvt_color=True, center_crop=True)
        video_queue.put(frames)

    def on_error(ws, error):
        print(error)

    def on_close(ws, close_status_code, close_msg):
        print("Astronaut.io connection closed")
        ws.close()

    while True:
        ws = websocket.WebSocketApp(
            "ws://astronaut.io/socket.io/?EIO=3&transport=websocket",
            on_message = on_message,
            on_error = on_error,
            on_close = on_close
        )
        ws.run_forever()
        print("Stream ended, reconnecting")
        time.sleep(5)

class AstronautIo(App):
    def __init__(
            self,
            desired_quality=144,
            size=(96, 48),
            max_duration_sec=20,
            _global_settings=None
        ):
        super().__init__()
        self.size = size
        self.desired_quality = desired_quality
        self.max_duration = max_duration_sec
        self.video_queue = mp.Queue(maxsize=2)
        self.start_time = None
        self.ws_process = mp.Process(target=_run_ws_download, args=(self.video_queue, self.desired_quality, self.size, self.max_duration))
        self.current_video = None
        self._start()
        self.ws_process.start()

    def get_colors(self):
        return imp.get_fg_bg_colors(self.frame)

    def _run(self):
        while self.video_queue.empty():
            time.sleep(1)
        print("Starting astronaut.io stream")
        while True:
            if self.current_video is None:
                print("Getting new video")
                self.current_video = self.video_queue.get()
                print("Got new video")
                self.start_time = time.time()
            
            frame_index = int((time.time() - self.start_time) * 30)
            if frame_index >= len(self.current_video) or (time.time() - self.start_time) > self.max_duration:
                self.current_video = None
                continue
            frame = self.current_video[frame_index]
            try:
                self.frame_queue.put_nowait(frame)
            except mp.queues.Full:
                pass

            time.sleep(1/60)
