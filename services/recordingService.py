# services/recordingService.py
import os

import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import tempfile
import threading
import queue

class AudioRecorder:
    def __init__(self, sample_rate=44100, chunk_duration=5):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_frames = int(self.chunk_duration * self.sample_rate)
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_buffer = []
        self.record_thread = None

    def start_recording(self):
        self.is_recording = True
        self.audio_buffer = []
        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.audio_queue.put(None)  # Signal to stop recording
        if self.record_thread:
            self.record_thread.join()

    def _record_audio(self):
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_queue.put(indata.copy())

        with sd.InputStream(callback=callback, channels=1, samplerate=self.sample_rate):
            while self.is_recording:
                sd.sleep(100)

    def process_audio(self):
        audio_array = np.concatenate(self.audio_buffer)
        output_file = os.path.join(tempfile.gettempdir(), "temp_recorded_audio.wav")
        wavfile.write(output_file, self.sample_rate, audio_array)
        return output_file

    def transcribe_audio(self, convert_audio_to_text):
        while True:
            chunk = self.audio_queue.get()
            if chunk is None:
                break  # Recording stopped

            self.audio_buffer.append(chunk)
            if len(self.audio_buffer) * chunk.shape[0] >= self.chunk_frames:
                output_file = self.process_audio()
                transcription = convert_audio_to_text(output_file)
                yield transcription
                self.audio_buffer = []

        if self.audio_buffer:
            output_file = self.process_audio()
            transcription = convert_audio_to_text(output_file)
            yield transcription
