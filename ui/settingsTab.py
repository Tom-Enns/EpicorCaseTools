import wx
from configparser import ConfigParser
import os

config = ConfigParser()

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
        grid = wx.FlexGridSizer(11, 2, 5, 5)

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

        # OPENAI_APIKEY
        self.add_text_field(grid, "OPENAI API KEY:", 'OPENAI_APIKEY')

        # PINECONE_APIKEY
        self.add_text_field(grid, "PINECONE API KEY:", 'PINECONE_APIKEY')

        # PINECONE_DB
        self.add_text_field(grid, "PINECONE DB:", 'PINECONE_DB')

        # PINECONE_ENVIRONMENT
        self.add_text_field(grid, "PINECONE ENVIRONMENT:", 'PINECONE_ENVIRONMENT')

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

    def on_select_folder_button_clicked(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.DOC_PATH.SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_save_button_clicked(self, event):

        config_vars = {
            'BASE_URL': self.BASE_URL.GetValue(),
            'SIXS_API_KEY': self.SIXS_API_KEY.GetValue(),
            'SIXS_BASIC_AUTH': self.SIXS_BASIC_AUTH.GetValue(),
            'DOC_PATH': self.DOC_PATH.GetValue(),
            'OPENAI_APIKEY': self.OPENAI_APIKEY.GetValue(),
            'PINECONE_APIKEY': self.PINECONE_APIKEY.GetValue(),
            'PINECONE_DB': self.PINECONE_DB.GetValue(),
            'PINECONE_ENVIRONMENT': self.PINECONE_ENVIRONMENT.GetValue(),
        }

        # Check configuration variables
        self.check_config_vars(config_vars)

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

    def check_config_vars(self, config_vars):
        unset_vars = [var_name for var_name, var_value in config_vars.items() if not var_value]

        if unset_vars:
            wx.MessageBox(f"Configuration variables {', '.join(unset_vars)} are not set or are blank", "Warning", wx.OK | wx.ICON_WARNING)
            return