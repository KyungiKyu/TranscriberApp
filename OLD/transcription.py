import os
import wave
import pyaudio
import threading
import asyncio
import aiohttp
from deepgram import Deepgram
import websockets
import json
import requests

class AudioRecorder:
    def __init__(self, deepgram_api_key):
<<<<<<< Updated upstream:OLD/transcription.py
        self.deepgram_api_key = deepgram_api_key
        self.deepgramLive = None
        self.loop = asyncio.get_event_loop()

    async def start_transcribing(self):
        # Initialize Deepgram SDK
        deepgram = Deepgram(self.deepgram_api_key)

        # Create a websocket connection to Deepgram
        try:
            self.deepgramLive = await deepgram.transcription.live({
                'punctuate': True,
                'interim_results': False,
                'language': 'en-US'
            })
        except Exception as e:
            print(f'Could not open socket: {e}')
            return

        # Register an event handler for receiving transcriptions
        self.deepgramLive.register_handler(self.deepgramLive.event.TRANSCRIPT_RECEIVED, self.handle_transcript)

        # URL of the streaming audio
        URL = 'http://stream.live.vc.bbcmedia.co.uk/bbc_world_service'

        # Start streaming audio to Deepgram
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as audio:
                while self.deepgramLive:
                    data = await audio.content.readany()
                    await self.deepgramLive.send(data)

                    # Break if no data is received
                    if not data:
                        break

        # Finish transcription
        await self.deepgramLive.finish()

    def handle_transcript(self, transcript):
        print("Transcript received: ", transcript)

    def start_recording(self,mic_index):
        if self.deepgramLive:
            print("Transcription is already in progress.")
            return

        # Start transcription in a separate thread
        threading.Thread(target=lambda: self.loop.run_until_complete(self.start_transcribing())).start()
        print("Transcription started.")

    def stop_recording(self, save_path):
        if not self.deepgramLive:
            print("No transcription in progress.")
            return

        # Stop the transcription
        self.loop.run_until_complete(self.deepgramLive.finish())
        self.deepgramLive = None
        print("Transcription stopped.")

    def _record(self):
=======
        self.audio_frames = []
        self.is_recording = False
        self.stream = None
        self.deepgram_socket = None
        self.live_transcription_text = ""
        self.deepgram_client = Deepgram(deepgram_api_key)
        self.language = 'de-De'  # Update this based on your preference

    def _record(self):
        p = pyaudio.PyAudio()
        self.stream = p.open(format=pyaudio.paInt16,
                             channels=1,
                             rate=16000,
                             input=True,
                             input_device_index=self.mic_index,
                             frames_per_buffer=1024)

>>>>>>> Stashed changes:transcription.py
        while self.is_recording:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.audio_frames.append(data)

        self.stream.stop_stream()
        self.stream.close()

    def start_recording(self, mic_index, language):
        if self.is_recording:
            print("Recording is already in progress.")
            return

        self.is_recording = True
        self.mic_index = mic_index

        recording_thread = threading.Thread(target=self._record)
        recording_thread.start()

<<<<<<< Updated upstream:OLD/transcription.py
=======
        print("Recording started.")

    def stop_recording(self, save_path):
        self.is_recording = False

        wf = wave.open(save_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()

        self.audio_frames = []  # Reset the audio frames buffer

        print(f"Recording saved to {save_path}.")
        self.start_transcribe_file(save_path)

>>>>>>> Stashed changes:transcription.py
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
