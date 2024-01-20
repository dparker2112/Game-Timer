class DataTracker:
    def __init__(self):
        # Initialize counters for buttons and encoder
        self.button_presses = [0, 0, 0, 0, 0, 0]  # Six buttons
        self.encoder_position = 0
        self.large_counter = 0

    def increment_button_press(self, button_index):
        if 0 <= button_index < len(self.button_presses):
            self.button_presses[button_index] += 1

    def update_encoder_position(self, new_position):
        self.encoder_position = new_position

    def increment_large_counter(self):
        self.large_counter += 1

    def get_status(self):
        return {
            "button_presses": self.button_presses,
            "encoder_position": self.encoder_position,
            "large_counter": self.large_counter
        }
