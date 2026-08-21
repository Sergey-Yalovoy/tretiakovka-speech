from audio.service import AudioService
from storage.local import LocalFileStorage
from tts.silero_tts import SileroTTS

speakers = ['aidar', 'baya', 'eugene', 'kseniya', 'xenia']
with open('test-text', 'r') as f:
    text = f.read()

storage = LocalFileStorage(
    root="./media",
)

tts = SileroTTS(speaker='kseniya',
                max_chunk_size=300,
                )

audio_service = AudioService(
    tts=tts,
    storage=storage,
)

audio = audio_service.generate(
   text
)

print(audio.key)


# storage = S3AudioStorage(
#     bucket="audio",
#     endpoint_url="http://minio:9000",
#     region_name="us-east-1",
# )
#
# tts = SileroTTS()
#
# audio_service = AudioService(
#     tts=tts,
#     storage=storage,
# )