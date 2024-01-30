import wave
import speech_recognition as sr
import pyaudio
import threading
import openai
import numpy as np
import os
import uuid

class AudioRecorder:
    def __init__(self):
        openai.api_key = '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'
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_frames = []
        self.audio_frames_save = []
        self.is_recording = False
        self.stream = None
        self.temp_transcription_file = os.getcwd() + "\\TEMP\\transcription_temp.txt"
        self.audio_frames2 = []

    def record_audio(self, device_index, filename):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=2,
                            rate=44100, input=True,
                            frames_per_buffer=1024,
                            input_device_index=device_index)

        frames = []

        while self.is_recording:
            data = stream.read(1024)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(frames))

    def combine_wav_files(self, wav_file1, wav_file2, output_file):
        with wave.open(wav_file1, 'rb') as wf1:
            frames1 = np.frombuffer(wf1.readframes(-1), dtype=np.int16)
            with wave.open(wav_file2, 'rb') as wf2:
                if wf1.getparams() != wf2.getparams():
                    raise ValueError("WAV files have different parameters")
                frames2 = np.frombuffer(wf2.readframes(-1), dtype=np.int16)
                combined_frames = np.average([frames1, frames2], axis=0).astype(np.int16)
                with wave.open(output_file, 'wb') as out_wf:
                    out_wf.setparams(wf1.getparams())
                    out_wf.writeframes(combined_frames.tobytes())

    def start_recording(self, mic_index):
        self.audio_frames = []
        self.is_recording = True

        mic_thread = threading.Thread(target=self.record_audio, args=(mic_index, os.getcwd() + "\\TEMP\\temp1.wav"))
        mic_thread.start()

        audio = pyaudio.PyAudio()
        stereo_mix_index = None
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if "Stereo Mix" in info['name']:
                stereo_mix_index = i
                break

        if stereo_mix_index is None:
            print("Stereo Mix device not found.")
            return

        stereo_mix_thread = threading.Thread(target=self.record_audio, args=(stereo_mix_index, os.getcwd() + "\\TEMP\\temp2.wav"))
        stereo_mix_thread.start()

    def _record(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.audio_frames.append(data)
        print("Recording stopped.")

    def _transcribe(self):
        silence_threshold = 500
        max_silent_chunks = 10
        silent_chunk_count = 0
        accumulated_frames = []

        while self.is_recording:
            # if not self.audio_frames_save:
            #     continue

            # # Creating a new AudioData instance from the audio_frames
            # audio_data = sr.AudioData(b''.join(self.audio_frames_save), 16000, 2)

            if self.audio_frames:
                data = self.audio_frames.pop(0)
                audio_int16 = np.frombuffer(data, np.int16)

                if np.abs(audio_int16).mean() < silence_threshold:
                    silent_chunk_count += 1
                else:
                    silent_chunk_count = 0
                    accumulated_frames.append(data)

                if silent_chunk_count >= max_silent_chunks and accumulated_frames:
                    audio_data = b''.join(accumulated_frames)
                    accumulated_frames.clear()

                    temp_filename = os.path.join(os.getcwd(), f"temp_audio_{uuid.uuid4().hex}.wav")
                    try:
                        with wave.open(temp_filename, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                            wf.setframerate(16000)
                            wf.writeframes(audio_data)

                        with open(temp_filename, 'rb') as audio_file:
                            response = openai.Audio.transcribe("whisper-1", audio_file)
                            transcription = response['text']

                            if not os.path.isfile(self.temp_transcription_file):
                                f = open(self.temp_transcription_file, 'x')
                                f.close()

                            f = open(self.temp_transcription_file, 'a')
                            f.write(transcription + '\n')
                            f.close()
                            print(transcription)
                    except Exception as e:
                        print(f"An error occurred: {str(e)}")
                    finally:
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)

    def tempfile_to_savefile(self, tempfile, savefile):
        with open(tempfile, 'r') as f:
            data = f.read()

        with open(savefile, 'a') as f:
            f.write(data)

        os.remove(tempfile)

    def stop_recording(self, save_path):
        if not self.is_recording:
            print("No recording is in progress.")
            return

        self.is_recording = False
        self.combine_wav_files(os.getcwd() + "\\TEMP\\temp1.wav", os.getcwd() + "\\TEMP\\temp2.wav", save_path)

        if not save_path.endswith('.wav'):
            save_path += '.wav'

        transcription_file = save_path.replace('.wav', '.txt')  # Assigning transcription_file here
        self.tempfile_to_savefile(self.temp_transcription_file,transcription_file)

        self.stream.stop_stream()
        self.stream.close()

        wf = wave.open(save_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

        print(f"Recording saved to {save_path}.")
        print(f"Transcription saved to {transcription_file}.")
        if os.path.isfile(self.temp_transcription_file):
            os.remove(self.temp_transcription_file)

    def start_transcribe_file(self, path):
        transcription_thread = threading.Thread(target=self.transcribe_file, args=(path,))
        transcription_thread.start()

    def transcribe_file(self, path):
        audio_file = open(path, 'rb')
        transcript = openai.Audio.transcribe('whisper-1', audio_file)

        f = open(str(path.split('.')[0] + '.txt'), 'w+')
        f.write(transcript['text'])
        f.close()