import os
import signal
import numpy as np
import time
import multiprocessing

from layers import BackgroundLayer, NotificationLayer, WidgetLayer
from apps import Time, Weather, Calendar, YtStream, Setup
from helpers.image_processing import alpha_blend

class Renderer:
    def __init__(self, apps):
        self.update_queues = {
            "background_updates": multiprocessing.Queue(maxsize=2),
            "notification_updates": multiprocessing.Queue(maxsize=2),
            "widget_updates": multiprocessing.Queue(maxsize=2),
        }
        self.background_layer = BackgroundLayer(self.update_queues["background_updates"])
        self.notification_layer = NotificationLayer(self.update_queues["notification_updates"])
        self.widget_layer = WidgetLayer(self.update_queues["widget_updates"])
        self.apps = self.create_apps(apps)

    def create_apps(self, app_dict):
        apps = []
        for app_name, options in app_dict.items():
            # match app_name:
            #     case "time":
            #         apps.append(Time(self.update_queues, **options))
            #     case "weather":
            #         apps.append(Weather(self.update_queues, **options))
            #     case "calendar":
            #         apps.append(Calendar(self.update_queues, **options))
            #     case "yt_stream":
            #         apps.append(YtStream(self.update_queues, **options))
            #     case "setup":
            #         apps.append(Setup(self.update_queues, **options))
            #     case _:
            #         raise ValueError(f"Invalid app: {app_name}")
            if app_name == "time":
                apps.append(Time(self.update_queues, **options))
            elif app_name == "weather":
                apps.append(Weather(self.update_queues, **options))
            elif app_name == "calendar":
                apps.append(Calendar(self.update_queues, **options))
            elif app_name == "yt_stream":
                apps.append(YtStream(self.update_queues, **options))
            elif app_name == "setup":
                apps.append(Setup(self.update_queues, **options))
            else:
                raise ValueError(f"Invalid app: {app_name}")
        return apps

    def update_apps(self, app_dict):
        for app in self.apps:
            if app.process is not None and app.process.is_alive():
                app.process.terminate()
                app.process.join()
                app.process = None

        self.background_layer.clear()
        self.notification_layer.clear()
        self.widget_layer.clear()

        self.apps = self.create_apps(app_dict)

    def get_frame(self):
        frame = alpha_blend([
            self.background_layer.get_frame(),
            self.notification_layer.get_frame(),
            self.widget_layer.get_frame(),
        ])
        return frame
