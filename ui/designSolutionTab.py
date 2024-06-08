import json
import os

import wx
import wx.html2
from services.googleAIService import get_solution_statement


class SolutionTab(wx.Panel):
    def __init__(self, parent, case_tab):
        super(SolutionTab, self).__init__(parent)

        self.case_tab = case_tab

        vbox = wx.BoxSizer(wx.VERTICAL)

        get_solution_button = wx.Button(self, label='Generate Solution')
        get_solution_button.Bind(wx.EVT_BUTTON, self.on_get_solution)

        self.web_view = wx.html2.WebView.New(self)
        self.web_view.LoadURL("file://" + os.path.abspath("components/markdown_editor.html"))

        vbox.Add(self.web_view, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(get_solution_button, 0, wx.ALL | wx.CENTER, 5)

        self.SetSizer(vbox)

    def on_get_solution(self, event):
        if not self.case_tab.role:
            wx.MessageBox('Role is not set. Please set it in the settings.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        design_need = self.case_tab.page4.design_need_text.GetValue()
        instructions = self.case_tab.page5.transcription_box.GetValue()

        if not design_need or not instructions:
            wx.MessageBox('Please ensure both Design Need and Directions are filled.', 'Missing Information',
                          wx.OK | wx.ICON_WARNING)
            return

        final_input = (f"The customer has requested the following: {design_need}\nCreate the solution statement only "
                       f"and do so based on the following instructions: {instructions}")
        response = get_solution_statement(self.case_tab.solution_examples, self.case_tab.role, final_input)
        print(f'Response is: {response}')
        escaped_response = json.dumps(response)
        script = f"""
        simplemde.value({escaped_response});
        """
        self.web_view.RunScript(script)
