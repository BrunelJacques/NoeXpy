#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Application :    lanceur de xGithub programme d'installation et MAJ
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
#--------------------------------------------------------------------------


import os, sys
import importlib.util

# imports préalables aux connexions git
try:
    mess = "lancement gitPython"
    messRaise = "Installer git par commande windows 'pip install gitpython'\n"
    SEP = "\\"
    if "linux" in sys.platform:
        messRaise = "Installer git sous linux: 'sudo apt install git'"
        SEP = "/"

    # tentative d'installation du package github si non présent
    if not importlib.util.find_spec('git'):
        mess = "test de présence de package github"
        import subprocess

        commande = ['pip', 'install', 'github']
        subprocess.call(commande)
    import git

    mess = "lancement wxPython"
    messRaise = "Installer wxPython par commande 'pip install wxPython'"
    if "linux" in sys.platform:
        messRaise = ("Installer wxPython sous Linux:\n" +
                     "pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython")
    import wx

    del mess
    del messRaise
except Exception as err:
    raise Exception("Echec %s: %s\n%s" % (mess, err, messRaise))


# Lancement
if __name__ == "__main__":
    app = wx.App(0)
    os.chdir("..")
    from xpy import xGithub
    dlg = xGithub.DLG("NoeXpy")
    dlg.ShowModal()
    app.MainLoop()