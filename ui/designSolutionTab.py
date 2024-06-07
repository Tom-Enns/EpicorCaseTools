import wx
from ui.richTextTab import RichTextTab
from services.googleAIService import get_solution_statement


def escape_js_string(s):
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\"", "\\\"")


class SolutionTab(RichTextTab):
    def __init__(self, parent, case_tab):
        super(SolutionTab, self).__init__(parent)
        self.case_tab = case_tab
        get_solution_button = wx.Button(self, label='Generate Solution')
        get_solution_button.Bind(wx.EVT_BUTTON, self.on_get_solution)
        self.Sizer.Add(get_solution_button, 0, wx.ALL | wx.CENTER, 5)

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
        escaped_response = escape_js_string(response)
        self.case_tab.log_js_message(self.web_view, f"Generated Solution: {escaped_response}")
        script = f"""
        simplemde.value(`{escaped_response}`);
        """
        self.web_view.RunScript(script)