import wx
from configparser import ConfigParser
import os

config = ConfigParser()
DOC_PATH = ""


def check_config_vars(config_vars):
    unset_vars = [var_name for var_name, var_value in config_vars.items() if not var_value]

    if unset_vars:
        wx.MessageBox(f"Configuration variables {', '.join(unset_vars)} are not set or are blank", "Warning",
                      wx.OK | wx.ICON_WARNING)
        return


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
        grid = wx.FlexGridSizer(12, 2, 5, 5)  # Updated to 12 rows

        # BASE URL
        self.add_text_field(grid, "BASE URL:", 'BASE_URL')

        # SIXS API KEY
        self.add_text_field(grid, "SIXS API KEY:", 'SIXS_API_KEY')

        # SIXS BASIC AUTH
        self.add_text_field(grid, "SIXS BASIC AUTH:", 'SIXS_BASIC_AUTH')

        # DOC PATH
        self.add_doc_path_field(grid)

        # ALWAYS ON TOP
        self.add_checkbox_field(grid, "ALWAYS ON TOP:", 'ALWAYS_ON_TOP')

        # GOOGLE API KEY
        self.add_text_field(grid, "GOOGLE API KEY:", 'GOOGLE_API_KEY')

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

    def on_select_folder_button_clicked(self):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.DOC_PATH.SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_save_button_clicked(self):
        config_vars = {
            'BASE_URL': self.BASE_URL.GetValue(),
            'SIXS_API_KEY': self.SIXS_API_KEY.GetValue(),
            'SIXS_BASIC_AUTH': self.SIXS_BASIC_AUTH.GetValue(),
            'DOC_PATH': self.DOC_PATH.GetValue(),
            'GOOGLE_API_KEY': self.GOOGLE_API_KEY.GetValue(),  # Add Google API key
        }

        # Check configuration variables
        check_config_vars(config_vars)

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

        wx.MessageBox("Configuration saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
