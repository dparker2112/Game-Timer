#https://github.com/rm-hull/luma.examples
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309
import RPi.GPIO as GPIO

# Pin configuration (adjust based on your wiring)
RST_PIN = 25  # GPIO pin for Reset
DC_PIN = 24   # GPIO pin for Data/Command

# SPI device on SPI port 0, device 0 (adjust if needed)
serial = spi(device=0, port=0, gpio_DC=DC_PIN, gpio_RST=RST_PIN)

# Initialize the SSD1309 display
device = ssd1309(serial)

# Display text
with canvas(device) as draw:
    draw.text((10, 10), "Hello, World!", fill="white")

