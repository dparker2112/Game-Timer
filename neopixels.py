import board
import RPi.GPIO as GPIO
import neopixel
import classes

pixel_pin1 = board.D18
pixel_pin2= board.D21

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

# The number of NeoPixels
num_pixels_ring = 24
num_pixels_strip = 144

ringPixels = neopixel.NeoPixel(
    pixel_pin1, num_pixels_ring, brightness=0.2, auto_write=False, pixel_order=ORDER
)

stripPixels = neopixel.NeoPixel(
    pixel_pin2, num_pixels_strip, brightness=0.2, auto_write=False, pixel_order=ORDER
)

neoRingLEDS = classes.LedRGB()
neoStripLEDS = classes.LedRGB()

ringPixels.fill((neoRingLEDS.r, neoRingLEDS.g, neoRingLEDS.b))
ringPixels.show()
stripPixels.fill((neoStripLEDS.r, neoStripLEDS.g, neoStripLEDS.b))
stripPixels.show()