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

        # Sort By Dropdown setup
        self.sort_by_choices = ["Case", "Case Owner", "Case Assignee", "Customer", "Project", "Description", "Task",
                                "Task Start Date", "Task Due Date", "Task Status", "Task Set", "Quoted Hours",
                                "Job Est Hours", "Act Hours", "Lab Hours", "Case Est Hours", "Remain Hours",
                                "Days Since Last Comment", "Request Date", "Dev Start Date", "Delivery Date",
                                "Sched Hrs Remain", "Days Till Due Date"]
        self.sort_by_dropdown = wx.Choice(self, choices=self.sort_by_choices)
        top_bar_layout.Add(wx.StaticText(self, label="Sort By:"), 0, wx.ALL | wx.CENTER, 5)
        top_bar_layout.Add(self.sort_by_dropdown, 0, wx.ALL | wx.EXPAND, 5)

        # Case Assignee Filter setup
        self.case_assignee_filter = wx.Choice(self, choices=[])
        top_bar_layout.Add(wx.StaticText(self, label="Case Assignee:"), 0, wx.ALL | wx.CENTER, 5)
        top_bar_layout.Add(self.case_assignee_filter, 0, wx.EXPAND | wx.ALL, 5)

        # Task Description Filter setup
        self.task_description_filter = wx.Choice(self, choices=[])
        top_bar_layout.Add(wx.StaticText(self, label="Task:"), 0, wx.ALL | wx.CENTER, 5)
        top_bar_layout.Add(self.task_description_filter, 0, wx.EXPAND | wx.ALL, 5)

        # Refresh Button setup
        img = wx.Image('refreshicon.png', wx.BITMAP_TYPE_ANY)
        img = img.Scale(12, 12, wx.IMAGE_QUALITY_HIGH)  # Adjusting scale to match your UI's button size
        refresh_icon = wx.Bitmap(img)
        self.refresh_button = wx.BitmapButton(self, id=wx.ID_ANY, bitmap=refresh_icon)
        top_bar_layout.Add(self.refresh_button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Add the top bar to the layout
        layout.Add(top_bar_layout, 0, wx.EXPAND | wx.ALL, 5)

        # Setup for the cases list
        self.cases_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
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

        # Bind event handlers
        self.case_assignee_filter.Bind(wx.EVT_CHOICE, self.on_filter_changed)
        self.task_description_filter.Bind(wx.EVT_CHOICE, self.on_filter_changed)
        self.sort_by_dropdown.Bind(wx.EVT_CHOICE, self.on_sort_by_changed)
        self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh_clicked)

    def load_cases(self):
        # Save the current selections
        current_assignee_selection = self.case_assignee_filter.GetStringSelection()
        current_task_selection = self.task_description_filter.GetStringSelection()
        current_sort_selection = self.sort_by_dropdown.GetStringSelection()

        # Reload your cases data
        self.cases = self.epicor_service.fetch_cases()

        # Repopulate the dropdowns
        case_assignees = sorted(
            set(case.get('SalesRep1_Name', 'Unknown') for case in self.cases if case.get('SalesRep1_Name')))
        task_descriptions = sorted(set(case.get('Task_TaskDescription') or 'No Description' for case in self.cases))

        self.case_assignee_filter.Clear()
        self.case_assignee_filter.AppendItems(["All"] + case_assignees)
        self.task_description_filter.Clear()
        self.task_description_filter.AppendItems(["All"] + task_descriptions)

        # Restore the selections
        if current_assignee_selection in case_assignees or current_assignee_selection == "All":
            self.case_assignee_filter.SetStringSelection(current_assignee_selection)
        else:
            self.case_assignee_filter.SetSelection(0)

        if current_task_selection in task_descriptions or current_task_selection == "All":
            self.task_description_filter.SetStringSelection(current_task_selection)
        else:
            self.task_description_filter.SetSelection(0)

        if current_sort_selection in self.sort_by_choices:
            self.sort_by_dropdown.SetStringSelection(current_sort_selection)
        else:
            self.sort_by_dropdown.SetSelection(0)

        # Apply sorting if needed
        if current_sort_selection and current_sort_selection in self.sort_by_choices:
            sort_column_index = self.sort_by_choices.index(current_sort_selection)
            self.sort_cases(sort_column_index)

        # Update the list to reflect changes
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

                index = self.cases_list.InsertItem(self.cases_list.GetItemCount(), row_values[0])
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

    def on_sort_by_changed(self, event):
        sort_column = self.sort_by_dropdown.GetSelection()
        self.sort_cases(sort_column)
        self.update_cases_list()

    def sort_cases(self, col_index):
        column_keys = ["HDCase_HDCaseNum", "SalesRep_Name", "SalesRep1_Name", "Customer_Name", "Project_ProjectID",
                       "HDCase_Description", "Task_TaskDescription", "Task_StartDate", "Task_DueDate",
                       "Task_StatusCode", "HDCase_TaskSetID", "HDCase_Quantity", "ProjPhase_TotEstLbrHrs",
                       "ProjPhase_TotActLbrHrs", "Calculated_LaborHours", "HDCase_EstimatedHrs_c",
                       "Calculated_RemainingHours", "Calculated_DaysSinceLastComment", "HDCase_RequestDate_c",
                       "HDCase_DevStartDate_c", "HDCase_DeliveryDate_c", "Calculated_SchedHoursRemaining",
                       "Calculated_DaysTillDueDate"]
        sort_key = column_keys[col_index]

        self.cases.sort(key=lambda x: x.get(sort_key, '') or '')
