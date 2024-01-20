import RPi.GPIO as GPIO
import time
from typing import Callable, Optional

rotary_clk = 22   # Rotary Encoder Clock
rotary_dt = 5    # Rotary Encoder Data
rotary_bt = 6

def on_rotary_change(value):
    print(value)

def encoder_button_pressed(pin):
    print(f"Encoder button on pin {pin} pressed")

class Encoder:
    def __init__(self, clk_pin: int, dt_pin: int, value_change_callback: Callable[[int], None], 
                 button_pin: Optional[int] = None, button_callback: Optional[Callable[[int], None]] = None) -> None:
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.button_pin = button_pin
        self.value_change_callback = value_change_callback
        self.counter = 0
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(clk_pin, GPIO.BOTH, callback=self._update)

        self.clkLastState = GPIO.input(clk_pin)

        if self.button_pin is not None and button_callback is not None:
            GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)

    def _update(self, channel: int) -> None:
        clkState = GPIO.input(self.clk_pin)
        dtState = GPIO.input(self.dt_pin)
        if clkState != self.clkLastState:
            if dtState != clkState:
                self.counter += 1
            else:
                self.counter -= 1
            self.value_change_callback(self.counter)
        self.clkLastState = clkState

def init_encoder():
    Encoder(rotary_clk, rotary_dt, on_rotary_change,button_pin=rotary_bt, button_callback=encoder_button_pressed)


def main():
    init_encoder()
    try:
        while True:
            time.sleep(5)
            print("running")
    except KeyboardInterrupt:
        GPIO.cleanup()


if __name__ == "__main__":
    main()