import wave
import speech_recognition as sr
import pyaudio
import threading
import openai
import numpy as np
import os
import uuid
import time
import librosa
import soundfile as sf
import shutil

class AudioRecorder:
    def __init__(self):
        openai.api_key = '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'
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_frames = []
        self.audio_frames_save = []
        self.is_recording = False
        self.stream = None
        self.recording_stopped_event = threading.Event()
        self.shutdown_event = threading.Event()
        self.sessions = {}


    def start_recording(self, mic_index, sys_sound_device):
        self.shutdown_event.clear()

        self.current_session_id = uuid.uuid4().hex
        self.sessions[self.current_session_id] = {
            "temp_filename1": os.path.join(os.getcwd(), f"TEMP\\temp1_{uuid.uuid4().hex}.wav"),
            "temp_filename2": os.path.join(os.getcwd(), f"TEMP\\temp2_{uuid.uuid4().hex}.wav"),
            # Commenting out the temp_transcription_file creation
            # "temp_transcription_file": os.path.join(os.getcwd(), f"TEMP/transcription_temp_{uuid.uuid4().hex}.txt")
        }

        # Commenting out the creation of the empty temporary transcription file
        # if not os.path.isfile(self.sessions[self.current_session_id]["temp_transcription_file"]):
        #     with open(self.sessions[self.current_session_id]["temp_transcription_file"], 'x') as f:
        #         pass

        self.recording_thread1 = threading.Thread(target=self._record, args=(mic_index, self.sessions[self.current_session_id]["temp_filename1"]))
        self.recording_thread2 = threading.Thread(target=self._record, args=(sys_sound_device, self.sessions[self.current_session_id]["temp_filename2"]))


        self.audio_frames = []
        self.is_recording = True
        self.recording_stopped_event.clear()

        p = pyaudio.PyAudio()
        self.stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            input_device_index=mic_index,
                            frames_per_buffer=1024)

        self.recording_thread1 = threading.Thread(target=self._record, args=(mic_index, self.sessions[self.current_session_id]["temp_filename1"]))
        self.recording_thread2 = threading.Thread(target=self._record, args=(sys_sound_device, self.sessions[self.current_session_id]["temp_filename2"]))

        self.recording_thread1.start()
        self.recording_thread2.start()

        # transcription_thread = threading.Thread(target=self._transcribe)
        # transcription_thread.start()

        print("Recording started.")

    def _record(self, mic_index, temp_filename):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=mic_index,
                        frames_per_buffer=1024)

        with wave.open(temp_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)

            while self.is_recording:
                if self.shutdown_event.is_set():
                    break
                data = stream.read(1024)
                wf.writeframes(data)

        stream.stop_stream()
        stream.close()

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
                            print(response)

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

    def combine_wav_files(self, wav_file1, wav_file2, output_file):
        # Load the first .wav file
        y1, sr1 = librosa.load(wav_file1, sr=None, mono=True)  # Ensure it's mono

        # Load the second .wav file
        y2, sr2 = librosa.load(wav_file2, sr=None, mono=True)  # Ensure it's mono

        # Resample the audio if sample rates do not match
        if sr1 != sr2:
            y2 = librosa.resample(y2, sr2, sr1)
            sr2 = sr1

        # If the lengths of y1 and y2 do not match, pad the shorter one with zeros
        if len(y1) > len(y2):
            y2 = np.pad(y2, (0, len(y1) - len(y2)))
        elif len(y1) < len(y2):
            y1 = np.pad(y1, (0, len(y2) - len(y1)))

        # Mix the audio
        combined_audio = y1 + y2

        # Normalize the audio to prevent clipping
        combined_audio = combined_audio / np.max(np.abs(combined_audio), axis=0)

        # Save the combined audio
        sf.write(output_file, combined_audio, sr1)


    def stop_recording(self, save_path):
        if not self.is_recording:
            print("No recording is in progress.")
            return

        self.is_recording = False
        self.shutdown_event.set()  # Signal the recording threads to finish

        # Ensure the threads have finished
        self.recording_thread1.join()
        self.recording_thread2.join()

        session_id = self.current_session_id
        if not session_id or session_id not in self.sessions:
            print("Error: Session not found.")
            return

        temp_filename1 = self.sessions[session_id]["temp_filename1"]
        temp_filename2 = self.sessions[session_id]["temp_filename2"]


        # Combine the two temporary files into a combined .wav file
        combined_filename = os.path.join(os.getcwd(), f"Temp//temp_combined_{uuid.uuid4().hex}.wav")
        self.combine_wav_files(temp_filename1, temp_filename2, combined_filename)

        if not save_path.endswith('.wav'):
            save_path += '.wav'

        # Copy the combined audio to the desired save_path
        shutil.copyfile(combined_filename, save_path)

        # Remove temporary files
        #os.remove(temp_filename1)
        #os.remove(temp_filename2)
        os.remove(combined_filename)

        print(f"Recording saved to {save_path}.")

        # Start transcribing the saved audio file
        self.start_transcribe_file(save_path)

        # Cleanup: remove session from the sessions dictionary after processing
        del self.sessions[session_id]



    def start_transcribe_file(self, path):
        transcription_thread = threading.Thread(target=self.transcribe_file, args=(path,))
        transcription_thread.start()

    def transcribe_file(self, path):
        audio_file = open(path, 'rb')
        transcript = openai.Audio.transcribe('whisper-1', audio_file)

        f = open(str(path.split('.')[0] + '.txt'), 'w+')
        f.write(transcript['text'])
        f.close()