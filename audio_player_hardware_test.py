import pygame
import random
import os
import threading
from pydub import AudioSegment
from io import BytesIO
import time

class AudioPlayer:
    def __init__(self, folder_path, logger):
        self.logger = logger
        self.folder_path = folder_path
        self.file_list = [file for file in os.listdir(folder_path) if file.endswith('.wav')]
        self.reinitialize_mixer()
        self.test_running = False
        self.thread = None

    def _get_audio_info(self, file_path):
        """Get the sample rate, bit depth, and size of the audio file."""
        audio = AudioSegment.from_file(file_path)
        sample_rate = audio.frame_rate
        bit_depth = audio.sample_width * 8  # sample_width is in bytes
        channels = audio.channels
        file_size = os.path.getsize(file_path)  # File size in bytes
        return sample_rate, audio.sample_width, file_size, channels
    
    def _get_random_segment(self, file_path, length):
        audio = AudioSegment.from_wav(file_path)
        if len(audio) <= length * 1000:
            return audio
        start = random.randint(0, len(audio) - length * 1000)
        return audio[start:start + length * 1000]

    def play_random_segment(self, length):
        if not self.file_list:
            self.logger.info("No WAV files found in the folder.")
            return
        
        audio_file = random.choice(self.file_list)
        file_path = os.path.join(self.folder_path, audio_file)
        [sample_rate, sample_width, file_size, channels] = self._get_audio_info(file_path)
        segment_size = sample_rate * sample_width * length * channels
        audio_string = f"sample rate: {sample_rate}, sample_width: {sample_width}, channels: {channels}, segment size: {segment_size}, file size: {file_size}"
        self.reinitialize_mixer()
        
        segment = self._get_random_segment(file_path, length)
        self.logger.info(f"playing {audio_file} for {str(length)}s")
        self.logger.info(audio_string)
        playback_io = BytesIO()
        segment.export(playback_io, format="wav")
        playback_io.seek(0)

        pygame.mixer.music.load(playback_io)
        pygame.mixer.music.play()

    def stop(self):
        pygame.mixer.music.stop()

    def stop_and_cleanup(self):
        """Stop the current playback and clean up the mixer."""
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    def reinitialize_mixer(self):
        """Reinitialize the Pygame mixer."""
        pygame.mixer.init(frequency=22050)
    
    def hardware_test(self):
        playTime = getRandomTime()
        self.reinitialize_mixer()
        self.play_random_segment(playTime)
        for i in range(0, playTime):
            time.sleep(1)
            if(not self.test_running):
                self.stop_and_cleanup()
                return
        for i in range(0, 5):
            time.sleep(1)
            if(not self.test_running):
                self.stop_and_cleanup()
                return
        self.stop_and_cleanup()

    def _hardware_test_thread(self):
        while(self.test_running):
            self.hardware_test()

    def start_hardware_test(self):
        self.test_running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._hardware_test_thread)
            self.thread.start()

    def stop_hardware_test(self):
        self.test_running = False
        if self.thread is not None:
            self.thread.join()
    



def getRandomTime():
    return random.randint(10,40)

if __name__ == "__main__":
    audio_player = AudioPlayer("audio")
    audio_player.start_hardware_test()
    time.sleep(10*60)
    audio_player.stop_hardware_test()
