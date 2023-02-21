# trying PyAudio instead
import pyaudio
import wave

# plays a WAV file, defaults to beep.wav
# based on https://coderslegacy.com/python/pyaudio-recording-and-playing-sound/
def play_sound(filename="beep.wav"):
    # initialize the stream
    p = pyaudio.PyAudio()
    sound_file = wave.open(filename, 'rb')
    chunk_size = 1024

    stream = p.open(format = p.get_format_from_width(sound_file.getsampwidth()),
                    channels = sound_file.getnchannels(),
                    rate = sound_file.getframerate(),
                    output = True)
    
    # read the WAV data
    data = sound_file.readframes(chunk_size)

    # play the sound
    while data != b'':
        stream.write(data)
        data = sound_file.readframes(chunk_size)

    # close the stream
    stream.stop_stream()
    stream.close()

if __name__ == "__main__":
    play_sound()
