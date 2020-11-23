# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx

# Exemple de matrice de configuration d'un panel à envoyer à xGestionConfig
MATRICE_CONFIG = {
    # Chapitre  = categorie ou box verticale
    ("Mémorisation","Chapitre de mémorisation"): [
        # Alinea 11 = ligne dans la box
        {'genre': 'Enum', 'name': 'memoriser', 'label': 'Mémoriser les paramètres', 'value': 3,
         'labels': ["Non", "Oui", "Peut-être"], 'values': [0, 1, 3],
         'help': 'Faut-il mémoriser les paramètres?'},
        # Alinea 12
        {'genre': 'Dir', 'name': 'repertoire', 'label': 'Choix du répertoire', 'value': '',
         'help': 'Veuillez choisir le répertoire'},
    ],
    # Chapitre 2
        ("Autres éléments","Chapitre des autes éléments"): [
        # Alinea 21 et suivants
        {'genre': 'Bool', 'name': 'ouiNon', 'label': 'Etes-vous oui ou non', 'value': True,
         'help': 'Cochez pour le oui'},
        {'genre': 'String', 'name': 'monTexte', 'label': 'Saisir un ctrl', 'value': '',
         'help': 'Saisir votre ctrl'},
        {'genre': 'Int', 'name': 'entier', 'label': 'Saisir un entier', 'value': 0,
         'help': 'Saisir votre nombre entier'},
        {'genre': 'Float', 'name': 'saisieNbre', 'label': 'Saisir un nombre réel', 'value': 0.0,
         'help': 'Saisir votre nombre réel', 'btnLabel': ' ! ', 'btnHelp': 'Là vous pouvez lancer une action par clic',
         'btnAction': 'OnClicFloat', 'ctrlAction': 'OnEnterFloat'},
        {'genre': 'Colour', 'name': 'couleur', 'label': 'Choisir votre couleur', 'value': wx.Colour(255, 0, 0),
         'help': 'Saisir votre couleur préférée', 'btnLabel': None, 'btnHelp': None},
        {'genre': 'multichoice', 'name': 'choix', 'label': 'Choix multiples', 'value': [],
         'labels': ["choix 1", "choix 2", "choix3"]},
    ]
}

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent

    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        # The "\t..." syntax defines an accelerator key that also triggers
        menu = [
            # Première colonne
            {"code": "&menu_fichier\tCtrl-F", "label": (u"Fichier"), "items": [
                #descriptif des lignes : code, label, bulle, image, action, genre, actif
                {"code": "nouveau_fichier", "label": (u"&Créer un nouveau fichier\tCtrl-N"),
                 "infobulle": (u"Créer un nouveau fichier"), "image": "Images/16x16/Fichier_nouveau.png",
                 "action": "On_fichier_Nouveau", "genre": wx.ITEM_NORMAL, "actif": True},
                {"code": "ouvrir_fichier", "label": (u"Ouvrir un fichier"), "infobulle": (u"Ouvrir un fichier existant"),
                 "image": "Images/16x16/Fichier_ouvrir.png", "action":"On_fichier_Ouvrir","actif": True},
                {"code": "fermer_fichier", "label": (u"Fermer le fichier"), "infobulle": (u"Fermer le fichier ouvert"),
                 "image": "Images/16x16/Fichier_fermer.png", "action": "On_fichier_Fermer", "actif": False},
                "-",
                {"code": "fichier_informations", "label": (u"Informations sur le fichier"),
                 "infobulle": (u"Informations sur le fichier"), "image": "Images/16x16/Information.png",
                 "action": "xInfos", "actif": True},
                "-",
                {"code": "creer_sauvegarde", "label": (u"Créer une sauvegarde"), "infobulle": (u"Créer une sauvegarde"),
                 "image": "Images/16x16/Sauvegarder.png", "action": "On_fichier_Sauvegarder"},
                {"code": "restaurer_sauvegarde", "label": (u"Restaurer une sauvegarde"),
                 "infobulle": (u"Restaurer une sauvegarde"), "image": "Images/16x16/Restaurer.png",
                 "action": "On_fichier_Restaurer"},
                "-",
                {"code": "quitter", "label": (u"Quitter"), "infobulle": (u"Quitter l'application"),
                 "image": "Images/16x16/Quitter.png", "action": "xQuitter"},
            ],
             },

            # Deuxième colonne
            {"code": "menu_parametrage", "label": (u"Paramétrage"), "items": [
                {"code": "preferences", "label": (u"Préférences"), "infobulle": (u"Préférences"),
                 "image": "Images/16x16/Mecanisme.png", "action": "On_param_preferences"},
                "-",
                {"code": "utilisateurs", "label": (u"Utilisateurs"), "infobulle": (u"Paramétrage des utilisateurs"),
                 "image": "Images/16x16/Personnes.png", "action": "On_param_utilisateurs"},
                "-",
            ],
             },
        ]
        return menu

    def On_fichier_Nouveau(self,event):
        """ Créé une nouvelle base de données """
        print('Bonjour On_fichier_Nouveau')
        return

    def On_fichier_Ouvrir(self,event):
        print('Bonjour On_fichier_Ouvrir')

    def On_fichier_Fermer(self,event):
        print('Bonjour On_fichier_Fermer')

    def On_fichier_Sauvegarder(self,event):
        print('Bonjour On_fichier_Sauvegarder')

    def On_fichier_Restaurer(self,event):
        print('Bonjour On_fichier_Restaurer')

    def On_param_preferences(self,event):
        print('Bonjour On_param_preferences')

    def On_param_utilisateurs(self,event):
        print('Bonjour On_param_utilisateurs')

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
                    #print("action", dictligne['code'])
                    act = "MENU."+dictligne['action']+"(None)"
                    print(act + "\t action >>\t", end='')
