import time
import multiprocessing
import requests

import numpy as np
import cv2

import helpers.text as text
import helpers.image_processing as imp
from helpers.yt_streamer import YtStreamer
import fonts.fonts as fonts


class Widget:
    def __init__(self, name, render, priority):
        self.name = name
        self.render = render
        self.priority = priority


class Notification:
    def __init__(self, key, render, duration=60):
        self.key = key
        self.render = render
        self.duration = duration


class App:
    def __init__(self, update_queues):
        self.notification_updates = update_queues["notification_updates"] if "notification_updates" in update_queues else None
        self.widget_updates = update_queues["widget_updates"] if "widget_updates" in update_queues else None
        self.background_updates = update_queues["background_updates"] if "background_updates" in update_queues else None
        self.process = multiprocessing.Process(target=self._run)

    def _start(self):
        self.process.start()

    def _run(self):
        pass


color = (255, 255, 255, 255)
outline = (0, 0, 0, 170)

class Time(App):
    def __init__(self, update_queues, time_format="%-I:%M"):
        super().__init__(update_queues)
        self.time_format = time_format
        self._start()

    def _run(self):
        while True:
            time_str = time.strftime(self.time_format)
            time_pixels = text.render_string(
                time_str,
                container_size=(30, 7),
                container_padding=(0, 0, 1, 0),
                container_pos="tr",
                color=color,
                outline_color=outline
            )
            self.widget_updates.put(Widget("time", time_pixels, 0))

class Calendar(App):
    def __init__(self, layers):
        super().__init__(layers)
        self._start()

    def _run(self):
        def create_event(k, s, d):
            label = text.render_string(
                f"{s} min",
                text_font=fonts.FOUR_TALL,
                container_size=(63, 6),
                container_padding=(0, 0, 0, 0),
                container_pos="tl",
                color=color,
                outline_color=outline
            )
            contents = text.render_string(
                "Weekly DCGR Meeting",
                ellipsis=True,
                container_size=(63, 8),
                container_pos="tl",
                color=color,
                outline_color=outline
            )
            pixels = np.vstack((label, contents))
            height = pixels.shape[0]

            # Create a bar to the left
            bar = np.zeros((height, 3, 4), dtype=np.uint8)
            bar[:, :, :] = outline
            bar[1:-2, 1:-1, :] = color
            bar[-1, :, :] = (0, 0, 0, 0)

            pixels = np.hstack((bar, pixels))

            # Add a spacer to the bottom
            spacer = np.zeros((1, pixels.shape[1], 4), dtype=np.uint8)
            pixels = np.vstack((pixels, spacer))

            self.notification_updates.put(Notification(k, pixels, d))

        create_event("cal-1", 1, 15)
        create_event("cal-2", 2, 20)
        create_event("cal-3", 3, 5)
        
        time.sleep(1)


class Weather(App):
    PIRATE_API_KEY = "R8DbhW2ey6vfKHLy"

    def __init__(self, layers, lat=0, lon=0, units="us"):
        super().__init__(layers)
        self.lat = lat
        self.lon = lon
        self.units = units
        self._start()

    def _run(self):
        while True:
            # Get weather data
            try:
                request = f"https://api.pirateweather.net/forecast/{self.PIRATE_API_KEY}/{self.lat},{self.lon}?units={self.units}"
                response = requests.get(request)
                data = response.json()
            except:
                time.sleep(5)
                continue

            # Render weather data
            icon = data["currently"]["icon"].replace("-", "_").upper()
            temp = round(data["currently"]["temperature"])
            weather_string = f"![{icon}] {temp}°"
            weather_pixels = text.render_string(
                weather_string,
                text_font=fonts.FOUR_TALL,
                container_size=(30, 11),
                container_padding=(0, 0, 1, 0),
                container_pos="tr",
                color=color,
                outline_color=outline,
                relative_vert_offset=1
            )
            self.widget_updates.put(Widget("weather", weather_pixels, 0))

            time.sleep(5 * 60)

class YtStream(App):
    def __init__(self, update_queues, url, desired_quality=360, crop=None, size=(96, 48)):
        super().__init__(update_queues)
        self.url = url
        self.desired_quality = desired_quality
        print(f"Starting stream for {url} at {desired_quality}p")
        self.crop = crop
        self.size = size
        self._start()

    def _run(self):
        self.streamer = YtStreamer(self.url, self.desired_quality)
        while True:
            frame = self.streamer.next_frame()
            # frame = imp.adjust_brightness(frame, -50)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            if self.crop:
                frame = imp.crop_percentages(frame, self.crop)
            frame = imp.center_crop(frame, self.size[0]/self.size[1])
            frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)
            self.background_updates.put(frame)

class Setup(App):
    def __init__(self, update_queues):
        super().__init__(update_queues)
        self._start()

    def _run(self):
        lines = [
            "Open 'dotboard.local'",
            "in your browser to",
            "configure",
        ]

        rendered_lines = []
        for line in lines:
            rendered_lines.append(text.render_string(
                line,
                container_size=(96, 8),
                container_pos="tm",
                color=color,
                outline_color=outline
            ))

        pixels = np.vstack(rendered_lines)
        pixels = imp.contain(pixels, (96, 48), position="mm")
        self.background_updates.put(pixels)
