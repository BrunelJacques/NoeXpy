#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import os
import io
import sys
import shutil
import platform
import subprocess
import appdirs
import zipfile

frozen = getattr(sys, 'frozen', '')
if not frozen:
    REP_COURANT = os.path.dirname(os.path.abspath(__file__))
    REP_PARENT = os.path.dirname(REP_COURANT)
else :
    REP_PARENT = os.path.dirname(sys.executable)

if REP_PARENT not in sys.path :
    sys.path.insert(1, REP_PARENT)

def GetMainPath(fichier=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_PARENT, fichier)

def GetRepData(fichier=""):
    # Vérifie si un répertoire 'Portable' existe
    chemin = GetMainPath("Portable")
    if os.path.isdir(chemin):
        chemin = os.path.join(chemin, "Data")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)
        return os.path.join(chemin, fichier)

    # Recherche le chemin du répertoire des données
    if sys.platform == "win32" and platform.release() != "Vista" :

        chemin = appdirs.site_data_dir(appname=None, appauthor=None)
        #chemin = chemin.decode("iso-8859-15")

        chemin = os.path.join(chemin, "noethys")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)

    else :

        chemin = appdirs.user_data_dir(appname=None, appauthor=None)
        #chemin = chemin.decode("iso-8859-15")

        chemin = os.path.join(chemin, "noethys")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)

        chemin = os.path.join(chemin, "Data")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)

    # Ajoute le dirname si besoin
    return os.path.join(chemin, fichier)

def GetRepTemp(fichier=""):
    chemin = GetRepUtilisateur("Temp")
    return os.path.join(chemin, fichier)

def GetRepUpdates(fichier=""):
    path = GetRepUtilisateur("Updates")
    return os.path.join(path, fichier)

def GetRepLang(fichier=""):
    chemin = GetRepUtilisateur("Lang")
    return os.path.join(chemin, fichier)

def GetRepSync(fichier=""):
    chemin = GetRepUtilisateur("Sync")
    return os.path.join(chemin, fichier)

def GetRepExtensions(fichier=""):
    chemin = GetRepUtilisateur("Extensions")
    return os.path.join(chemin, fichier)

def GetRepUtilisateur(fichier=""):
    """ Recherche le répertoire Utilisateur pour stockage des fichiers de config et provisoires """
    # Vérifie si un répertoire 'Portable' existe
    chemin = GetMainPath("Portable")
    if os.path.isdir(chemin):
        return os.path.join(chemin, fichier)

    # Recherche le chemin du répertoire de l'utilisateur
    chemin = appdirs.user_config_dir(appname=None, appauthor=None, roaming=True)
    #chemin = chemin.decode("iso-8859-15")

    # Ajoute 'noethys' dans le chemin et création du répertoire
    chemin = os.path.join(chemin, "noethys")
    if not os.path.isdir(chemin):
        os.mkdir(chemin)

    # Ajoute le dirname si besoin
    return os.path.join(chemin, fichier)

def DeplaceFichiers():
    """ Vérifie si des fichiers du répertoire Data ou du répertoire Utilisateur sont à déplacer vers le répertoire Utilisateur>AppData>Roaming """

    # Déplace les fichiers de config et le journal
    for nom in ("journal.log", "Config.json", "Customize.ini") :
        for rep in ("", GetMainPath("Data"), os.path.join(os.path.expanduser("~"), "noethys")) :
            fichier = os.path.join(rep, nom)
            if os.path.isfile(fichier) :
                print(["déplacement fichier config :", fichier, " > ", GetRepUtilisateur(nom)])
                shutil.move(fichier, GetRepUtilisateur(nom))

    # Déplace les fichiers xlang
    if os.path.isdir(GetMainPath("Lang")) :
        for nomFichier in os.listdir(GetMainPath("Lang")) :
            if nomFichier.endswith(".xlang") :
                print(["déplacement fichier xlang :", fichier, " > ", GetRepLang(nomFichier)])
                shutil.move(u"Lang/%s" % nomFichier, GetRepLang(nomFichier))

    # Déplace les fichiers du répertoire Sync
    if os.path.isdir(GetMainPath("Sync")) :
        for nomFichier in os.listdir(GetMainPath("Sync")) :
            shutil.move(GetMainPath("Sync/%s" % nomFichier), GetRepSync(nomFichier))

    # Déplace les fichiers de données du répertoire Data
    if GetRepData() != "Data/" and os.path.isdir(GetMainPath("Data")) :
        for nomFichier in os.listdir(GetMainPath("Data")) :
            if nomFichier.endswith(".dat") and "_" in nomFichier and "EXEMPLE_" not in nomFichier and "_archive.dat" not in nomFichier :
                # Déplace le fichier vers le répertoire des fichiers de données
                print(["copie base de donnees :", nomFichier, " > ", GetRepData(nomFichier)])
                shutil.copy(GetMainPath(u"Data/%s" % nomFichier), GetRepData(nomFichier))
                # Renomme le fichier de données en archive (par sécurité)
                try :
                    os.rename(GetMainPath(u"Data/%s" % nomFichier), GetMainPath(u"Data/%s" % nomFichier.replace(".dat", "_archive.dat")))
                except :
                    pass

def OuvrirRepertoire(rep):
    if platform.system() == "Windows":
        subprocess.Popen(["explorer", rep])
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", rep])
    else:
        subprocess.Popen(["xdg-open", rep])

def GetUnicodeFromFile(fileName):
    # lecture du contenu unicode d'un fichier
    import codecs
    fichier = codecs.open(fileName, encoding='utf-8', mode='r')
    return fichier.read()

def GetBytesFromFile(fileName, buffer=True):
    # lecture du contenu 'nature' via buffer d'un fichier
    file = open(fileName, "rb")
    data = file.read()
    file.close()
    if not buffer:
        return data
    buffer = io.BytesIO(data)
    bytesBuffer = buffer.read()
    return bytesBuffer

def SetFileFromBytes(fileName,dataBytes):
    # Création du fichier dans le répertoire Temp
    try:
        file = open(fileName, "wb")
        file.write(dataBytes)
        file.close()
    except Exception as err:
        print(err)
        return err
    return 'ok'

#- Gestion des fichiers Zip -------------------------------------------------

def VerificationZip(fichier=""):
    """ Vérifie que le fichier est une archive zip valide """
    return zipfile.is_zipfile(fichier)

def SelectionFichier(intro="Choix",wildcard="*.zip",defaultDir=None,
                     style=wx.FD_OPEN,
                     retourCourt=False,
                     verifZip=False):
    # Demande l'emplacement d'un fichier lambda (si non zip modifier wildcard)
    if not defaultDir:
        standardPath = wx.StandardPaths.Get()
        defaultDir = standardPath.GetDocumentsDir()
    dlg = wx.FileDialog(None, message=intro,
                        defaultDir=defaultDir,
                        defaultFile="",
                        wildcard=wildcard,
                        style=style)
    if dlg.ShowModal() == wx.ID_OK:
        if retourCourt:
            fichier = dlg.GetFilename()
        else:
            fichier = dlg.GetPath()
    else:
        fichier =None
    dlg.Destroy()
    if fichier and verifZip:
        # Vérifie que c'est un fichier ZIP ok
        valide = VerificationZip(fichier)
        if valide == False:
            dlg = wx.MessageDialog(None,
                       "Le fichier ZIP semble corrompu !",
                       "Erreur", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            fichier = None
    return fichier

def GetZipFile(nameFile='',modeRW='r'):
    # connecte au fichier en mode écriture ou lecture, retourne fichier ou message erreur
    try:
        zip =  zipfile.ZipFile(nameFile, modeRW, compression=zipfile.ZIP_DEFLATED)
    except Exception as err:
        zip = "Accès au fichier Zip impossible \n%s" % err
    return zip

def GetListeFichiersZip(fichierZip):
    """ Récupère la liste des fichiers du ZIP """
    listeFichiers = []
    for fichier in fichierZip.namelist():
        listeFichiers.append(fichier)
    return listeFichiers

def GetOneFileInZip(myZipFile,oneFile):
    with myZipFile.open(oneFile) as myFile:
        return myFile.read()

def ExtractAll(file,path):
    if isinstance(file,(str,bytes)):
        fileName = file
    else:
        fileName = file.filename
    with zipfile.ZipFile(fileName) as myzip:
        myzip.extractall(path)

if __name__ == "__main__":
    # Teste les déplacements de fichiers
    # DeplaceFichiers()

    # Répertoire utilisateur
    print(GetRepUtilisateur())

    # Répertoire des données
    chemin = GetRepData()
    print(1, os.path.join(chemin, "Testé.pdf"))
    print(2, os.path.join(chemin, "Test.pdf"))