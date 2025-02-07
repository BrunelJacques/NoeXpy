#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# Application :    Gestion GITHUB install ou mise à jour d'application
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# --------------------------------------------------------------------------

"""
import git
import os

# ATTENTION le client GIT doit être en place par http://Git-scm.com
# Définir l'URL du dépôt et le chemin local
repo_url = 'https://github.com/votre-utilisateur/votre-repo.git'
local_path = 'chemin/vers/votre/dossier'

# Vérifier si le dossier existe déjà
if os.path.exists(local_path):
    # Si le dossier existe, mettre à jour le dépôt
    repo = git.Repo(local_path)
    origin = repo.remotes.origin
    origin.pull()
    print(f"Le dépôt a été mis à jour dans {local_path}")
else:
    # Si le dossier n'existe pas, cloner le dépôt
    repo = git.Repo.clone_from(repo_url, local_path)
    print(f"Le dépôt a été cloné dans {local_path}")
"""# exemple usage git donné par copilot

import os, wx
from xpy import xGithub



# Lancement
if __name__ == "__main__":
    os.chdir("..")
    app = wx.App(False)
    app.MainLoop()
    ret = xGithub.IsPullNeeded(os.getcwd(), withPull=False, mute=False)
    if ret == None:
        print("Echec du test mises à jour GitHub")
    elif ret == False:
        mess = "Tout semble correct\n\nAucune mise à jour nécessaire"
        wx.MessageBox(mess,"Test GitHub",style= wx.ICON_INFORMATION)
    else:
        print("Mise à jour nécessaire: %s" % str(ret))
        dlg = xGithub.DLG("NoeXpy")
        dlg.ShowModal()
