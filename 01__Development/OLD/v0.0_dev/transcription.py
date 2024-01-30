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
        self.transcription_file = None

    def start_recording(self, mic_index, language):
        if self.is_recording:
            print("Recording is already in progress.")
            return

        print(language)

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
        transcription_thread = threading.Thread(target=self._transcribe)
        transcription_thread.start()

        print("Recording and transcribing started.")

    def _record(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.audio_frames.append(data)
        print("Recording stopped.")

    def _transcribe(self):
        while self.is_recording:
            if not self.audio_frames:
                continue

            # Creating a new AudioData instance from the audio_frames
            audio_data = sr.AudioData(b''.join(self.audio_frames), 16000, 2)

            try:
                transcription = self.recognizer.recognize_google(audio_data)  # Transcribe using Google's API
                if self.transcription_file:  # Check if transcription_file is assigned
                    with open(self.transcription_file, 'a') as f:  # Open the transcription file in append mode
                        f.write(transcription + '\n')  # Write the transcribed text to the file
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Could not request results; {e}")  # Handle exceptions when there is an API request error

    def stop_recording(self, save_path):
        if not self.is_recording:
            print("No recording is in progress.")
            return

        self.is_recording = False

        if not save_path.endswith('.wav'):
            save_path += '.wav'

        self.transcription_file = save_path.replace('.wav', '.txt')  # Assigning transcription_file here

        self.stream.stop_stream()
        self.stream.close()

        wf = wave.open(save_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

        print(f"Recording saved to {save_path}.")
        print(f"Transcription saved to {self.transcription_file}.")

    def transcribe_file(self, path):
        r = sr.Recognizer()

        audio = sr.AudioFile(path)

        with audio as source:
            audio = r.record(source)
            result = r.recognize_google(audio)

        print(result)

        f = open(path.replace('.wav','.txt'),'w+')
        f.write(result)
        f.close()