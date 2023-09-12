from rgbmatrix import RGBMatrix, RGBMatrixOptions
# from rust_matrix_driver import Matrix as RustMatrix
from PIL import Image
import numpy as np
import cv2
import time

import spidev
# class Matrix:
#     def __init__(self, dimensions):
#         print(f"Initializing {dimensions[0]}x{dimensions[1]} matrix")
#         options = RGBMatrixOptions()
#         options.rows = dimensions[1]
#         options.cols = dimensions[0]
#         options.chain_length = 1
#         options.parallel = 3
#         options.row_address_type = 0
#         options.multiplexing = 0
#         options.pwm_bits = 11
#         options.brightness = 100
#         options.pwm_lsb_nanoseconds = 150
#         options.led_rgb_sequence = "RGB"
#         options.pixel_mapper_config = ""
#         options.panel_type = ""
#         options.gpio_slowdown = 3
#         options.disable_hardware_pulsing = False
#         options.pwm_dither_bits = 2
#         options.show_refresh_rate = True

#         self.matrix = RGBMatrix(options=options)
#         self.prev_pixels = None
#         self.off_screen_canvas = self.matrix.CreateFrameCanvas()

#         self.gamma_table = self._gen_gamma_table(2.8)

#     def _gen_gamma_table(self, gamma):
#         gamma_table = np.zeros(256, dtype=np.uint8)
#         for i in range(256):
#             gamma_table[i] = int(pow(i / 255.0, gamma) * 255.0 + 0.5)
#         return gamma_table

#     def set_pixels(self, pixels):
#         pixels = cv2.LUT(pixels, self.gamma_table)
#         self.off_screen_canvas.SetImage(Image.fromarray(pixels))
#         self.matrix.SwapOnVSync(self.off_screen_canvas)

#     def clear(self):
#         self.matrix.Clear()


# class Matrix:
#     def __init__(self, dimensions):
#         print("Initializing {}x{} matrix".format(dimensions[0], dimensions[1]))
#         self.matrix = RustMatrix(dimensions[0], dimensions[1])

#     def set_pixels(self, pixels):
#         self.matrix.update(pixels)

#     def clear(self):
#         pass

class Matrix:
    def __init__(self, dimensions):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 1)
        self.spi.no_cs = True
        self.spi.mode = 0b11
        self.spi.max_speed_hz = 16_000_000

        print("Initializing {}x{} matrix".format(dimensions[0], dimensions[1]))

    def set_pixels(self, pixels):
        data = pixels.tobytes()
        self.spi.xfer3(data)

    def clear(self):
        pass
