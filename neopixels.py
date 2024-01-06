import board
import RPi.GPIO as GPIO
import neopixel
import time
from classes import LEDStrip, wheel
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin1 = board.D18
pixel_pin2= board.D21

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

# The number of NeoPixels
num_pixels_ring = 24
num_pixels_strip = 24

ringPixels = LEDStrip(ORDER, num_pixels_ring, pixel_pin1)
stripPixels = LEDStrip(ORDER, num_pixels_ring, pixel_pin2)

def test_pixels():
    # Comment this line out if you have RGBW/GRBW NeoPixels
    ringPixels.fill(255, 0, 0)
    stripPixels.fill(255, 0, 0)
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((255, 0, 0, 0))
    ringPixels.show()
    stripPixels.show()
    time.sleep(1)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    ringPixels.fill(0, 255, 0)
    stripPixels.fill(0, 255, 0)
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 255, 0, 0))
    ringPixels.show()
    stripPixels.show()
    time.sleep(1)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    ringPixels.fill(0, 0, 255)
    stripPixels.fill(0, 0, 255)
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 0, 255, 0))
    ringPixels.show()
    stripPixels.show()
    time.sleep(1)

    for i in range(0,255):
        ringPixels.rainbow_cycle()  # rainbow cycle with 1ms delay per step
        time.sleep(0.01)

    for i in range(0,255):
        stripPixels.rainbow_cycle()  # rainbow cycle with 1ms delay per step
        time.sleep(0.01)


if __name__ == "__main__":
    for i in range(0,10):
        print(i)
        test_pixels()
