from neopixel import NeoPixel, RGB, GRB

def wheel(pos, ORDER):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (RGB, GRB) else (r, g, b, 0)


class LEDStrip:
    def __init__(self, order, num_pixels, gpio):
        self.strip = NeoPixel(gpio, num_pixels, brightness=0.2, auto_write=False, pixel_order=order)
        self.j = 0
        self.order = order
        self.num_pixels = num_pixels

    def fill(self, r,g,b, show = False):
        self.strip.fill((r,g,b))
        if show:
            self.show()

    def show(self):
        self.strip.show()

    def setState(self, state):
        self.state = state
        self.update = 1
    
    def rainbow_cycle(self):
        for i in range(self.num_pixels):
            pixel_index = (i * 256 // self.num_pixels) + self.j
            self.strip[i] = wheel(pixel_index & 255, self.order)
        self.show()
        self.j += 1