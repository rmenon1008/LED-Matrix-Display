from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import numpy as np
import cv2

class Matrix:
    def __init__(self, dimensions):
        print("Initializing {}x{} matrix".format(dimensions[0], dimensions[1]))
        options = RGBMatrixOptions()
        options.rows = dimensions[1]
        options.cols = dimensions[0]
        options.chain_length = 1
        options.parallel = 3
        options.row_address_type = 0
        options.multiplexing = 0
        options.pwm_bits = 8
        options.brightness = 50
        options.pwm_lsb_nanoseconds = 300
        options.led_rgb_sequence = "RGB"
        options.pixel_mapper_config = ""
        options.panel_type = ""
        options.gpio_slowdown = 2
        options.disable_hardware_pulsing = False
        # options.pwm_dither_bits = 2
        options.show_refresh_rate = True

        self.matrix = RGBMatrix(options=options)
        self.off_screen_canvas = self.matrix.CreateFrameCanvas()

        self.gamma_table = self._gen_gamma_table(2.8)

    def _gen_gamma_table(self, gamma):
        gamma_table = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            gamma_table[i] = int(pow(i / 255.0, gamma) * 255.0 + 0.5)
        return gamma_table

    def set_pixels(self, pixels):
        pixels = cv2.LUT(pixels, self.gamma_table)
        self.off_screen_canvas.SetImage(Image.fromarray(pixels))
        self.matrix.SwapOnVSync(self.off_screen_canvas)
    
    def clear(self):
        self.matrix.Clear()
