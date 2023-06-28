from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import time

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

    def set_pixels(self, pixels):
        self.off_screen_canvas.SetImage(Image.fromarray(pixels))
        self.matrix.SwapOnVSync(self.off_screen_canvas)
    
    def clear(self):
        self.matrix.Clear()
