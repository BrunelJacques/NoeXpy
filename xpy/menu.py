# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
""" Exemple de la construction de la barre de menus à mettre avec les sources de l'appli """
class MENU():
    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        # The "\t..." syntax defines an accelerator key that also triggers
        menu = [
            # Première colonne
            {"code": "&menu_fichier\tCtrl-F", "label": (u"Fichier"), "items": [
                #descriptif des lignes : code, label, bulle, image, action, genre, actif
                {"code": "Action 11", "label": (u"&première action\tCtrl-N"),
                 "infobulle": (u"lancement d'une action 11"), "image": "Images/16x16/Fichier_nouveau.png",
                 "action": "On_fichier_Nouveau", "genre": wx.ITEM_NORMAL, "actif": True},
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

    def On_fichier_Nouveau(self):
        print('Bonjour Action 11 xpy')
        return

    def On_param_preferences(self):
        print('Bonjour On_param_preferences')

    def On_param_utilisateurs(self):
        print('Bonjour On_param_utilisateurs')

if __name__ == "__main__":
    """ Affichage du menu"""
    menu = MENU().ParamMenu()
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
                    eval(act)
