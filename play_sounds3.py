import vlc
import time
p = vlc.MediaPlayer("sounds/rand/01_M.mp3")
p.play()
time.sleep(3)
p.stop()