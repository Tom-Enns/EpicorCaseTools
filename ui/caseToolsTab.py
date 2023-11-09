import wx
import traceback
from services.caseService import CaseService

class CaseToolsTab(wx.Panel):
    def __init__(self, parent):
        super(CaseToolsTab, self).__init__(parent)

        self.case_service = CaseService()
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Text box for the start case number
        self.start_case_number_text = wx.TextCtrl(self)
        vbox.Add(self.start_case_number_text, flag=wx.EXPAND | wx.ALL, border=5)

        # Text box for the end case number
        self.end_case_number_text = wx.TextCtrl(self)
        vbox.Add(self.end_case_number_text, flag=wx.EXPAND | wx.ALL, border=5)

        # Button to start the embedding process
        self.embed_cases_button = wx.Button(self, label="Embed Cases")
        vbox.Add(self.embed_cases_button, flag=wx.EXPAND | wx.ALL, border=5)
        self.embed_cases_button.Bind(wx.EVT_BUTTON, self.on_embed_cases_button_clicked)

        self.SetSizer(vbox)

    def on_embed_cases_button_clicked(self, event):
        try:
            start_case_number = int(self.start_case_number_text.GetValue())
            end_case_number = int(self.end_case_number_text.GetValue())
            self.case_service.embed_cases(range(start_case_number, end_case_number + 1))
        except Exception as e:
            error_message = str(e) + "\n\n" + traceback.format_exc()
            wx.MessageBox(error_message, 'Error', wx.OK | wx.ICON_ERROR)