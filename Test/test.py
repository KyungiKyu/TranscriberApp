from pyannote.audio import Pipeline
import os

YOUR_AUTH_TOKEN = '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'
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                    use_auth_token=YOUR_AUTH_TOKEN)

diarization = pipeline(os.getcwd()+'\\DATA\\song.mp3')

with open("audio.rttm", "w") as rttm:
    diarization.write_rttm(rttm)