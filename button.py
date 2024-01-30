import RPi.GPIO as GPIO
import time
from typing import Callable, Optional
# Pin Definitions
button1_pin = 2  # Button 1
button2_pin = 3  # Button 2
button3_pin = 4  # Button 3
button4_pin = 17  # Button 4
button5_big_pin = 27  # Button 5 (big)


# Variables for rotary encoder
counter = 0
clkLastState = 0

class Button:
    def __init__(self, pin: int, callback: Callable[[int], None]) -> None:
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=callback, bouncetime=400)


def button_callback(channel):
    print(f"Button {channel} pressed")


def init_gpio():
    # # GPIO Setup
    # GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
    # GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(button3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(button4_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(button5_big_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(rotary_bt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(rotary_clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.setup(rotary_dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # # Interrupt Setup
    # GPIO.add_event_detect(button1_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
    # GPIO.add_event_detect(button2_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
    # GPIO.add_event_detect(button3_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
    # GPIO.add_event_detect(button4_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
    # GPIO.add_event_detect(button5_big_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
    # GPIO.add_event_detect(rotary_bt, GPIO.FALLING, callback=button_callback, bouncetime=200)
    # GPIO.add_event_detect(rotary_clk, GPIO.BOTH, callback=rotary_encoder_callback)
    Button(button1_pin, button_callback)
    Button(button2_pin, button_callback)
    Button(button3_pin, button_callback)
    Button(button4_pin, button_callback)
    Button(button5_big_pin, button_callback)
    #Encoder(rotary_clk, rotary_dt, on_rotary_change)


def main():
    init_gpio()
    try:
        while True:
            time.sleep(5)
            print("running")
    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == "__main__":
    main()