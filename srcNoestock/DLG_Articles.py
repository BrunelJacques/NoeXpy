#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des stocks et prix de journée
# Usage :          Gestion des articles
# Auteur:          Jacques BRUNEL 2021-02 Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import xpy.xGestion_TableauRecherche    as xgtr
import xpy.xUTILS_Identification        as xuid
import srcNoestock.UTILS_Stocks         as nust
from srcNoelite     import DB_schema
from xpy.outils     import xformat

TITRE2 = "Recherche d'un article"
INTRO2 = "les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche"
TITRE = "Gestion des articles en stock"
INTRO = "La saisie des articles permet aussi d'ajuster les quantités en stock et les prix de référence"

def GetDicOlv(cutend=None):
    # le cutend est utilisé pour limiter les colonnes affichées en recherche F4
    dicBandeau = {'titre':TITRE2,
                  'texte':INTRO2,
                  'hauteur':20, 'nomImage':"xpy/Images/80x80/Legumes.png"}
    # Composition de la matrice de l'OLV articles, retourne un dictionnaire
    nbcol = len(DB_schema.DB_TABLES['stArticles'])
    if cutend:
        nbcol -= cutend
    table = DB_schema.DB_TABLES['stArticles'][:nbcol]
    lstChamps = xformat.GetLstChamps(table)
    #lstTypes = xformat.GetLstTypes(table)
    lstNomsColonnes = xformat.GetLstChamps(table)
    lstLargeurColonnes = [200, 60, 128,-1, 60, 70, -1, -1, -1, -1, -1, -1, 90][:nbcol]
    lstColonnes = xformat.GetLstColonnes(table=table,lstLargeur=lstLargeurColonnes,lstNoms=lstNomsColonnes)
    matriceSaisie =  xformat.DicOlvToMatrice(('ligne',""),{'lstColonnes':lstColonnes})
    # Personnalisation
    lgSize = 150
    for lg in lstLargeurColonnes: lgSize += max(lg,50)
    sizeSaisie = (500, max(len(lstColonnes) * 50, 400))
    return   {
                'lstColonnes': lstColonnes,
                'lstChamps':lstChamps,
                'getDonnees': nust.SqlArticles,
                'lstNomsBtns': ['creer','modifier'],
                'size':(lgSize,700),
                'sizeSaisie': sizeSaisie,
                'ctrlSize': (150,30),
                'matriceSaisie': matriceSaisie,
                'dicBandeau': dicBandeau,
                'sortColumnIndex': 0,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetOneIDarticle(db,value,**kwds):
    f4 = kwds.pop('f4',False)
    # recherche d'un article unique à partir d'une saisie d'id partielle
    while True:
        # tant qu'on récupère pas au moins un enregistrement on réduit value
        recordset = nust.SqlOneArticle(db,value)
        if recordset == None or len(recordset) >= 1 or len(value) == 0:
            break
        value = value[:-1]
    # traitement du recordset obtenu
    if recordset == None:
        IDarticle = None
    elif len(recordset) == 1 and not f4:
        IDarticle = recordset[0][0]
    else:
        # article unique non trouvé, on lance la gestion des articles pour un choix filtré sur value
        cutend = len(DB_schema.DB_TABLES['stArticles'])-4
        # on affiche seulement trois premières colonnes
        dicOlv = GetDicOlv(cutend=cutend)
        dicOlv['withObsoletes'] = False
        # pas de bouton pour que le dbl click ne lance pas de modif d'article
        del dicOlv['lstNomsBtns']
        dlg = DLG_articles(db=db,value=value,dicOlv=dicOlv)
        ret = dlg.ShowModal()
        IDarticle = None
        if ret == wx.OK:
            selection = dlg.GetSelection()
            if not selection and len(dlg.ctrlOlv.innerList) >0:
                selection = dlg.ctrlOlv.innerList[0]
            if selection:
                IDarticle = selection.IDarticle
        dlg.Destroy()
    return IDarticle

# gestion des articles via tableau de recherche ---------------------------------------------------------
class DLG_articles(xgtr.DLG_tableau):
    def __init__(self,**kwds):
        value = kwds.pop('value',None)
        dicOlv = kwds.pop('dicOlv',None)
        if not dicOlv:
            dicOlv = GetDicOlv(cutend=2)
            dicOlv['dicBandeau']['titre'] = TITRE
            dicOlv['dicBandeau']['texte'] = INTRO

        kwds['dicOlv'] = dicOlv
        db = kwds.pop('db',None)
        if db == None:
            import xpy.xUTILS_DB as xdb
            db = xdb.DB()
        kwds['db'] = db

        #kwds['dicParams'] = {'bandeau': dicBandeau}
        super().__init__(None, **kwds)
        self.db = db
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()

        if  isinstance(value,str):
            self.pnlOlv.ctrlOutils.barreRecherche.SetValue(value)
        # enlève le filtre si pas de réponse
        if len(self.ctrlOlv.innerList) == 0:
            self.pnlOlv.ctrlOutils.barreRecherche.SetValue('')
        self.pnlOlv.ctrlOutils.barreRecherche.OnSearch(None)
        self.pnlOlv.ctrlOlv.SetFocus()

    def FmtDonneesDB(self,nomsCol,donnees,complete=True):
        table = DB_schema.DB_TABLES['stArticles']
        lstNomsColonnes = xformat.GetLstChamps(table)
        lstChamps = xformat.GetLstChamps(table)
        lstDonnees = []
        # alimente les données saisies
        for col in nomsCol:
            lstDonnees.append((lstChamps[lstNomsColonnes.index(col)],donnees[nomsCol.index(col)]))
        if len(donnees) < len(lstNomsColonnes) and complete:
            # tous les champs n'ont pas été saisis, complementation avec des valeurs par défaut
            lstTypes = xformat.GetLstTypes(table)
            lstValDef = xformat.ValeursDefaut(lstNomsColonnes,lstTypes)
            champsNonSaisis = [ lstChamps[lstNomsColonnes.index(x)] for x in lstNomsColonnes if x not in nomsCol]
            for champ in champsNonSaisis:
                lstDonnees.append((champ,lstValDef[lstChamps.index(champ)]))
        return lstDonnees

    def GereDonnees(self,**kwd):
        kwd['db'] = self.db
        nust.SauveArticle(self,**kwd)

    def ValideSaisie(self,dlgSaisie,*args,**kwd):
        #appel de l'écran de saisie en sortie
        mode = kwd.get('mode', None)
        dDonnees = dlgSaisie.pnl.GetValues(fmtDD=False)
        mess = "Incohérence relevée dans les données saisies\n"
        lg = len(mess)
        IDarticle = dDonnees['IDarticle']
        if mode == 'ajout':
            lstArticles = nust.SqlOneArticle(IDarticle, flou = False)
            if len(lstArticles) > 0:
                mess += "\n- L'article '%s' est déjà présent, passez en modification\n" % IDarticle
        for champ in ('IDarticle','magasin'):
            if not (dDonnees[champ]) or len(dDonnees[champ]) == 0:
                    mess += "\n- La saisie de '%s' est obligatoire\n"%champ
        for champ in ('txTva','prixMoyen'):
            if not(dDonnees[champ]) or float(dDonnees[champ]) == 0.0:
                mess += "\n- La saisie de '%s' est obligatoire\n"%champ
        if len(mess) != lg:
            wx.MessageBox(mess, "Entrée refusée!!!", style=wx.ICON_HAND)
            return wx.NO

        # formatage
        for champ in ('IDarticle','fournisseur'):
            if (dDonnees[champ]): dDonnees[champ] = dDonnees[champ].upper()
        for champ in ('magasin','rayon'):
            if (dDonnees[champ]): dDonnees[champ] = dDonnees[champ].capitalize()

        return wx.OK


# Pour tests ------------------------------------------------------------
if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
    dlg = DLG_articles()
    ret = dlg.ShowModal()
    print(ret)