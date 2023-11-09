import wx
import os
import base64
from configparser import ConfigParser
from services.epicorService import EpicorService

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

epicor_service = EpicorService()

class UploadTab(wx.Panel):

    def __init__(self, parent):
        super(UploadTab, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.case_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.case_input, flag=wx.EXPAND | wx.ALL, border=5)

        self.files_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        vbox.Add(self.files_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.files_list.InsertColumn(0, 'Files')
        self.files_list.SetColumnWidth(0, 350)

        upload_button = wx.Button(self, label="Upload")
        vbox.Add(upload_button, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        self.case_input.Bind(wx.EVT_KILL_FOCUS, self.on_input_focus_lost)
        self.case_input.Bind(wx.EVT_TEXT_ENTER, self.load_files_for_case)
        upload_button.Bind(wx.EVT_BUTTON, self.on_upload_button_clicked)

    def on_input_focus_lost(self, event):
        self.load_files_for_case(event)
        event.Skip()

    def load_files_for_case(self, event):
        case_num = self.case_input.GetValue()
        case_folder_path = os.path.join(DOC_PATH, case_num)

        if not os.path.exists(case_folder_path):
            return

        self.populate_files_list(case_folder_path)

    def populate_files_list(self, case_folder_path):
        print("loadingUploadFilesList")
        files = os.listdir(case_folder_path)
        print(files)
        self.files_list.ClearAll()
        self.files_list.InsertColumn(0, 'Files')
        self.files_list.SetColumnWidth(0, 350)
        for i, file in enumerate(files):
            self.files_list.InsertItem(i, file)

    def on_upload_button_clicked(self, event):
        selected_index = self.files_list.GetFirstSelected()
        if selected_index == -1:
            wx.MessageBox('No file selected')
            return

        file_name = self.files_list.GetItem(selected_index, 0).GetText()

        doc_type = self.get_document_type()
        if doc_type:
            self.upload_document(file_name, doc_type)

    def get_document_type(self):
        doc_type_dialog = wx.SingleChoiceDialog(self, "What type of document is this?", "Document Type", ["Design Doc", "Supporting Doc"])
        if doc_type_dialog.ShowModal() == wx.ID_OK:
            choice = doc_type_dialog.GetStringSelection()
            return "OGDocs" if choice == "Design Doc" else "Supp"

    def upload_document(self, file_name, doc_type):
        case_num = self.case_input.GetValue()
        case_folder_path = os.path.join(DOC_PATH, case_num)
        file_path = os.path.join(case_folder_path, file_name)

        with open(file_path, 'rb') as f:
            encoded_content = base64.b64encode(f.read()).decode('utf-8')

        self.handle_upload_response(epicor_service.upload_document_logic(case_num, file_name, doc_type, encoded_content))

    def handle_upload_response(self, response):
        if response is not None:
            if response.status_code == 200:
                wx.MessageBox('File uploaded successfully!', 'Success', wx.OK | wx.ICON_INFORMATION)
            else:
                # This will handle cases like 400, 403, 500, etc.
                wx.MessageBox(f'Failed to upload file. Server responded with: {response.status_code}', 'Error',
                              wx.OK | wx.ICON_ERROR)

            print('Response HTTP Status Code:', response.status_code)
            print('Response HTTP Response Body:', response.content)
        else:
            wx.MessageBox('HTTP Request failed', 'Error', wx.OK | wx.ICON_ERROR)
