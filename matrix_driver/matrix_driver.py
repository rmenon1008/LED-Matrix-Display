from rgbmatrix import RGBMatrix, RGBMatrixOptions

class Matrix:
    def __init__(self, dimensions):
        print("Initializing {}x{} matrix".format(dimensions[0], dimensions[1]))
        options = RGBMatrixOptions()
        options.rows = dimensions[1]
        options.cols = dimensions[0]
        options.chain_length = 1
        options.parallel = 1
        options.row_address_type = 0
        options.multiplexing = 0
        options.pwm_bits = 11
        options.brightness = 100
        options.pwm_lsb_nanoseconds = 130
        options.led_rgb_sequence = "RGB"
        options.pixel_mapper_config = ""
        options.panel_type = ""
        options.gpio_slowdown = 4
        options.disable_hardware_pulsing = False

        self.matrix = RGBMatrix(options=options)

    def set_pixels(self, pixels):
        self.matrix.SetImage(pixels, 0, 0)
    
    def clear(self):
        self.matrix.Clear()
