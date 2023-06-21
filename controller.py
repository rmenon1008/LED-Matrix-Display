from matrix import Matrix
from layer import YtStreamLayer, NotificationLayer, WidgetLayer
import cv2
import os
import atexit
import signal
import numpy as np
from image_processing import alpha_blend
from apps import Time, Weather
import time


dimensions = (96, 48) # (height, width)

# matrix = Matrix(dimensions)

URL = "https://www.youtube.com/watch?v=sJU17dB-raw"  # Quad camera
# URL = "https://www.youtube.com/watch?v=N609loYkFJo"
# streamLayer = YtStreamLayer(dimensions, URL, 240)
# # timeLayer = TimeLayer(dimensions)

# while True:
#     matrix.set_pixels(alpha_blend(streamLayer.get_frame(), timeLayer.get_frame()))

signal.signal(signal.SIGINT, lambda x, y: os._exit(0))

class Controller:
    def __init__(self, dimensions):
        self.matrix = Matrix(dimensions)
        self.layers = {
            "background": YtStreamLayer(dimensions, URL, 240, crop=(0, 0, 63, 70)),
            "notification": NotificationLayer(),
            "widget": WidgetLayer()
        }

        self.apps = [
            Time(self.layers, time_format="%-I:%M"),
            Weather(self.layers, lat=47.6062, lon=122.3321)
        ]

    def run(self):
        frame_times = []
        while True:
            start_time = time.time()
            self.matrix.set_pixels(
                alpha_blend([
                    layer.get_frame() for layer in self.layers.values()
                ])
            )
            frame_times.append(time.time() - start_time)
            frame_times = frame_times[-15:]
            fps = round(1 / np.mean(frame_times), 2)
            print("FPS:", fps, end='\r')


controller = Controller(dimensions)
controller.run()
