import pyaudio
import wave
import threading
import numpy as np

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORDING_DURATION = 5  # seconds
FILE1 = "temp1.wav"
FILE2 = "temp2.wav"
OUTPUT_FILENAME = "combined.wav"
recording = True

def record_audio(device_index, filename):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=device_index)

    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORDING_DURATION)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def combine_wav_files(wav_file1, wav_file2, output_file):
    # Open the first .wav file
    with wave.open(wav_file1, 'rb') as wf1:
        # Extract frames and convert to numpy array
        frames1 = np.frombuffer(wf1.readframes(-1), dtype=np.int16)

        # Open the second .wav file
        with wave.open(wav_file2, 'rb') as wf2:
            # Ensure parameters of both files match
            if wf1.getparams() != wf2.getparams():
                raise ValueError("WAV files have different parameters")

            # Extract frames and convert to numpy array
            frames2 = np.frombuffer(wf2.readframes(-1), dtype=np.int16)

            # Combine the frames
            combined_frames = np.average([frames1, frames2], axis=0).astype(np.int16)

            # Save the combined frames to the output file
            with wave.open(output_file, 'wb') as out_wf:
                out_wf.setparams(wf1.getparams())
                out_wf.writeframes(combined_frames.tobytes())

# List all audio devices and let the user choose two
audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    print(f"Device {i}: {info['name']}")

device1 = 1
device2 = 3

# Start recording threads
t1 = threading.Thread(target=record_audio, args=(device1, FILE1))
t2 = threading.Thread(target=record_audio, args=(device2, FILE2))

t1.start()
t2.start()

# Wait for threads to finish
t1.join()
t2.join()

# Combine the two audio files
combine_wav_files(FILE1, FILE2, OUTPUT_FILENAME)
