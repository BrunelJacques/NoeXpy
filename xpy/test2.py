import wx
import wx.html


class MyHtmlFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(600, 400))
        html = wx.html.HtmlWindow(self)

        dlg = wx.TextEntryDialog(self, 'Enter a URL', 'HTMLWindow')

        if dlg.ShowModal() == wx.ID_OK:
            html.LoadPage(dlg.GetValue())


app = wx.App()
frm = MyHtmlFrame(None, "Simple HTML Browser")
frm.Show()
app.MainLoop()