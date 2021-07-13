import wx

########################################################################
class MyPanel(wx.Panel):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)

        self.text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.text.Bind(wx.EVT_KEY_DOWN, self.onEnter)
        btn = wx.Button(self, label="Do something")
        self.text.SetFocus()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(btn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(sizer)

    #----------------------------------------------------------------------
    def onEnter(self, event):
        """"""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER or keycode == wx.WXK_TAB:
            self.process_text(event=None)
            event.EventObject.Navigate()
        event.Skip()

    #----------------------------------------------------------------------
    def process_text(self, event):
        """
        Do something with the text
        """
        text = self.text.GetValue()
        print(text.upper())
        for word in text.split():
            print(word)

########################################################################
class MyFrame(wx.Frame):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="TextCtrl Demo")
        panel = MyPanel(self)
        self.Show()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame()
    app.MainLoop()