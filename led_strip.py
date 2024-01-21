import neopixel
import threading
from threading import Lock
import time
import random

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

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
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


class LEDStrip:
    _lock = Lock()
    def __init__(self, num_pixels, gpio):
        self.strip = neopixel.NeoPixel(gpio, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER)
        self.j = 0
        self.order = ORDER
        self.num_pixels = num_pixels
        self.thread = None
        self.running = False

    def fill(self, r,g,b, show = False):
        self.strip.fill((r,g,b))
        if show:
            self.show()

    def show(self):
        with LEDStrip._lock:
            self.strip.show()
    
    def off(self):
        self.fill((0,0,0), True)

    def setState(self, state):
        self.state = state
        self.update = 1
    
    def rainbow_cycle_update(self):
        for i in range(self.num_pixels):
            pixel_index = (i * 256 // self.num_pixels) + self.j
            self.strip[i] = wheel(pixel_index & 255, self.order)
        self.show()
        self.j += 1
    
    def _rainbow_cycle_thread(self):
        self.thread_active = True
        self.j = random.randint(0,255)
        while(self.running):
            for i in range(0,255):
                self.rainbow_cycle_update()  # rainbow cycle with 1ms delay per step
                time.sleep(0.01)

    def start_rainbow_cycle(self):
        self.running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._rainbow_cycle_thread)
            self.thread.start()

    def stop_rainbow_cycle(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
