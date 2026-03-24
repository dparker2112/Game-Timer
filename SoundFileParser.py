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
            lowered = entry.lower()
            if lowered in {"desktop.ini", "thumbs.db"}:
                continue
            words = re.split('[_.]', entry)
            if len(words) < 3:
                print(f"Error: Invalid file name '{entry}'")
                continue

            # Extract key - support both numbered and named files
            key_str = words[0]
            try:
                # Try to convert to int for backwards compatibility
                key = int(key_str)
                key_type = 'int'
            except ValueError:
                # Use as string for named files
                key = key_str
                key_type = 'str'
            
            sound_type = words[1]
            if sound_type not in ['M', 'E', 'B']:
                print(f"Error: Unknown sound type '{sound_type}' in file '{entry}'")
                continue
            
            # Initialize the sound entry if not exists
            if key not in temp_dict:
                temp_dict[key] = {'B': '', 'M': '', 'E': '', 'key_type': key_type}
            
            temp_dict[key][sound_type] = entry

        # Validate and transfer complete entries to the main dictionary
        sound_dict = {}
        for key, val in temp_dict.items():
            # Must have at least M and E files
            if val['M'] and val['E']:
                if val['key_type'] == 'int':
                    sound_dict[key] = [val['B'], val['M'], val['E']]
                else:
                    sound_dict[key] = [val['B'], val['M'], val['E']]
            else:
                missing = []
                if not val['M']:
                    missing.append('M')
                if not val['E']:
                    missing.append('E')
                print(f"Warning: Skipping {key} - missing {', '.join(missing)} files")
        
        return sound_dict
    
    def load_sounds(self):
        sound_dict = {
            'r': (self.process_directory(rand_sound_dir), os.path.join(self.base_dir, rand_sound_dir)),
            's': (self.process_directory(short_sound_dir), os.path.join(self.base_dir, short_sound_dir)),
            'n': (self.process_directory(long_sound_dir), os.path.join(self.base_dir, long_sound_dir))
        }
        return sound_dict
    
    def get_sound_dict(self):
        return self.sound_dict
    
    def get_game_title(self):
        if self.game_title:
            return self.game_title.strip()
        else:
            return None