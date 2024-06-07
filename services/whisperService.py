import whisper
from pydub import AudioSegment
import os

def convert_audio_to_text(file_path):
    # Determine the file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    # Supported formats
    supported_formats = ['.mp3', '.mp4', '.wav', '.m4a', '.flac', '.ogg', '.wma']

    if file_extension not in supported_formats:
        raise ValueError(f"Unsupported file format: {file_extension}")

    # Convert audio file to WAV format using pydub
    audio = AudioSegment.from_file(file_path)
    wav_file_path = file_path.replace(file_extension, ".wav")
    audio.export(wav_file_path, format="wav")

    # Load Whisper model
    model = whisper.load_model("base")

    # Transcribe audio using Whisper with fp16 set to False
    result = model.transcribe(wav_file_path, fp16=False)
    transcribed_text = result['text']

    # Clean up the temporary WAV file
    os.remove(wav_file_path)

    return transcribed_text