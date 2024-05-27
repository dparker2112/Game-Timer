import os
import re
base_dir = "sounds"
game_info_file = "game.txt"
short_sound_dir = "sixty"
rand_sound_dir = "rand"
long_sound_dir = "ninety"


class SoundFileParser:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.game_title = self.read_game_title(game_info_file)
        self.sound_dict = self.load_sounds()

    def read_game_title(self, game_info_file):
        try:
            with open(os.path.join(self.base_dir, game_info_file)) as f:
                game_title = f.readline().strip()
            return game_title
        except:
            return None

    def process_directory(self, dir_name):
        temp_dict = {}
        try:
            entries = os.listdir(os.path.join(self.base_dir, dir_name))
        except:
            return temp_dict
        for entry in entries:
            words = re.split('[_.]', entry)
            if len(words) < 3:
                print(f"Error: Invalid file name '{entry}'")
                continue

            try:
                key = int(words[0])
            except ValueError:
                #print(f"Error: Invalid key number in file name '{entry}'")
                continue
            
            sound_type = words[1]
            if key not in temp_dict:
                temp_dict[key] = {'M': '', 'E': ''}
            if sound_type in ['M', 'E']:
                temp_dict[key][sound_type] = entry
            else:
                print(f"Error: Unknown sound type '{sound_type}' in file '{entry}'")

        # Validate and transfer only complete entries to the main dictionary
        sound_dict = {key: [val['M'], val['E']] for key, val in temp_dict.items() if val['M'] and val['E']}
        return sound_dict
    
    def load_sounds(self):
        sound_dict = {
            'r': (self.process_directory(rand_sound_dir), os.path.join(base_dir, rand_sound_dir)),
            's': (self.process_directory(short_sound_dir), os.path.join(base_dir, short_sound_dir)),
            'n': (self.process_directory(long_sound_dir), os.path.join(base_dir, long_sound_dir))
        }
        return sound_dict
    
    def get_sound_dict(self):
        return self.sound_dict
    
    def get_game_title(self):
        if self.game_title:
            return self.game_title.strip()
        else:
            return None