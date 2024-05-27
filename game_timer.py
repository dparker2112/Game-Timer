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
from led_strip import LEDStrip
from data_tracker import DataTracker
import board
from audio_player import AudioPlayer
from logging.handlers import RotatingFileHandler
import sys
import signal
from enum import Enum
import pygame
from detect_drive import detect_usb_drives, copy_drive, mount_drive, unmount_drive
from SoundFileParser import SoundFileParser
from play_sounds2 import SoundPlayer
import random

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
        self.drive = False
        self.gameLoaded = False
        self.activeGame = None
        base_dir = "sounds"
        soundFileParser = SoundFileParser(base_dir)
        self.default_game_title = soundFileParser.get_game_title()
        self.default_sound_dirs = soundFileParser.get_sound_dict()
        self.sound_dir_key = "s"
        
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

        self.tracker.setGame(self.default_game_title)
        self.loadedSounds = dict()


        #initialize led strips
        self.ringPixels = LEDStrip(start_pixel=0, length=num_pixels_ring, gpio=pixel_pin, num_pixels_total=num_pixels_ring+num_pixels_strip)
        self.stripPixels = LEDStrip(start_pixel=num_pixels_ring, length=num_pixels_strip)
        
        self.update_current_sound()
        #initialize audio player
        #self.audio_player = AudioPlayer("audio", logger)
        self.initialize_pygame()

    def update_audio_directory(self, key):
        if self.gameLoaded:
            self.sound_dir_key = key
            sounds, sound_dir = self.loadedSounds[key]
            self.player = SoundPlayer(sounds, sound_dir)
            self.player.select_random_sound()
            self.tracker.setSoundFile(key, self.player.get_current_sound())

        else:
            self.sound_dir_key = key
            sounds, sound_dir = self.default_sound_dirs[key]
            self.player = SoundPlayer(sounds, sound_dir)
            self.player.select_random_sound()
            self.tracker.setSoundFile(key, self.player.get_current_sound())
    
    def update_current_sound(self):
        if self.gameLoaded:
            sounds, sound_dir = self.loadedSounds[self.sound_dir_key]
            self.player = SoundPlayer(sounds, sound_dir)
            self.player.select_random_sound()
            self.tracker.setSoundFile(self.sound_dir_key,self.player.get_current_sound())

        else:
            sounds, sound_dir = self.default_sound_dirs[self.sound_dir_key]
            self.player = SoundPlayer(sounds, sound_dir)
            self.player.select_random_sound()
            self.tracker.setSoundFile(self.sound_dir_key,self.player.get_current_sound())
        print(self.player.get_current_sound())


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
        if self.sound_dir_key != 'r':
            self.update_audio_directory('r')

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
                    if self.sound_dir_key == 's':
                        self.update_current_sound()
                    else:
                        self.update_audio_directory('s')
                    self.tracker.set_total_time(60)
                elif index + 1 == 2:

                    if self.sound_dir_key == 'n':
                        self.update_current_sound()
                    else:
                        self.update_audio_directory('n')
                    print("2")
                    self.tracker.set_total_time(90)
                elif index + 1 == 3:
                    print("3")
                    self.tracker.set_total_time(random.randint(60, 120))
                elif index + 1 == 4:
                    print("4")
                    if self.tracker.countdown_active():
                        self.player.stop()
                        self.stripPixels.stop_current_pattern()
                        self.stripPixels.start_rainbow_cycle()
                        self.ringPixels.stop_current_pattern()
                        self.ringPixels.start_rainbow_cycle()
                        self.tracker.stop_countdown()

                elif index + 1 == 5:
                    print("5")
                    if self.tracker.countdown:
                        if self.tracker.countdown_pause:
                            self.tracker.resume_countdown()
                            self.player.pause()
                            #self.audio_player.resume_countdown_song()
                            self.stripPixels.resume_theater_chase()
                            self.ringPixels.resume_theater_chase()
                            print("resume")
                        else:
                            self.tracker.pause_countdown()
                            self.stripPixels.pause_theater_chase()
                            self.ringPixels.pause_theater_chase()
                            self.player.pause()
                            #self.audio_player.pause_countdown_song()
                            print("pause")
                    else:
                        self.tracker.start_countdown()
                        self.stripPixels.stop_current_pattern()
                        self.ringPixels.stop_current_pattern()
                        print(self.tracker.countdown_time)
                        print("start")
                        self.stripPixels.start_theater_chase(self.tracker.countdown_time)
                        self.ringPixels.start_theater_chase(self.tracker.countdown_time)
                        print("started")
                        self.player.start(self.tracker.countdown_time)
                        #self.audio_player.play_countdown_song()
                        
                else:
                    self.logger.error("unhandled button press")

    def manage_sound_files(self):
        if not self.tracker.countdown_active():
            self.base_dir = "sounds"
            drive_address = detect_usb_drives()
            if self.drive:
                if drive_address == None:
                    self.base_dir = "sounds"
                    self.drive = False
                    self.tracker.setDrive(self.drive)
                    print("drive removed")
                    self.tracker.setGame(self.default_game_title)
                    self.gameLoaded = False
                    self.tracker.setGameLoaded(self.gameLoaded)
            else:
                if drive_address:
                    self.drive = True
                    self.tracker.setDrive(self.drive)
                    mount_point = mount_drive(drive_address)
                    print(f"drive detected at {drive_address}, mounted at {mount_point}")
                    soundFileParser = SoundFileParser(mount_point)
                    usb_game_title = soundFileParser.get_game_title()
                    sound_dirs = soundFileParser.get_sound_dict()

                    unmount_drive(mount_point)
                    print(usb_game_title)
                    print(sound_dirs)

                    if usb_game_title and len(sound_dirs.keys()) > 0:
                        soundFileParser = SoundFileParser("temp")
                        tempGame = soundFileParser.get_game_title()
                        if tempGame != usb_game_title:
                            print("copying game")
                            copy_drive(drive_address, "temp", overwrite=True)

                        else:
                            print("game already copied")
                        self.gameLoaded = True
                        self.loadedSounds = soundFileParser.get_sound_dict()
                        self.tracker.setGameLoaded(self.gameLoaded)
                        self.tracker.setGame(tempGame)


    def app(self):
        self.stripPixels.start_rainbow_cycle()
        self.ringPixels.start_rainbow_cycle()
        #self.audio_player.start_hardware_test()
        count = 0
        count2 = 0
        self.logger.info("starting test")
        while not kill_signal:
            self.manage_sound_files()
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
                #self.audio_player.start_countdown_end_song()
                self.stripPixels.stop_current_pattern()
                self.stripPixels.start_game_over_pattern()
                self.ringPixels.stop_current_pattern()
                self.ringPixels.start_game_over_pattern()
                
            if(self.tracker.updateReady()):
                #self.logger.info("updating display")
                self.oled_display.display_app(self.tracker.get_status())
            time.sleep(0.02)

            #self.oled_display.draw_multiple_texts()
        self.logger.info("cleaning up")
        self.stop()

    def stop(self):
        self.logger.info("cleaning up")
        self.stripPixels.stop_current_pattern()
        self.ringPixels.stop_current_pattern()
        self.stripPixels.off()
        self.ringPixels.off()
        self.player.stop()
        #self.audio_player.stop_hardware_test()
        self.oled_display.clear_display()

    def initialize_pygame(self):
        pygame.init()
        pygame.mixer.init()
        print("Pygame initialized")


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
        #game_timer.test()
        game_timer.app()
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