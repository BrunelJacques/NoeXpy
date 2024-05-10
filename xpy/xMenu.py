#!/bin/python

import wx

class Accueil(wx.Frame):

    def __init__(self, *args, **kw):
        super(Accueil, self).__init__(*args, **kw)
        pnl = wx.Panel(self)
        st = wx.StaticText(pnl, label="Choisir une option du menu!", pos=(25,25))
        font = st.GetFont()
        #font.PointSize += 5
        #font = font.Bold()
        st.SetFont(font)

        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("xPY roule pour vous!")

    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        action11 = fileMenu.Append(-1, "&Action11\tCtrl-H",
                "L'action 11 produit un message Box!")
        action12 = fileMenu.Append(-1, "&Action12\tCtrl-A",
                "L'action 12 produit un message Box!")
        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&Fichier")
        menuBar.Append(helpMenu, "&Info")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnAction11, action11)
        self.Bind(wx.EVT_MENU, self.OnAction12, action12)
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnAction11(self, event):
        """Say Action11 to the user."""
        wx.MessageBox("Action11 again from wxPython")

    def OnAction12(self, event):
        wx.MessageBox("Voici le résultat de l'action 12",caption="Retour")

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a wxPython Action21 World sample",
                      "About Action21 ",
                      wx.OK|wx.ICON_INFORMATION)


if __name__ == '__main__':
    app = wx.App()
    frm = Accueil(None, title='xPY morceaux choisis')
    frm.Show()
    app.MainLoop()