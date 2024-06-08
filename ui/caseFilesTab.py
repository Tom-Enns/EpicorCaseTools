import wx
from ui.downloadTab import DownloadTab
from ui.uploadTab import UploadTab
from ui.caseUpdateTab import CaseUpdateTab
from ui.designNeedTab import DesignNeedTab
from ui.designDirectionsTab import DirectionsTab
from ui.designSolutionTab import SolutionTab
#from ui.designSummaryTab import ProblemSummaryTab
#from ui.designComponentsTab import DesignComponentsTab
from services.epicorService import EpicorService
from services.googleAIService import load_examples, load_role


def escape_js_string(s):
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\"", "\\\"")


class CaseTab(wx.Panel):
    def __init__(self, parent):
        super(CaseTab, self).__init__(parent)
        self.epicor_service = EpicorService()

        # Load examples and role
        self.solution_examples = load_examples('samples/solution_examples.json')
        self.problem_summary_examples = load_examples('samples/problem_summary_examples.json')
        self.role = load_role('samples/systemprompt.txt')

        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)  # Create a horizontal box sizer

        # Text box for the case number
        hbox.Add(wx.StaticText(self, label="Case Number:"), flag=wx.LEFT | wx.TOP, border=5)
        self.case_number_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox.Add(self.case_number_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)  # Set proportion to 1

        # Load button
        load_button = wx.Button(self, label="Load")
        hbox.Add(load_button, flag=wx.LEFT | wx.TOP, border=5)
        load_button.Bind(wx.EVT_BUTTON, self.on_case_number_updated)

        vbox.Add(hbox, flag=wx.EXPAND | wx.ALL, border=5)  # Add the horizontal box sizer to the vertical box sizer

        # Create a notebook (tab control)
        self.notebook = wx.Notebook(self)

        # Create the page windows as children of the notebook
        self.page1 = DownloadTab(self.notebook, self)
        self.page2 = UploadTab(self.notebook, self)
        self.page3 = CaseUpdateTab(self.notebook, self)
        self.page4 = DesignNeedTab(self.notebook, self)
        self.page5 = DirectionsTab(self.notebook)
        self.page6 = SolutionTab(self.notebook, self)
        #self.page7 = ProblemSummaryTab(self.notebook, self)
        #self.page8 = DesignComponentsTab(self.notebook, self)

        # Add the pages to the notebook with the label to show on the tab
        self.notebook.AddPage(self.page1, "Download")
        self.notebook.AddPage(self.page2, "Upload")
        self.notebook.AddPage(self.page3, "Update")
        self.notebook.AddPage(self.page4, "Design Need")
        self.notebook.AddPage(self.page5, "Directions")
        self.notebook.AddPage(self.page6, "Solution")
        #self.notebook.AddPage(self.page7, "Problem Summary")
        #self.notebook.AddPage(self.page8, "Design Components")

        # Add notebook to the main sizer
        vbox.Add(self.notebook, 1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        # Bind events
        self.case_number_text.Bind(wx.EVT_KILL_FOCUS, self.on_case_number_updated)
        self.case_number_text.Bind(wx.EVT_TEXT_ENTER, self.on_case_number_updated)

        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed)

    def get_case_number(self):
        return self.case_number_text.GetValue()

    def on_case_number_updated(self, event):
        self.page1.refresh_data()
        self.page2.refresh_data()
        self.page3.refresh_data()
        event.Skip()

    def on_tab_changed(self, event):
        if event.GetSelection() in [0, 1]:  # DownloadTab or UploadTab
            self.page1.refresh_data()
            self.page2.refresh_data()
            self.page3.refresh_data()
        event.Skip()

    def log_js_message(self, web_view, message):
        escaped_message = escape_js_string(message)
        web_view.RunScript(f'logMessage(`{escaped_message}`);')

    def clear_fields(self):
        self.page4.clear_fields()
        self.page5.clear_fields()
        self.page6.web_view.RunScript('simplemde.value("");')
        self.page7.web_view.RunScript('simplemde.value("");')
        self.page8.web_view.RunScript('simplemde.value("");')
