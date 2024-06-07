import wx
from ui.caseUpdateTab import CaseUpdateTab
from ui.uploadTab import UploadTab
from ui.downloadTab import DownloadTab


class CaseFilesTab(wx.Panel):
    def __init__(self, parent):
        super(CaseFilesTab, self).__init__(parent)

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
        notebook = wx.Notebook(self)

        # Create the page windows as children of the notebook
        self.page1 = DownloadTab(notebook, self)
        self.page2 = UploadTab(notebook, self)
        self.page3 = CaseUpdateTab(notebook, self)

        # Add the pages to the notebook with the label to show on the tab
        notebook.AddPage(self.page1, "Download")
        notebook.AddPage(self.page2, "Upload")
        notebook.AddPage(self.page3, "Update")

        # Add notebook to the main sizer
        vbox.Add(notebook, 1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        # Bind events
        self.case_number_text.Bind(wx.EVT_KILL_FOCUS, self.on_case_number_updated)
        self.case_number_text.Bind(wx.EVT_TEXT_ENTER, self.on_case_number_updated)

        notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed)

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
