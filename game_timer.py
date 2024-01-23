import logging
import traceback
import time
from data_tracker import DataTracker as Tracker
import RPi.GPIO as GPIO
from datetime import datetime
#from neopixels import test_pixels
from button import Button
from encoder import Encoder
from oled import OLED_Display
from led_strip2 import LEDStrip
from data_tracker import DataTracker
import board
import pygame
#pins for buttons
button_pins = [2, 3, 4, 17, 27]

#pins for encoder
rotary_clk = 22   # Rotary Encoder Clock
rotary_dt = 5    # Rotary Encoder Data
rotary_bt = 6    # Rotary Encoder Button

#led strips
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18


# The number of NeoPixels
num_pixels_ring = 24
num_pixels_strip = 24

class GameTimer:
    def __init__(self):
        #initialize pins
        for pin in button_pins:
            Button(pin, self.button_callback)
        #initialize encoder
        Encoder(rotary_clk, rotary_dt, self.on_rotary_change,button_pin=rotary_bt, button_callback=self.encoder_button_pressed)
        
        #initialize display
        self.oled_display = OLED_Display()

        # Initialize Tracker class
        self.tracker = DataTracker(button_pins)

        #initialize led strips
        self.ringPixels = LEDStrip(start_pixel=0, length=16, gpio=pixel_pin, num_pixels_total=32)
        self.stripPixels = LEDStrip(start_pixel=16, length=16)

    def button_callback(self, channel):
        print(f"Button {channel} pressed")
        self.tracker.increment_button_counter(channel)

    def on_rotary_change(self, value):
        print(value)
        #send the new encoder position to the data tracker
        self.tracker.update_encoder_position(value)

    def encoder_button_pressed(self, pin):
        print(f"Encoder button on pin {pin} pressed")
        self.tracker.increment_encoder_counter()
   
    def test(self):
        self.stripPixels.start_rainbow_cycle()
        self.ringPixels.start_rainbow_cycle()
        count = 0
        count2 = 0
        while True:
            if(self.tracker.updateReady()):
                print("updating display")
                self.oled_display.display_status(self.tracker.get_status())
            if(count >= 100):
                count2+=100
                print(f"running {count2/10}s")
                count = 0
                self.tracker.increment_large_counter()
            count+=1
            time.sleep(0.1)
            #self.oled_display.draw_multiple_texts()
    
    def stop(self):
        print("cleaning up")
        self.stripPixels.stop_rainbow_cycle()
        self.ringPixels.stop_rainbow_cycle()
        self.stripPixels.off()
        self.ringPixels.off()


def main():
    try:
        game_timer = GameTimer()
        game_timer.test()
    except KeyboardInterrupt:
        game_timer.stop()
        GPIO.cleanup()
    except Exception as e:
        game_timer.stop()
        print("An error occurred:")
        traceback.print_exc()  # This prints details of the exception
        GPIO.cleanup()


if __name__ == "__main__":
    main()