import neopixel
import board
import threading
from threading import Lock
import time
import random

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
#ORDER = neopixel.GRB
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

pixel_pin = board.D18

class LEDStrip:
    _lock = threading.Lock()
    _shared_strip = None
    _num_pixels_total = 0

    def __init__(self, start_pixel, length, gpio=None, num_pixels_total=None):
        self.start_pixel = start_pixel
        self.length = length
        self.order = ORDER
        self.j = 0

        with LEDStrip._lock:
            if LEDStrip._shared_strip is None and gpio is not None and num_pixels_total is not None:
                LEDStrip._num_pixels_total = num_pixels_total
                LEDStrip._shared_strip = neopixel.NeoPixel(gpio, num_pixels_total, brightness=0.2, auto_write=False, pixel_order=self.order)

        self.thread = None
        self.running = False

    def fill(self, r, g, b, show=False):
        for i in range(self.start_pixel, self.start_pixel + self.length):
            LEDStrip._shared_strip[i] = (r, g, b)

        if show:
            self.show()

    def show(self):
        with LEDStrip._lock:
            LEDStrip._shared_strip.show()

    def off(self):
        self.fill(0, 0, 0, True)

    def setState(self, state):
        self.state = state
        self.update = 1
   
    def rainbow_cycle_update(self):
        indices = ""
        for i in range(self.length):
            pixel_index = (((self.start_pixel + i) * 256 // self.length) + self.j) % 256 
            #indices += str(pixel_index) + " "
            LEDStrip._shared_strip[self.start_pixel + i] = wheel(pixel_index & 255, self.order)
        #print(indices)
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


if __name__ == "__main__":
    ringPixels = LEDStrip(start_pixel=0, length=16, gpio=pixel_pin, num_pixels_total=32)
    stripPixels = LEDStrip(start_pixel=16, length=16)
    i = 0
    while(True):
        if(i%10==0):
            print(i)
        ringPixels.off()
        for i in range(0,255):
            ringPixels.rainbow_cycle_update()  # rainbow cycle with 1ms delay per step
            stripPixels.rainbow_cycle_update()  # rainbow cycle with 1ms delay per step
            time.sleep(0.01)

        i+=1

