import wx
import json
from services.documentService import convert_doc_to_text, extract_sections_from_doc
from services.openAIService import OpenAIService
from services.pineconeService import PineconeService
from services.epicorService import EpicorService
import pyperclip



epicor_service = EpicorService()

class QueryTab(wx.Panel):
    def __init__(self, parent):
        super(QueryTab, self).__init__(parent)
        self.last_case_number = None
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Case number input
        self.case_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        vbox.Add(self.case_input, flag=wx.EXPAND | wx.ALL, border=5)

        self.case_input.Bind(wx.EVT_KILL_FOCUS, self.on_input_focus_lost)
        self.case_input.Bind(wx.EVT_TEXT_ENTER, self.on_input_enter)

        # Attachments list
        self.attachments_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        vbox.Add(self.attachments_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # Download and query button
        self.query_button = wx.Button(self, label="Download and Query")
        self.query_button.Bind(wx.EVT_BUTTON, self.on_download)
        vbox.Add(self.query_button, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

    def on_download(self, event):
         # Get selected document
        index = self.attachments_list.GetFirstSelected()
        if index == -1:
            wx.MessageBox('No attachment selected')
            return

        case_num = int(self.case_input.GetValue())
        filename = self.attachments_list.GetItem(index, 0).GetText()
        xFileRefNum = int(self.attachments_list.GetItem(index, 2).GetText())  # Add this line

        # Download the file
        file_path = self.download_file(case_num, filename, xFileRefNum)  # Modify this line
        if not file_path:
            wx.MessageBox('File could not be downloaded')
            return

        # Extract sections and query services
        sections = extract_sections_from_doc(file_path)
        need = sections['need']

        openai_service = OpenAIService()
        embeddings_data = openai_service.generate_embeddings(need)
        embeddings = embeddings_data['data'][0]['embedding']

        pinecone_service = PineconeService()
        results = pinecone_service.query(embeddings, 20)

        # Extract case numbers from results, sort, remove duplicates and current case number
        case_numbers = sorted(set(int(match['id'].split('-')[1]) for match in results['matches']), reverse=True)
        case_numbers = [case for case in case_numbers if case != case_num][:3]

        case_sections = {}
        # For each case number, show a popup with attachments
        for case in case_numbers:
            attachments = epicor_service.get_case_by_id(case)
            if attachments:
                dialog = wx.SingleChoiceDialog(self, "Select an attachment", f"Attachments for case {case}", [att['FileName'] for att in attachments])
                if dialog.ShowModal() == wx.ID_OK:
                    selected_attachment = attachments[dialog.GetSelection()]
                    # Download the selected attachment and extract sections
                    print(f"XFileRefNum: {selected_attachment['XFileRefNum']}")
                    content = epicor_service.download_file(selected_attachment['XFileRefNum'])
                    print(f"Downloaded content: {content}")
                    if content:
                        file_path = epicor_service.save_attachment(case, selected_attachment['FileName'], content)
                        full_text = convert_doc_to_text(file_path)

                        # And then add the full text to the dictionary
                        case_sections[case] = full_text

        # Print the JSON of the sections for all cases
        print(json.dumps(case_sections)) 
        # Load the prompt.txt file
        with open('prompt.txt', 'r') as file:
            prompt_text = file.read()

        # Replace {designneed} with the design need from the current case
        prompt_text = prompt_text.replace('{designneed}', need)

        # Replace {oldcasestext} with the text version of case_sections
        prompt_text = prompt_text.replace('{oldcasestext}', json.dumps(case_sections))

        # Copy the final text to the clipboard
        pyperclip.copy(prompt_text)
        wx.MessageBox('Prompt copied to clipboard', 'Information', wx.OK | wx.ICON_INFORMATION)
        
    def get_attachments(self, case_num):
        self.attachments_list.DeleteAllItems()

        attachments = epicor_service.get_case_by_id(case_num)
        if attachments:
            self.populate_attachments_list(attachments)

    def populate_attachments_list(self, attachments):
        self.attachments_list.ClearAll()

        self.attachments_list.InsertColumn(0, 'FileName')
        self.attachments_list.SetColumnWidth(0, 300)

        self.attachments_list.InsertColumn(1, 'DocTypeID')

        self.attachments_list.InsertColumn(2, 'XFileRefNum')
        self.attachments_list.SetColumnWidth(2, 0)

        for i, attachment in enumerate(attachments):
            self.add_attachment_to_list(i, attachment)

    def add_attachment_to_list(self, i, attachment):
        file_name = attachment['FileName'].split('\\')[-1]
        self.attachments_list.InsertItem(i, file_name)

        doc_type_id = str(attachment.get('DocTypeID', 'N/A'))
        self.attachments_list.SetItem(i, 1, doc_type_id)

        xFileRefNum = str(attachment['XFileRefNum'])
        self.attachments_list.SetItem(i, 2, xFileRefNum)

    def on_input_focus_lost(self, event):
            self.retrieve_attachments_if_case_changed()
            event.Skip()

    def on_input_enter(self, event):
        self.retrieve_attachments_if_case_changed()
        event.Skip()

    def retrieve_attachments_if_case_changed(self):
        try:
            case_num = int(self.case_input.GetValue())
        except ValueError:
            return

        if case_num != self.last_case_number:
            self.get_attachments(case_num)
            self.last_case_number = case_num
    
    def download_file(self, case_num, filename, xFileRefNum):
        content = epicor_service.download_file(xFileRefNum)
        if content:
            file_path = epicor_service.save_attachment(case_num, filename, content)
            if not file_path:
                print(f"File could not be saved: {filename}")
        else:
            print(f"No content to write for: {filename}")
        return file_path if content else None