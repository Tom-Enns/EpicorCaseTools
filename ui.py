import wx
import os
import sys
from configparser import ConfigParser
from ui.settingsTab import SettingsTab
from ui.downloadTab import DownloadTab
from ui.uploadTab import UploadTab
from ui.queryTab import QueryTab
from ui.askAITab import AskAITab
from ui.caseToolsTab import CaseToolsTab
from ui.tasksTab import TasksTab
from ui.caseUpdateTab import CaseUpdateTab
from ui.caseTab import CaseTab
from services.loggingService import LoggingService


#start logging service
LoggingService.setup_logging()

# Load configuration
config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

# Set document path
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

# Main application window
class Mywin(wx.Frame):

    def __init__(self, parent, title):
        # Load configuration variables
        config_vars = self.load_config_vars()
        
        # Check configuration variables
        self.check_config_vars(config_vars)

        # Initialize window
        super(Mywin, self).__init__(parent, title=title, size=(390, 270), style=wx.DEFAULT_FRAME_STYLE | (wx.STAY_ON_TOP if config.getboolean('DEFAULT', 'ALWAYS_ON_TOP', fallback=False) else 0))

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

    def load_config_vars(self):
        return {
            'BASE_URL': config.get('DEFAULT', 'BASE_URL', fallback=None),
            'SIXS_API_KEY': config.get('DEFAULT', 'SIXS_API_KEY', fallback=None),
            'SIXS_BASIC_AUTH': config.get('DEFAULT', 'SIXS_BASIC_AUTH', fallback=None),
            'DOC_PATH': config.get('DEFAULT', 'DOC_PATH', fallback=None),
        }

    def check_config_vars(self, config_vars):
        for var_name, var_value in config_vars.items():
            if not var_value:
                wx.MessageBox(f"Configuration variable {var_name} is not set or is blank", "Warning", wx.OK | wx.ICON_WARNING)

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
        # Tabs
        self.caseTab = CaseTab(self.nb)
        #self.downloadTab = DownloadTab(self.nb)
        #self.uploadTab = UploadTab(self.nb)
        #self.caseUpdateTab = CaseUpdateTab(self.nb)
        self.tasksTab = TasksTab(self.nb)
        self.queryTab = QueryTab(self.nb) 
        self.askAITab = AskAITab(self.nb)  
        self.caseToolsTab = CaseToolsTab(self.nb) 
        self.settingsTab = SettingsTab(self.nb) 
        
    
        self.nb.AddPage(self.caseTab, " Case ")
        #self.nb.AddPage(self.downloadTab, " Download ")
        #self.nb.AddPage(self.uploadTab, " Upload ")
        #self.nb.AddPage(self.caseUpdateTab, "Case Update")
        self.nb.AddPage(self.tasksTab, " Tasks ")
        self.nb.AddPage(self.queryTab, " Query ") 
        self.nb.AddPage(self.askAITab, " Ask AI ")
        self.nb.AddPage(self.caseToolsTab, " Case Tools ")
        self.nb.AddPage(self.settingsTab, " Settings ") 
        
       
        



app = wx.App()
Mywin(None, "Case Tools")
app.MainLoop()
