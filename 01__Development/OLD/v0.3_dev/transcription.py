import wave
import speech_recognition as sr
import pyaudio
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

from PyQt6.QtCore import QEvent, QCoreApplication

# Configure logging
logging.basicConfig(filename=str(os.path.join(os.getenv('APPDATA'), 'TranscriptionApp','transcription.log')), level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

# Event Classes
class MessageEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, message):
        super().__init__(MessageEvent.EVENT_TYPE)
        self.message = message

class AudioRecorder():

    def __init__(self, handler):
        super().__init__()

        self.openai_client = OpenAI(api_key = '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') #TODO: implement secure api key

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
        self.p = pyaudio.PyAudio()

        f = open(os.path.join(self.program_folder, 'system_message.json'))
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



    def start_transcribe_file(self, path, file_import=None):
        transcription_thread = threading.Thread(target=self.transcribe_file, args=(path,file_import,))
        transcription_thread.start()

    def transcribe_file(self, path, file_import):
        if file_import == None: # When recording
            audio_file = open(path, 'rb')
            transcript = self.openai_client.audio.transcriptions.create(model=self.audio_model, file=audio_file)
            audio_file.close()

            f = open(str(path.split('.')[0] + '.txt'), 'w+')
            f.write(transcript.text)
            f.close()

            while self.transcription_mapping[path] == None:
                pass

            project_folder = os.path.join(self.data_folder,self.transcription_mapping[path])
            project_name = project_folder.split('\\')[::-1][0]

            # Copy the transcribed audio and text to the desired DATA folder
            try:
                shutil.copyfile(path, os.path.join(project_folder, self.transcription_mapping[path] + '.wav'))
            except:
                logger.exception(f"Error copying file to DATA folder: {os.path.join(project_folder, self.transcription_mapping[path] + '.wav')} does not exist!")
                event = MessageEvent('Something went wrong trying to save your recording! \nPlease contact the support team.')
                QCoreApplication.instance().postEvent(self.handler, event)

            if os.path.exists(os.path.join(project_folder, self.transcription_mapping[path] + '.wav')):
                logger.info(f"Recording saved to {os.path.join(project_folder, self.transcription_mapping[path] + '.wav')}.")

            try:
                shutil.copyfile(path.replace('.wav','.txt'), os.path.join(project_folder, self.transcription_mapping[path] + '_transcript' + '.txt'))
            except:
                logger.exception(f"Error copying file to DATA folder: {os.path.join(project_folder, self.transcription_mapping[path] + '.txt')} does not exist!")
                event = MessageEvent('Something went wrong trying to save your transcription! \nplease contact the support team.')
                QCoreApplication.instance().postEvent(self.handler, event)

            if os.path.exists(os.path.join(project_folder, self.transcription_mapping[path] + '.txt')):
                logger.info(f"Transcription saved to {os.path.join(project_folder, self.transcription_mapping[path] + '.txt')}.")

            self.transcription_mapping.pop(path)

            self.handler.populate_recordings()

            os.remove(path)
            os.remove(path.replace('.wav','.txt'))

        else:   # When importing a file
            project_folder = '\\'.join(str(path).split('\\')[:-1])
            project_name = project_folder.split('\\')[::-1][0]

            audio_file = open(path, 'rb')
            transcript = self.openai_client.audio.transcriptions.create(model=self.audio_model, file=audio_file)
            audio_file.close()

            f = open(str(path.split('.')[0] + '_transcript' + '.txt'), 'w+')
            f.write(transcript.text)
            f.close()

        text_file_location = os.path.join(project_folder,f'{project_name}_transcript.txt')

        self.start_create_keynote(text_file_location)
        self.start_create_protocol(text_file_location)

    def start_create_keynote(self, path):
        keynote_thread = threading.Thread(target=self.create_keynote, args=(path,))
        keynote_thread.start()

    def start_create_protocol(self, path):
        protocol_thread = threading.Thread(target=self.create_protocol, args=(path,))
        protocol_thread.start()

    def create_keynote(self, path):
        f = open(path)
        transcription_text = f.read()
        f.close()

        keynote_text = self.openai_client.chat.completions.create(model=self.chat_model, messages=[self.system_message_keynote,{'role':'user','content':f'This will be your basis on which you will create your keynotes: \n{transcription_text}'}])

        f = open(path.replace('_transcript', '_keynote'), 'w+')
        f.write(keynote_text.choices[0].message.content)
        f.close()

    def create_protocol(self, path):
        f = open(path)
        transcription_text = f.read()
        f.close()

        protocol_text = self.openai_client.chat.completions.create(model=self.chat_model, messages=[self.system_message_protocol,{'role':'user','content':f'This will be your basis on which you will create your protcol: \n{transcription_text}'}])

        f = open(path.replace('_transcript','_protocol'), 'w+')
        f.write(protocol_text.choices[0].message.content)
        f.close()