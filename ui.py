import wx
import os
import base64
import subprocess
import sys
from configparser import ConfigParser
from epicorlogic import get_case_by_id, download_file, save_attachment, upload_document_logic

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

# Main application window
class Mywin(wx.Frame):

    def __init__(self, parent, title):
        # Load configuration variables
        config_vars = self.load_config_vars()
        
        # Check configuration variables
        self.check_config_vars(config_vars)

        # Initialize window
        super(Mywin, self).__init__(parent, title=title, size=(390, 270), style=wx.DEFAULT_FRAME_STYLE | (wx.STAY_ON_TOP if config.getboolean('DEFAULT', 'ALWAYS_ON_TOP', fallback=False) else 0))

        # Set icon
        self.set_icon()

        # Initialize panel and notebook
        panel = wx.Panel(self)
        self.nb = wx.Notebook(panel)

        # Initialize tabs
        self.init_tabs()

        # Adjust the tabs' margin
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.nb, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)

        self.Show()

    def load_config_vars(self):
        return {
            'BASE_URL': config.get('DEFAULT', 'BASE_URL', fallback=None),
            'SIXS_API_KEY': config.get('DEFAULT', 'SIXS_API_KEY', fallback=None),
            'SIXS_BASIC_AUTH': config.get('DEFAULT', 'SIXS_BASIC_AUTH', fallback=None),
            'DOC_PATH': config.get('DEFAULT', 'DOC_PATH', fallback=None),
        }

    def check_config_vars(self, config_vars):
        for var_name, var_value in config_vars.items():
            if not var_value:
                wx.MessageBox(f"Configuration variable {var_name} is not set or is blank", "Warning", wx.OK | wx.ICON_WARNING)

    def set_icon(self):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(bundle_dir, 'CaseToolsIcon.ico')
        self.SetIcon(wx.Icon(icon_path))

    def init_tabs(self):
        # Tabs
        self.downloadTab = DownloadTab(self.nb)
        self.uploadTab = UploadTab(self.nb)
        self.settingsTab = SettingsTab(self.nb)  # New settings tab

        self.nb.AddPage(self.downloadTab, " Download ")
        self.nb.AddPage(self.uploadTab, " Upload ")
        self.nb.AddPage(self.settingsTab, " Settings ")  # Add the settings tab to the notebook


# Settings tab
class SettingsTab(wx.Panel):

    def __init__(self, parent):
        super(SettingsTab, self).__init__(parent)

        # Load configuration
        self.config = ConfigParser()
        self.config.read(os.path.expanduser('~/.myapp.cfg'))

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(6, 2, 5, 5)

        # BASE URL
        self.add_text_field(grid, "BASE URL:", 'BASE_URL')

        # SIXS API KEY
        self.add_text_field(grid, "API KEY:", 'SIXS_API_KEY')

        # SIXS BASIC AUTH
        self.add_text_field(grid, "BASIC AUTH:", 'SIXS_BASIC_AUTH')

        # DOC PATH
        self.add_doc_path_field(grid)

        # ALWAYS ON TOP
        self.add_checkbox_field(grid, "ALWAYS ON TOP:", 'ALWAYS_ON_TOP')

        grid.AddGrowableCol(1, 1)  # Make the second column growable

        vbox.Add(grid, 1, flag=wx.EXPAND)

        save_button = wx.Button(self, label="Save")
        vbox.Add(save_button, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        save_button.Bind(wx.EVT_BUTTON, self.on_save_button_clicked)

    def add_text_field(self, grid, label, config_key):
        grid.Add(wx.StaticText(self, label=label), flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        text_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        text_ctrl.SetValue(self.config.get('DEFAULT', config_key, fallback=''))
        grid.Add(text_ctrl, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=5)
        setattr(self, config_key, text_ctrl)

    def add_doc_path_field(self, grid):
        doc_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.DOC_PATH = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.DOC_PATH.SetValue(self.config.get('DEFAULT', 'DOC_PATH', fallback=''))
        doc_path_sizer.Add(self.DOC_PATH, proportion=1, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=5)
        select_folder_button = wx.Button(self, label="Select Folder")
        select_folder_button.Bind(wx.EVT_BUTTON, self.on_select_folder_button_clicked)
        doc_path_sizer.Add(select_folder_button, flag=wx.ALL, border=5)
        grid.Add(wx.StaticText(self, label="DOC PATH:"), flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        grid.Add(doc_path_sizer, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=5)

    def add_checkbox_field(self, grid, label, config_key):
        grid.Add(wx.StaticText(self, label=label), flag=wx.ALL | wx.ALIGN_RIGHT, border=5)
        checkbox = wx.CheckBox(self)
        checkbox.SetValue(self.config.getboolean('DEFAULT', config_key, fallback=False))
        grid.Add(checkbox, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=5)
        setattr(self, config_key, checkbox)

    def on_select_folder_button_clicked(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.DOC_PATH.SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_save_button_clicked(self, event):
        config_vars = {
            'BASE_URL': self.BASE_URL.GetValue(),
            'SIXS_API_KEY': self.SIXS_API_KEY.GetValue(),
            'SIXS_BASIC_AUTH': self.SIXS_BASIC_AUTH.GetValue(),
            'DOC_PATH': self.DOC_PATH.GetValue(),
        }

        # Check configuration variables
        self.check_config_vars(config_vars)

        # Save configuration
        self.config['DEFAULT'] = config_vars
        self.config['DEFAULT']['ALWAYS_ON_TOP'] = str(self.ALWAYS_ON_TOP.GetValue())  # Save the state of the checkbox

        with open(os.path.expanduser('~/.myapp.cfg'), 'w') as configfile:
            self.config.write(configfile)

        # Reload the configuration
        global config
        config.read(os.path.expanduser('~/.myapp.cfg'))

        # Update global variables
        global DOC_PATH
        DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

    def check_config_vars(self, config_vars):
        for var_name, var_value in config_vars.items():
            if not var_value:
                wx.MessageBox(f"Configuration variable {var_name} is not set or is blank", "Warning", wx.OK | wx.ICON_WARNING)
                return

class DownloadTab(wx.Panel):

    def __init__(self, parent):
        super(DownloadTab, self).__init__(parent)
        self.last_case_number = None
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.input, flag=wx.EXPAND | wx.ALL, border=5)

        self.attachments = wx.ListCtrl(self, style=wx.LC_REPORT)
        vbox.Add(self.attachments, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

        self.attachments.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_download)
        self.input.Bind(wx.EVT_KILL_FOCUS, self.on_input_focus_lost)
        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_input_enter)

    def on_input_focus_lost(self, event):
        self.retrieve_attachments_if_case_changed()
        event.Skip()

    def on_input_enter(self, event):
        self.retrieve_attachments_if_case_changed()
        event.Skip()

    def retrieve_attachments_if_case_changed(self):
        try:
            case_num = int(self.input.GetValue())
        except ValueError:
            return

        if case_num != self.last_case_number:
            self.get_attachments(case_num)
            self.last_case_number = case_num

    def get_attachments(self, case_num):
        self.attachments.DeleteAllItems()

        attachments = get_case_by_id(case_num)
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
        case_num = int(self.input.GetValue())

        self.download_file(case_num, filename, xFileRefNum)

    def download_file(self, case_num, filename, xFileRefNum):
        if filename.endswith(".docx"):
            self.handle_docx_file(case_num, filename)

        content = download_file(xFileRefNum)
        if content:
            file_path = save_attachment(case_num, filename, content)
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
            if os.name == 'nt':  # Check if the operating system is Windows
                file_path = file_path.replace('/', '\\')
            os.startfile(file_path)
        except Exception as e:
            print(f"Error opening file: {str(e)}")


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
        files = os.listdir(case_folder_path)
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

        self.handle_upload_response(upload_document_logic(case_num, file_name, doc_type, encoded_content))

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


app = wx.App()
Mywin(None, "Case Tools")
app.MainLoop()
