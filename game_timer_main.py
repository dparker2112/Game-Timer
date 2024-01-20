import logging
import traceback
import time
from data_tracker import DataTracker as Tracker
import RPi.GPIO as GPIO
from datetime import datetime
from neopixels import test_pixels
from button import Button
from encoder import Encoder

now = datetime.now()
dt_string = "/home/GameTimerUser/Game-Timer/log/log-startTime-"+now.strftime("%d-%m-%Y--%H-%M")+".log"
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.

### pin definitions
button1_pin = 2  # Button 1
button2_pin = 3  # Button 2
button3_pin = 4  # Button 3
button4_pin = 17  # Button 4
button5_big_pin = 27  # Button 5 (big)
rotary_clk = 22   # Rotary Encoder Clock
rotary_dt = 5    # Rotary Encoder Data
rotary_bt = 6    # Rotary Encoder Button



def button_callback(channel):
    print(f"Button {channel} pressed")

def on_rotary_change(value):
    print(value)

def encoder_button_pressed(pin):
    print(f"Encoder button on pin {pin} pressed")

def init_gpio():
    print("gpio initialized")
    Button(button1_pin, button_callback)
    Button(button2_pin, button_callback)
    Button(button3_pin, button_callback)
    Button(button4_pin, button_callback)
    Button(button5_big_pin, button_callback)
    Encoder(rotary_clk, rotary_dt, on_rotary_change,button_pin=rotary_bt, button_callback=encoder_button_pressed)

#def init_oled():


def main():
    init_gpio()
    # Initialize Tracker
    tracker = Tracker()
    try:
        while True:
            print("running")
            test_pixels()
    except KeyboardInterrupt:
        GPIO.cleanup()
    except Exception as e:
        print("An error occurred:")
        traceback.print_exc()  # This prints details of the exception
        GPIO.cleanup()


if __name__ == "__main__":
    main()