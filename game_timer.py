import logging
import os
import traceback
import time
from data_tracker import DataTracker
import RPi.GPIO as GPIO
#from neopixels import test_pixels
from button import Button
from encoder import Encoder
from oled import OLED_Display
from led_strip2 import LEDStrip
from data_tracker import DataTracker
import board
from audio_player_hardware_test import AudioPlayer
from logging.handlers import RotatingFileHandler
import sys
import signal
from enum import Enum

class GameTimerState(Enum):
    IDLE = 0
    TIMER_START = 1
    COUNTING_DOWN = 2
    WARNING = 3
    TIME_UP = 4

kill_signal = False

#pins for buttons
button_dict = {0: 2,
               1: 3,
               2: 4,
               3: 17,
               4: 27}
button_pins = []
for key in button_dict:
    button_pins.append(button_dict[key])

# Reverse the button_dict to make GPIO pins the keys
reversed_button_dict = {pin: button for button, pin in button_dict.items()}
#print(reversed_button_dict)

#button_pins = [button1_pin, button2_pin, 17, 27]
extra_pins = [0, 1, 14, 15]
#pins for encoder
rotary_clk = 22   # Rotary Encoder Clock
rotary_dt = 5    # Rotary Encoder Data
rotary_bt = 6    # Rotary Encoder Button

#led strips
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D21


# The number of NeoPixels
num_pixels_ring = 16
num_pixels_strip = 18

class GameTimer:
    def __init__(self, logger):
        self.logger = logger
        self.state = GameTimerState.IDLE
        #initialize pins
        self.button_array = []
        self.extra_button_array = []
        self.button_flags = []
        for pin in button_pins:
            self.button_array.append(Button(pin, self.button_callback, self.logger))
            self.button_flags.append(False)
        
        for pin in extra_pins:
            self.extra_button_array.append(Button(pin, self.extra_button_callback, self.logger))
        #initialize encoder
        Encoder(rotary_clk, rotary_dt, self.on_rotary_change,button_pin=rotary_bt, button_callback=self.encoder_button_pressed)
        
        #initialize display
        self.oled_display = OLED_Display()

        # Initialize Tracker class
        self.tracker = DataTracker(logger, button_pins, extra_pins)

        #initialize led strips
        self.ringPixels = LEDStrip(start_pixel=0, length=num_pixels_ring, gpio=pixel_pin, num_pixels_total=num_pixels_ring+num_pixels_strip)
        self.stripPixels = LEDStrip(start_pixel=num_pixels_ring, length=num_pixels_strip)

        #initialize audio player
        self.audio_player = AudioPlayer("audio", logger)
        

    def set_button_flags(self, index):
        #print(f"setting button flag {index}")
        self.button_flags[index] = True
        #print(self.button_flags)

    def button_callback(self, channel):
        self.logger.info(f"Button {channel} pressed")
        self.tracker.increment_button_counter(channel)
        #set the flag
        self.set_button_flags(reversed_button_dict[channel])
        
    
    def extra_button_callback(self, channel):
        self.logger.info(f"Extra GPIO {channel} pressed")
        self.tracker.increment_extra_gpio_counter(channel)

    def on_rotary_change(self, value, direction):
        self.logger.info(value)
        #send the new encoder position to the data tracker
        self.tracker.update_encoder_position(value)
        self.tracker.update_total_time(direction)

    def encoder_button_pressed(self, pin):
        self.logger.info(f"Encoder button on pin {pin} pressed")
        self.tracker.increment_encoder_counter()
        self.tracker.update_increment()
   
    def test(self):
        self.stripPixels.start_rainbow_cycle()
        self.ringPixels.start_rainbow_cycle()
        self.audio_player.start_hardware_test()
        
        count = 0
        count2 = 0
        self.logger.info("starting test")
        while not kill_signal:
            current_button_states = []
            for index in range(len(self.button_array)):
                current_button_states.append(self.button_array[index].get_state())
            self.tracker.update_button_states(current_button_states)
            extra_button_states = []
            for index in range(len(self.extra_button_array)):
                extra_button_states.append(self.extra_button_array[index].get_state())
            self.tracker.update_extra_button_states(extra_button_states)
            self.handle_button_presses()
            #handle counter, and if it is done, print a message
            if(self.tracker.update_countdown()):
                self.logger.info("time has expired")
            if(self.tracker.updateReady()):
                self.logger.info("updating display")
                self.oled_display.display_status(self.tracker.get_status())
            if(count >= 1000):
                count2+=1000
                self.logger.info(f"running {count2/10}s")
                count = 0
                self.tracker.increment_large_counter()
            count+=1
            time.sleep(0.1)

            #self.oled_display.draw_multiple_texts()
        self.logger.info("cleaning up")
        self.stop()
    def handle_button_presses(self):
        for index, value in enumerate(self.button_flags):
            if value:
                self.button_flags[index] = False
                if index + 1 == 1:
                    print("1")
                elif index + 1 == 2:
                    print("2")
                elif index + 1 == 3:
                    print("3")
                elif index + 1 == 4:
                    print("4")
                elif index + 1 == 5:
                    print("5")
                    self.tracker.start_countdown()
                else:
                    self.logger.error("unhandled button press")


    def app(self):
        self.logger.info("starting app")
        while not kill_signal:
            self.handle_button_presses()
            match(self.state):
                case GameTimerState.IDLE:
                    print("idle")
                case GameTimerState.TIMER_START:
                    print("timer start")
                case GameTimerState.COUNTING_DOWN:
                    print("counting down")
                case GameTimerState.WARNING:
                    print("warning")
                case GameTimerState.TIME_UP:
                    print("time up")
                case _:
                    self.logger.error("got to unhandled state")
            
        self.logger.info("cleaning up")
        self.stop()
    
    def stop(self):
        self.logger.info("cleaning up")
        self.stripPixels.stop_rainbow_cycle()
        self.ringPixels.stop_rainbow_cycle()
        self.stripPixels.off()
        self.ringPixels.off()
        self.audio_player.stop_hardware_test()
        self.oled_display.clear_display()


def setup_logging():
    log_directory = "logs"
    log_filename = "my_app.log"
    # Create log directory if it does not exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    full_log_path = os.path.join(log_directory, log_filename)

    # Create a logger object
    logger = logging.getLogger('my_app')
    logger.setLevel(logging.INFO)  # Set the logging level
    
    # Create a handler that writes log messages to a file, with log rotation
    handler = RotatingFileHandler(
        full_log_path, maxBytes=5*1024*1024, backupCount=5
    )

    handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger

def cleanup_logging(logger):
    # Close all handlers
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)

    # Optional: Shutdown logging
    logging.shutdown()

class StreamToLogger:
    """
    Redirects stdout and stderr to logging module.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.recursion_guard = False

    def write(self, message):
        if self.recursion_guard:
            return
        self.recursion_guard = True
        try:
            if message.rstrip() != "":
                self.logger.log(self.level, message.rstrip())
        finally:
            self.recursion_guard = False


    def flush(self):
        # This flush method is needed for compatibility with file-like objects.
        pass

def sigterm_handler(_signo, _stack_frame):
    # Cleanup logic
    print("SIGTERM received, shutting down")
    global kill_signal 
    kill_signal = True

# Register the SIGTERM handler
signal.signal(signal.SIGTERM, sigterm_handler)




def main():
    try:
        logger = setup_logging()
        # Redirect stderr and stdout
        # sys.stderr = StreamToLogger(logger, logging.ERROR)
        # sys.stdout = StreamToLogger(logger, logging.INFO)
        print("This is a test message") 
        game_timer = GameTimer(logger)
        game_timer.test()
    except KeyboardInterrupt:
        logger.info("cleanup")
        game_timer.stop()
        GPIO.cleanup()
    except Exception as e:
        cleanup_logging(logger)
        game_timer.stop()
        logger.exception("An error occurred")
        traceback.print_exc()  # This prints details of the exception
        GPIO.cleanup()


if __name__ == "__main__":
    main()