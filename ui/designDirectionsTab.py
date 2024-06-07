import wx
import threading
import re
from services.recordingService import AudioRecorder
from services.whisperService import convert_audio_to_text

class DirectionsTab(wx.Panel):
    def __init__(self, parent):
        super(DirectionsTab, self).__init__(parent)
        self.recorder = AudioRecorder()
        self.transcribed_text = ""
        self.init_ui()

    def init_ui(self):
        transcription_vbox = wx.BoxSizer(wx.VERTICAL)
        transcription_vbox.Add(wx.StaticText(self, label='Directions:'), flag=wx.LEFT | wx.TOP, border=5)
        self.transcription_box = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        transcription_vbox.Add(self.transcription_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.record_btn = wx.Button(self, label="Record")
        self.record_btn.Bind(wx.EVT_BUTTON, self.on_record)
        transcription_vbox.Add(self.record_btn, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(transcription_vbox)

    def on_record(self, event):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            self.record_btn.SetLabel("Record")
        else:
            self.recorder.start_recording()
            self.record_btn.SetLabel("Stop")
            self.start_transcription()

    def start_transcription(self):
        def transcribe():
            for transcription in self.recorder.transcribe_audio(convert_audio_to_text):
                if not self.is_gibberish(transcription):
                    self.transcribed_text += transcription + "\n"
                    wx.CallAfter(self.transcription_box.SetValue, self.transcribed_text)

        threading.Thread(target=transcribe).start()

    def is_gibberish(self, text):
        gibberish_pattern = re.compile(r'^[\d\.\%\s]+$')
        return bool(gibberish_pattern.match(text))

    def clear_fields(self):
        self.transcription_box.SetValue('')
        self.transcribed_text = ''
