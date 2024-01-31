import wave
import speech_recognition as sr
import pyaudio
from pydub import AudioSegment
import threading
from openai import OpenAI
import numpy as np
import os
import uuid
import sounddevice as sd
import librosa
import soundfile as sf
import shutil
import logging
import json
import configparser

from PyQt6.QtCore import QEvent, QCoreApplication

# Configure logging
logging.basicConfig(filename=str(os.path.join(os.getenv('APPDATA'), 'TranscriptionApp','transcription.log')), level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

global config_path
config_path = os.path.join(os.getenv('APPDATA'), 'TranscriptionApp','settings.ini')

global config
config = configparser.ConfigParser()
config.read(config_path)

# Event Classes
class MessageEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, message):
        super().__init__(MessageEvent.EVENT_TYPE)
        self.message = message

class AudioRecorder():

    def __init__(self, handler):
        super().__init__()

        self.openai_client = OpenAI(api_key = '') #TODO: implement secure api key

        self.audio_model = 'whisper-1'
        self.chat_model = 'gpt-4'

        self.transcription_mapping = {}
        self.handler = handler
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_frames = []
        self.audio_frames_save = []
        self.is_recording = False
        self.stream = None
        self.recording_stopped_event = threading.Event()
        self.shutdown_event = threading.Event()
        self.sessions = {}
        self.program_folder = os.path.join(os.getenv('APPDATA'), 'TranscriptionApp')
        self.data_folder = os.path.join(self.program_folder, 'DATA')
        self.temp_folder = os.path.join(self.program_folder, 'TEMP')
        self.asset_folder = os.path.join(self.program_folder, 'Assets')
        self.p = pyaudio.PyAudio()

        f = open(os.path.join(self.asset_folder,'GPT-Templates', 'system_message.json'))
        data = json.load(f)
        f.close()

        self.system_message_keynote = data['keynote']
        self.system_message_protocol = data['protocol']

        logger.info('All nescessary class variables are declared and working!')

        try:
            if not os.path.exists(self.program_folder) or not os.path.exists(self.data_folder) or not os.path.exists(self.temp_folder):
                logger.exception('Program folder was missing!')
                os.makedirs(self.program_folder)
                os.makedirs(self.data_folder)
                os.makedirs(self.temp_folder)
        except:
            pass

    def start_recording(self, mic_index, sys_sound_device):
        self.shutdown_event.clear()

        self.current_session_id = uuid.uuid4().hex
        logger.info(f"Current recording SessionID is: {self.current_session_id}")
        self.sessions[self.current_session_id] = {
            "temp_filename1": os.path.join(self.temp_folder, f"temp1_{uuid.uuid4().hex}.wav"),
            "temp_filename2": os.path.join(self.temp_folder, f"temp2_{uuid.uuid4().hex}.wav"),
        }

        self.audio_frames = []
        self.is_recording = True
        self.recording_stopped_event.clear()

        self.recording_thread1 = threading.Thread(target=self._record, args=(mic_index, self.sessions[self.current_session_id]["temp_filename1"]))
        self.recording_thread2 = threading.Thread(target=self._record, args=(sys_sound_device, self.sessions[self.current_session_id]["temp_filename2"]))

        self.recording_thread1.start()
        logger.info(f"Started Microphone Thread for session {self.current_session_id}!")
        self.recording_thread2.start()
        logger.info(f"Started System sounds Thread for session {self.current_session_id}!")

    def _record(self, mic_index, temp_filename):
        try:
            logger.info(f"Opening Stream for device {sd.query_devices(mic_index)['name']}...")
            stream = self.p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            input_device_index=mic_index,
                            frames_per_buffer=1024)

            logger.info(f"Stream for Microphone {sd.query_devices(mic_index)['name']} open!")

            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)

                while self.is_recording:
                    if self.shutdown_event.is_set():
                        break
                    data = stream.read(1024)
                    wf.writeframes(data)

            stream.stop_stream()
            stream.close()

        except:
            logger.exception(f"Error with Microphone {sd.query_devices(mic_index)['name']}")
            event = MessageEvent(f"Something went wrong trying to start your recording! \nPlease contact the support team. \n\nInformation: {sd.query_devices(mic_index)['name']}")
            QCoreApplication.instance().postEvent(self.handler, event)

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

    def stop_recording(self):
        if not self.is_recording:
            logger.info("Tried to stop Recording but no recording is in progress.")
            return

        self.is_recording = False
        self.shutdown_event.set()  # Signal the recording threads to finish

        # Ensure the threads have finished
        self.recording_thread1.join()
        self.recording_thread2.join()

        session_id = self.current_session_id
        if not session_id or session_id not in self.sessions:
            logger.error("Error: Session not found.")
            return

        temp_filename1 = self.sessions[session_id]["temp_filename1"]
        temp_filename2 = self.sessions[session_id]["temp_filename2"]

        # Combine the two temporary files into a combined .wav file
        combined_filename_path = os.path.join(self.temp_folder, f"temp_combined_{uuid.uuid4().hex}.wav")
        self.transcription_mapping[combined_filename_path] = None
        self.combine_wav_files(temp_filename1, temp_filename2, combined_filename_path)

        # Remove temporary files
        os.remove(temp_filename1)
        os.remove(temp_filename2)

        # Start transcribing the saved audio file
        self.start_transcribe_file(combined_filename_path)

        # Cleanup: remove session from the sessions dictionary after processing
        del self.sessions[session_id]

        return combined_filename_path

    def start_transcribe_file(self, path,file_import=None, mapping_id=None):
        transcription_thread = threading.Thread(target=self.transcribe_file, args=(path,file_import,mapping_id,))
        transcription_thread.start()

    def transcribe_file(self, path, file_import, mapping_id):
        max_size = 26214400  # OpenAI's max size in bytes
        file_size = os.path.getsize(path)
        transcription_parts = []

        if file_size > max_size:
            transcription_parts = self.split_file(path, max_size)
        else:
            transcription_parts.append(path)

        transcript_texts = [""] * len(transcription_parts)
        transcription_threads = []

        def transcribe_part(file_path, index):
            try:
                with open(file_path, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(model=self.audio_model, file=audio_file)
                transcript_texts[index] = transcript.text
            except Exception as e:
                logger.error(f"Error transcribing file part {index}: {e}")

        for i, part_path in enumerate(transcription_parts):
            thread = threading.Thread(target=transcribe_part, args=(part_path, i))
            transcription_threads.append(thread)
            thread.start()

        for thread in transcription_threads:
            thread.join()

        full_transcript = "".join(transcript_texts)

        if file_import is None:  # When recording
            while self.transcription_mapping[path] is None:
                pass

            project_folder = os.path.join(self.data_folder, self.transcription_mapping[path])
            project_name = self.transcription_mapping[path]

            mapping_id = path

        else:  # When importing a file
            project_folder = '\\'.join(str(path).split('\\')[:-1])
            project_name = project_folder.split('\\')[-1]

        transcript_file_path = os.path.join(self.transcription_mapping[mapping_id],'transcript.txt')
        with open(transcript_file_path, 'w') as f:
            f.write(full_transcript)

        if file_import is None:
            try:
                shutil.copyfile(path, os.path.join(project_name, project_name.split('\\')[::-1][0] + '.wav'))
            except Exception as e:
                logger.error(f"Error copying audio file: {e}")

        self.handler.populate_recordings()

        # Clean up temporary files
        for part_path in transcription_parts:
            if os.path.exists(part_path):
                os.remove(part_path)
        if os.path.exists(path) and file_import is None:
            os.remove(path)

        # Invoke the methods to create keynotes and protocols
        keynote_thread = self.start_create_keynote(mapping_id)
        protocol_thread = self.start_create_protocol(mapping_id)

        # Wait for the threads to finish
        keynote_thread.join()
        protocol_thread.join()

        self.transcription_mapping.pop(mapping_id)

    def split_file(self, file_path, max_size):
        # Array to store temp file names
        temp_files = []

        try:
            with open(file_path, 'rb') as file:
                while True:
                    # Read a chunk of max_size
                    data = file.read(max_size)
                    if not data:
                        break  # Exit loop if no more data

                    # Generate a unique file name using UUID
                    temp_file_name = f"temp_split_{uuid.uuid4()}.wav"
                    temp_file_path = os.path.join(self.temp_folder, temp_file_name)

                    # Write the chunk to the temp file
                    with open(temp_file_path, 'wb') as temp_file:
                        temp_file.write(data)

                    # Add the temp file name to the list
                    temp_files.append(temp_file_path)

        except IOError as e:
            print(f"An error occurred: {e}")

        return temp_files

    def start_create_keynote(self, mapping_id):
        keynote_thread = threading.Thread(target=self.create_keynote, args=(mapping_id,))
        keynote_thread.start()

        return keynote_thread

    def start_create_protocol(self, mapping_id):
        protocol_thread = threading.Thread(target=self.create_protocol, args=(mapping_id,))
        protocol_thread.start()

        return protocol_thread

    def create_keynote(self, mapping_id):
        path = os.path.join(self.transcription_mapping[mapping_id], 'transcript.txt')
        f = open(path)
        transcription_text = f.read()
        f.close()

        keynote_text = self.openai_client.chat.completions.create(model=self.chat_model, messages=[self.system_message_keynote,{'role':'user','content':f'This will be your basis on which you will create your keynotes: \n{transcription_text}'}])

        path = os.path.join(self.transcription_mapping[mapping_id], 'transcript.txt')
        f = open(path.replace('transcript', 'keynote'), 'w+')
        f.write(keynote_text.choices[0].message.content)
        f.close()

    def create_protocol(self, mapping_id):
        path = os.path.join(self.transcription_mapping[mapping_id], 'transcript.txt')
        f = open(path)
        transcription_text = f.read()
        f.close()


        config.read(config_path)
        template = config['Templates']['current_template']
        template = open(f'{os.path.join(os.getenv("APPDATA"),"TranscriptionApp","Assets","custom-Templates",template)}.md','r').read()

        protocol_text = self.openai_client.chat.completions.create(model=self.chat_model, messages=[self.system_message_protocol,{'role':'user','content':f'This will be your basis on which you will create your protcol: \n{transcription_text}\n\nThis will be your Template: \n{template}'}])

        path = os.path.join(self.transcription_mapping[mapping_id], 'transcript.txt')
        f = open(path.split('.')[0].replace('transcript','protocol')+'.md', 'w+')
        f.write(protocol_text.choices[0].message.content)
        f.close()