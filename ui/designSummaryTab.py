import wx
from ui.richTextTab import RichTextTab
from services.googleAIService import generate_google_ai_response

def escape_js_string(s):
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\"", "\\\"")

class ProblemSummaryTab(RichTextTab):
    def __init__(self, parent, case_tab):
        super(ProblemSummaryTab, self).__init__(parent)
        self.case_tab = case_tab
        generate_problem_summary_button = wx.Button(self, label='Generate Problem Summary')
        generate_problem_summary_button.Bind(wx.EVT_BUTTON, self.on_generate_problem_summary)
        self.Sizer.Add(generate_problem_summary_button, 0, wx.ALL | wx.CENTER, 5)

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
        self.case_tab.log_js_message(self.web_view, f"Generated Problem Summary: {escaped_response}")
        script = f"""
        simplemde.value(`{escaped_response}`);
        """
        self.web_view.RunScript(script)
