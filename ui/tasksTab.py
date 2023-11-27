# tasksTab.py

import wx
from services.epicorService import EpicorService
import re

epicor_service = EpicorService()

class TasksTab(wx.Panel):

    def __init__(self, parent):
        super(TasksTab, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.case_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        vbox.Add(wx.StaticText(self, label="Case"), flag=wx.ALL, border=5)
        vbox.Add(self.case_input, flag=wx.EXPAND | wx.ALL, border=5)

        self.case_input.Bind(wx.EVT_TEXT_ENTER, self.on_case_enter)

        self.assignee_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.assignee_input.SetValue("Steve Maksymetz")
        vbox.Add(wx.StaticText(self, label="Assign Next Task To"), flag=wx.ALL, border=5)
        vbox.Add(self.assignee_input, flag=wx.EXPAND | wx.ALL, border=5)

        self.assign_button = wx.Button(self, label="Assign Task")
        vbox.Add(self.assign_button, flag=wx.ALL, border=5)

        self.SetSizer(vbox)

        self.assign_button.Bind(wx.EVT_BUTTON, self.on_assign)

    def on_assign(self, event):
        case_num = int(self.case_input.GetValue())
        assign_next_to_name = self.assignee_input.GetValue()

        # Complete the current task
        is_task_complete = epicor_service.complete_current_case_task(case_num)

        if is_task_complete:
            # If the task is completed successfully, assign the next task
            assign_response = epicor_service.assign_current_case_task(case_num, assign_next_to_name)

            if assign_response:
                message = f"Task completed and assigned successfully. Response: {assign_response}"
            else:
                message = "Failed to assign task."
        else:
            message = "Failed to complete task."

        wx.MessageBox(message, "Task Assignment Status", wx.OK | wx.ICON_INFORMATION)
    
    def on_case_enter(self, event):
        case_num = int(self.case_input.GetValue())
        case_info = epicor_service.get_case_info(case_num)

        if case_info['CurrentTask'] == 'Write Design Spec':
            assignee = re.match(r'(.+?):', case_info['CaseOwner']).group(1)
        elif case_info['CurrentTask'] == 'Assign Resource':
            assignee = 'Steve Maksymetz'
        else:
            assignee = ''

        self.assignee_input.SetValue(assignee)