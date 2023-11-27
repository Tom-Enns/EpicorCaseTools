import wx
import json
from services.documentService import convert_doc_to_text, extract_sections_from_doc
from services.epicorService import EpicorService
from services.embeddingsService import EmbeddingsGeneratorService
from services.docService import DocService
import pyperclip
from services.loggingService import LoggingService

logger = LoggingService.get_logger(__name__)



epicor_service = EpicorService()

class QueryTab(wx.Panel):
    def __init__(self, parent):
        super(QueryTab, self).__init__(parent)
        self.last_case_number = None
        self.init_ui()
        self.embeddings_service = EmbeddingsGeneratorService()
        self.doc_service = DocService()

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
        xFileRefNum = int(self.attachments_list.GetItem(index, 2).GetText())  

        # Download the file
        file_path = self.download_file(case_num, filename, xFileRefNum)  
        if not file_path:
            wx.MessageBox('File could not be downloaded')
            return

        # Extract sections and query services
        sections = extract_sections_from_doc(file_path)
        ogneed = sections['need']

        results = self.embeddings_service.generate_and_find_similar_embeddings(ogneed, 20)

        logger.info(f"Results from Embeddings search are: {results}")

        # Extract case numbers from results, sort, remove duplicates and current case number

        case_numbers = sorted(set(int(match['metadata']['CaseNum']) for match in results['matches']), reverse=True)
        case_numbers = [case for case in case_numbers if case != case_num][:3]
        logger.info(f"Case numbers from Embeddings search are: {case_numbers}")

        case_sections = {}
        # For each case number, show a popup with attachments
        # For each case number, retrieve the 'Need', 'Problem', and 'Solution' from Epicor
        for case in case_numbers:
            case_info = epicor_service.get_case_info(case)
            if case_info:
                # Extract 'Need', 'Problem', and 'Solution' from case_info
                need = case_info.get('DesignNeed')
                problem = case_info.get('DesignProblem')
                solution = case_info.get('DesignSolution')

                # Check if all fields are filled out
                if all([need, problem, solution]):
                    # Add the extracted information to the dictionary
                    case_sections[case] = {'Need': need, 'Problem': problem, 'Solution': solution}
                else:
                    # Download the design document and extract the data
                    attachments = epicor_service.get_case_by_id(case)
                    if attachments:
                        dialog = wx.SingleChoiceDialog(self, "Select an attachment", f"Attachments for case {case}", [att['FileName'] for att in attachments])
                        if dialog.ShowModal() == wx.ID_OK:
                            selected_attachment = attachments[dialog.GetSelection()]
                            content = epicor_service.download_file(selected_attachment['XFileRefNum'])
                            if content:
                                file_path = epicor_service.save_attachment(case, selected_attachment['FileName'], content)
                                sections = self.doc_service.extract_all_sections_from_design_doc(file_path)
                                filtered_sections = {key: value for key, value in sections.items() if key in ['Need', 'Problem', 'Solution']}
                                case_sections[case] = filtered_sections

        # Print the JSON of the sections for all cases
        print(json.dumps(case_sections, indent=4))
        # Load the prompt.txt file
        with open('prompt.txt', 'r') as file:
            prompt_text = file.read()

        # Replace {designneed} with the design need from the current case
        prompt_text = prompt_text.replace('{designneed}', ogneed)

        # Replace {oldcasestext} with the text version of case_sections
        formatted_case_sections = json.dumps(case_sections, indent=4)
        prompt_text = prompt_text.replace('{oldcasestext}', formatted_case_sections)

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