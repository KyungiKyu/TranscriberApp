import os
import wave
import speech_recognition as sr
import pyaudio
import threading

class AudioRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_frames = []
        self.is_recording = False
        self.stream = None
        self.save_path = None

    def start_recording(self, mic_index):
        if self.is_recording:
            print("Recording is already in progress.")
            return

        self.audio_frames = []
        self.is_recording = True

        p = pyaudio.PyAudio()
        self.stream = p.open(format=pyaudio.paInt16,
                             channels=1,
                             rate=16000,
                             input=True,
                             input_device_index=mic_index,
                             frames_per_buffer=1024)

        recording_thread = threading.Thread(target=self._record)
        recording_thread.start()

        print("Recording started.")

    def _record(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.audio_frames.append(data)

        print("Recording stopped.")

    def _transcribe(self):
        while self.is_recording or self.audio_frames:
            if not self.audio_frames:
                continue

            # Creating a new AudioData instance from the audio_frames
            audio_data = sr.AudioData(b''.join(self.audio_frames), 16000, 2)

            try:
                transcription = self.recognizer.recognize_google(audio_data)
                if self.transcription_file:
                    with open(self.transcription_file, 'a') as f:
                        f.write(transcription + '\n')
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Could not request results; {e}")


    def stop_recording(self, save_path):
        if not self.is_recording:
            print("No recording is in progress.")
            return

        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()

        if not save_path.endswith('.wav'):
            save_path += '.wav'

        wf = wave.open(save_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

        print(f"Recording saved to {save_path}.")