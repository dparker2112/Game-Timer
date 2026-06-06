import os
import random
import re
import time
import threading
import queue
import vlc
from SoundFileParser import SoundFileParser

class SoundPlayer():
    def __init__(self, sounds, sound_dir, cutoff_end_sound=True):
        self.soundPlayerThread = None
        self.sounds = sounds
        self.sound_dir = sound_dir
        self.cutoff_end_sound = cutoff_end_sound
        self.running = True
        self.paused = False
        self.current_sound = None
        self.runtime = 0
        self.start_time = 0
        self.pause_start_time = 0
        self.total_pause_duration = 0
        self.player = None
        self.loop = False
        self.ordered_keys = self._build_ordered_keys()

    def _extract_leading_number(self, text):
        try:
            m = re.match(r"^(\d+)", str(text).strip())
            return int(m.group(1)) if m else None
        except Exception:
            return None

    def _build_ordered_keys(self):
        keys = list(self.sounds.keys()) if self.sounds else []
        def key_func(k):
            files = self.sounds[k]
            m_file = files[1] if len(files) > 1 else ''
            if isinstance(k, int):
                return (0, k, str(m_file).lower())
            num = self._extract_leading_number(m_file)
            if num is None:
                num = self._extract_leading_number(k)
            if num is not None:
                return (0, num, str(m_file).lower())
            return (1, str(m_file or k).lower())
        return sorted(keys, key=key_func)

    def start(self, duration):
        if self.soundPlayerThread is None:
            self.paused = False
            self.duration = duration
            self.soundPlayerThread = threading.Thread(target=self.run)
            self.soundPlayerThread.start()
            self.running = True
        else:
            self.stop()
            if self.soundPlayerThread is None:
                self.paused = False
                self.duration = duration
                self.soundPlayerThread = threading.Thread(target=self.run)
                self.soundPlayerThread.start()
                self.running = True
            else:
                print("failed to start audio")

    def join(self):
        self.running = False
        if self.soundPlayerThread:
            self.soundPlayerThread.join()
            self.soundPlayerThread = None

    def run(self):
        sound_files = self.sounds[self.current_sound]
        beginning_sound = sound_files[0]
        main_sound = sound_files[1]
        ending_sound = sound_files[2]

        round_start_time = time.time()
        end_trigger_offset = 2.0
        end_trigger_time = max(0.0, self.duration - end_trigger_offset)

        def _elapsed_active_time():
            return time.time() - round_start_time - self.total_pause_duration

        # Start with beginning sound (if any). It plays immediately while the timer is already running.
        if beginning_sound:
            print(f"Playing beginning sound: {beginning_sound}")
            if self.play_sound_with_duration(beginning_sound) <= 0:
                print("Error playing beginning sound")

        # Start main sound after B finishes (no crossfade).
        # We do not rely on looping for timing; the thread will switch to E at (T - 2s).
        if beginning_sound:
            while self.running and (self.player is not None) and self.player.is_playing():
                if _elapsed_active_time() >= self.duration:
                    break
                time.sleep(0.05)

        if not self.running or _elapsed_active_time() >= self.duration:
            if self.cutoff_end_sound and self.player:
                self.player.stop()
            print("exiting sound thread")
            return

        print(f"Playing main sound: {main_sound}")
        if not self.play_sound(main_sound, loop=False):
            print("Error playing main sound")
            return

        # Wait until it is time to trigger E (T - 2s), accounting for pauses.
        while self.running:
            if _elapsed_active_time() >= self.duration:
                break
            if _elapsed_active_time() >= end_trigger_time:
                break
            time.sleep(0.05)

        if self.running and _elapsed_active_time() < self.duration:
            print("Switching to ending sound.")
            if self.player:
                self.player.stop()
            ending_duration = self.play_sound_with_duration(ending_sound, loop=False)

            # By default, cut off E at the exact end of the timer. If disabled, let E play out.
            if self.cutoff_end_sound:
                while self.running and _elapsed_active_time() < self.duration:
                    time.sleep(0.05)
                if self.player:
                    self.player.stop()
            else:
                if ending_duration > 0:
                    e_start = time.time()
                    while self.running and (time.time() - e_start) < ending_duration:
                        time.sleep(0.05)

        print("exiting sound thread")

    def play_sound_with_duration(self, sound_file, loop=False):
        """Play a sound and return the duration in seconds."""
        sound_path = os.path.join(self.sound_dir, sound_file)
        print(f"Loading sound from path: {sound_path}")
        try:
            # NOTE: Using an EndReached callback to loop can race with track switching
            # (e.g. stopping main and immediately creating a new player for the ending
            # sound). Use VLC's native repeat option for looping instead.
            self.loop = loop
            self.player = vlc.MediaPlayer()

            # Create media and apply repeat option when looping
            media = vlc.Media(sound_path)
            if loop:
                media.add_option("input-repeat=-1")
            self.player.set_media(media)

            # Get media duration
            media.parse()  # Parse to get accurate duration
            duration_ms = media.get_duration()
            duration_sec = duration_ms / 1000.0 if duration_ms > 0 else 0
            
            self.player.play()
            return duration_sec
        except Exception as e:
            print(f"Error loading sound: {e}")
            return 0

    def play_sound(self, sound_file, loop=False):
        """Legacy method for compatibility - calls play_sound_with_duration but ignores duration."""
        self.play_sound_with_duration(sound_file, loop)
        return True

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            self.player.pause()
            self.pause_start_time = time.time()
        else:
            self.total_pause_duration += time.time() - self.pause_start_time
            self.player.play()
        print("Paused" if self.paused else "Unpaused")

    def stop(self):
        self.running = False
        if self.player:
            print("stopping")
            self.player.stop()
        print("stopping")
        self.join()
        print("Stopped")

    def select_random_sound(self):
        if self.sounds:
            self.current_sound = random.choice(list(self.sounds.keys()))
            sound_files = self.sounds[self.current_sound]
            print(f"Selected sound {sound_files[1]} (beginning: {sound_files[0] if sound_files[0] else 'None'}, ending: {sound_files[2]})")

    def select_first_sound(self):
        if self.ordered_keys:
            self.current_sound = self.ordered_keys[0]
            sound_files = self.sounds[self.current_sound]
            print(f"Selected sound {sound_files[1]} (beginning: {sound_files[0] if sound_files[0] else 'None'}, ending: {sound_files[2]})")

    def select_next_sound(self):
        if not self.ordered_keys:
            return
        keys = self.ordered_keys
        if self.current_sound in keys:
            idx = keys.index(self.current_sound)
            next_idx = (idx + 1) % len(keys)
        else:
            next_idx = 0
        self.current_sound = keys[next_idx]
        sound_files = self.sounds[self.current_sound]
        print(f"Selected sound {sound_files[1]} (beginning: {sound_files[0] if sound_files[0] else 'None'}, ending: {sound_files[2]})")

    def get_current_sound(self):
        if self.current_sound is None and self.ordered_keys:
            self.current_sound = self.ordered_keys[0]
        return self.sounds[self.current_sound][1]

def input_thread(input_queue):
    while True:
        input_text = input()
        input_queue.put(input_text)

def main():
    base_dir = "sounds"
    soundFileParser = SoundFileParser(base_dir)
    game_title = soundFileParser.get_game_title()
    sound_dirs = soundFileParser.get_sound_dict()
    print(f"Game Title: {game_title}")
    print(sound_dirs)

    choice = input("Choose a dictionary (r: random, s: short, n: long): ").lower()
    if choice in sound_dirs:
        sounds, sound_dir = sound_dirs[choice]
        print(sound_dir)
        player = SoundPlayer(sounds, sound_dir, cutoff_end_sound=True)
        player.select_random_sound()
        print(player.get_current_sound())
        if choice == 'r':
            player.start(180)
        elif choice == 's':
            player.start(60)
        else:
            player.start(90)

        input_queue = queue.Queue()
        input_handling_thread = threading.Thread(target=input_thread, args=(input_queue,))
        input_handling_thread.daemon = True
        input_handling_thread.start()

        print("Control keys: [i] Play/Pause, [o] Stop, [e] Exit")
        while player.running:
            try:
                command = input_queue.get(timeout=0.1)
                if command == 'i':
                    player.pause()
                elif command == 'o':
                    player.stop()
                    break
                elif command == 'e':
                    player.stop()
                    player.running = False
                    break
            except queue.Empty:
                continue
        print("exiting")
    else:
        print("Invalid choice.")
    print("done")

if __name__ == '__main__':
    main()
