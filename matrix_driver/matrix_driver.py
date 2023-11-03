import spidev
import RPi.GPIO as gpio

import time

class Matrix:
    RESET_PIN = 14
    def __init__(self, _):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 1)
        self.spi.no_cs = True
        self.spi.mode = 0b11
        self.spi.max_speed_hz = 16_000_000

        print("Initializing matrix...")

    def set_pixels(self, pixels):
        data = pixels.tobytes()
        self.spi.writebytes2(data)

    def __del__(self):
        self.spi.close()
        self.reset()

    def reset(self):
        gpio.setmode(gpio.BCM)
        gpio.setup(self.RESET_PIN, gpio.OUT)
        gpio.output(self.RESET_PIN, gpio.LOW)
        time.sleep(0.05)
        gpio.output(self.RESET_PIN, gpio.HIGH)
        gpio.cleanup()
        time.sleep(0.2)

