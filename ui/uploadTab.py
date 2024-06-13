import sys
import subprocess
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


def handle_upload_response(response):
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


class UploadTab(wx.Panel):
    def __init__(self, parent, case_tab):
        super(UploadTab, self).__init__(parent)
        self.case_tab = case_tab
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.files_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        vbox.Add(self.files_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.files_list.InsertColumn(0, 'Files')
        self.files_list.SetColumnWidth(0, 350)

        upload_button = wx.Button(self, label="Upload")
        vbox.Add(upload_button, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        upload_button.Bind(wx.EVT_BUTTON, self.on_upload_button_clicked)
        self.files_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_file_double_clicked)  # Bind the double-click event

    def get_case_number(self):
        case_number_str = self.case_tab.get_case_number()
        if not case_number_str:  # Add this check
            return None
        try:
            return int(case_number_str)
        except ValueError:
            print(f"Invalid case number: {case_number_str}")
            return None

    def refresh_data(self):
        case_num = self.get_case_number()
        if not case_num:  # Add this check
            return
        case_folder_path = os.path.join(DOC_PATH, str(case_num))  # Convert case_num to string

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
        doc_type_dialog = wx.SingleChoiceDialog(self, "What type of document is this?", "Document Type",
                                                ["Design Doc", "Supporting Doc"])
        if doc_type_dialog.ShowModal() == wx.ID_OK:
            choice = doc_type_dialog.GetStringSelection()
            return "OGDocs" if choice == "Design Doc" else "Supp"

    def upload_document(self, file_name, doc_type):
        case_num = self.get_case_number()
        case_folder_path = os.path.join(DOC_PATH, str(case_num))
        file_path = os.path.join(case_folder_path, file_name)

        with open(file_path, 'rb') as f:
            encoded_content = base64.b64encode(f.read()).decode('utf-8')

        handle_upload_response(
            epicor_service.upload_document_logic(case_num, file_name, doc_type, encoded_content))

    def on_file_double_clicked(self, event):
        # New event handler for double-click
        selected_index = event.GetIndex()
        file_name = self.files_list.GetItem(selected_index, 0).GetText()
        case_num = self.get_case_number()
        if case_num is None:
            wx.MessageBox("Case number is not valid.", "Error")
            return
        file_path = os.path.join(DOC_PATH, str(case_num), file_name)
        if os.path.exists(file_path):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                else:  # macOS, Linux
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, file_path])
            except Exception as e:
                wx.MessageBox(f"Failed to open file: {e}", "Error")
        else:
            wx.MessageBox("File does not exist.", "Error")
