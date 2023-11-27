import wx
import os
import subprocess
from configparser import ConfigParser
from services.epicorService import EpicorService

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

epicor_service = EpicorService()

class DownloadTab(wx.Panel):

    def __init__(self, parent, case_tab):
        super(DownloadTab, self).__init__(parent)
        self.case_tab = case_tab
        self.last_case_number = None
        self.init_ui()
        self.refresh_data()

    def get_case_number(self):
        case_number_str = self.case_tab.get_case_number()
        if not case_number_str:  # Add this check
            return None
        try:
            return int(case_number_str)
        except ValueError:
            print(f"Invalid case number: {case_number_str}")
            return None

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.attachments = wx.ListCtrl(self, style=wx.LC_REPORT)
        vbox.Add(self.attachments, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        self.attachments.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_download)

    def refresh_data(self):
        case_num = self.get_case_number()
        if not case_num:  # Add this check
            return
        if case_num != self.last_case_number:
            self.get_attachments(case_num)
            self.last_case_number = case_num

    def get_attachments(self, case_num):
        self.attachments.DeleteAllItems()

        attachments = epicor_service.get_case_by_id(case_num)
        if attachments:
            self.populate_attachments_list(attachments)

    def populate_attachments_list(self, attachments):
        self.attachments.ClearAll()

        self.attachments.InsertColumn(0, 'FileName')
        self.attachments.SetColumnWidth(0, 300)

        self.attachments.InsertColumn(1, 'DocTypeID')

        self.attachments.InsertColumn(2, 'XFileRefNum')
        self.attachments.SetColumnWidth(2, 0)

        for i, attachment in enumerate(attachments):
            self.add_attachment_to_list(i, attachment)

    def add_attachment_to_list(self, i, attachment):
        file_name = attachment['FileName'].split('\\')[-1]
        self.attachments.InsertItem(i, file_name)

        doc_type_id = str(attachment.get('DocTypeID', 'N/A'))
        self.attachments.SetItem(i, 1, doc_type_id)

        self.attachments.SetItem(i, 2, str(attachment['XFileRefNum']))

    def on_download(self, event):
        index = self.attachments.GetFirstSelected()
        if index == -1:
            wx.MessageBox('No attachment selected')
            return

        filename = self.attachments.GetItem(index, 0).GetText()
        xFileRefNum = int(self.attachments.GetItem(index, 2).GetText())
        case_num = self.get_case_number()

        self.download_file(case_num, filename, xFileRefNum)

    def download_file(self, case_num, filename, xFileRefNum):
        if filename.endswith(".docx"):
            self.handle_docx_file(case_num, filename)

        content = epicor_service.download_file(xFileRefNum)
        if content:
            file_path = epicor_service.save_attachment(case_num, filename, content)
            if file_path:
                self.open_file(file_path)
        else:
            print(f"No content to write for: {filename}")

    def handle_docx_file(self, case_num, filename):
        design_file_name = f"Design - Case {case_num} V1.docx"
        case_folder_path = os.path.join(DOC_PATH, str(case_num))

        if not os.path.exists(os.path.join(case_folder_path, design_file_name)):
            dialog = wx.MessageDialog(self,
                                      "There is no Design V1 saved to this case folder yet, do you want to rename this file?",
                                      style=wx.YES_NO)
            result = dialog.ShowModal()
            if result == wx.ID_YES:
                filename = design_file_name
            dialog.Destroy()

    def open_file(self, file_path):
        try:
            subprocess.run(["open", file_path])
            print(f"File opened: {file_path}")
        except Exception as e:
            print(f"Error opening file: {str(e)}")