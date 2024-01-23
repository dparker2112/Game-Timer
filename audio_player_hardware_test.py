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

    def _get_random_segment(self, file_path, length):
        audio = AudioSegment.from_wav(file_path)
        if len(audio) <= length * 1000:
            return audio
        start = random.randint(0, len(audio) - length * 1000)
        return audio[start:start + length * 1000]

    def play_random_segment(self, length):
        if not self.file_list:
            print("No WAV files found in the folder.")
            return
        
        audio_file = random.choice(self.file_list)

        file_path = os.path.join(self.folder_path, audio_file)
        segment = self._get_random_segment(file_path, length)
        print(f"playing {audio_file} for {str(length)}s")
        playback_io = BytesIO()
        segment.export(playback_io, format="wav")
        playback_io.seek(0)

        pygame.mixer.music.load(playback_io)
        pygame.mixer.music.play()

    def stop(self):
        pygame.mixer.music.stop()

# Usage example
# audio_player = AudioPlayer("path_to_your_folder")
# audio_player.play_random_segment()
audio_player = AudioPlayer("audio")
# Usage
audio_player = AudioPlayer("audio")
def getRandomTime():
    return random.randint(10,40)

for i in range(0,15):
    playTime = getRandomTime()
    audio_player.play_random_segment(playTime)
    # To stop the playback
    time.sleep(playTime)
    audio_player.stop()