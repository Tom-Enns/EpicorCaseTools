import json
import wx
from components.richTextComponent import RichTextTab
from services.googleAIService import generate_google_ai_response


class DesignComponentsTab(RichTextTab):
    def __init__(self, parent, case_tab):
        super(DesignComponentsTab, self).__init__(parent)
        self.case_tab = case_tab
        generate_design_components_button = wx.Button(self, label='Generate Design Components')
        generate_design_components_button.Bind(wx.EVT_BUTTON, self.on_generate_design_components)
        self.Sizer.Add(generate_design_components_button, 0, wx.ALL | wx.CENTER, 5)

    def on_generate_design_components(self, event):
        if not self.case_tab.role:
            wx.MessageBox('Role is not set. Please set it in the settings.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        solution = self.case_tab.page6.web_view.RunScript('simplemde.value();')

        if not solution:
            wx.MessageBox('Please ensure the Solution is filled.', 'Missing Information',
                          wx.OK | wx.ICON_WARNING)
            return

        prompt = f"Generate the design components for the following solution statement:\n\n{solution}\n\nReturn this in a markdown table."
        response = generate_google_ai_response(self.case_tab.role, prompt)
        escaped_response = json.dumps(response)
        script = f"""
        simplemde.value('{escaped_response}');
        """
        self.web_view.RunScript(script)
