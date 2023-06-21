import time
import numpy as np
import text
import threading
import cv2
import requests
import fonts


class Widget:
    def __init__(self, name, render, priority):
        self.name = name
        self.render = render
        self.priority = priority


class Notification:
    def __init__(self, app, render, duration=60):
        self.app = app
        self.render = render
        self.duration = duration


class App:
    def __init__(self, layers):
        self.notification_layer = layers["notification"] if "notification" in layers else None
        self.widget_layer = layers["widget"] if "widget" in layers else None
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        pass

    def add_notification(self, notification):
        self.notification_layer.add_notification(notification)

    def update_widget(self, widget):
        self.widget_layer.update_widget(widget)


class Time(App):
    def __init__(self, layers, time_format="%-I:%M"):
        self.time_format = time_format
        super().__init__(layers)

    def _run(self):
        counter = 0
        while True:
            counter += 1
            time_str = time.strftime(self.time_format)
            time_pixels = text.render_string(
                time_str,
                text_font=fonts.NUMBERS_FOUR_TALL,
                container_size=(36, 5),
                container_padding=(1, 1, 0, 0),
                container_pos="tr",
                color=(128, 128, 128, 128)
            )

            self.update_widget(Widget("time", time_pixels, 0))

            time.sleep(1)


class Weather(App):
    PIRATE_API_KEY = "R8DbhW2ey6vfKHLy"

    def __init__(self, layers, lat=0, lon=0, units="us"):
        self.lat = lat
        self.lon = lon
        self.units = units
        super().__init__(layers)

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
                container_size=(36, 10),
                container_padding=(1, 1, 0, 0),
                container_pos="tr",
                color=(128, 128, 128, 128)
            )
            self.update_widget(Widget("weather", weather_pixels, 0))

            time.sleep(10)
