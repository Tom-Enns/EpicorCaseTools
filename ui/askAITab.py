import wx
import wx.html2
import markdown
from services.omnaiService import ask_question

class AskAITab(wx.Panel):
    def __init__(self, parent):
        super(AskAITab, self).__init__(parent)

        self.init_ui()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Text box for the question
        self.question_text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        vbox.Add(self.question_text, flag=wx.EXPAND | wx.ALL, border=5)

        # Dropdown for the endpoint
        self.endpoint_dropdown = wx.ComboBox(self, choices=["ask", "appstudio", "administration", "customization"], style=wx.CB_READONLY)
        vbox.Add(self.endpoint_dropdown, flag=wx.EXPAND | wx.ALL, border=5)

        # Button to send the question
        self.send_button = wx.Button(self, label="Ask AI")
        vbox.Add(self.send_button, flag=wx.EXPAND | wx.ALL, border=5)
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_button_clicked)

        # WebView for the response
        self.response_view = wx.html2.WebView.New(self)
        vbox.Add(self.response_view, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox)

    def on_send_button_clicked(self, event):
        endpoint = self.endpoint_dropdown.GetValue()
        question = self.question_text.GetValue()

        response = ask_question(endpoint, question)
        if response is not None:
            response_text = response.get('response', '')
        else:
            response_text = "Request failed"

        # Convert the markdown text to HTML
        html_content = markdown.markdown(response_text, output_format='xhtml1')

        # Add CSS to use the system font
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    font-size: 12px;  # Adjust this value as needed
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Display the HTML in the WebView
        self.response_view.SetPage(html, "")