#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os
import sys
import appdirs
import tempfile

frozen = getattr(sys, 'frozen', '')
if not frozen:
    rep = os.path.abspath(__file__)
    REP_RACINE = rep.split('xpy')[0]
else :
    REP_RACINE = os.path.dirname(sys.executable)

if REP_RACINE not in sys.path :
    sys.path.insert(1, REP_RACINE)

def GetRepRacine(fichier=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_RACINE, fichier)

def GetRepData(fichier=""):
    chemin = appdirs.user_data_dir()
    return os.path.join(chemin, fichier)

def GetRepTemp(fichier=""):
    chemin = tempfile.gettempdir()
    return os.path.join(chemin, fichier)

def GetRepUser(fichier=""):
    chemin = appdirs.user_config_dir(appname=None, appauthor=None, roaming=False)
    return os.path.join(chemin, fichier)

    # Recherche le chemin du répertoire de l'utilisateur
    #chemin = chemin.decode("iso-8859-15")

if __name__ == "__main__":
    # Répertoires
    print(GetRepRacine('racine'))
    print(GetRepUser('user'))
    print(GetRepData('datas'))
    print(GetRepTemp('temp'))

