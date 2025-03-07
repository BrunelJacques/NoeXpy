#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, Partage de param�tres dans une base de donn�e
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
    # Pour m�moriser ou r�cup�rer tous les param�tres d'une cat�gorie
    """ Le dictionnaire sera �clat� en autant d'enregistrements que d'items
    Renseigner dictParametres est indispensable pour un set,
        la plupart des types sont accept�s dans le dict
    Pour un get, fournir le dictParam�tres permet de r�cup�rer une valeur par d�faut
        et limite le retour aux valeurs dans dicParametres,
        si la valeur est r�cup�r�e, elle sera dans le type de la valeur par d�faut.
    En l'absence de dictParam�tres, on retourne tous les params de la cat�gorie
    """
    if not categorie or categorie == "":
        mess = 'Le param�tre cat�gorie est obligatoire '
        raise Exception(mess)
    DB = xUTILS_DB.DB()

    # Si aucun fichier n'est charg�, on renvoie la valeur par d�faut :
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

    # Le dictParametre n'�tant pas fourni on retournera toute la cat�gorie
    if not dictParametres or len(dictParametres) == 0:
        for nom, valeur in dictDonnees.items():
            dictParametres[nom] = valeur

    # On boucle sur chaque valeur fournie
    for nom, valeur in dictParametres.items():
        # Pr�paration de la valeur par d�faut
        type_parametre = type(valeur)
        valeurTmp = str(valeur)
        if nom in dictDonnees:
            # la valeur �tait stock�e
            if mode == "get":
                valeur = dictDonnees[nom]
                # On le formate pour le r�cup�rer sous le format fourni par d�faut
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
                # On modifie la valeur du param�tre
                dictFinal[nom] = valeur
                if dictDonnees[nom] != valeurTmp:
                    listeModifications.append((valeurTmp, categorie, nom))

        else:
            if mode == "set":
                # Le parametre n'existe pas, on le cr�� :
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
    """ M�morise ou r�cup�re un param�tre quelconque dans la base de donn�es
        si mode = 'get' : valeur est la valeur par d�faut
        si mode = 'set' : valeur est la valeur � donner au param�tre """

    if not nom or nom == "":
        mess = 'Le param�tre nom est obligatoire '
        raise Exception(mess)

    # Recherche du parametre
    DB = xUTILS_DB.DB()

    # valeurTmp sera le retour par d�faut
    valeurTmp = valeur

    # Si aucun fichier n'est charg�, on renvoie la valeur par d�faut :
    if DB.echec == 1:
        erreur = DB.erreur
        DB.Close()
        if mode == "get":
            return valeur
        else:
            mess = "Echec d'acc�s � la base:\n\nErr: %s" % (erreur)
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
                # On le formate pour le r�cup�rer sous le type fourni
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
                # la valeur fournie est None ou non fournie, ce qui ressemble � vide est None
                if valeurTmp == '' or valeurTmp == 'None':
                    valeurTmp == None
        else:
            # en 'set' On modifie la valeur pr�c�dente
            IDparametre = listeDonnees[0][0]
            listeDonnees = [("categorie", categorie), ("nom", nom),
                            ("parametre", str(valeur)), ]
            DB.ReqMAJ("parametres", listeDonnees, "IDparametre", IDparametre)
            valeurTmp = valeur
    elif mode == 'set':
        # Le parametre n'existe pas, on le cr�� :
        listeDonnees = [("categorie", categorie), ("nom", nom),
                        ("parametre", str(valeur)), ]
        newID = DB.ReqInsert("parametres", listeDonnees)
        valeurTmp = valeur
    DB.Close()
    return valeurTmp


# ----------------------- TESTS ---------------------------------------------------------
if __name__ == "__main__":

    # va tester l'�criture dans la table PARAMETRES de la base de donn�e par d�faut
    setCateg = ParametresCategorie(mode="set", categorie="parametres_test",
                                   dictParametres={"today": datetime.date.today(),
                                                   "test": "�crit"})
    getCateg = ParametresCategorie(mode="get", categorie="parametres_test",
                                   dictParametres={"today": datetime.date(2000, 5, 10),
                                                   "test": "no retour"})
    print("Ecrit", setCateg, "\nLu categories", getCateg)

    getParam2 = Parametres(mode="get", nom="aDic")
    print("sans valeur fournie:", getParam2, type(getParam2))

