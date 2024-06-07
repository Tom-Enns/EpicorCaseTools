import wx
import os
import pyperclip
from services.meetingParserService import MeetingParserService


class TeamsTab(wx.Panel):
    def __init__(self, parent):
        super(TeamsTab, self).__init__(parent)

        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.openButton = wx.Button(self, label='Open File')
        self.openButton.Bind(wx.EVT_BUTTON, self.onOpenFile)
        vbox.Add(self.openButton, flag=wx.EXPAND | wx.ALL, border=5)

        self.outputText = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        vbox.Add(self.outputText, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

    def onOpenFile(self):
        print(os.getcwd())
        wildcard = "Text files (*.txt;*.vtt)|*.txt;*.vtt"
        dialog = wx.FileDialog(self, "Open Text File", wildcard=wildcard)

        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()

            cleaned_content = MeetingParserService.remove_timestamps(path)

            with open('samples/airole.txt', 'r', encoding='utf-8') as file:
                airole_text = file.read()

            output_text = airole_text.replace('{meetingtranscript}', cleaned_content)

            self.outputText.SetValue(output_text)
            pyperclip.copy(output_text)

        dialog.Destroy()
