import os
import wave
import pyaudio
import threading
import asyncio
from deepgram import Deepgram
import json
import requests

class AudioRecorder:
    def __init__(self, deepgram_api_key):
        self.audio_frames = []
        self.is_recording = False
        self.stream = None
        self.live_transcription_text = ""
        self.transcribtion_file = None
        self.language = 'de-De'  # Update this based on your preference
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

        # Create a new event loop for the thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Use asyncio.run to run the coroutine
        response = loop.run_until_complete(
            self.deepgram_client.transcription.prerecorded(
                {'buffer': audio_data, 'mimetype': 'audio/wav'},
                {'punctuate': True, 'diarize': True}
            )
        )

        try:
            transcription = response['results']['channels'][0]['alternatives'][0]['transcript']
            self.live_transcription_text += transcription + '\n'  # Append transcription
            print(transcription)
        except Exception as e:
            print(f"Error in transcribing: {e}")

    def stop_recording(self, save_path):
        if not self.is_recording:
            print("No recording is in progress.")
            return

        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()

        wf = wave.open(save_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

        self.transcription_file = save_path.replace('.wav', '.json')
        with open(self.transcription_file, 'w') as f:
            json.dump({'transcription': self.live_transcription_text, 'summary': os.path.basename(save_path)}, f)

        # Call the summarization method here
        self.summarize_transcription(self.transcription_file)

        self.live_transcription_text = ""  # Reset the live transcription text

        print(f"Recording saved to {save_path}.")
        print(f"Transcription saved to {self.transcription_file}.")

    def start_transcribe_file(self, path):
        transcription_thread = threading.Thread(target=self._run_async_transcription, args=(path,))
        transcription_thread.start()

    def _run_async_transcription(self, path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.transcribe_file(path))

    async def transcribe_file(self, path):
        with open(path, 'rb') as audio_file:
            response = await self.deepgram_client.transcription.prerecorded(
                {'buffer': audio_file, 'mimetype': 'audio/wav'},
                {'punctuate': True, 'diarize': True}
            )
        try:
            transcription = response['results']['channels'][0]['alternatives'][0]['transcript']
            transcription_file = path.replace('.wav', '.json')
            with open(transcription_file, 'w') as f:
                json.dump({'transcription': transcription, 'summary': os.path.basename(path)}, f)

            # Call the summarization method here
            self.summarize_transcription(transcription_file)

            print(f"Transcription saved to {transcription_file}.")
        except Exception as e:
            print(f"Error in transcribing: {e}")


    def summarize_transcription(self, transcription_file):
        # Load the transcription from the file
        with open(transcription_file, 'r') as f:
            data = json.load(f)
        transcription = data['transcription']

        # Setup the request data for pplx-api
        headers = {
            'Authorization': 'Bearer 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',
            'Content-Type': 'application/json',
        }
        payload = {
            "model": "mistral-7b-instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following text: {transcription}"}
            ]
        }

        # Make the POST request to pplx-api
        response = requests.post('https://api.perplexity.ai/chat/completions', headers=headers, json=payload)
        response_data = response.json()

        try:
            # Extract the summary from the response
            summary = response_data['choices'][0]['message']['content']

            # Update the summary in the existing JSON file
            data['summary'] = summary
            with open(transcription_file, 'w') as f:
                json.dump(data, f, indent=4)

            print(f"Summary saved to {transcription_file}.")

        except Exception as e:
            print(f"Error in summarizing: {e}")
