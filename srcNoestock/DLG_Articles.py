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
import xpy.xGestion_TableauRecherche as xgtr
import xpy.xUTILS_Identification        as xuid
import srcNoestock.UTILS_Stocks         as nust
from srcNoelite     import DB_schema
from xpy.outils     import xformat

TITRE2 = "Recherche d'un article"
INTRO2 = "les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche"
TITRE = "Gestion des articles en stock"
INTRO = "La saisie des articles permet aussi d'ajuster les quantités en stock et les prix de référence"


def GetOlvColonnes(table):
    lstNomsColonnes = xformat.GetLstChamps(table)
    lstLargeurColonnes = [200, 60, 128,-1, 60, 80, 80, -1, -1, -1, -1, -1, 90]
    lstColonnes = xformat.GetLstColonnes(table=table,lstLargeur=lstLargeurColonnes,lstNoms=lstNomsColonnes)
    return lstColonnes, lstLargeurColonnes

def GetMatriceSaisie(db,lstColonnes):
    keyBox = ('ligne', "")
    matrice = xformat.DicOlvToMatrice(keyBox, {'lstColonnes': lstColonnes})
    for ligne in matrice[keyBox]:
        if ligne['name'] == 'magasin':
            ligne['genre'] = 'Combo'
            ligne['values'] = nust.SqlMagasins(db)
            ligne['value'] = ""
        if ligne['name'] == 'rayon':
            ligne['genre'] = 'Combo'
            ligne['values'] = nust.SqlRayons(db)
            ligne['value'] = ""
        if ligne['name'] == 'fournisseur':
            ligne['genre'] = 'Combo'
            ligne['values'] = nust.SqlFournisseurs(db)
            ligne['value'] = ""
        if ligne['genre'].lower() in ('str','combo'):
            ligne['ctrlAction'] = "ValideNbCar"
    return matrice

def GetMatriceRenameArt(matriceSaisie):
    keyBox = ('rename', "")
    matrice = {keyBox: [xformat.DeepCopy(matriceSaisie['ligne', ""][0]),
                        xformat.DeepCopy(matriceSaisie['ligne', ""][0])
                        ]}
    matrice[keyBox][1]['label'] = 'Nouveau nom'
    matrice[keyBox][1]['name'] = 'newID'
    matrice[keyBox][1]['txtSize'] = 100
    matrice[keyBox][0]['txtSize'] = 100
    return matrice

def GetDicOlv(db,cutend=None):
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
    lstColonnes, lstLargeurColonnes = GetOlvColonnes(table)
    matriceSaisie =  GetMatriceSaisie(db,lstColonnes)
    # Personnalisation
    lgSize = 150
    for lg in lstLargeurColonnes[:nbcol]: lgSize += max(lg,50)
    sizeSaisie = (500, max(len(lstColonnes) * 50, 400))
    return   {
                'lstColonnes': lstColonnes,
                'lstChamps':lstChamps,
                'getDonnees': nust.SqlArticles,
                'lstNomsBtns': ['creer','modifier','dupliquer'],
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
    IDarticle = None
    if  len(value)>0:
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

    if IDarticle:
        return IDarticle
    # article unique non trouvé, on lance la gestion des articles pour un choix filtré sur value
    cutend = len(DB_schema.DB_TABLES['stArticles'])-4
    # on affiche seulement trois premières colonnes
    dicOlv = GetDicOlv(db,cutend=cutend)
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
        db = kwds.pop('db',None)
        if db == None:
            import xpy.xUTILS_DB as xdb
            db = xdb.DB()
        value = kwds.pop('value',None)
        dicOlv = kwds.pop('dicOlv',None)
        if not dicOlv:
            dicOlv = GetDicOlv(db,cutend=2)
            dicOlv['dicBandeau']['titre'] = TITRE
            dicOlv['dicBandeau']['texte'] = INTRO

        kwds['dicOlv'] = dicOlv
        kwds['db'] = db

        super().__init__(None, **kwds)
        self.pnlOlv.estAdmin = True # force la gestion possible
        self.db = db
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        # personnalisation du bouton dupliquer
        if hasattr(self.pnlOlv,'lstBtnCtrl'):
            self.pnlOlv.lstBtnCtrl[2][0].SetToolTip("Changer le nom de l'article sélectionné ")
        if  isinstance(value,str):
            self.pnlOlv.ctrlOutils.barreRecherche.SetValue(value)
        # enlève le filtre si pas de réponse
        if len(self.ctrlOlv.innerList) == 0:
            self.pnlOlv.ctrlOutils.barreRecherche.SetValue('')
        self.pnlOlv.ctrlOutils.barreRecherche.OnSearch(None)
        self.ctrlOlv.SetFocus()
        if len(self.ctrlOlv.innerList) > 0:
            self.ctrlOlv.SelectObject(0)
            self.ctrlOlv.Refresh()

    def OnDupliquer(self,event):
        olv = self.ctrlOlv
        if olv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas d'article pointé !" ,
                          'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        matriceSaisie = xformat.DeepCopy(GetMatriceSaisie(self.db,self.dicOlv['lstColonnes']))
        matriceRename = xformat.DeepCopy(GetMatriceRenameArt(matriceSaisie))

        self.dicOlv['matriceSaisie'] = matriceRename

        ligne = olv.GetSelectedObject()
        ixLigne = olv.modelObjects.index(ligne)
        dDonnees = xformat.TrackToDdonnees(ligne,olv)
        self.dicOlv['mode'] = 'modif'
        dlgSaisie = xgtr.DLG_saisie(self.lanceur,self.dicOlv,kwValideSaisie=self.dicOlv)
        dlgSaisie.pnl.SetValues(dDonnees,)
        ret = dlgSaisie.ShowModal()
        if ret == wx.OK:
            ctrlNewID = dlgSaisie.GetPnlCtrl('newID',)
            newID = ctrlNewID.GetValue()
            nust.RenameArticle(self.db,self,ligne.IDarticle,newID)
            olv.MAJ()
        olv.Select(ixLigne)
        self.dicOlv['matriceSaisie'] = matriceSaisie

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
            lstArticles = nust.SqlOneArticle(self.db,IDarticle, flou = False)
            if len(lstArticles) > 0:
                mess += "\n- L'article '%s' est déjà présent, passez en modification\n" % IDarticle
        for champ in ('IDarticle','magasin','newID'):
            if not champ in dDonnees: continue
            if not (dDonnees[champ]) or len(dDonnees[champ]) == 0:
                    mess += "\n- La saisie de '%s' est obligatoire\n"%champ
        for champ in ('txTva','prixMoyen'):
            if not champ in dDonnees: continue
            if not(dDonnees[champ]) or float(dDonnees[champ]) == 0.0:
                mess += "\n- La saisie de '%s' est obligatoire\n"%champ
        if len(mess) != lg:
            wx.MessageBox(mess, "Entrée refusée!!!", style=wx.ICON_HAND)
            return wx.NO

        # formatage
        for champ in ('IDarticle','fournisseur','newID'):
            if not champ in dDonnees: continue
            if (dDonnees[champ]): dDonnees[champ] = dDonnees[champ].upper()
        for champ in ('magasin','rayon'):
            if not champ in dDonnees: continue
            if (dDonnees[champ]): dDonnees[champ] = dDonnees[champ].capitalize()
        return wx.OK

    def ValideNbCar(self,evt):
        value = evt.EventObject.GetValue()
        if len(value) > 32:
            wx.MessageBox("La longeur est limitée à 32 caratères\n\nvous en avez saisi %d"%len(value),"Saisie tronquée!")
            value = value[:32]
        if evt.EventObject.name in ['IDarticle','fournisseur','newID']:
            value = value.upper()
        if evt.EventObject.name in ['magasin','rayon']:
            value = value.capitalize()
        value = xformat.NoPunctuation(value,punct="\".:;?#%\\^`{|}~'").strip()
        evt.EventObject.SetValue(value)
        evt.Skip()

# Pour tests ------------------------------------------------------------
if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
    dlg = DLG_articles()
    ret = dlg.ShowModal()
    print(ret)