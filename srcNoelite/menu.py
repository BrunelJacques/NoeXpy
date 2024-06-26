# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2020-03    Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
from srcNoelite import DLG_Km_saisie, DLG_Transposition_fichier, DLG_Reglements_gestion, DLG_Adresses_gestion
from srcNoelite import DB_schema
from xpy        import xUTILS_Identification, xGestionConfig, xUTILS_DB

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent

    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        menu = [
        # Première colonne
        {"code": "&params\tCtrl-P", "label": ("Paramètres_et_outils"), "items": [
            {"code": "config", "label": ("&Mise à jour des programmes\tCtrl-R"),
             "infobulle": ("Release ou réinstallation ailleurs"),
             "image": "Images/16x16/Utilisateur_reseau.png",
             "action": "On_github", "genre": wx.ITEM_NORMAL},
            {"code": "config", "label": ("&Accès aux Bases de données\tCtrl-A"),
             "infobulle": ("Reconfigurer l'accès à la base de données principale"),
             "image": "Images/16x16/Utilisateur_reseau.png",
             "action": "On_config", "genre": wx.ITEM_NORMAL},
            "-",
        {"code": "utilisateurs", "label": ("Utilisateurs"), "infobulle": ("Paramétrage des utilisateurs"),
         "image": "Images/16x16/Personnes.png", "action": "On_utilisateurs"},
        "-",
        {"code": "transpose", "label": ("Transposition fichier"),
                "infobulle": ("Outil de reformatage d'un fichier pour la compta"),
        "image": "Images/16x16/Conversion.png", "action": "On_transpose"},
        {"code": "kmSaisie", "label": ("Saisie-import des km véhicules"),
                "infobulle": ("Outil d'import et de saisie pour refacturer les km pour la compta analytique"),
        "image": "Images/16x16/Conversion.png", "action": "On_kmSaisie"},
        "-",
        {"code": "quitter", "label": ("Quitter"), "infobulle": ("Fin de travail Noelite"),
         "image": "Images/16x16/Quitter.png", "action": "xQuitter"},
        ]},
        # deuxième colonne
        {"code": "&params\tCtrl-P", "label": ("Actions_Noethys"), "items": [
            {"code": "modifAdresses", "label": ("&Modification d'adresses Individus\tCtrl-I"),
             "infobulle": ("Gestion de l'adresses de rattachement des personnes (soit la leur soit celle de leur hébergeur"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_Adresses_individus", "genre": wx.ITEM_NORMAL},
            {"code": "modifAdressesF", "label": ("&Modification d'adresses Familles\tCtrl-F"),
             "infobulle": ("Gestion des adresses des familles, mais pas de tous les individus de la famille"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_Adresses_familles", "genre": wx.ITEM_NORMAL},
            "-",
            {"code": "gestionReglements", "label": ("&Gestion des règlements\tCtrl-R"),
             "infobulle": ("Gestion de bordereau de règlements : remise de chèques, arrivée de virements, de dons..."),
             "image": "Images/16x16/Impayes.png",
             "action": "On_reglements_bordereau", "genre": wx.ITEM_NORMAL},
        ]},

        # quatrième colonne
        {"code": "&params\tCtrl-S", "label": ("Système"),
         "items": [
             {"code": "gesbases", "label": ("Gestion des bases"),
              "infobulle": ("Création, copie de bases de données"),
              "image": "Images/16x16/Utilisateur_reseau.png", "action": "On_gesBases"},
             {"code": "gestables", "label": ("Ajout tables manquantes"),
              "infobulle": ("Outil permettant de créer les tables manquantes dans la base"),
              "image": "Images/16x16/Actualiser2.png",
              "action": "On_gesTables"},
             {"code": "ctrltables", "label": ("Ctrl des champs de chaque table"),
              "infobulle": ("Outil permettant de créer les tables manquantes ou les champs manquants dans la base"),
              "image": "Images/16x16/Actualiser2.png",
              "action": "On_ctrlTables"},
         ]}
        ]
        return menu

    def CouleurFondBureau(self):
        return wx.Colour(96,73,123)

    def ParamBureau(self):
        #appelé pour construire une page d'accueil, même structure que les items du menu pour gérer des boutons
        lstItems = [
            {"code": "modifAdresses", "label": ("&Modification d'adresses Individus"),
             "infobulle": ("Gestion de l'adresses de rattachement des personnes (soit la leur soit celle de leur hébergeur"),
             "image": "Images/80x80/Adresse.png",
             "action": self.menuClass.On_Adresses_individus, "genre": wx.ITEM_NORMAL},
            {"code": "modifAdressesF", "label": ("&Modification d'adresses Familles"),
             "infobulle": ("Gestion des adresses des familles, mais pas de tous les individus de la famille"),
             "image": "Images/80x80/Adresse-famille.jpg",
             "action": self.menuClass.On_Adresses_familles, "genre": wx.ITEM_NORMAL},
            {"code": "gestionReglements", "label": ("&Gestion des règlements"),
             "infobulle": ("Gestion de bordereau de règlements : remise de chèques, arrivée de virements, de dons..."),
             "image": "Images/80x80/Euro.png",
             "action": self.menuClass.On_reglements_bordereau, "genre": wx.ITEM_NORMAL},
        ]
        return lstItems

    def On_Adresses_individus(self, event):
        dlg = DLG_Adresses_gestion.Dialog(mode='individus',titre="Choisissez un individu")
        dlg.ShowModal()

    def On_Adresses_familles(self, event):
        texte = "Double clic pour lancer la gestion de l'adresse du correspondant de la famille"
        dlg = DLG_Adresses_gestion.Dialog(mode='familles',titre="Choisissez une famille",intro=texte)
        dlg.ShowModal()

    def On_reglements_bordereau(self, event):
        dlg = DLG_Reglements_gestion.Dialog()
        dlg.ShowModal()

    def On_github(self,event):
        from xpy import xGithub
        dlg = xGithub.DLG("NoeXpy")
        ret = dlg.ShowModal()
        del dlg

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        return self.parent.SaisieConfig()

    def On_utilisateurs(self,event):
        ret = xUTILS_Identification.AfficheUsers(self.parent)

    def On_transpose(self,event):
        dlg = DLG_Transposition_fichier.Dialog()
        dlg.ShowModal()

    def On_kmSaisie(self,event):
        dlg = DLG_Km_saisie.Dialog()
        dlg.ShowModal()

    def On_gesBases(self,event):
        dlg = xGestionConfig.DLG_listeConfigs(self.parent)
        dlg.ShowModal()
        del dlg

    def On_gesTables(self,event):
        xUTILS_DB.Init_tables(parent= self.parent,mode= "creation",
                              db_tables=DB_schema.DB_TABLES,db_ix=DB_schema.DB_IX,db_pk=DB_schema.DB_PK)

    def On_ctrlTables(self,event):
        xUTILS_DB.Init_tables(parent=self.parent,mode="ctrl",
                              db_tables=DB_schema.DB_TABLES)


if __name__ == "__main__":
    """ Affichage du menu"""
    menu = MENU(None).ParamMenu()
    for dictColonne in menu:
        print(dictColonne['code'], dictColonne['label'])
        for ligne in dictColonne['items']:
            print('\t',end='')
            if isinstance(ligne,str):
                print(ligne)
            elif isinstance(ligne,dict):
                print(ligne['code'],"\t", ligne['label'],"\n\t\t",ligne.keys())
            else: print("problème!!!!!!!!!!!")
    for dictColonne in menu:
        for dictligne in dictColonne['items']:
            if 'action' in dictligne:
                if dictligne['action'][:1] != 'x':
                    act = "MENU."+dictligne['action']+"(None)"
                    print(act + "\t action >>\t")
