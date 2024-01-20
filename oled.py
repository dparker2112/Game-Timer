from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
from PIL import ImageFont
import time

###
### note that oled display is 128 x 64
###

class OLED_Display:
    def __init__(self, device=0, port=0):
        # Initialize SPI interface and OLED display device
        self.serial = spi(device=device, port=port)
        self.device = ssd1309(self.serial)

    def draw_text(self, text, position=(10, 40)):
        # Draw text on the display at the specified position
        with canvas(self.device) as draw:
            #draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            draw.text(position, text, fill="white")

    def draw_multiple_texts(self, texts):
        """
        Draw multiple texts on the display.
        :param texts: A list of tuples, where each tuple contains the text and its position (e.g., [("Hello", (10, 40)), ("World", (10, 60))])
        """
        with canvas(self.device) as draw:
            #draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            for text, position in texts:
                draw.text(position, text, fill="white")
    def clear_display(self):
        # Clear the display
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black")
    
    def display_status(self, status):
        # Load a font in two different sizes
        small_font = ImageFont.load_default()
        large_font = ImageFont.truetype("DejaVuSans.ttf", 20)  # Adjust size as needed

        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")

            # Display button counts with small font
            for i, count in enumerate(status["button_presses"]):
                draw.text((10, 10 + i * 12), f"Button {i+1}: {count}", fill="white", font=small_font)

            # Display encoder position with small font
            draw.text((10, 70), f"Encoder Pos: {status['encoder_position']}", fill="white", font=small_font)

            # Display large counter with large font
            draw.text((10, 90), f"Large Counter: {status['large_counter']}", fill="white", font=large_font)

def main():
    # Example usage
    oled_display = OLED_Display()

    # Display multiple texts
    texts_to_display = [
        ("Hello", (0, 20)),
        ("World", (40, 30)),
        ("Another line", (60, 40))
    ]
    #oled_display.draw_multiple_texts(texts_to_display)
    oled_display.draw_text(texts_to_display[0][0],texts_to_display[0][1] )
    time.sleep(2)
    oled_display.draw_text(texts_to_display[1][0],texts_to_display[1][1] )
    time.sleep(2)
    oled_display.draw_text(texts_to_display[2][0],texts_to_display[2][1] )
    time.sleep(10)

    # Clear display
    oled_display.clear_display()



if __name__ == "__main__":
    main()
