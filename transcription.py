import os
import wave
import pyaudio
import threading
from deepgram import Deepgram
import speech_recognition as sr

class AudioRecorder:
    def __init__(self, deepgram_api_key):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_frames = []
        self.is_recording = False
        self.stream = None
        self.transcription_file = None
        self.language = 'en-US'  # Update this based on your preference
        self.deepgram_client = Deepgram(deepgram_api_key)

    def start_recording(self, mic_index, language):
        if self.is_recording:
            print("Recording is already in progress.")
            return

        self.language = language
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
        transcription_thread = threading.Thread(target=self._transcribe_live)
        transcription_thread.start()

        print("Recording and transcribing started.")

    def _record(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.audio_frames.append(data)
        print("Recording stopped.")

    def _transcribe_live(self):
        # Live transcription with Deepgram
        audio_data = b''.join(self.audio_frames)
        response = self.deepgram_client.transcription.prerecorded(
            {'buffer': audio_data, 'mimetype': 'audio/wav'},
            {'punctuate': True, 'diarize': True}
        )
        try:
            transcription = response['results']['channels'][0]['alternatives'][0]['transcript']
            if self.transcription_file:
                with open(self.transcription_file, 'a') as f:
                    f.write(transcription + '\n')
                    print(transcription)
        except Exception as e:
            print(f"Error in transcribing: {e}")

    def stop_recording(self, save_path):
        if not self.is_recording:
            print("No recording is in progress.")
            return

        self.is_recording = False

        if not save_path.endswith('.wav'):
            save_path += '.wav'

        self.transcription_file = save_path.replace('.wav', '.txt')

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

    def start_transcribe_file(self, path):
        transcription_thread = threading.Thread(target=self.transcribe_file, args=(path,))
        transcription_thread.start()

    def transcribe_file(self, path):
        with open(path, 'rb') as audio_file:
            response = self.deepgram_client.transcription.prerecorded(
                {'buffer': audio_file, 'mimetype': 'audio/wav'},
                {'punctuate': True, 'diarize': True}
            )
        try:
            transcription = response['results']['channels'][0]['alternatives'][0]['transcript']
            transcription_file = path.replace('.wav', '.txt')
            with open(transcription_file, 'w') as f:
                f.write(transcription)
            print(f"Transcription saved to {transcription_file}.")
        except Exception as e:
            print(f"Error in transcribing: {e}")
