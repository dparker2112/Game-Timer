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

pixel_pin = board.D21

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
    
    def theater_chase_update(self):
        """Create a theater chase effect on the LED strip using a wheel for color."""
        # Advance the pattern by one step
        self.j = (self.j + 1) % 256  # Ensure j cycles through 0-255 for color wheel

        for i in range(self.length):
            pixel_index = self.start_pixel + i
            if (i + self.j) % 3 == 0:  # Only modify every third pixel based on the current step
                LEDStrip._shared_strip[pixel_index] = wheel((i+self.j) % 256, self.order)
            else:
                LEDStrip._shared_strip[pixel_index] = (0, 0, 0)
            # Pixels not being explicitly set here will retain their state, 
            # creating a continuous "chase" without turning off LEDs

        self.show()
    
    def game_over_update(self, progress):
        # Divide the progress into 6 segments (3 on, 3 off for blinking)
        segment = progress // (300 / 6)

        # Determine if the LEDs should be on or off based on the current segment
        # Segments 0, 2, 4 correspond to LEDs on; 1, 3, 5 correspond to LEDs off
        leds_on = segment % 2 == 0

        color = (255, 0, 0) if leds_on else (0, 0, 0)

        for i in range(self.length):
            pixel_index = self.start_pixel + i
            LEDStrip._shared_strip[pixel_index] = color

        self.show()

    
    def _rainbow_cycle_thread(self):
        self.thread_active = True
        self.j = random.randint(0,255)
        while(self.running):
            for i in range(0,255):
                if not self.running:
                    return
                self.rainbow_cycle_update()  # rainbow cycle with 1ms delay per step
                time.sleep(0.01)
    
    def _theater_chase_thread(self, length):
        initial_delay = 0.4  # Starting delay
        default_delay = 0.2
        min_delay = 0.1     # Minimum delay
        total_steps = 100    # Defines how granular the acceleration will be

        self.thread_active = True
        self.j = random.randint(0, 255)

        if length is not None:
            # The total time the animation should take
            total_animation_time = length  # Length is expected to be in seconds

            # Assuming the animation smoothly accelerates, average delay is (initial_delay + min_delay) / 2
            average_delay = (initial_delay + min_delay) / 2

            # Estimate the total number of steps/actions within the total animation time
            estimated_total_steps = total_animation_time / average_delay

            # Calculate how much to decrease the delay each step to ensure we end with min_delay at the last step
            delay_decrement = (initial_delay - min_delay) / estimated_total_steps
            delay = initial_delay
        else:
            # If no length is given, use a fixed delay without decrement
            step_time = initial_delay
            delay_decrement = 0
            delay = initial_delay

        steps_done = 0
        while self.running:
            if not self.pause:
                self.theater_chase_update()
                steps_done += 1
                # Decrease delay to gradually speed up, but not below min_delay
                delay = max(min_delay, delay - delay_decrement)

            time.sleep(delay)
        self.thread_active = False

    def _game_over_thread(self):
        self.thread_active = True
        self.j = random.randint(0,255)
        progress = 0
        while progress < 300 and self.running:
            self.game_over_update(progress)  # rainbow cycle with 1ms delay per step
            progress += 1
            time.sleep(0.02)
        self.thread_active = False
        if(self.running):
            self.thread = None
            self.start_rainbow_cycle()

    def start_theater_chase(self,length = None):
        self.running = True
        self.pause = False
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=lambda: self._theater_chase_thread(length))
            self.thread.start()

        

    def pause_theater_chase(self):
        self.pause = True
    
    def resume_theater_chase(self):
        self.pause = False



    def start_rainbow_cycle(self):
        self.running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._rainbow_cycle_thread)
            self.thread.start()

    def start_game_over_pattern(self):
        self.running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._game_over_thread)
            self.thread.start()


    def stop_current_pattern(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None


if __name__ == "__main__":
    ringPixels = LEDStrip(start_pixel=0, length=16, gpio=pixel_pin, num_pixels_total=32)
    stripPixels = LEDStrip(start_pixel=16, length=16)
    i = 0
    ringPixels.start_rainbow_cycle()
    stripPixels.start_game_over_pattern()
    try:
        while(True):
            if(i%10==0):
                print(i)
                time.sleep(5)
            i+=1
    except KeyboardInterrupt:
        ringPixels.stop_current_pattern()
        stripPixels.stop_current_pattern()
        ringPixels.off()
        stripPixels.off()


