import wx
import os
import tempfile
import base64
from services.epicorService import EpicorService
from services.docService import DocService
import wx.lib.mixins.listctrl as listmix
from configparser import ConfigParser

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)


class FileSelectionDialog(wx.Dialog, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, files):
        super(FileSelectionDialog, self).__init__(parent, title="Select a Document", size=(600, 400))

        self.files = files

        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.list_ctrl.InsertColumn(0, 'FileName', width=300)
        self.list_ctrl.InsertColumn(1, 'Location', width=100)
        self.list_ctrl.InsertColumn(2, 'DocTypeID', width=100)

        for file in files:
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), file['FileName'])
            self.list_ctrl.SetItem(index, 1, file['location'])
            self.list_ctrl.SetItem(index, 2, file['DocTypeID'])

        ok_button = wx.Button(self, wx.ID_OK)
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(ok_button)
        hbox.Add(cancel_button, flag=wx.LEFT, border=5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        vbox.Add(hbox, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        self.SetSizer(vbox)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated, self.list_ctrl)

    def on_item_activated(self, event):
        self.EndModal(wx.ID_OK)

    def get_selected_file(self):
        index = self.list_ctrl.GetFirstSelected()
        if index == -1:
            return None
        return self.files[index]


class DesignNeedTab(wx.Panel):
    def __init__(self, parent, case_tab):
        super(DesignNeedTab, self).__init__(parent)
        self.DOC_PATH = DOC_PATH
        self.design_need_text = None
        self.case_tab = case_tab
        self.epicor_service = EpicorService()
        self.doc_service = DocService()
        self.init_ui()

    def init_ui(self):
        design_vbox = wx.BoxSizer(wx.VERTICAL)
        design_vbox.Add(wx.StaticText(self, label='Design Need:'), flag=wx.LEFT | wx.TOP, border=5)
        self.design_need_text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        design_vbox.Add(self.design_need_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        get_design_need_button = wx.Button(self, label='Get Design Need From Case Doc')
        get_design_need_button.Bind(wx.EVT_BUTTON, self.on_get_design_need)
        design_vbox.Add(get_design_need_button, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(design_vbox)

    def on_get_design_need(self, event):
        case_number = self.case_tab.get_case_number()
        if not case_number:
            wx.MessageBox('Please enter a case number.', 'Error', wx.OK | wx.ICON_ERROR)
            return

        # Clear all fields except for the case field
        #self.case_tab.clear_fields()

        attachments = self.epicor_service.get_case_by_id(int(case_number))
        local_files = self.get_local_files(case_number)
        files = self.combine_files(attachments, local_files)
        print(f'we found files{files}')

        if files:
            dialog = FileSelectionDialog(self, files)
            if dialog.ShowModal() == wx.ID_OK:
                selected_file = dialog.get_selected_file()
                if selected_file:
                    if selected_file['location'] == 'Epicor':
                        self.load_design_need(selected_file['XFileRefNum'])
                    elif selected_file['location'] == 'Local':
                        self.load_local_design_need(selected_file['path'])
            dialog.Destroy()
        else:
            wx.MessageBox('No attachments found for the selected case.', 'No Attachments', wx.OK | wx.ICON_INFORMATION)

    def get_local_files(self, case_number):
        case_folder_path = os.path.join(self.DOC_PATH, str(case_number))
        if not os.path.exists(case_folder_path):
            return []

        files = []
        for file_name in os.listdir(case_folder_path):
            files.append({
                'FileName': file_name,
                'DocTypeID': '',
                'XFileRefNum': '',
                'location': 'Local',
                'path': os.path.join(case_folder_path, file_name)
            })
        return files

    def combine_files(self, epicor_files, local_files):
        combined_files = []
        for file in epicor_files:
            file['location'] = 'Epicor'
            file['FileName'] = file['DrawDesc']
            combined_files.append(file)
        combined_files.extend(local_files)
        return combined_files

    def load_design_need(self, x_file_ref_num):
        file_content = self.epicor_service.download_file(x_file_ref_num)
        if file_content:
            temp_file_path = os.path.join(tempfile.gettempdir(), f"temp_{x_file_ref_num}.docx")
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
                print(f"File written to {temp_file_path} with size {len(file_content)} bytes")

            sections = self.doc_service.extract_all_sections_from_design_doc(temp_file_path)
            design_need = sections.get("Need", "")
            self.design_need_text.SetValue(design_need)
        else:
            wx.MessageBox('Failed to download the selected document.', 'Download Error', wx.OK | wx.ICON_ERROR)

    def load_local_design_need(self, file_path):
        sections = self.doc_service.extract_all_sections_from_design_doc(file_path)
        design_need = sections.get("Need", "")
        self.design_need_text.SetValue(design_need)

    def clear_fields(self):
        self.design_need_text.SetValue('')
