# File: ui/caseListTab.py
import sys

import wx
from services.epicorService import EpicorService  # Ensure you have this import

class CaseListTab(wx.Panel):
    def __init__(self, parent):
        super(CaseListTab, self).__init__(parent)
        self.epicor_service = EpicorService()  # Instance of your Epicor service
        self.init_ui()
        self.load_cases()

    def init_ui(self):
        layout = wx.BoxSizer(wx.VERTICAL)

        # Top bar layout for filters and refresh button
        top_bar_layout = wx.BoxSizer(wx.HORIZONTAL)

        # Case Assignee Filter setup
        self.case_assignee_filter = wx.Choice(self, choices=[])
        top_bar_layout.Add(wx.StaticText(self, label="Case Assignee:"), 0, wx.ALL | wx.CENTER, 5)
        top_bar_layout.Add(self.case_assignee_filter, 1, wx.EXPAND | wx.ALL, 5)

        # Task Description Filter setup
        self.task_description_filter = wx.Choice(self, choices=[])
        top_bar_layout.Add(wx.StaticText(self, label="Task:"), 0, wx.ALL | wx.CENTER, 5)
        top_bar_layout.Add(self.task_description_filter, 1, wx.EXPAND | wx.ALL, 5)

        # Refresh Button
        img = wx.Image('refreshicon.png', wx.BITMAP_TYPE_ANY)
        # Scale the image to fit the size of standard buttons in your UI
        img = img.Scale(12, 12, wx.IMAGE_QUALITY_HIGH)  # Example size: 24x24 pixels
        refresh_icon = wx.Bitmap(img)
        self.refresh_button = wx.BitmapButton(self, id=wx.ID_ANY, bitmap=refresh_icon, size=(-1, -1))
        self.refresh_button.SetMinSize((30, 30))  # Ensure the button itself has a standard size, adjust as needed
        self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_clicked)
        top_bar_layout.Add(self.refresh_button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        layout.Add(top_bar_layout, 0, wx.EXPAND)

        layout.Add(top_bar_layout, 0, wx.EXPAND)

        # Cases list with updated columns
        self.cases_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        columns = [("Case", 100), ("Case Owner", 100), ("Case Assignee", 100), ("Customer", 150), ("Project", 100),
                   ("Description", 200), ("Task", 150), ("Task Start Date", 100),
                   ("Task Due Date", 100), ("Task Status", 100), ("Task Set", 100),
                   ("Quoted Hours", 100), ("Job Est Hours", 100), ("Act Hours", 100),
                   ("Lab Hours", 100), ("Case Est Hours", 100), ("Remain Hours", 100),
                   ("Days Since Last Comment", 150), ("Request Date", 100), ("Dev Start Date", 100),
                   ("Delivery Date", 100), ("Sched Hrs Remain", 100), ("Days Till Due Date", 100)]
        for i, (col, width) in enumerate(columns):
            self.cases_list.InsertColumn(i, col, width=width)

        layout.Add(self.cases_list, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(layout)

        # Bind filter event handlers
        self.case_assignee_filter.Bind(wx.EVT_CHOICE, self.on_filter_changed)
        self.task_description_filter.Bind(wx.EVT_CHOICE, self.on_filter_changed)

    def load_cases(self):
        self.cases = self.epicor_service.fetch_cases()
        case_assignees = sorted(set(case.get('SalesRep1_Name', 'Unknown') for case in self.cases if case.get('SalesRep1_Name')))
        task_descriptions = sorted(set(case.get('Task_TaskDescription', 'No Description') for case in self.cases))

        self.case_assignee_filter.SetItems(["All"] + case_assignees)
        self.task_description_filter.SetItems(["All"] + task_descriptions)
        self.case_assignee_filter.SetSelection(0)
        self.task_description_filter.SetSelection(0)

        self.update_cases_list()

    def update_cases_list(self):
        self.cases_list.DeleteAllItems()
        for case in self.cases:
            if self.should_case_be_displayed(case):
                # Prepare row values with appropriate handling of None values and formatting
                row_values = [
                    str(case.get('HDCase_HDCaseNum', 'Unknown')),
                    case.get('SalesRep_Name', 'No Case Owner'),
                    case.get('SalesRep1_Name', 'No Case Assignee'),
                    case.get('Customer_Name', 'No Customer'),
                    case.get('Project_ProjectID', 'No Project'),
                    case.get('HDCase_Description', 'No Description'),
                    case.get('Task_TaskDescription', 'No Task'),
                    case.get('Task_StartDate', 'No Start Date'),
                    case.get('Task_DueDate', 'No Due Date'),
                    case.get('Task_StatusCode', 'No Status'),
                    case.get('HDCase_TaskSetID', 'No Task Set'),
                    str(case.get('HDCase_Quantity', 'No Quoted Hours')),
                    str(case.get('ProjPhase_TotEstLbrHrs', 'No Job Est Hours')),
                    str(case.get('ProjPhase_TotActLbrHrs', 'No Act Hours')),
                    str(case.get('Calculated_LaborHours', 'No Lab Hours')),
                    str(case.get('HDCase_EstimatedHrs_c', 'No Case Est Hours')),
                    str(case.get('Calculated_RemainingHours', 'No Remain Hours')),
                    str(case.get('Calculated_DaysSinceLastComment', 'No Days Since Last Comment')),
                    case.get('HDCase_RequestDate_c', 'No Request Date'),
                    case.get('HDCase_DevStartDate_c', 'No Dev Start Date'),
                    case.get('HDCase_DeliveryDate_c', 'No Delivery Date'),
                    str(case.get('Calculated_SchedHoursRemaining', 'No Sched Hrs Remain')),
                    str(case.get('Calculated_DaysTillDueDate', 'No Days Till Due')),
                ]
                # Convert all values to strings and handle None cases
                row_values = [str(value) if value is not None else 'N/A' for value in row_values]

                index = self.cases_list.InsertItem(sys.maxsize, row_values[0])
                for col, value in enumerate(row_values[1:], 1):
                    self.cases_list.SetItem(index, col, value)

    def should_case_be_displayed(self, case):
        selected_assignee = self.case_assignee_filter.GetStringSelection()
        selected_task = self.task_description_filter.GetStringSelection()
        return ((selected_assignee == "All" or selected_assignee == case.get('SalesRep1_Name', '')) and
                (selected_task == "All" or selected_task == case.get('Task_TaskDescription', '')))

    def on_filter_changed(self, event):
        self.update_cases_list()

    def on_refresh_clicked(self, event):
        # Reload your case data and refresh the list
        self.load_cases()