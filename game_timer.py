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
import hashlib
from detect_drive import detect_usb_drives, copy_drive, mount_drive, unmount_drive
from SoundFileParser import SoundFileParser
from play_sounds2 import SoundPlayer
import random

# Logging configuration - switch between 'file' and 'journalctl'
LOGGING_MODE = 'journalctl'  # Change to 'file' to use file-based logging

# Audio behavior: when True, stop (cut off) the ending sound exactly when the timer ends.
# When False, allow the ending sound to continue playing after "time up".
CUTOFF_END_SOUND_AT_TIMER_END = True

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
        self.loadedSounds = dict()
        base_dir = "sounds"
        soundFileParser = SoundFileParser(base_dir)
        self.default_game_title = soundFileParser.get_game_title()
        self.default_sound_dirs = soundFileParser.get_sound_dict()
        self.sound_dir_key = "s"
        self.bank_selected = False
        
        # Check for persistent game on startup
        self.check_for_persistent_game()
        
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

        if self.gameLoaded:
            self.tracker.setGame(self.activeGame)
        else:
            self.tracker.setGame(self.default_game_title)
        self.active_sound_dir = None


        #initialize led strips
        self.ringPixels = LEDStrip(start_pixel=0, length=num_pixels_ring, gpio=pixel_pin, num_pixels_total=num_pixels_ring+num_pixels_strip)
        self.stripPixels = LEDStrip(start_pixel=num_pixels_ring, length=num_pixels_strip)
        
        #initialize audio player
        #self.audio_player = AudioPlayer("audio", logger)
        self.initialize_pygame()
        self.log_audio_tree()

    def check_for_persistent_game(self):
        """Check if there's a valid game already loaded in temp directory"""
        try:
            temp_parser = SoundFileParser("temp")
            temp_game = temp_parser.get_game_title()
            temp_sound_dirs = temp_parser.get_sound_dict()
            
            # Check if temp directory has a valid game
            if temp_game and temp_sound_dirs and any(temp_sound_dirs[k][0] for k in temp_sound_dirs):
                self.gameLoaded = True
                self.loadedSounds = temp_sound_dirs
                self.activeGame = temp_game
                print(f"Found persistent game: {temp_game}")
            else:
                print("No persistent game found, using defaults")
                self.gameLoaded = False
                self.loadedSounds = dict()
                self.activeGame = None
        except Exception as e:
            print(f"Error checking for persistent game: {e}")
            self.gameLoaded = False
            self.loadedSounds = dict()
            self.activeGame = None

    def update_audio_directory(self, key):
        self.sound_dir_key = key
        
        # Always prioritize loaded games over defaults
        if self.gameLoaded and self.loadedSounds:
            sounds, sound_dir = self.loadedSounds[key]
            if self.active_sound_dir != sound_dir:
                self.logger.info(f"active sound_dir -> {sound_dir} (source=loaded, bank={key})")
                self.active_sound_dir = sound_dir
            self.player = SoundPlayer(sounds, sound_dir, cutoff_end_sound=CUTOFF_END_SOUND_AT_TIMER_END)
            self.player.select_first_sound()
            self.tracker.setSoundFile(key, self.player.get_current_sound())
        else:
            # Use defaults only if no game is loaded
            sounds, sound_dir = self.default_sound_dirs[key]
            if self.active_sound_dir != sound_dir:
                self.logger.info(f"active sound_dir -> {sound_dir} (source=defaults, bank={key})")
                self.active_sound_dir = sound_dir
            self.player = SoundPlayer(sounds, sound_dir, cutoff_end_sound=CUTOFF_END_SOUND_AT_TIMER_END)
            self.player.select_first_sound()
            self.tracker.setSoundFile(key, self.player.get_current_sound())
        self.bank_selected = True
    
    def update_current_sound(self):
        if self.gameLoaded and self.loadedSounds:
            sounds, sound_dir = self.loadedSounds[self.sound_dir_key]
            source = "loaded"
        else:
            sounds, sound_dir = self.default_sound_dirs[self.sound_dir_key]
            source = "defaults"

        if self.active_sound_dir != sound_dir or not hasattr(self, 'player') or self.player is None:
            self.logger.info(f"active sound_dir -> {sound_dir} (source={source}, bank={self.sound_dir_key})")
            self.active_sound_dir = sound_dir
            self.player = SoundPlayer(sounds, sound_dir, cutoff_end_sound=CUTOFF_END_SOUND_AT_TIMER_END)
            self.player.select_first_sound()
        else:
            self.player.select_next_sound()

        self.tracker.setSoundFile(self.sound_dir_key, self.player.get_current_sound())
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
                    if self.sound_dir_key == 's' and self.bank_selected:
                        self.update_current_sound()
                    else:
                        self.update_audio_directory('s')
                    self.tracker.set_total_time(60)
                elif index + 1 == 2:

                    if self.sound_dir_key == 'n' and self.bank_selected:
                        self.update_current_sound()
                    else:
                        self.update_audio_directory('n')
                    print("2")
                    self.tracker.set_total_time(90)
                elif index + 1 == 3:
                    print("3")
                    self.tracker.set_total_time(random.randint(60, 120))
                    if self.sound_dir_key == 'r' and self.bank_selected:
                        self.update_current_sound()
                    else:
                        self.update_audio_directory('r')
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
                    # Drive removed - keep using loaded game, don't revert
                    self.drive = False
                    self.tracker.setDrive(self.drive)
                    print("drive removed but keeping loaded game")
                    # Don't revert to default - keep gameLoaded as is
                else:
                    # Drive still present - do nothing
                    pass
            else:
                if drive_address:
                    # New drive detected - load game
                    self.drive = True
                    self.tracker.setDrive(self.drive)
                    mount_point = mount_drive(drive_address)
                    print(f"drive detected at {drive_address}, mounted at {mount_point}")

                    def _should_skip_hash_item(name):
                        if name.startswith('.') or name.endswith(('.tmp', '~')):
                            return True
                        lowered = name.lower()
                        return lowered in {"desktop.ini", "thumbs.db"} or name == "System Volume Information"

                    def _compute_usb_content_sha256(root_dir):
                        h = hashlib.sha256()
                        for current_root, dirs, files in os.walk(root_dir):
                            dirs[:] = sorted([d for d in dirs if not _should_skip_hash_item(d)])
                            for filename in sorted(files):
                                if _should_skip_hash_item(filename):
                                    continue
                                full_path = os.path.join(current_root, filename)
                                rel_path = os.path.relpath(full_path, root_dir)
                                h.update(rel_path.encode('utf-8', errors='ignore'))
                                with open(full_path, 'rb') as f:
                                    while True:
                                        chunk = f.read(1024 * 64)
                                        if not chunk:
                                            break
                                        h.update(chunk)
                        return h.hexdigest()

                    soundFileParser = SoundFileParser(mount_point)
                    usb_game_title = soundFileParser.get_game_title()
                    sound_dirs = soundFileParser.get_sound_dict()

                    has_sounds = any(sound_dirs[k][0] for k in sound_dirs)

                    usb_hash = None
                    try:
                        usb_hash = _compute_usb_content_sha256(mount_point)
                        print(f"usb content sha256: {usb_hash[:8] if usb_hash else 'None'}")
                    except Exception as e:
                        print(f"Error computing usb hash: {e}")
                        # Continue without hash comparison - will copy based on title only

                    unmount_drive(mount_point)
                    print(usb_game_title)
                    print(sound_dirs)

                    if usb_game_title and has_sounds:
                        # Check if we have valid sound files (not just empty entries)
                        valid_sounds = {}
                        for key, sounds in sound_dirs.items():
                            sound_dict = sounds[0]  # Get the sound dictionary
                            # Filter out entries with missing M files
                            valid_entries = {k: v for k, v in sound_dict.items() if v[1]}  # v[1] is the M file
                            if valid_entries:
                                valid_sounds[key] = (valid_entries, sounds[1])
                        
                        if not valid_sounds:
                            print("No valid sound files found (all missing M files)")
                            unmount_drive(mount_point)
                            return
                        
                        temp_parser_before = SoundFileParser("temp")
                        temp_game_before = temp_parser_before.get_game_title()
                        temp_hash_path = os.path.join("temp", ".usb_content_sha256")
                        temp_hash_before = None
                        try:
                            with open(temp_hash_path, 'r') as f:
                                temp_hash_before = f.read().strip() or None
                        except Exception:
                            temp_hash_before = None

                        needs_copy = False
                        if temp_game_before != usb_game_title:
                            needs_copy = True
                            print(f"Game title changed: {temp_game_before} -> {usb_game_title}")
                        if usb_hash and temp_hash_before and usb_hash != temp_hash_before:
                            needs_copy = True
                            print(f"Content hash changed: {temp_hash_before[:8]} -> {usb_hash[:8]}")
                        
                        # Only copy if we don't have a matching hash
                        if needs_copy:
                            print("copying game")
                            copy_drive(drive_address, "temp", overwrite=True)

                            if usb_hash:
                                try:
                                    with open(temp_hash_path, 'w') as f:
                                        f.write(usb_hash)
                                    print(f"Saved hash: {usb_hash[:8]}")
                                except Exception as e:
                                    print(f"Error writing usb hash: {e}")
                        else:
                            print("game already loaded (same hash)")

                        temp_parser = SoundFileParser("temp")
                        tempGame = temp_parser.get_game_title()
                        self.gameLoaded = True
                        self.loadedSounds = temp_parser.get_sound_dict()
                        self.tracker.setGameLoaded(self.gameLoaded)
                        self.tracker.setGame(tempGame)
                        print(f"Game loaded: {tempGame}")
                        self.bank_selected = False
                        self.active_sound_dir = None


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
                self.player.select_next_sound()
                self.tracker.setSoundFile(self.sound_dir_key, self.player.get_current_sound())
                
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
        if hasattr(self, 'player') and self.player:
            self.player.stop()
        #self.audio_player.stop_hardware_test()
        self.oled_display.clear_display()

    def log_audio_tree(self):
        roots = ["sounds"]
        try:
            if os.path.isdir("temp"):
                roots.append("temp")
        except Exception:
            pass
        for root in roots:
            try:
                self.logger.info(f"audio tree root: {root}")
                for current_root, dirs, files in os.walk(root):
                    dirs[:] = sorted(dirs)
                    files = sorted(files)
                    rel = os.path.relpath(current_root, root)
                    depth = 0 if rel == '.' else rel.count(os.sep) + 1
                    prefix = '  ' * depth
                    name = root if depth == 0 else os.path.basename(current_root)
                    self.logger.info(f"{prefix}{name}/")
                    for f in files:
                        if f.startswith('.'):
                            continue
                        self.logger.info(f"{prefix}  {f}")
            except Exception as e:
                self.logger.info(f"error walking {root}: {e}")

    def initialize_pygame(self):
        pygame.init()
        pygame.mixer.init()
        print("Pygame initialized")


def setup_logging():
    global LOGGING_MODE
    
    if LOGGING_MODE == 'journalctl':
        return setup_journalctl_logging()
    else:
        return setup_file_logging()

def setup_journalctl_logging():
    """Setup logging to systemd journal (journalctl)"""
    try:
        import systemd.journal
        # Create a logger that writes to systemd journal
        logger = logging.getLogger('game_timer')
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add systemd journal handler
        handler = systemd.journal.JournalHandler(SYSLOG_IDENTIFIER='game_timer')
        handler.setLevel(logging.INFO)
        
        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(handler)
        
        print("Logging configured for journalctl - view with: journalctl -f -t game_timer")
        return logger
        
    except ImportError:
        print("Warning: systemd.journal not available, falling back to file logging")
        global LOGGING_MODE
        LOGGING_MODE = 'file'
        return setup_file_logging()

def setup_file_logging():
    """Setup traditional file-based logging"""
    log_directory = "logs"
    log_filename = "my_app.log"
    # Create log directory if it does not exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    full_log_path = os.path.join(log_directory, log_filename)

    # Create a logger object
    logger = logging.getLogger('game_timer')
    logger.setLevel(logging.INFO)  # Set the logging level
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
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
    
    print("Logging configured for file output - view logs in: logs/my_app.log")
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
        sys.stderr = StreamToLogger(logger, logging.ERROR)
        sys.stdout = StreamToLogger(logger, logging.INFO)
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