from typing import List, Any, Type

import wx
import os
import subprocess
import shutil
from configparser import ConfigParser
from services.epicorService import EpicorService

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

epicor_service = EpicorService()


def open_file(file_path):
    try:
        subprocess.run(["open", file_path])
        print(f"File opened: {file_path}")
    except Exception as e:
        print(f"Error opening file: {str(e)}")


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

        # 'Download' button
        self.download_button = wx.Button(self, label="Download All Supporting Docs")
        vbox.Add(self.download_button, flag=wx.EXPAND | wx.ALL, border=5)
        self.download_button.Bind(wx.EVT_BUTTON, self.on_download_button_click)

        # 'Create Design Doc' button
        self.create_design_doc_button = wx.Button(self, label="Create Design Doc")
        vbox.Add(self.create_design_doc_button, flag=wx.EXPAND | wx.ALL, border=5)
        self.create_design_doc_button.Bind(wx.EVT_BUTTON, self.on_create_design_doc)

        # Attachments list
        self.attachments = wx.ListCtrl(self, style=wx.LC_REPORT)
        vbox.Add(self.attachments, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.attachments.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate_list_item)
        self.SetSizer(vbox)

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

        cols = list(['FileName', 'DocTypeID', 'XFileRefNum'])
        col_width = wx.LIST_AUTOSIZE_USEHEADER

        for i in range(0, len(cols)):
            self.attachments.InsertColumn(i, cols[i])
            self.attachments.SetColumnWidth(i, col_width)

        for i, attachment in enumerate(attachments):
            self.add_attachment_to_list(i, attachment)

    def add_attachment_to_list(self, i, attachment):
        file_name = attachment['FileName'].split('\\')[-1]
        self.attachments.InsertItem(i, file_name)

        doc_type_id = str(attachment.get('DocTypeID', 'N/A'))
        self.attachments.SetItem(i, 1, doc_type_id)

        self.attachments.SetItem(i, 2, str(attachment['XFileRefNum']))

    def on_download_button_click(self, event):
        """
        Download button clicked. Download all attachments.
        :param event:
        :return:
        """
        for i in range(0, self.attachments.GetItemCount()):
            # Only download 'Supporting' docs or uncategorized.
            # We don't want to download things that have already been sent out, sign-offs, etc.
            doc_type_id = self.attachments.GetItem(i, 1).GetText()
            print(doc_type_id)
            if doc_type_id == '' or doc_type_id == 'Supp':
                self.download_file_by_list_index(i)

    def on_activate_list_item(self, event):
        """
        Download the double-clicked file
        :param event:
        """
        # What got clicked?
        selected_index = event.GetIndex()
        self.download_file_by_list_index(selected_index)

    def download_file_by_list_index(self, index):
        """
        Take an index from the attachment list and download the represented file.
        :param index: Row Index
        """
        filename = self.attachments.GetItem(index, 0).GetText()
        xFileRefNum = int(self.attachments.GetItem(index, 2).GetText())
        case_num = self.get_case_number()

        case_folder_path = os.path.join(DOC_PATH, str(case_num))

        # If this looks like a design doc, ask the user if the want to up the revision. V1, V2, etc
        filename = self.ask_to_rename_design_docs(case_folder_path, filename, case_num)

        content = epicor_service.download_file_by_xRefNum(xFileRefNum)
        if content:
            file_path = epicor_service.save_attachment(case_num, filename, content)
            if file_path:
                open_file(file_path)
        else:
            print(f"No content to write for: {filename}")

    def ask_to_rename_design_docs(self, case_folder_path, filename, case_num):
        """
        See if we have existing design docs. If this looks like a design doc, ask to rename it as the next version.
        :param case_folder_path: Path to the case folder
        :param filename: File we're downloading
        :param case_num: Case number
        :return: Chosen file name.
        """

        is_named_like_design_doc = filename.lower().endswith(".docx") and "design" in filename.lower()

        # If this isn't a design doc, we don't want to bother with renaming
        if not is_named_like_design_doc:
            return filename

        # We'll suggest renaming the design to that next available rev.
        design_version = 1
        proposed_design_file_name = f"Design - Case {case_num} V{design_version}.docx"

        # Let's start with V1 and find the next revision.
        while os.path.exists(os.path.join(case_folder_path, proposed_design_file_name)):
            design_version += 1
            proposed_design_file_name = f"Design - Case {case_num} V{design_version}.docx"

        # Ask user to change. If they decline, stick with original name.
        with wx.MessageDialog(self,
                              f"Do you want to rename '{filename}' to '{proposed_design_file_name}'?",
                              style=wx.YES_NO) as dialog:
            result = dialog.ShowModal()
            if result == wx.ID_YES:
                filename = proposed_design_file_name

        return filename

    def on_create_design_doc(self):
        # Get the case number
        case_num = self.get_case_number()
        if not case_num:
            wx.MessageBox('No case number selected')
            return

        # Define the source file path
        source_file_path = "/Users/tomenns/Documents/DevDesignDocTemplate.docx"

        # Define the destination file path
        design_file_name = f"Design - Case {case_num} V1.docx"
        case_folder_path = os.path.join(DOC_PATH, str(case_num))
        destination_file_path = os.path.join(case_folder_path, design_file_name)

        # Create the directory if it does not exist
        os.makedirs(case_folder_path, exist_ok=True)

        # Copy the file
        try:
            shutil.copyfile(source_file_path, destination_file_path)
            wx.MessageBox(f"Design doc created at {destination_file_path}")

            # Open the file
            subprocess.run(["open", destination_file_path], check=True)
        except Exception as e:
            print(f"Error creating design doc: {str(e)}")
