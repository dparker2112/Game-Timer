import RPi.GPIO as GPIO
import time

# Pin Definitions
button1_pin = 2  # Button 1
button2_pin = 3  # Button 2
button3_pin = 4  # Button 2
button4_pin = 17  # Button 2
#button2_pin = 3  # Button 2
rotary_clk = 22   # Rotary Encoder Clock
rotary_dt = 5    # Rotary Encoder Data
rotary_bt = 6
# Variables for rotary encoder
counter = 0
clkLastState = 0

def button_callback(channel):
    print(f"Button {channel} pressed")

def rotary_encoder_callback(channel):
    global counter, clkLastState
    clkState = GPIO.input(rotary_clk)
    dtState = GPIO.input(rotary_dt)
    if clkState != clkLastState:
        if dtState != clkState:
            counter += 1
        else:
            counter -= 1
        print(f"Rotary Count: {counter}")
    clkLastState = clkState

# GPIO Setup
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button4_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rotary_bt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rotary_clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rotary_dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Interrupt Setup
GPIO.add_event_detect(button1_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
GPIO.add_event_detect(button2_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
GPIO.add_event_detect(button3_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
GPIO.add_event_detect(button4_pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
GPIO.add_event_detect(rotary_bt, GPIO.FALLING, callback=button_callback, bouncetime=200)
GPIO.add_event_detect(rotary_clk, GPIO.BOTH, callback=rotary_encoder_callback)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
