import os
import wx
import wx.html2


class RichTextTab(wx.Panel):
    def __init__(self, parent):
        super(RichTextTab, self).__init__(parent)

        self.web_view = None
        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.web_view = wx.html2.WebView.New(self)
        self.web_view.LoadURL("file://" + os.path.abspath("components/markdown_editor.html"))

        vbox.Add(self.web_view, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(vbox)
