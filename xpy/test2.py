from threading import Thread
from time import sleep
import wx


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="TEST", size=(400, 400))
        self.Show()
        self.__someDialog = None
        self.__okButton = wx.Button(self, -1, "Press me")
        self.Bind(wx.EVT_BUTTON, self.__onOK)

        self.__myThread = Thread(target=self.__waitThenClose, name="Closer")
        self.__myThread.setDaemon(True)
        self.__myThread.start()

    def __onOK(self, evt):
        self.__someDialog = SomeDialog(self)
        self.__someDialog.ShowModal()

    def closeOpenDialogs(self, evt=None):
        lst = wx.GetTopLevelWindows()
        for i in range(len(lst) - 1, 0, -1):
            dialog = lst[i]
            if isinstance(dialog, wx.Dialog):
                print("Closing " + str(dialog))
                # dialog.Close(True)
                wx.CallAfter(dialog.Close)
                # sleep(1)
                # dialog.Destroy()

    def __waitThenClose(self):
        for x in range(0, 10):
            print( "Sleeping...")
            sleep(1)
        wx.CallAfter(self.closeOpenDialogs)
        wx.CallAfter(self.Close, True)


class SomeDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=-1, title='Some Dialog')
        self.SetSize((300, 300))
        self.__anotherDialog = None
        self.__okButton = wx.Button(self, -1, "Press me")
        self.Bind(wx.EVT_BUTTON, self.__onOK)
        wx.EVT_CLOSE(self, self.__on_btn_cancel)

    def __onOK(self, evt):
        self.__anotherDialog = AnotherDialog(self)
        self.__anotherDialog.SetWindowStyleFlag(
            wx.FRAME_FLOAT_ON_PARENT|wx.DEFAULT_DIALOG_STYLE)
        self.__anotherDialog.Show()

    def __on_btn_cancel(self, event):
        event.Skip()
        self.EndModal(wx.ID_CANCEL)


class AnotherDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=-1, title='Another Dialog')
        self.SetSize((200, 200))
        wx.EVT_CLOSE(self, self.__on_btn_cancel)
        parent.Disable()

    def __on_btn_cancel(self, event):
        event.Skip()
        self.GetParent().Enable()
        # self.EndModal(wx.ID_CANCEL)


if __name__ == "__main__":
    app = wx.App()
    mainFrame = MainFrame()
    app.MainLoop()