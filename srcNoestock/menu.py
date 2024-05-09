# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:         Jacques BRUNEL,
# Copyright:       (c) 2021-01    Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
from xpy         import xUTILS_Identification, xGestionConfig, xUTILS_DB
from srcNoestock import DLG_Articles, DLG_Mouvements, DLG_MvtOneArticle
from srcNoestock import DLG_Effectifs, DLG_PrixJour, DLG_Inventaires
from srcNoelite  import DB_schema

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent
        self.parent.ConnectBase()
        xUTILS_DB.Init_tables(parent=self.parent,mode="test",
                          tables=self.parent.dictAppli['LST_TABLES'],
                          db_tables=DB_schema.DB_TABLES)

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
            {"code": "config", "label": ("&Mise à jour des programmes\tCtrl-R"),
             "infobulle": ("Release ou réinstallation ailleurs"),
             "image": "Images/16x16/Utilisateur_reseau.png",
             "action": "On_github", "genre": wx.ITEM_NORMAL},
            "-",
            {"code": "identification", "label": ("S'identifier"),
                "infobulle": ("Appel de l'écran d'identification"),
                "image": "Images/16x16/Homme.png",
                "action": "On_identification"},
            "-",
            {"code": "quitter", "label": ("Quitter"),
                "infobulle": ("Fin de travail Noelite"),
                "image": "Images/16x16/Quitter.png",
                "action": "xQuitter"},
            ]},
        # deuxième colonne
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

             {"code": "oneArticle", "label": ("&Suivi mouvements"),
              "infobulle": (
                  "Suivi des mouvements d'un article particulier ou de tous les mouvements d'une période"),
              "image": "Images/80x80/Validation.png",
              "action": "On_oneArticle", "genre": wx.ITEM_NORMAL},

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
              "image": "Images/80x80/Euro.png",
              "action": "On_prixJournee", "genre": wx.ITEM_NORMAL},
         ]},
        # troisième colonne
        {"code": "&param\tCtrl-S", "label": ("Paramétrer"),
        "items": [
            {"code": "analytiques", "label": ("Paramétrer les codes analytiques"),
             "infobulle": ("Les codes analytiques sont partagés entre diverses applications"),
             "image": "Images/80x80/Analytic.png",
             "action": "On_analytiques"},
            {"code": "articles", "label": ("Gestion des articles"),
             "infobulle": ("La gestion des articles permet de compléter ou corriger toutes les données de la table"),
             "image": "Images/80x80/Legumes.png",
             "action": "On_articles"},
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
            {"code": "inStock", "label": ("&Entrée en stock"),
             "infobulle": ("Saisie d'une entrée en stock (livraison, achat direct, retour camp, correctifs...)"),
             "image": "Images/80x80/Entree.png",
             "action": self.menuClass.On_inStock, "genre": wx.ITEM_NORMAL},

            {"code": "outStocks", "label": ("&Sortie du stock"),
             "infobulle": ("Saisie d'une sortie de stock, (repas en cuisine, extérieur, autre camp, correctifs)"),
             "image": "Images/80x80/Sortie.png",
             "action": self.menuClass.On_outStock, "genre": wx.ITEM_NORMAL},

            {"code": "oneArticle", "label": ("&Suivi mouvements"),
             "infobulle": (
                 "Suivi des mouvements d'un article particulier ou de tous les mouvements d'une période"),
             "image": "Images/80x80/Validation.png",
             "action": self.menuClass.On_oneArticle, "genre": wx.ITEM_NORMAL},

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
             "image": "Images/80x80/Euro.png",
             "action": self.menuClass.On_prixJournee, "genre": wx.ITEM_NORMAL},
        ]
        return lstItems

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        ret = self.parent.SaisieConfig()
        if ret == wx.OK:
            self.parent.ConnectBase()

    def On_github(self,event):
        from xpy import xGithub
        dlg = xGithub.DLG("NoeXpy")
        ret = dlg.ShowModal()
        del dlg

    def On_analytiques(self,event):
        try:
            from srcNoelite import DLG_Analytique
            dlg = DLG_Analytique.DLG()
            ret = dlg.ShowModal()
            del dlg
        except:
            pass

    def On_articles(self,event):
        dlg = DLG_Articles.DLG_articles()
        ret = dlg.ShowModal()
        del dlg

    def On_identification(self,event):
        dlg = xUTILS_Identification.Dialog(self.parent)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            self.parent.dictUser = dlg.GetDictUtilisateur()
        self.parent.MakeStatusText()
        self.parent.GestMenu(True)
        del dlg

    def On_gesBases(self,event):
        dlg = xGestionConfig.DLG_saisieUneConfig(self.parent, modeBase='creation')
        ret = dlg.ShowModal()
        del dlg

    def On_gesTables(self,event):
        xUTILS_DB.Init_tables(parent= self.parent,mode= "creation",
                              tables= self.parent.dictAppli['LST_TABLES'],
                              db_tables=DB_schema.DB_TABLES,db_ix=DB_schema.DB_IX,db_pk=DB_schema.DB_PK)

    def On_ctrlTables(self,event):
        xUTILS_DB.Init_tables(parent=self.parent,mode="ctrl",
                              tables=self.parent.dictAppli['LST_TABLES'],
                              db_tables=DB_schema.DB_TABLES)

    def On_inStock(self,event):
        dlg = DLG_Mouvements.DLG(sens='entrees')
        dlg.ShowModal()
        del dlg

    def On_outStock(self,event):
        dlg = DLG_Mouvements.DLG(sens='sorties')
        ret = dlg.ShowModal()
        dlg.Destroy()
        del dlg

    def On_oneArticle(self,event):
        dlg = DLG_MvtOneArticle.DLG()
        dlg.ShowModal()
        dlg.Destroy()
        del dlg

    def On_effectifs(self,event):
        dlg = DLG_Effectifs.DLG()
        ret = dlg.ShowModal()
        dlg.Destroy()
        del dlg

    def On_inventaires(self,event):
        dlg = DLG_Inventaires.DLG()
        ret = dlg.ShowModal()
        dlg.Destroy()
        del dlg

    def On_prixJournee(self,event):
        dlg = DLG_PrixJour.DLG()
        ret = dlg.ShowModal()
        dlg.Destroy()
        del dlg

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
