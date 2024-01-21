class DataTracker:
    def __init__(self, button_pins):
        # Initialize counters for buttons and encoder
        self.update = True
        self.encoder_position = 0
        self.encoder_button_presses = 0
        self.button_presses = [0] * len(button_pins)  # Initialize counts for each button
        self.large_counter = 0
        self.button_pin_to_index = {pin: index for index, pin in enumerate(button_pins)}
        
    def increment_button_counter(self, button_pin):
        self.update = True
        button_index = self.button_pin_to_index[button_pin]
        if 0 <= button_index < len(self.button_presses):
            self.button_presses[button_index] += 1
        else:
            print(f"invalid button index: {button_index}")

    def update_encoder_position(self, new_position):
        self.update = True
        self.encoder_position = new_position

    def increment_encoder_counter(self):
        self.update = True
        self.encoder_button_presses += 1

    def increment_large_counter(self):
        self.update = True
        self.large_counter += 1

    def updateReady(self):
        return self.update

    def get_status(self):
        self.update = False
        return {
            "button_presses": self.button_presses,
            "encoder_position": self.encoder_position,
            "encoder_button_presses": self.encoder_button_presses,
            "large_counter": self.large_counter
        }
