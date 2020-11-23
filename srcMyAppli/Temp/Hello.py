#!/bin/python

import wx

class Panel(wx.Panel):
    def __init__(self, parent, rien,  *args, title='', **kw):
        super(Panel, self).__init__(parent, *args, **kw)
        #wx.Panel.__init__(self, parent, *args, **kw)
        print(rien, " - ",  args,kw)
        st = wx.StaticText(self, label=title+" vient de frame", pos=(10,50))
        font = st.GetFont()
        font.PointSize += 5
        font = font.Bold()
        st.SetFont(font)

class Accueil(wx.Frame):
    def __init__(self,  *args, **kw):
        super(Accueil, self).__init__(*args, **kw)
        print(args,kw)
        pnl = Panel(self, *args,**kw)


if __name__ == '__main__':
    app = wx.App()
    frm = Accueil(None, title='Titre général')
    frm.Show()
    app.MainLoop()