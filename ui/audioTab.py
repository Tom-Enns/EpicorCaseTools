# ui/audioTab.py
import base64
import os
import tempfile
import threading
import wx
import re
from wx.html2 import WebView
from services.whisperService import convert_audio_to_text
from services.epicorService import EpicorService
from services.docService import DocService
from services.googleAIService import get_solution_statement, load_examples, load_role, generate_google_ai_response
from services.recordingService import AudioRecorder
from ui.richTextTab import RichTextTab

def escape_js_string(s):
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\"", "\\\"")

class AudioTab(wx.Panel):
    def __init__(self, parent):
        super(AudioTab, self).__init__(parent)

        self.epicor_service = EpicorService()
        self.doc_service = DocService()
        self.recorder = AudioRecorder()

        # Load examples and role
        self.solution_examples = load_examples('samples/solution_examples.json')
        self.problem_summary_examples = load_examples('samples/problem_summary_examples.json')
        self.role = load_role('samples/systemprompt.txt')

        # Main vertical box sizer
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Case Number
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self, label='Case Number:'), flag=wx.LEFT | wx.TOP, border=5)
        self.case_number_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox.Add(self.case_number_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(hbox, flag=wx.EXPAND | wx.ALL, border=5)

        # Notebook for sub-tabs
        self.notebook = wx.Notebook(self)

        # Design Need Tab
        design_need_tab = wx.Panel(self.notebook)
        design_vbox = wx.BoxSizer(wx.VERTICAL)
        design_vbox.Add(wx.StaticText(design_need_tab, label='Design Need:'), flag=wx.LEFT | wx.TOP, border=5)
        self.design_need_text = wx.TextCtrl(design_need_tab, style=wx.TE_MULTILINE)
        design_vbox.Add(self.design_need_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        get_design_need_button = wx.Button(design_need_tab, label='Get Design Need From Case Doc')
        get_design_need_button.Bind(wx.EVT_BUTTON, self.on_get_design_need)
        design_vbox.Add(get_design_need_button, 0, wx.ALL | wx.CENTER, 5)
        design_need_tab.SetSizer(design_vbox)
        self.notebook.AddPage(design_need_tab, 'Design Need')

        # Transcription Tab
        transcription_tab = wx.Panel(self.notebook)
        transcription_vbox = wx.BoxSizer(wx.VERTICAL)
        transcription_vbox.Add(wx.StaticText(transcription_tab, label='Transcription:'), flag=wx.LEFT | wx.TOP, border=5)
        self.transcription_box = wx.TextCtrl(transcription_tab, style=wx.TE_MULTILINE)
        transcription_vbox.Add(self.transcription_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.record_btn = wx.Button(transcription_tab, label="Record")
        self.record_btn.Bind(wx.EVT_BUTTON, self.on_record)
        transcription_vbox.Add(self.record_btn, 0, wx.ALL | wx.CENTER, 5)
        transcription_tab.SetSizer(transcription_vbox)
        self.notebook.AddPage(transcription_tab, 'Transcription')

        # Solution Tab
        solution_tab = RichTextTab(self.notebook)
        get_solution_button = wx.Button(solution_tab, label='Generate Solution')
        get_solution_button.Bind(wx.EVT_BUTTON, self.on_get_solution)
        solution_tab.Sizer.Add(get_solution_button, 0, wx.ALL | wx.CENTER, 5)
        self.notebook.AddPage(solution_tab, 'Solution')

        # Problem Summary Tab
        problem_summary_tab = RichTextTab(self.notebook)
        generate_problem_summary_button = wx.Button(problem_summary_tab, label='Generate Problem Summary')
        generate_problem_summary_button.Bind(wx.EVT_BUTTON, self.on_generate_problem_summary)
        problem_summary_tab.Sizer.Add(generate_problem_summary_button, 0, wx.ALL | wx.CENTER, 5)
        self.notebook.AddPage(problem_summary_tab, 'Problem Summary')

        # Design Components Tab
        design_components_tab = RichTextTab(self.notebook)
        generate_design_components_button = wx.Button(design_components_tab, label='Generate Design Components')
        generate_design_components_button.Bind(wx.EVT_BUTTON, self.on_generate_design_components)
        design_components_tab.Sizer.Add(generate_design_components_button, 0, wx.ALL | wx.CENTER, 5)
        self.notebook.AddPage(design_components_tab, 'Design Components')

        vbox.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(vbox)

        self.transcribed_text = ""

    def log_js_message(self, web_view, message):
        escaped_message = escape_js_string(message)
        web_view.RunScript(f'logMessage(`{escaped_message}`);')

    def clear_fields(self):
        self.design_need_text.SetValue('')
        self.transcription_box.SetValue('')
        self.notebook.GetPage(2).web_view.RunScript('simplemde.value("");')
        self.notebook.GetPage(3).web_view.RunScript('simplemde.value("");')
        self.notebook.GetPage(4).web_view.RunScript('simplemde.value("");')
        self.transcribed_text = ''

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

    def on_get_design_need(self, event):
        case_number = self.case_number_text.GetValue()
        if not case_number:
            wx.MessageBox('Please enter a case number.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        # Clear all fields except for the case field
        self.clear_fields()

        attachments = self.epicor_service.get_case_by_id(int(case_number))
        if attachments:
            doc_choices = [f"{doc['FileName'].split('/')[-1]} ({doc['XFileRefNum']})" for doc in attachments]
            with wx.SingleChoiceDialog(self, 'Select a document:', 'Document Selection', doc_choices) as dialog:
                if dialog.ShowModal() == wx.ID_OK:
                    selected_doc = attachments[dialog.GetSelection()]
                    self.load_design_need(selected_doc['XFileRefNum'])
        else:
            wx.MessageBox('No attachments found for the selected case.', 'No Attachments',
                          wx.OK | wx.ICON_INFORMATION)

    def load_design_need(self, x_file_ref_num):
        file_content = self.epicor_service.download_file(x_file_ref_num)
        if file_content:
            temp_file_path = os.path.join(tempfile.gettempdir(), f"temp_{x_file_ref_num}.docx")
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(base64.b64decode(file_content))

            sections = self.doc_service.extract_all_sections_from_design_doc(temp_file_path)
            design_need = sections.get("Need", "")
            self.design_need_text.SetValue(design_need)
        else:
            wx.MessageBox('Failed to download the selected document.', 'Download Error', wx.OK | wx.ICON_ERROR)

    def on_get_solution(self, event):
        if not self.role:
            wx.MessageBox('Role is not set. Please set it in the settings.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        design_need = self.design_need_text.GetValue()
        instructions = self.transcription_box.GetValue()

        if not design_need or not instructions:
            wx.MessageBox('Please ensure both Design Need and Transcription are filled.', 'Missing Information',
                          wx.OK | wx.ICON_WARNING)
            return

        final_input = f"The customer has requested the following: {design_need}\nCreate the solution statement only and do so based on the following instructions: {instructions}"
        response = get_solution_statement(self.solution_examples, self.role, final_input)
        escaped_response = escape_js_string(response)
        self.log_js_message(self.notebook.GetPage(2).web_view, f"Generated Solution: {escaped_response}")
        script = f"""
        simplemde.value(`{escaped_response}`);
        """
        self.notebook.GetPage(2).web_view.RunScript(script)

    def on_generate_problem_summary(self, event):
        if not self.role:
            wx.MessageBox('Role is not set. Please set it in the settings.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        design_need = self.design_need_text.GetValue()
        solution = self.notebook.GetPage(2).web_view.RunScript('simplemde.value();')

        if not design_need or not solution:
            wx.MessageBox('Please ensure both Design Need and Solution are filled.', 'Missing Information',
                          wx.OK | wx.ICON_WARNING)
            return

        prompt = f"I need you to create only the problem summary for the following Design Need and solution.\nDesign Need: {design_need}\nSolution: {solution}"
        response = generate_google_ai_response(self.role, prompt)
        escaped_response = escape_js_string(response)
        self.log_js_message(self.notebook.GetPage(3).web_view, f"Generated Problem Summary: {escaped_response}")
        script = f"""
        simplemde.value(`{escaped_response}`);
        """
        self.notebook.GetPage(3).web_view.RunScript(script)

    def on_generate_design_components(self, event):
        if not self.role:
            wx.MessageBox('Role is not set. Please set it in the settings.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        solution = self.notebook.GetPage(2).web_view.RunScript('simplemde.value();')

        if not solution:
            wx.MessageBox('Please ensure the Solution is filled.', 'Missing Information',
                          wx.OK | wx.ICON_WARNING)
            return

        prompt = f"Generate the design components for the following solution statement:\n\n{solution}\n\nReturn this in a markdown table."
        response = generate_google_ai_response(self.role, prompt)
        escaped_response = escape_js_string(response)
        self.log_js_message(self.notebook.GetPage(4).web_view, f"Generated Design Components: {escaped_response}")
        script = f"""
        simplemde.value(`{escaped_response}`);
        """
        self.notebook.GetPage(4).web_view.RunScript(script)
