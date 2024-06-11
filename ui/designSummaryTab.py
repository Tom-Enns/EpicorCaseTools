import os

import wx
from services.googleAIService import generate_google_ai_response
from utilities.utilities import escape_js_string


class DesignSummaryTab(wx.Panel):
    def __init__(self, parent, case_tab):
        super(DesignSummaryTab, self).__init__(parent)

        self.case_tab = case_tab

        vbox = wx.BoxSizer(wx.VERTICAL)

        get_solution_button = wx.Button(self, label='Generate Summary')
        get_solution_button.Bind(wx.EVT_BUTTON, self.on_generate_problem_summary)

        self.web_view = wx.html2.WebView.New(self)
        self.web_view.LoadURL("file://" + os.path.abspath("components/markdown_editor.html"))

        vbox.Add(self.web_view, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(get_solution_button, 0, wx.ALL | wx.CENTER, 5)

        self.SetSizer(vbox)

    def on_generate_problem_summary(self, event):
        if not self.case_tab.role:
            wx.MessageBox('Role is not set. Please set it in the settings.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        design_need = self.case_tab.page4.design_need_text.GetValue()
        solution = self.web_view.RunScript('simplemde.value();')

        if not design_need or not solution:
            wx.MessageBox('Please ensure both Design Need and Solution are filled.', 'Missing Information',
                          wx.OK | wx.ICON_WARNING)
            return

        prompt = f"I need you to create only the problem summary for the following Design Need and solution.\nDesign Need: {design_need}\nSolution: {solution}"
        response = generate_google_ai_response(self.case_tab.role, prompt)
        escaped_response = escape_js_string(response)
        script = f"""
            try {{
                simplemde.value("{escaped_response}");
                logMessage("Content set successfully");
            }} catch (e) {{
                logMessage("Error setting content: " + e.message);
            }}
            """
        self.web_view.RunScript(script)
