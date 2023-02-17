from playsound import playsound
import sys
import time

def play_sound(filename="beep.wav"):
    playsound(filename)
    time.sleep(.5)
    sys.exit()

if __name__ == "__main__":
    play_sound()
