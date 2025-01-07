#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, Partage de paramètres dans une base de donnée
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Modifs JB
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx
import datetime
from xpy import xUTILS_DB
from xpy.outils.xformat import DateSqlToDatetime

TYPE_COULEUR = wx._core.Colour


def ParametresCategorie(mode="get", categorie="", dictParametres={}, **kwd):
    # Pour mémoriser ou récupérer tous les paramètres d'une catégorie
    """ Le dictionnaire sera éclaté en autant d'enregistrements que d'items
    Renseigner dictParametres est indispensable pour un set,
        la plupart des types sont acceptés dans le dict
    Pour un get, fournir le dictParamètres permet de récupérer une valeur par défaut
        et limite le retour aux valeurs dans dicParametres,
        si la valeur est récupérée, elle sera dans le type de la valeur par défaut.
    En l'absence de dictParamètres, on retourne tous les params de la catégorie
    """
    if not categorie or categorie == "":
        mess = 'Le paramètre catégorie est obligatoire '
        raise Exception(mess)
    DB = xUTILS_DB.DB()

    # Si aucun fichier n'est chargé, on renvoie la valeur par défaut :
    if DB.echec == 1:
        return dictParametres

    req = """SELECT IDparametre, nom, parametre FROM parametres WHERE categorie="%s";""" % categorie
    DB.ExecuterReq(req, mess="UTILS_Parametres.ParametresCategorie")
    listeDonnees = DB.ResultatReq()
    dictDonnees = {}
    for IDparametre, nom, parametre in listeDonnees:
        dictDonnees[nom] = parametre

    listeAjouts = []
    listeModifications = []
    dictFinal = {}

    # Le dictParametre n'étant pas fourni on retournera toute la catégorie
    if not dictParametres or len(dictParametres) == 0:
        for nom, valeur in dictDonnees.items():
            dictParametres[nom] = valeur

    # On boucle sur chaque valeur fournie
    for nom, valeur in dictParametres.items():
        # Préparation de la valeur par défaut
        type_parametre = type(valeur)
        valeurTmp = str(valeur)
        if nom in dictDonnees:
            # la valeur était stockée
            if mode == "get":
                valeur = dictDonnees[nom]
                # On le formate pour le récupérer sous le format fourni par défaut
                try:
                    if type_parametre == int:
                        valeur = int(valeur)
                    elif type_parametre == str:
                        valeur = valeur
                    elif type_parametre == float:
                        valeur = float(valeur)
                    elif type_parametre == tuple:
                        valeur = eval(valeur)
                    elif type_parametre == list:
                        valeur = eval(valeur)
                    elif type_parametre == datetime.date:
                        valeur = DateSqlToDatetime(valeur)
                    elif type_parametre == dict:
                        valeur = eval(valeur)
                    elif type_parametre == bool:
                        valeur = eval(valeur)
                    elif type_parametre == TYPE_COULEUR and valeur != "":
                        valeur = eval(valeur)
                except:
                    valeur = None
                dictFinal[nom] = valeur

            if mode == "set":
                # On modifie la valeur du paramètre
                dictFinal[nom] = valeur
                if dictDonnees[nom] != valeurTmp:
                    listeModifications.append((valeurTmp, categorie, nom))

        else:
            if mode == "set":
                # Le parametre n'existe pas, on le créé :
                listeAjouts.append((categorie, nom, valeurTmp))
            dictFinal[nom] = valeur

    # Sauvegarde des modifications
    if len(listeModifications) > 0:
        DB.Executermany("UPDATE parametres SET parametre=? WHERE categorie=? and nom=?",
                        listeModifications, commit=False)

    # Sauvegarde des ajouts
    if len(listeAjouts) > 0:
        DB.Executermany(
            "INSERT INTO parametres (categorie, nom, parametre) VALUES (?, ?, ?)",
            listeAjouts, commit=False)

    # Commit et fermeture de la DB
    if len(listeModifications) > 0 or len(listeAjouts) > 0:
        DB.Commit()
    DB.Close()
    return dictFinal


def Parametres(mode="get", categorie="", nom="", valeur=None, **kwd):
    """ Mémorise ou récupère un paramètre quelconque dans la base de données
        si mode = 'get' : valeur est la valeur par défaut
        si mode = 'set' : valeur est la valeur à donner au paramètre """

    if not nom or nom == "":
        mess = 'Le paramètre nom est obligatoire '
        raise Exception(mess)

    # Recherche du parametre
    DB = xUTILS_DB.DB()

    # valeurTmp sera le retour par défaut
    valeurTmp = valeur

    # Si aucun fichier n'est chargé, on renvoie la valeur par défaut :
    if DB.echec == 1:
        erreur = DB.erreur
        DB.Close()
        if mode == "get":
            return valeur
        else:
            mess = "Echec d'accès à la base:\n\nErr: %s" % (erreur)
            wx.MessageBox(mess, "UTILS_Parametre.Parametres", style=wx.ICON_STOP)
            return erreur
    if not categorie or len(categorie) == 0:
        whereCat = ""
    else:
        whereCat = "categorie='%s' AND" % categorie

    req = """SELECT IDparametre, parametre FROM parametres WHERE %s nom='%s';""" % (
    whereCat, nom)
    DB.ExecuterReq(req, mess="xUTILS_Parametres.Parametres")
    listeDonnees = DB.ResultatReq()
    if len(listeDonnees) != 0:
        if mode == "get":
            # Le parametre est lu :
            valeurTmp = listeDonnees[0][1]
            if valeur != None:
                # On le formate pour le récupérer sous le type fourni
                type_parametre = type(valeur)
                if type_parametre == int:
                    valeurTmp = int(valeurTmp)
                elif type_parametre == float:
                    valeurTmp = float(valeurTmp)
                elif type_parametre == str:
                    valeurTmp = valeurTmp
                elif type_parametre == tuple:
                    valeurTmp = eval(valeurTmp)
                elif type_parametre == list:
                    valeurTmp = eval(valeurTmp)
                elif type_parametre == datetime.date:
                    valeurTmp = DateSqlToDatetime(valeurTmp)
                elif type_parametre == dict:
                    valeurTmp = eval(valeurTmp)
                elif type_parametre == bool:
                    valeurTmp = eval(valeurTmp)
            else:
                # la valeur fournie est None ou non fournie, ce qui ressemble à vide est None
                if valeurTmp == '' or valeurTmp == 'None':
                    valeurTmp == None
        else:
            # en 'set' On modifie la valeur précédente
            IDparametre = listeDonnees[0][0]
            listeDonnees = [("categorie", categorie), ("nom", nom),
                            ("parametre", str(valeur)), ]
            DB.ReqMAJ("parametres", listeDonnees, "IDparametre", IDparametre)
            valeurTmp = valeur
    elif mode == 'set':
        # Le parametre n'existe pas, on le créé :
        listeDonnees = [("categorie", categorie), ("nom", nom),
                        ("parametre", str(valeur)), ]
        newID = DB.ReqInsert("parametres", listeDonnees)
        valeurTmp = valeur
    DB.Close()
    return valeurTmp


# ----------------------- TESTS ---------------------------------------------------------
if __name__ == "__main__":

    # va tester l'écriture dans la table PARAMETRES de la base de donnée par défaut
    setCateg = ParametresCategorie(mode="set", categorie="parametres_test",
                                   dictParametres={"today": datetime.date.today(),
                                                   "test": "écrit"})
    getCateg = ParametresCategorie(mode="get", categorie="parametres_test",
                                   dictParametres={"today": datetime.date(2000, 5, 10),
                                                   "test": "no retour"})
    print("Ecrit", setCateg, "\nLu categories", getCateg)

    getParam2 = Parametres(mode="get", nom="aDic")
    print("sans valeur fournie:", getParam2, type(getParam2))

