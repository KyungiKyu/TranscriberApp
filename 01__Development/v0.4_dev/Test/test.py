import sounddevice as sd
import numpy as np
import wavio

# Parameters
filename = 'system_audio_output.wav'
duration = 10  # seconds
samplerate = 44100  # Hz
channels = 2  # Stereo

# Replace with the index of VB-Cable Output
vb_cable_index = 1  # Use sounddevice.query_devices() to find this

def record_audio(filename, duration, samplerate, channels, device):
    print(f"Recording system audio for {duration} seconds...")
    with sd.InputStream(samplerate=samplerate, channels=channels, device=device):
        audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels)
        sd.wait()
    wavio.write(filename, audio_data, samplerate, sampwidth=2)
    print(f"Recording saved as {filename}")

try:
    record_audio(filename, duration, samplerate, channels, vb_cable_index)
except Exception as e:
    print(f"An error occurred: {e}")
