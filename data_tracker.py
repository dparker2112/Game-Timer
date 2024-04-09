import time

class DataTracker:
    def __init__(self, logger, button_pins, extra_gpio):
        # Initialize counters for buttons and encoder
        self.update = True
        self.logger = logger
        self.encoder_position = 0
        self.encoder_button_presses = 0
        self.button_presses = [0] * len(button_pins)  # Initialize counts for each button
        self.button_states = [1] * len(button_pins)
        self.extra_gpio_presses = [0] * len(extra_gpio)  # Initialize counts for each button
        self.extra_button_states = [1] * len(extra_gpio)
        self.large_counter = 0
        self.button_pin_to_index = {pin: index for index, pin in enumerate(button_pins)}
        self.extra_gpio_to_index = {pin: index for index, pin in enumerate(extra_gpio)}
        self.increment = 5
        self.time = 30
        self.countdown_time = self.time
        self.remaining_time = 0
        self.time_left = 0
        self.countdown = False
        self.countdown_pause = False
        self.lastUpdate = 0
    def start_countdown(self):
        self.countdown_time = self.time
        self.countdown = True
        self.countdown_pause = False
        self.start_time = time.time()

    def pause_countdown(self):
        self.countdown_pause = True
        runtime = time.time() - self.start_time
        self.remaining_time = self.countdown_time - runtime
    
    def stop_countdown(self):
        self.countdown = False
        self.countdown_pause = False

    def resume_countdown(self):
        self.countdown_pause = False
        self.countdown_time = self.remaining_time
        self.start_time = time.time()

    def update_countdown(self):
        if self.countdown_pause:
            return False
        if self.countdown:
            runtime = time.time() - self.start_time
            if(runtime >= self.countdown_time):
                self.countdown = False
                self.update = True
                return True
            self.time_left = self.countdown_time - runtime
            if (time.time() - self.lastUpdate) >= 0.01:
                self.update = True
        return False

    def increment_button_counter(self, button_pin):
        self.update = True
        button_index = self.button_pin_to_index[button_pin]
        if 0 <= button_index < len(self.button_presses):
            self.button_presses[button_index] += 1
        else:
            self.logger.info(f"invalid button index: {button_index}")
    
    def increment_extra_gpio_counter(self, button_pin):
        self.update = True
        button_index = self.extra_gpio_to_index[button_pin]
        if 0 <= button_index < len(self.button_presses):
            self.extra_gpio_presses[button_index] += 1
        else:
            self.logger.info(f"invalid button index: {button_index}")

    def lists_different(self, list1, list2):
        if len(list1) != len(list2):
            return True
        for item1, item2 in zip(list1, list2):
            if item1 != item2:
                return True
        return False


    def update_button_states(self, new_states):
        if(self.lists_different(new_states, self.button_states)):
            self.update = True
            self.button_states = list(new_states)

    def update_extra_button_states(self, new_states):
        if(self.lists_different(new_states, self.extra_button_states)):
            self.update = True  
            self.extra_button_states = list(new_states)

    def update_encoder_position(self, new_position):
        self.update = True
        self.encoder_position = new_position
    
    def update_total_time(self, direction):
        self.update = True
        temp = self.time
        self.time = self.time + direction * self.increment
        if(self.time <= 0):
            self.time = temp
        self.logger.info(f"updated time: {self.time}")

    def set_total_time(self, seconds):
        self.update = True
        self.time = seconds
        self.logger.info(f"updated time: {self.time}")

    def update_increment(self):
        self.update = True
        if self.increment == 1:
            self.increment = 5
        elif self.increment == 5:
            self.increment = 10
        else:
            self.increment = 1

    def increment_encoder_counter(self):
        self.update = True
        self.encoder_button_presses += 1

    def increment_large_counter(self):
        self.update = True
        self.large_counter += 1
    
    def increment_large_counter(self):
        self.update = True
        self.large_counter += 1

    def updateReady(self):
        if(self.update):
            self.lastUpdate = time.time()
        return self.update

    def get_status(self):
        self.update = False
        displayTime = self.time
        if self.countdown or self.countdown_pause:
            displayTime = self.time_left
        return {
            "button_presses": self.button_presses,
            "encoder_position": self.encoder_position,
            "encoder_button_presses": self.encoder_button_presses,
            "extra_gpio_presses": self.extra_gpio_presses,
            "large_counter": self.large_counter,
            "total_time": displayTime,
            "increment" : self.increment,
            "button_states": self.button_states,
            "extra_button_states": self.extra_button_states,
        }
