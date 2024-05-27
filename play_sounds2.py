import os
import random
import time
import threading
import queue
import vlc
from SoundFileParser import SoundFileParser

class SoundPlayer():
    def __init__(self, sounds, sound_dir):
        self.soundPlayerThread = None
        self.sounds = sounds
        self.sound_dir = sound_dir
        self.running = True
        self.paused = False
        self.current_sound = None
        self.runtime = 0
        self.start_time = 0
        self.pause_start_time = 0
        self.total_pause_duration = 0
        self.player = None
        self.loop = False

    def start(self, duration):
        if self.soundPlayerThread is None:
            self.duration = duration
            self.soundPlayerThread = threading.Thread(target=self.run)
            self.soundPlayerThread.start()
            self.running = True

    def join(self):
        if self.soundPlayerThread:
            self.soundPlayerThread.join()
            self.soundPlayerThread = None

    def run(self):
        sound_files = self.sounds[self.current_sound]
        print(f"Playing main sound: {sound_files[0]}")
        if not self.play_sound(sound_files[0], loop=True):
            print("Error playing main sound")
            return
        main_sound_length = self.duration
        self.start_time = time.time()
        while self.running:
            if self.current_sound:
                elapsed_time = time.time() - self.start_time - self.total_pause_duration
                if elapsed_time < main_sound_length - 2:
                    time.sleep(0.1)
                else:
                    break
        if self.running:
            print("Switching to ending sound.")
            self.player.stop()
            self.play_sound(sound_files[1])
            time.sleep(2)

    def play_sound(self, sound_file, loop=False):
        sound_path = os.path.join(self.sound_dir, sound_file)
        print(f"Loading sound from path: {sound_path}")
        try:
            self.loop = loop
            self.player = vlc.MediaPlayer(sound_path)
            event_manager = self.player.event_manager()
            event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)
            self.player.play()
            return True
        except Exception as e:
            print(f"Error loading sound: {e}")
            return False

    def on_end_reached(self, event):
        if self.loop:
            self.player.stop()
            self.player.play()

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
            self.player.stop()
        print("Stopped")

    def select_random_sound(self):
        if self.sounds:
            self.current_sound = random.choice(list(self.sounds.keys()))
            print(f"Selected sound {self.sounds[self.current_sound][0]}")

    def get_current_sound(self):
        return self.sounds[self.current_sound][0]

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
        player = SoundPlayer(sounds, sound_dir)
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
