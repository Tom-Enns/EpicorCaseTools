import wx
import os
import sys
from configparser import ConfigParser
from ui.settingsTab import SettingsTab
from ui.teamsTab import TeamsTab
from ui.caseFilesTab import CaseTab
from ui.caseListTab import CaseListTab

from services.loggingService import LoggingService

# start logging service
LoggingService.setup_logging()

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)


# Main application window
def load_config_vars():
    return {
        'BASE_URL': config.get('DEFAULT', 'BASE_URL', fallback=None),
        'SIXS_API_KEY': config.get('DEFAULT', 'SIXS_API_KEY', fallback=None),
        'SIXS_BASIC_AUTH': config.get('DEFAULT', 'SIXS_BASIC_AUTH', fallback=None),
        'DOC_PATH': config.get('DEFAULT', 'DOC_PATH', fallback=None),
    }


def check_config_vars(config_vars):
    for var_name, var_value in config_vars.items():
        if not var_value:
            wx.MessageBox(f"Configuration variable {var_name} is not set or is blank", "Warning",
                          wx.OK | wx.ICON_WARNING)


class Mywin(wx.Frame):

    def __init__(self, parent, title):
        # Load configuration variables
        self.caseListTab = None
        self.caseTab = None
        self.TeamsTab = None
        self.settingsTab = None
        self.richTextTab = None
        self.designTab = None

        config_vars = load_config_vars()

        # Check configuration variables
        check_config_vars(config_vars)

        # Initialize window
        super(Mywin, self).__init__(parent, title=title, size=(800, 600), style=wx.DEFAULT_FRAME_STYLE | (
            wx.STAY_ON_TOP if config.getboolean('DEFAULT', 'ALWAYS_ON_TOP', fallback=False) else 0))

        # Set icon
        self.set_icon()

        # Initialize panel and notebook
        panel = wx.Panel(self)
        self.nb = wx.Notebook(panel)

        # Initialize tabs
        self.init_tabs()

        # Adjust the tabs' margin
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.nb, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)

        self.Show()

    def set_icon(self):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(bundle_dir, 'CaseToolsIcon.ico')
        self.SetIcon(wx.Icon(icon_path))

    def init_tabs(self):
        self.caseListTab = CaseListTab(self.nb)
        self.caseTab = CaseTab(self.nb)
        self.TeamsTab = TeamsTab(self.nb)
        self.settingsTab = SettingsTab(self.nb)

        self.nb.AddPage(self.caseListTab, "Open Cases")
        self.nb.AddPage(self.caseTab, "Files")
        self.nb.AddPage(self.TeamsTab, "Teams Tools")
        self.nb.AddPage(self.settingsTab, "Settings")


app = wx.App()
Mywin(None, "Case Tools")
app.MainLoop()
