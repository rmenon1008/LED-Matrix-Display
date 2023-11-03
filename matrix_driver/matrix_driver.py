import spidev

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
