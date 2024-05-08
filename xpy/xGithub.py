#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Application :    Gestion GITHUB install ou mise à jour d'application
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
#--------------------------------------------------------------------------

try:
    mess = "lancement gitPython"
    messRaise = "Installer git par commande 'pip install gitpython'"
    import git

    mess = "lancement wxPython"
    messRaise = "Installer wxPython par commande 'pip install wxPython'"
    import wx
except Exception as err:
    raise Exception("Echec %s: %s\n%s" % (mess, err, messRaise))

import os
import wx.propgrid as wxpg


def update_app(appli_path, stash_changes=False, reset_hard=False):
    try:
        # Ouvrir le dépôt Git
        repo = git.Repo(appli_path)

        # Stasher les changements locaux si nécessaire
        if stash_changes:
            repo.git.stash("save", "--include-untracked")
            print("Changements stashed.")

        # Réinitialiser les changements locaux si nécessaire
        if reset_hard:
            repo.git.reset("--hard", "HEAD")
            print("Changements locaux réinitialisés.")

        # Effectuer git pull depuis la branche actuelle
        origin = repo.remote(name='origin')
        origin.pull()

        print("Mise à jour réussie.")

    except git.exc.GitCommandError as e:
        print("Erreur lors de la mise à jour : ", e)


def clone_github_repo(repo_url, appli_path):
    try:
        # Cloner le dépôt GitHub dans le chemin spécifié
        repo = git.Repo.clone_from(repo_url, appli_path)
        mess = "Clonage réussi."
        style = wx.ICON_INFO

    except git.exc.GitCommandError as e:
        print("Erreur lors du clonage : ", e)


class Dialog(wx.Dialog):
    def __init__(self):
        super().__init__(None, title="Installateur d'appli GITHUB",
                         pos=(400, 200),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.initialPath = os.getcwd()
        self.lblPull = "   Release de l'existant"
        self.lblClone = "   Nouvelle installation"
        self.lstAplis = ['NoeXpy', 'Noethys-Matthania']
        self.Controls()
        self.Proprietes()
        self.InitSizer()

    def Controls(self):
        self.staticboxAppli = wx.StaticBox(self, label=" Choix de l'application ")
        self.staticboxDir = wx.StaticBox(self, label=" Répertoire de l'application ")

        self.comboAppli = wx.ComboBox(self, value=self.lstAplis[1], choices=self.lstAplis)
        self.radioClone = wx.RadioButton(self, label=self.lblPull, style=wx.RB_GROUP)
        self.radioPull = wx.RadioButton(self, label=self.lblClone)

        self.dirPicker = wx.DirPickerCtrl(self,
                                          message="Choisir le répertoire d'installation:",
                                          path=self.initialPath,
                                          style=wx.DIRP_USE_TEXTCTRL,
                                          name="dirPicker")
        self.checkForce = wx.CheckBox(self, label="Forcer l'opération si problème")
        self.btnOk = wx.Button(self, label="OK")

    def Proprietes(self):
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radioClone)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radioPull)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.btnOk)
        self.Bind(wxpg.EVT_PG_CHANGED, self.OnDirPicker, self.dirPicker)
        self.radioClone.SetToolTip(
            "Pour une nouvelle installation, l'emplacement doit être vide")
        self.radioPull.SetToolTip("Pour une mise à jour, être dans l'emplacement")
        self.comboAppli.SetToolTip("Choix de l'application à installer")
        self.dirPicker.SetToolTip(
            "Il s'agit du répertoire où l'application doit être installée")
        self.checkForce.SetToolTip(
            "Cette option permet d'ignorer les modifications locales, écrase l'existant")
        self.SetMinSize((350, 270))
        self.SetSize(450, 300)

    def InitSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizerAppli = wx.StaticBoxSizer(self.staticboxAppli)
        sizerAppli.Add(self.comboAppli, 0, wx.ALL, 5)
        sizerAppli.Add((10, 10), 1, wx.EXPAND, 0)
        sizerRadio = wx.BoxSizer(wx.VERTICAL)
        sizerRadio.Add(self.radioClone, 1, wx.TOP, 5)
        sizerRadio.Add(self.radioPull, 1, wx.BOTTOM | wx.EXPAND, 5)
        sizerAppli.Add(sizerRadio, 15, wx.EXPAND, 0)
        sizer.Add(sizerAppli, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 10)
        sizerDir = wx.StaticBoxSizer(self.staticboxDir, orient=wx.VERTICAL)
        sizerDir.Add(self.dirPicker, 1, wx.EXPAND | wx.ALL, 5)
        sizerDir.Add(self.checkForce, 0, wx.LEFT, 15)
        sizer.Add(sizerDir, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.btnOk, 0, wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 20)
        self.SetSizer(sizer)
        self.Show()

    def OnDirPicker(self, event):
        pass

    def OnRadio(self, event):
        radio_btn = event.GetEventObject()
        choix = radio_btn.GetLabel()
        if choix == self.lblClone:
            os.chdir("..")
            self.dirPicker.SetPath(os.getcwd())
        else:
            self.dirPicker.SetPath(self.initialPath)

    def on_ok(self, event):
        selected_dir = self.dirPicker.GetPath()
        selected_appli = self.comboAppli.GetValue()
        isPull = self.radioPull.GetValue()
        isClone = self.radioClone.GetValue()
        wx.MessageBox(f"Répertoire sélectionné : {selected_dir}", "Répertoire choisi",
                      wx.OK | wx.ICON_INFORMATION)
        # self.Close()


# Lancement
if __name__ == "__main__":
    os.chdir("..")
    app = wx.App(False)
    frame = Dialog()
    app.MainLoop()

    repo_url = "https://github.com/BrunelJacques/NoeXpy"  # Remplacez par l'URL de votre dépôt GitHub
    appli_path = "D:\\temp\\Noexpy_Test\\"

    # clone_github_repo(repo_url, appli_path)

    # pour un update
    # update_app(appli_path, stash_changes=True, reset_hard=False)
