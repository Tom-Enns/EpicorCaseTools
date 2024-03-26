import wx
import traceback
import re
from services.epicorService import EpicorService
from services.loggingService import LoggingService
from services.caseService import CaseService

logger = LoggingService.get_logger(__name__)

class CaseUpdateTab(wx.Panel):
    def __init__(self, parent, case_tab):
        super(CaseUpdateTab, self).__init__(parent)
        self.case_tab = case_tab
        self.epicor_service = EpicorService()
        self.case_service = CaseService()
        self.init_ui()


    def get_case_number(self):
        case_number_str = self.case_tab.get_case_number()
        logger.info(f"Getting case number from case tab: {case_number_str}")
        if not case_number_str:  # Add this check
            return None
        try:
            logger.info(f"Found Case number: {case_number_str}")
            return int(case_number_str)
        except ValueError:
            print(f"Invalid case number: {case_number_str}")
            return None

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Text box for the quantity
        vbox.Add(wx.StaticText(self, label="Hours:"), flag=wx.LEFT | wx.TOP, border=5)
        self.quantity_text = wx.TextCtrl(self)
        vbox.Add(self.quantity_text, flag=wx.EXPAND | wx.ALL, border=5)

        # Checkbox for completing the current task
        self.complete_task_checkbox = wx.CheckBox(self, label="Complete Current Task")
        vbox.Add(self.complete_task_checkbox, flag=wx.EXPAND | wx.ALL, border=5)
        self.complete_task_checkbox.SetValue(True)  # Checked by default

        # Checkbox for creating and attaching a quote
        self.create_attach_quote_checkbox = wx.CheckBox(self, label="Create and Attach Quote?")
        vbox.Add(self.create_attach_quote_checkbox, flag=wx.EXPAND | wx.ALL, border=5)
        self.create_attach_quote_checkbox.SetValue(False)  # Unchecked by default

        # Text box for the assignee
        self.assignee_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        vbox.Add(wx.StaticText(self, label="Assign Next Task To"), flag=wx.ALL, border=5)
        vbox.Add(self.assignee_input, flag=wx.EXPAND | wx.ALL, border=5)

        # Text box for the case comment
        vbox.Add(wx.StaticText(self, label="Case Comment:"), flag=wx.LEFT | wx.TOP, border=5)
        self.case_comment_text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        vbox.Add(self.case_comment_text, flag=wx.EXPAND | wx.ALL, border=5)

        # Button to start the update process
        self.update_case_button = wx.Button(self, label="Update Case:")
        vbox.Add(self.update_case_button, flag=wx.EXPAND | wx.ALL, border=5)
        self.update_case_button.Bind(wx.EVT_BUTTON, self.on_update_case_button_clicked)

        self.SetSizer(vbox)
    
    def refresh_data(self):
        case_num = self.get_case_number()
        logger.info(f"Refreshing data for case {case_num}")
        if case_num is None:
            self.assignee_input.SetValue('')
        elif case_num:
            case_info = self.epicor_service.get_case_info(case_num)

            # Update checkbox label
            self.complete_task_checkbox.SetLabel(f"Complete {case_info['CurrentTask']}")


            if case_info['CurrentTask'] == 'Write Design Spec':
                assignee = re.match(r'(.+?):', case_info['CaseOwner']).group(1)
            elif case_info['CurrentTask'] == 'Assign Resource':
                assignee = 'Steve Maksymetz'
            else:
                assignee = ''

            self.assignee_input.SetValue(assignee)

    def on_update_case_button_clicked(self, event):
        try:
            case_number = self.get_case_number()
            part_num = 'DevCon'
            quantity_str = self.quantity_text.GetValue()
            unit_price = 215
            hours_updated = False
            if quantity_str:
                quantity = float(quantity_str)
                self.epicor_service.update_case_part_and_price(case_number, part_num, quantity, unit_price)
                hours_updated = True
            quote_attached = False
            quote_number = None
            if self.create_attach_quote_checkbox.IsChecked():
                quote_number = self.case_service.create_and_attach_quote_to_case(case_number)
                if quote_number:
                    quote_attached = True
            assign_next_to_name = self.assignee_input.GetValue()
            task_completed = False
            task_assigned = False
            if self.complete_task_checkbox.IsChecked():
                is_task_complete = self.epicor_service.complete_current_case_task(case_number)
                if is_task_complete:
                    task_completed = True
                    if assign_next_to_name:
                        assign_response = self.epicor_service.assign_current_case_task(case_number, assign_next_to_name)
                        if assign_response:
                            task_assigned = True
            case_comment = self.case_comment_text.GetValue()
            comment_added = False
            if case_comment:
                self.epicor_service.add_case_comment(case_number, case_comment)
                comment_added = True
            message = 'Case Update Summary:\n'
            if hours_updated:
                message += f'- Hours added successfully\n'
            if quote_attached:
                message += f'- Quote {quote_number} created and attached successfully\n'
            if task_completed:
                message += '- Task completed successfully\n'
            if task_assigned:
                message += '- Next task assigned successfully\n'
            if comment_added:
                message += '- Case comment added successfully\n'
            wx.MessageBox(message, 'Case Update Status', wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            error_message = str(e) + '\n\n' + traceback.format_exc()
            wx.MessageBox(error_message, 'Error', wx.OK | wx.ICON_ERROR)