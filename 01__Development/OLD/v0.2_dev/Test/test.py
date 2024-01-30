import subprocess
import pyaudio
import wave
import threading

# Function to record audio
def record_audio(output_filename, device_index=None):
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = 5

    audio = pyaudio.PyAudio()

    # Start the stream to record audio
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=device_index)

    print(f"Recording to {output_filename}...")

    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print(f"Finished recording to {output_filename}")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the audio data to a file
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))


# 1. Set Stereo Mix as default recording device using PowerShell
ps_script = """
# Import the AudioDeviceCmdlets module
Import-Module AudioDeviceCmdlets

# Get all audio devices
$audioDevices = Get-AudioDevice -List | Where-Object { $_.Type -eq "Recording" }

# Find Stereo Mix
$stereoMix = $audioDevices | Where-Object { $_.Name -like "*Stereo Mix*" }

# Set Stereo Mix as default if found
if ($stereoMix) {
    Set-AudioDevice -Index $stereoMix.Index
    Write-Output "Stereo Mix set as default recording device."
    return $true
} else {
    Write-Output "Stereo Mix not found."
    return $false
}
"""

result = subprocess.run(['powershell', ps_script], capture_output=True, text=True)
print(result.stdout)

# 2. Record system audio in a separate thread
threading.Thread(target=record_audio, args=("system_output.wav",)).start()

# 3. Simultaneously record microphone input
# (You might need to adjust the device_index based on your setup)
record_audio("mic_output.wav")

