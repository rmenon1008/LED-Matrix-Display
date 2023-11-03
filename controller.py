#!/usr/bin/python3

from renderer import Renderer
# from matrix_emulator.matrix import Matrix
from matrix_driver.matrix_driver import Matrix

import time
import json

import cProfile

class Controller():
    def __init__(self):
        # Load the config file
        config = None
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            print("No config file found, using defaults")
            config = {}
        except json.decoder.JSONDecodeError:
            print("Config file is invalid, resetting to defaults")
            config = {}
        self.config = config

        # Initialize the matrix and app renderer
        self.matrix = Matrix(self.config.get("dimensions", None))
        self.renderer = Renderer(self.config)
        self.last_frame_times = []
    
    def _render_loop(self):
        self.last_frame_times.append(time.perf_counter())
        self.last_frame_times = self.last_frame_times[-10:]
        self.matrix.set_pixels(self.renderer.get_frame())
        # Calculate FPS using the last 20 frames
        times = [self.last_frame_times[i+1] - self.last_frame_times[i] for i in range(len(self.last_frame_times)-1)]
        fps = 1 / (sum(times) / len(times)) if len(times) > 0 else 0
        print(f"FPS: {round(fps, 2)}", end="\r")

def run_profile(t=1):
    controller = Controller()
    start_time = time.time()
    while time.time() - start_time < t:
        controller._render_loop()

def run():
    controller = Controller()
    while True:
        controller._render_loop()

if __name__ == "__main__":
    run()
    
