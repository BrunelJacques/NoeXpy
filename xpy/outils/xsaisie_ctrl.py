#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :  projet xpy
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx

class Tel(wx.TextCtrl):
    # Saisie d'un numéro de téléphone
    def __init__(self, parent, intitule=u""):
        self.mask = ""
        wx.TextCtrl.__init__(self, parent, -1, "", style=wx.TE_CENTRE)
        self.parent = parent
        self.SetMinSize((125, -1))
        self.SetToolTip(u"Saisissez un numéro de %s" % intitule)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
    
    def OnKillFocus(self, event):
        valide, messageErreur = self.Validation()
        if valide == False :
            wx.MessageBox(messageErreur, "Erreur de format")
        if event != None : event.Skip() 
    
    def Validation(self):
        text = self.GetValue()
        # Vérifie si Tél vide
        if text.strip() == "" :
            return True, None
        # filatrage des séparateurs obsolètes
        text = text.replace("."," ").strip()
        # insertion d'espaces s'il n'y en a pas
        if not " " in text and len(text) == 10:
            text = text[:2]+" "+text[2:4]+" "+text[4:6]+" "+text[6:8]+" "+text[8:10]
        if not " " in text and len(text) > 10:
            text = text[:3]+" "+text[3:6]+" "+text[6:9]+" "+text[9:12]+" "+text[12:]

        # reécrit le nombre reformaté
        self.SetNumero(text)

        message = None
        if not text[0] in "+0": message = u"Un numéro de téléphone commence par '0' ou '+'"
        # présence de 10 chiffres pour la france 7 pour l'étranger
        if text[0] == "0": lgon = 10
        elif text[:3]== "+33": lgon = 11
        else: lgon = 7
        for a in "() +-":
            text = text.replace(a,'')
        try:
            no = int(text[:lgon])
        except:
            message = u"'%s' n'est pas un nombre, au moins %s chiffres attendus!"%(text[:lgon],lgon)

        if len(text)<lgon:
            message = u"Pas assez long, au moins %s chiffres attendus!"%(lgon)

        if message : return False,message
        return True, None
    
    def SetNumero(self, numero=""):
        if numero == None : return
        try :
            self.SetValue(numero)
        except : 
            pass
    
    def GetNumero(self):
        tel = self.GetValue() 
        if tel.strip() == "" :
            return None
        else:
            return tel
    
class Mail(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, -1, "")
        self.parent = parent
        self.SetToolTip("Saisissez une adresse mail")
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
    
    def OnKillFocus(self, event):
        valide, messageErreur = self.Validation()
        if valide == False :
            dlg = wx.MessageDialog(self, messageErreur,"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        if event != None : event.Skip() 
    
    def Validation(self):
        # Vérifie si Email vide
        text = self.GetValue()
        if text != "":
            posAt = text.find("@")
            if posAt == -1:
                message = "L'adresse Email que vous avez saisie n'est pas valide !"
                return False, message
            posPoint = text.rfind(".")
            if posPoint < posAt :
                message = "L'adresse Email que vous avez saisie n'est pas valide !"
                return False, message
        return True, None
    
    def SetMail(self, mail=""):
        if mail == None : return
        self.SetValue(mail)
    
    def GetMail(self):
        mail = self.GetValue() 
        if mail == "" :
            return None
        else:
            return mail

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= Mail(panel)
        self.ctrl2= Tel(panel,intitule="téléphone")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.ctrl2, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()