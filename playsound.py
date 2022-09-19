# from pydub import AudioSegment
# from pydub.playback import play
# import threading 

# newBeat=False
# sound = AudioSegment.from_wav('beep.wav')
# beep_thread = threading.Thread(target=play, args=(sound,))

from pydub import AudioSegment
from pydub.playback import play

sound = AudioSegment.from_wav('beep.wav')
play(sound)
