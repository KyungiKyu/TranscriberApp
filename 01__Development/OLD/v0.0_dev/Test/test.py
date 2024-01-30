import os
import wave
import pyaudio
import numpy as np

def convert_mp3_to_wav(mp3_filepath, wav_filepath):
    # Open the MP3 file
    p = pyaudio.PyAudio()
    mp3_stream = p.open(format=pyaudio.paInt16,
                        channels=2,
                        rate=44100,
                        input=True,
                        output=True)

    # Read the MP3 file and store the data in a bytes object
    with open(mp3_filepath, 'rb') as f:
        mp3_data = f.read()

    # Convert the bytes object to a numpy array
    wav_data = np.frombuffer(mp3_data, dtype=np.int16)

    # Open a WAV file and write the data to it
    with wave.open(wav_filepath, 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wav_file.setframerate(44100)
        wav_file.writeframes(wav_data.tobytes())

    # Close the MP3 stream
    mp3_stream.stop_stream()
    mp3_stream.close()
    p.terminate()


if __name__ == "__main__":
    mp3_filepath = "D:/Downloads/My YouTuber merch is not the best.mp3"
    wav_filepath = "D:/Downloads/test.wav"

    # Check if the input MP3 file exists
    if not os.path.exists(mp3_filepath):
        raise FileNotFoundError(f"The MP3 file {mp3_filepath} does not exist.")

    # Convert the MP3 file to WAV format
    convert_mp3_to_wav(mp3_filepath, wav_filepath)
    print(f"Conversion complete. WAV file saved at {wav_filepath}")
