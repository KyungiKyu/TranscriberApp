import os
import wave
import pyaudio
import threading
import speech_recognition as sr
from pyannote.audio import Pipeline

class AudioRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_frames = []
        self.is_recording = False
        self.stream = None
        self.transcription_file = None
        self.language = 'de-DE'
        YOUR_AUTH_TOKEN = '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'
        self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=YOUR_AUTH_TOKEN)

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

            audio_data = sr.AudioData(b''.join(self.audio_frames), 16000, 2)
            try:
                transcription = self.recognizer.recognize_google(audio_data, language=self.language)
                if self.transcription_file:
                    with open(self.transcription_file, 'a') as f:
                        f.write(transcription + '\n')
                        print(transcription)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

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
        self.apply_diarization(save_path)

    def apply_diarization(self, audio_path):
        diarization = self.diarization_pipeline(audio_path)
        with open(self.transcription_file, 'r') as f:
            transcription = f.read()

        diarized_transcript = ""
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diarized_transcript += f"Speaker {speaker}: {transcription[turn.start:turn.end]}\n"

        with open(self.transcription_file, 'w') as f:
            f.write(diarized_transcript)

    def start_transcribe_file(self, path):
        transcription_thread = threading.Thread(target=self.transcribe_file, args=(path,))
        transcription_thread.start()

    def transcribe_file(self, path):
        with sr.AudioFile(path) as source:
            audio_data = self.recognizer.record(source)

        try:
            transcription = self.recognizer.recognize_sphinx(audio_data, language=self.language)
            transcription_file = path.replace('.wav', '.txt')
            with open(transcription_file, 'w') as f:
                f.write(transcription)
            print(f"Transcription saved to {transcription_file}.")
            self.apply_diarization(path)
        except sr.UnknownValueError:
            print("Sphinx could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Sphinx service; {e}")
