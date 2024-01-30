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

if sys.platform == 'win32':
    SEP = "\\"
else:
    SEP = "/"

frozen = getattr(sys, 'frozen', '')
if not frozen:
    rep = os.path.abspath(__file__)
    # la racine va s'arrête au niveau 'xpy'
    REP_RACINE = rep.split('%sxpy%s'%(SEP,SEP))[0]
else :
    REP_RACINE = os.path.dirname(sys.executable)

if REP_RACINE not in sys.path :
    sys.path.insert(1, REP_RACINE)

def GetRepRacine(ajout=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_RACINE, ajout)

def GetRepData(ajout="NoeXpy"):
    chemin = appdirs.user_data_dir()
    os.makedirs(chemin, exist_ok=True)
    return  os.path.join(chemin, ajout)

def GetRepTemp(ajout=""):
    chemin = tempfile.gettempdir()
    os.makedirs(chemin, exist_ok=True)
    return os.path.join(chemin, ajout)

def GetRepUser(ajout="",appname=None, roaming=False):
    chemin = appdirs.user_config_dir(appname=appname, roaming=roaming)
    os.makedirs(chemin, exist_ok=True)
    return os.path.join(chemin, ajout)

if __name__ == "__main__":
    # Répertoires
    print(GetRepRacine(),': GetRepRacine')
    print(GetRepUser(),': GetRepUser')
    print(GetRepData(),': GetRepData')
    print(GetRepTemp(),': GetRepTemp')

