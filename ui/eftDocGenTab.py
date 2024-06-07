# File: EpicorCaseTools-main/ui/eftDocGenTab.py
import base64

import wx
import os
from services.epicorService import EpicorService
from services.eftDocService import extract_eft_data, write_eft_data, save_updated_eft_doc
from services.caseService import CaseService
from configparser import ConfigParser

config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

class EFTDocGenTab(wx.Panel):
    def __init__(self, parent):
        super(EFTDocGenTab, self).__init__(parent)
        self.epicor_service = EpicorService()
        self.case_service = CaseService()
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(self, label='Case Number:'), flag=wx.LEFT | wx.TOP, border=5)
        self.case_number_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox.Add(self.case_number_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        load_button = wx.Button(self, label='Load')
        hbox.Add(load_button, flag=wx.LEFT | wx.TOP, border=5)
        load_button.Bind(wx.EVT_BUTTON, self.on_case_number_updated)
        vbox.Add(hbox, flag=wx.EXPAND | wx.ALL, border=5)

        form_sizer = wx.FlexGridSizer(8, 2, 10, 10)

        self.add_text_field(form_sizer, 'Case:', 'case')
        self.add_text_field(form_sizer, 'Customer:', 'customer')
        self.add_text_field(form_sizer, 'Database:', 'database')
        self.add_dropdown_field(form_sizer, 'Transaction Type:', 'transaction_type',
                                ['Payroll', 'AP Payment', 'Lockbox', 'Positive Pay', 'Other'])
        self.add_text_field(form_sizer, 'Bank:', 'bank')
        self.add_text_field(form_sizer, 'File Type:', 'file_type')
        self.add_text_field(form_sizer, 'Spec Sheet File Name:', 'spec_sheet_file_name')
        self.add_decimal_field(form_sizer, 'Quoted Hours:', 'quoted_hours', 20)

        vbox.Add(form_sizer, 0, wx.EXPAND | wx.ALL, 10)

        submit_button = wx.Button(self, label='Submit')
        submit_button.Bind(wx.EVT_BUTTON, self.on_submit)
        vbox.Add(submit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.SetSizer(vbox)
    def add_text_field(self, sizer, label, name):
        sizer.Add(wx.StaticText(self, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
        text_ctrl = wx.TextCtrl(self, name=name)
        sizer.Add(text_ctrl, 0, wx.EXPAND)

    def add_dropdown_field(self, sizer, label, name, choices):
        sizer.Add(wx.StaticText(self, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
        dropdown = wx.Choice(self, name=name, choices=choices)
        sizer.Add(dropdown, 0, wx.EXPAND)

    def add_decimal_field(self, sizer, label, name, default_value):
        sizer.Add(wx.StaticText(self, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
        decimal_ctrl = wx.TextCtrl(self, name=name, value=str(default_value))
        sizer.Add(decimal_ctrl, 0, wx.EXPAND)

    def on_case_number_updated(self, event):
        case_number = self.case_number_text.GetValue()
        if case_number:
            attachments = self.epicor_service.get_case_by_id(int(case_number))
            if attachments:
                doc_choices = [f"{doc['FileName'].split('/')[-1]} ({doc['XFileRefNum']})" for doc in attachments]
                with wx.SingleChoiceDialog(self, 'Select a document:', 'Document Selection', doc_choices) as dialog:
                    if dialog.ShowModal() == wx.ID_OK:
                        selected_doc = attachments[dialog.GetSelection()]
                        self.load_eft_data(selected_doc['XFileRefNum'])
            else:
                wx.MessageBox('No attachments found for the selected case.', 'No Attachments',
                              wx.OK | wx.ICON_INFORMATION)

    def load_eft_data(self, x_file_ref_num):
        file_content = self.epicor_service.download_file(x_file_ref_num)
        if file_content:
            case_number = self.case_number_text.GetValue()
            if case_number:
                case_folder_path = os.path.join(DOC_PATH, str(case_number))
                os.makedirs(case_folder_path, exist_ok=True)
                file_name = f"Downloaded_File_{x_file_ref_num}.docx"
                design_file_name = f'Design - Case {case_number} V1.docx'
                if not os.path.exists(os.path.join(case_folder_path, design_file_name)):
                    dialog = wx.MessageDialog(self,
                                              'The design document doesn\'t exist in the case folder. Do you want to rename it?',
                                              'Rename Design Document', wx.YES_NO | wx.ICON_QUESTION)
                    if dialog.ShowModal() == wx.ID_YES:
                        file_name = design_file_name
                    dialog.Destroy()
                saved_file_path = os.path.join(case_folder_path, file_name)
                with open(saved_file_path, 'wb') as dest_file:
                    dest_file.write(base64.b64decode(file_content))
                print(f"File saved successfully: {saved_file_path}")  # Logging statement
                eft_data = extract_eft_data(saved_file_path)
                print(f"Extracted EFT data: {eft_data}")  # Logging statement
                self.populate_form_fields(eft_data)
            else:
                wx.MessageBox('Please enter a valid case number.', 'Invalid Case Number', wx.OK | wx.ICON_WARNING)
        else:
            wx.MessageBox('Failed to download the selected design document.', 'Download Error', wx.OK | wx.ICON_ERROR)
    def populate_form_fields(self, eft_data):
        self.FindWindowByName('case').SetValue(eft_data.get('CaseNum', ''))
        self.FindWindowByName('customer').SetValue(eft_data.get('Company', ''))
        self.FindWindowByName('database').SetValue(eft_data.get('Database', ''))
        self.FindWindowByName('transaction_type').SetStringSelection(eft_data.get('TransactionType', ''))
        self.FindWindowByName('bank').SetValue(eft_data.get('BankName', ''))
        self.FindWindowByName('file_type').SetValue(eft_data.get('FileType', ''))
        self.FindWindowByName('spec_sheet_file_name').SetValue(eft_data.get('SpecSheetFileName', ''))
        self.FindWindowByName('quoted_hours').SetValue(str(eft_data.get('QuotedHours', '')))
    def on_submit(self, event):
        case_number = self.case_number_text.GetValue()
        if not case_number:
            wx.MessageBox('Please enter a case number.', 'Case Number Required', wx.OK | wx.ICON_WARNING)
            return

        # Retrieve form data
        case = self.FindWindowByName('case').GetValue()
        customer = self.FindWindowByName('customer').GetValue()
        database = self.FindWindowByName('database').GetValue()
        transaction_type = self.FindWindowByName('transaction_type').GetStringSelection()
        bank = self.FindWindowByName('bank').GetValue()
        file_type = self.FindWindowByName('file_type').GetValue()
        spec_sheet_file_name = self.FindWindowByName('spec_sheet_file_name').GetValue()
        quoted_hours = float(self.FindWindowByName('quoted_hours').GetValue())

        # Update the EFT design document
        attachments = self.epicor_service.get_case_attachment_list(int(case_number))
        design_docs = [a for a in attachments if a['DocTypeID'] == 'OGDocs']
        if design_docs:
            selected_doc = design_docs[0]  # Assume the first design document
            file_path = self.epicor_service.download_file(selected_doc['XFileRefNum'])
            if file_path:
                # Update the case using the existing methods from caseService
                self.case_service.update_case_part_and_price(int(case_number), 'DevCon', quoted_hours, 215)
                quote_number = self.case_service.create_and_attach_quote_to_case(int(case_number))
                self.case_service.complete_current_case_task(int(case_number))
                self.case_service.assign_current_case_task(int(case_number), 'Steve Maksymetz')
                self.case_service.add_case_comment(int(case_number), 'EFT design document updated and quote created.')

                updated_data = {
                    'CaseNum': case,
                    'QuoteNum': quote_number,
                    'Company': customer,
                    'Database': database,
                    'TransactionType': transaction_type,
                    'BankName': bank,
                    'FileType': file_type,
                    'SpecSheetFileName': spec_sheet_file_name,
                    'QuotedHours': quoted_hours,
                    'Status': '1'
                }
                write_eft_data(file_path, updated_data)
                updated_file_path = os.path.join(DOC_PATH, f"Updated_EFT_Design_{case_number}.docx")
                save_updated_eft_doc(file_path, updated_file_path)

                # Upload the updated EFT design document
                with open(updated_file_path, 'rb') as f:
                    encoded_content = base64.b64encode(f.read()).decode('utf-8')
                self.epicor_service.upload_document_logic(int(case_number), f"Updated_EFT_Design_{case_number}.docx", 'OGDocs', encoded_content)

                wx.MessageBox('EFT design document updated, case updated, and document uploaded successfully.', 'Success', wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox('Failed to download the selected design document.', 'Download Error', wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox('No design documents found for the selected case.', 'No Design Documents', wx.OK | wx.ICON_INFORMATION)