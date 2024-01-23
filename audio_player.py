import pygame
import random
import os
from pydub import AudioSegment
from io import BytesIO
import time

class AudioPlayer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.file_list = [file for file in os.listdir(folder_path) if file.endswith('.wav')]
        pygame.mixer.init()
        pygame.mixer.init(buffer=512)  # Try different values like 2048, 4096, etc.


    def _get_random_segment(self, file_path, length):
        """Get a random 60-second segment from the audio file."""
        audio = AudioSegment.from_wav(file_path)
        if len(audio) <= length * 1000:
            return audio
        start = random.randint(0, len(audio) - length * 1000)
        return audio[start:start + 60 * 1000]

    def play_random_segment(self, length):
        """Play a random 60-second segment from a random file."""
        if not self.file_list:
            print("No WAV files found in the folder.")
            return

        audio_file = random.choice(self.file_list)
        file_path = os.path.join(self.folder_path, audio_file)
        print(f"playing {audio_file} for {str(length)}s")
        #segment = self._get_random_segment(file_path, length)
        #playback_io = BytesIO()
        #segment.export(playback_io, format="wav")
        #playback_io.seek(0)

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

    def stop(self):
        """Stop the currently playing audio."""
        pygame.mixer.music.stop()
    
    def hardwareTest(self):
        playTime = getRandomTime()
        audio_player.play_random_segment(playTime)
        # To stop the playback
        time.sleep(playTime)
        audio_player.stop()
        

#ace of base...
    
def getRandomTime():
    return random.randint(10,40)

# Usage
audio_player = AudioPlayer("audio")
for i in range(0,15):
    playTime = getRandomTime()
    audio_player.play_random_segment(playTime)
    # To stop the playback
    time.sleep(playTime)
    audio_player.stop()
