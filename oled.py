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
        small_font = ImageFont.truetype("DejaVuSans.ttf", 8)
        large_font = ImageFont.truetype("DejaVuSans.ttf", 16)  # Adjust size as needed

        with canvas(self.device) as draw:
            #draw.rectangle(self.device.bounding_box, outline="white", fill="black")

            # Display button counts with small font
            states = status['button_states']
            other_states = status['extra_button_states']

            draw.text((4, 10), "Buttons:", fill="white", font=small_font)
            for i, count in enumerate(status["button_presses"]):
                state = not states[i]
            
                # Calculate position and size for background rectangle
                # Adjust the x, y, width, and height as needed to fit your layout
                x_pos = 40 + i * 15
                y_pos = 10  # Adjust if necessary
                width = 10  # Adjust the width as needed
                height = 10  # Adjust the height as needed

                if state:
                # Draw the background rectangle slightly larger than the text
                    draw.rectangle([x_pos, y_pos, x_pos + width, y_pos + height], fill="white")
                    draw.text((x_pos, y_pos), f"{i+1}", fill="black", font=small_font)
                else:
                    draw.text((x_pos, y_pos), f"{i+1}", fill="white", font=small_font)
                # Now draw the text over the background rectangle
                
                
                draw.text((x_pos, y_pos + 10), f"{count}", fill="white", font=small_font)

            # Display encoder position with small font
            draw.text((4, 30), f"Enc. Pos: {status['encoder_position']}", fill="white", font=small_font)

            # Display encoder position with small font
            draw.text((4, 40), f"Enc. count: {status['encoder_button_presses']}", fill="white", font=small_font)

            # Display total time with large font
            draw.text((65, 30), f"{round(status['total_time'],1)}", fill="white", font=large_font)
            
            # Display increment with small font
            draw.text((110, 30), f"{status['increment']}", fill="white", font=small_font)
            draw.text((4, 50), "extra gpio:", fill="white", font=small_font)
            for i, count in enumerate(status["extra_gpio_presses"]):
                state = not other_states[i]

                draw.text((55 + i * 15, 50), f"{count}", fill="white", font=small_font)
                if state:
                # Draw the background rectangle slightly larger than the text
                                    #x1        y1   x2          y2
                    draw.rectangle([55 +i * 15, 50, 65 + i * 15, 60], fill="white")
                    draw.text((55 + i * 15, 50), f"{count}", fill="black", font=small_font)
                else:
                    draw.text((55 + i * 15, 50), f"{count}", fill="white", font=small_font)

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
