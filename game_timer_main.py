import logging
from datetime import datetime
from neopixels import test_pixels
now = datetime.now()
dt_string = "/home/GameTimerUser/Game-Timer/log/log-startTime-"+now.strftime("%d-%m-%Y--%H-%M")+".log"
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.

for i in range(0,4):
    print(i)
    test_pixels()