# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2020-03    Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
from xpy import xUTILS_Identification, xGestionConfig

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent

    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        menu = [
        # Première colonne
        {"code": "&outils\tCtrl-O", "label": ("Outils"),
        "items": [
            {"code": "config", "label": ("&Accès aux Bases de données\tCtrl-A"),
                "infobulle": ("Reconfigurer l'accès à la base de données principale"),
                "image": "Images/16x16/Utilisateur_reseau.png",
                "action": "On_config", "genre": wx.ITEM_NORMAL},
            {"code": "synchro", "label": ("Synchroniser deux bases de données"),
                "infobulle": ("La synchronisation met à jour les bases de données dans les deux sens"),
                "image": "Images/16x16/Actualiser2.png",
                "action": "On_synchro"},
            "-",
            {"code": "identification", "label": ("S'identifier"),
                "infobulle": ("Appel de l'écran d'identification"),
                "image": "Images/16x16/Homme.png",
                "action": "On_identification"},
            "-",
            {"code": "sauve", "label": ("Sauvegarder"),
                "infobulle": ("Sauvegarde la base de données"),
                "image": "Images/16x16/Conversion.png", "action": "On_sauve"},
            {"code": "quitter", "label": ("Quitter"),
                "infobulle": ("Fin de travail Noelite"),
                "image": "Images/16x16/Quitter.png",
                "action": "xQuitter"},
            ]},
        # deuxième colonne
        {"code": "&params\tCtrl-S", "label": ("Système"),
         "items": [
            {"code": "gesbases", "label": ("Gestion des bases"),
                "infobulle": ("Création, copie de bases de données"),
                "image": "Images/16x16/Utilisateur_reseau.png", "action": "On_gesBases"},
            {"code": "gestables", "label": ("Ajout de tables"),
                "infobulle": ("Outil permettant de créer les tables manquantes dans la base"),
                "image": "Images/16x16/Actualiser2.png", 
                "action": "On_gesTables"},
        ]},
        # troisième colonne
        {"code": "&princip\tCtrl-P", "label": ("Principal"),
         "items": [
            {"code": "inStock", "label": ("&Entrée en stock"),
             "infobulle": ("Saisie d'une entrée en stock (livraison, achat direct, retour camp, correctifs...)"),
             "image": "Images/80x80/Entree.png",
             "action": "On_inStock", "genre": wx.ITEM_NORMAL},

             {"code": "outStocks", "label": ("&Sortie du stock"),
              "infobulle": ("Saisie d'une sortie de stock, (repas en cuisine, extérieur, autre camp, correctifs)"),
              "image": "Images/80x80/Sortie.png",
              "action": "On_outStock", "genre": wx.ITEM_NORMAL},

             {"code": "effectifs", "label": ("&Effectifs présents"),
              "infobulle": ("Gestion des effectifs journaliers des couverts"),
              "image": "Images/80x80/Famille.png",
              "action": "On_effectifs", "genre": wx.ITEM_NORMAL},

             {"code": "inventaires", "label": ("&Inventaires"),
              "infobulle": ("Etat du stock, contrôle, correction pour l'inventaire"),
              "image": "Images/80x80/Inventaire.png",
              "action": "On_inventaires", "genre": wx.ITEM_NORMAL},

             {"code": "prixJournee", "label": ("&Prix journée"),
              "infobulle": ("Calcul du prix de journée après saisie des sorties et de l'effectif"),
              "image": "Images/80x80/Loupe.png",
              "action": "On_prixJournee", "genre": wx.ITEM_NORMAL},
         ]}
        ]
        return menu

    def CouleurFondBureau(self):
        return wx.Colour(96,73,123)

    def ParamBureau(self):
        #appelé pour construire une page d'accueil, même structure que les items du menu pour gérer des boutons
        lstItems = [
            {"code": "inStock", "label": ("&Entrée en stock"),
             "infobulle": ("Saisie d'une entrée en stock (livraison, achat direct, retour camp, correctifs...)"),
             "image": "Images/80x80/Entree.png",
             "action": self.menuClass.On_inStock, "genre": wx.ITEM_NORMAL},

            {"code": "outStocks", "label": ("&Sortie du stock"),
             "infobulle": ("Saisie d'une sortie de stock, (repas en cuisine, extérieur, autre camp, correctifs)"),
             "image": "Images/80x80/Sortie.png",
             "action": self.menuClass.On_outStock, "genre": wx.ITEM_NORMAL},

            {"code": "effectifs", "label": ("&Effectifs présents"),
             "infobulle": ("Gestion des effectifs journaliers des couverts"),
             "image": "Images/80x80/Famille.png",
             "action": self.menuClass.On_effectifs, "genre": wx.ITEM_NORMAL},

            {"code": "inventaires", "label": ("&Inventaires"),
             "infobulle": ("Etat du stock, contrôle, correction pour l'inventaire"),
             "image": "Images/80x80/Inventaire.png",
             "action": self.menuClass.On_inventaires, "genre": wx.ITEM_NORMAL},

            {"code": "prixJournee", "label": ("&Prix journée"),
             "infobulle": ("Calcul du prix de journée après saisie des sorties et de l'effectif"),
             "image": "Images/80x80/Loupe.png",
             "action": self.menuClass.On_prixJournee, "genre": wx.ITEM_NORMAL},
        ]
        return lstItems

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        ret = self.parent.SaisieConfig()

    def On_synchro(self,event):
        pass
        #CTRL_Identification.AfficheUsers()

    def On_identification(self,event):
        dlg = xUTILS_Identification.Dialog(self.parent)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            self.parent.dictUser = dlg.GetDictUtilisateur()
            self.parent.MakeStatusText()

    def On_gesBases(self,event):
        dlg = xGestionConfig.DLG_saisieUneConfig(self.parent, modeBase='creation')
        ret = dlg.ShowModal()

    def On_gesTables(self,event):
        pass
    def On_sauve(self,event):
        pass
    def On_inStock(self,event):
        pass
    def On_outStock(self,event):
        pass
    def On_effectifs(self,event):
        pass
    def On_inventaires(self,event):
        pass
    def On_prixJournee(self,event):
        pass

if __name__ == "__main__":
    """ Affichage du menu"""
    menu = MENU(None).ParamMenu()
    for dictColonne in menu:
        print('COL: ',dictColonne['code'], dictColonne['label'])
        for ligne in dictColonne['items']:
            print('\t'*3,'LIG: ',end='')
            if isinstance(ligne,str):
                print(ligne)
            elif isinstance(ligne,dict):
                print(ligne['code'],"\t", ligne['label'],"\n","\t"*7,ligne.keys())
            else: print("problème!!!!!!!!!!!")
    print('\nFonctions ','-'*30)
    for dictColonne in menu:
        for dictligne in dictColonne['items']:
            if 'action' in dictligne:
                if dictligne['action'][:1] != 'x':
                    print('\t'*2,"MENU."+dictligne['action']+"(None)")
