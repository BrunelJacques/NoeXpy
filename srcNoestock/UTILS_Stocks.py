#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des stocks et prix de journée
# Usage : Ensemble de fonctions acompagnant les DLG
# Auteur:          Jacques BRUNEL 2020-04 Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import xpy.xGestion_TableauRecherche as xgtr
from srcNoelite     import DB_schema
from xpy.outils     import xformat

LIMITSQL =100

def ValideParams(pnl):
    pnlOrigine = pnl.GetPnlCtrl('origine', codebox='param1')
    origine = pnlOrigine.GetValue()
    pnlFournisseur = pnl.GetPnlCtrl('fournisseur', codebox='param2')
    fournisseur = pnlFournisseur.GetValue()
    pnlAnalytique = pnl.GetPnlCtrl('analytique', codebox='param2')
    analytique = pnlAnalytique.GetValue()

    if origine[:5] == 'achat':
        if (not fournisseur) or (len(fournisseur) == 0):
            wx.MessageBox("Veuillez saisir un fournisseur!")
            pnlFournisseur.SetFocus()
    elif origine[:5] == 'retou':
        if (not analytique) or (len(analytique) == 0):
            wx.MessageBox("Veuillez saisir un camp pour le retour de marchandise!")

def GetMatriceArticles(cutend=None):
    dicBandeau = {'titre':"Recherche d'un article",
                  'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

    # Composition de la matrice de l'OLV articles, retourne un dictionnaire
    if cutend:
        table = DB_schema.DB_TABLES['stArticles'][:-cutend]
    else:
        table = DB_schema.DB_TABLES['stArticles']
    lstChamps = xformat.GetLstChamps(table)
    lstTypes = xformat.GetLstTypes(table)
    lstNomsColonnes = xformat.GetLstNomsColonnes(table)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes,IDcache=False)
    lstColonnes = xformat.GetLstColonnes(table=table,lstLargeur=lstLargeurColonnes,lstNoms=lstNomsColonnes)
    matriceSaisie =  xformat.DicOlvToMatrice(('ligne',""),{'lstColonnes':lstColonnes})
    lgSize = 60
    for lg in lstLargeurColonnes: lgSize += lg
    sizeSaisie = (200, max(len(lstColonnes) * 50, 400))
    return   {
                'lstColonnes': lstColonnes,
                'lstChamps':lstChamps,
                'getDonnees': GetArticles,
                'size':(lgSize,400),
                'sizeSaisie': sizeSaisie,
                'matriceSaisie': matriceSaisie,
                'dicBandeau': dicBandeau,
                'sortColumnIndex': 0,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetArticles(**kwd):
    db = kwd.get('db',None)
    # appel des données à afficher
    filtreTxt = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)
    dicOlv = kwd.pop('dicOlv',{})
    lstChamps = dicOlv['lstChamps']
    lstColonnes = dicOlv['lstColonnes']
    lstCodesColonnes = [x.valueGetter for x in dicOlv['lstColonnes']]

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" %LIMITSQL

    # intégration du filtre recherche via le where dans tous les champs
    where = ''
    if filtreTxt and len(filtreTxt) >0:
            where = xformat.ComposeWhereFiltre(filtreTxt,lstChamps, lstColonnes = lstColonnes,lien='WHERE')

    req = """FLUSH TABLES stArticles;"""
    retour = db.ExecuterReq(req, mess="UTILS_Stocks.GetArticles Flush")

    req = """   SELECT %s 
                FROM stArticles 
                %s
                %s ;""" % (",".join(lstChamps),where,limit)

    retour = db.ExecuterReq(req, mess="UTILS_Stocks.GetArticles Select" )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    # composition des données du tableau à partir du recordset, regroupement par article
    dicArticles = {}

    ixID = lstCodesColonnes.index('IDarticle')
    for record in recordset:
        if not record[ixID] in dicArticles.keys():
            dicArticles[record[ixID]] = {}
            for ix in range(len(lstCodesColonnes)):
                dicArticles[record[ixID]][lstCodesColonnes[ix]] = record[ix]
    lstDonnees = []
    for key, dic in dicArticles.items():
        ligne = []
        for code in lstCodesColonnes:
            ligne.append(dic[code])
        lstDonnees.append(ligne)
    return lstDonnees

def GetArticle(db,value,**kwds):
    # lanceur de la gestion des articles pour un choix filtré sur value
    cutend = kwds.pop('cutend',6)
    dicOlv = GetMatriceArticles(cutend=cutend)
    dlg = DLG_articles(db=db,value=value,dicOlv=dicOlv)
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
        track = dlg.GetSelection()
        IDarticle = dlg.GetSelection().IDarticle
    else: IDarticle = None
    dlg.Destroy()
    return IDarticle

def CalculeLigne(dlg,track):
    try: qte = float(track.qte)
    except: qte = 0.0
    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0
    try: txTva = track.dicArticle['txTva']
    except: txTva = 0.0
    if dlg.ht_ttc == 'HT':
        mttHT = qte * pxUn
        mttTTC = round(mttHT * (1 + (txTva * 100)),2)
        prixTTC = round(pxUn * (1 + (txTva * 100)),6)
    elif dlg.ht_ttc == 'TTC':
        mttTTC = qte * pxUn
        mttHT = round(mttTTC / (1 + (txTva * 100)),2)
        prixTTC = pxUn
    else: raise("Taux de tva non renseigné")
    track.mttHT = mttHT
    track.mttTTC = mttTTC
    track.prixTTC = prixTTC

def ValideLigne(db,track):
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"

    # IDmouvement manquant
    if track.IDmouvement in (None,0) :
        track.messageRefus += "L'IDmouvement n'a pas été déterminé\n"

    # article manquant
    if track.IDarticle in (None,0) :
        track.messageRefus += "L'article n'est pas saisi\n"

    # qte null
    try:
        track.qte = float(track.qte)
    except:
        track.qte = None
    if not track.qte or track.qte == 0.0:
        track.messageRefus += "Le qte est à zéro\n"

    # pxUn null
    try:
        track.pxUn = float(track.pxUn)
    except:
        track.pxUn = None
    if not track.pxUn or track.pxUn == 0.0:
        track.messageRefus += "Le pxUn est à zéro\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.valide = False
    else: track.messageRefus = ""
    return

def SauveLigne(db,dlg,track):
    # --- Sauvegarde des différents éléments associés à la ligne ---
    if not track.valide:
        return False

    lstDonnees = [  ('date',track.date),
                    ('fournisseur',dlg.fournisseur),
                    ('origine',dlg.ordi),
                    ('IDarticle', track.IDarticle),
                    ('qte', track.qte),
                    ('prixUnit', track.prixTTC),
                    ('analytique', dlg.analytique),
                    ('ordi', dlg.ordi),
                    ('dateSaisie', dlg.today),
                    ('modifiable', 1),]

    try: IDmouvement = int(track.IDmouvement)
    except: IDmouvement = None

    if IDmouvement :
        ret = db.ReqMAJ("mouvements", lstDonnees, "IDmouvement", IDmouvement,mess="UTILS_Stocks.SauveLigne Modif: %d"%IDmouvement)
    else:
        ret = db.ReqInsert("mouvements",lstDonnees= lstDonnees, mess="UTILS_Stocks.SauveLigne Insert")
        if ret == 'ok':
            track.IDmouvement = db.newID
    
def DeleteLigne(db,track):
    # --- Supprime les différents éléments associés à la ligne ---
    if not track.IDreglement in (0, ''):
        ret = db.ReqDEL("stMouvements", "IDmouvement", track.IDmouvement,affichError=True)
    return
    
def GetFournisseurs(db=None,**kwd):
    # appel des noms de fournisseurs déjà utilisés par le passé
    req = """   
            SELECT stMouvements.fournisseur
            FROM stMouvements
            GROUP BY stMouvements.fournisseur
            ORDER BY stMouvements.fournisseur;
            """
    lstDonnees = []
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetFournisseurs')
    if retour == "ok":
        recordset = db.ResultatReq()
        lstDonnees = [list(x) for x in recordset]
    for nom in ('Boulanger','NoName'):
        if not nom in lstDonnees:
            lstDonnees.append(nom)
    return lstDonnees

def GetAnalytiques(db,axe="%%"):
    # appel des items Analytiques de l'axe précisé
    req = """   
            SELECT cpta_analytiques.IDanalytique, cpta_analytiques.abrege, cpta_analytiques.nom
            FROM cpta_analytiques
            WHERE (((cpta_analytiques.axe) Like '%s'))
            GROUP BY cpta_analytiques.IDanalytique, cpta_analytiques.abrege, cpta_analytiques.nom
            ORDER BY cpta_analytiques.abrege;
            """%axe
    lstDonnees = []
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetFournisseurs')
    if retour == "ok":
        recordset = db.ResultatReq()
        lstDonnees = [list(x) for x in recordset]
    return lstDonnees

class DLG_articles(xgtr.DLG_gestion):
    # gestion des articles via tableau de recherche
    def __init__(self,*args,**kwds):
        db = kwds.pop('db',None)
        value = kwds.pop('value',None)
        super().__init__(None, **kwds)
        self.db = db
        dicOlv = kwds.get('dicOlv',None)
        self.dicOlvTbl = xformat.CopyDic(dicOlv)


        if  isinstance(value,str):
            self.pnl.ctrlOutils.barreRecherche.SetValue(value)
        # enlève le filtre si pas de réponse
        if len(self.ctrlOlv.innerList) == 0:
            self.pnl.ctrlOutils.barreRecherche.SetValue('')

    def FmtDonneesDB(self,nomsCol,donnees,complete = True):
        table = DB_schema.DB_TABLES['stArticles']
        lstNomsColonnes = xformat.GetLstNomsColonnes(table)
        lstChamps = xformat.GetLstChamps(table)
        lstDonnees = []
        # alimente les données saisies
        for col in nomsCol:
            lstDonnees.append((lstChamps[lstNomsColonnes.index(col)],donnees[nomsCol.index(col)]))
        if len(donnees) < len(lstNomsColonnes) and complete:
            # tous les champs n'ont pas été saisis, complementation avec des valeurs par défaut
            altDonnees = []
            lstTypes = xformat.GetLstTypes(table)
            lstValDef = xformat.ValeursDefaut(lstNomsColonnes,lstTypes)
            champsNonSaisis = [ lstChamps[lstNomsColonnes.index(x)] for x in lstNomsColonnes if x not in nomsCol]
            for champ in champsNonSaisis:
                lstDonnees.append((champ,lstValDef[lstChamps.index(champ)]))
        return lstDonnees

    def GereDonnees(self, mode=None, nomsCol=[], donnees=[], ixligne=0):
        # à vocation a être substitué par des accès base de données
        if mode == 'ajout':
            self.donnees = self.donnees[:ixligne] + [donnees, ] + self.donnees[ixligne:]
            lstDonnees = self.FmtDonneesDB(nomsCol,donnees,complete=True)
            mess="DLG_articles.GereDonnees Ajout"
            self.db.ReqInsert('stArticles',lstDonnees=lstDonnees,mess=mess)

        elif mode == 'modif':
            self.donnees[ixligne] = donnees
            lstDonnees = self.FmtDonneesDB(nomsCol,donnees,complete=False)
            mess="DLG_articles.GereDonnees Modif"
            self.db.ReqMAJ('stArticles',lstDonnees[:-1],nomChampID=lstDonnees[0][0],ID=lstDonnees[0][1],mess=mess)

        elif mode == 'suppr':
            del self.donnees[ixligne]
            mess="DLG_articles.GereDonnees Suppr"
            self.db.ReqDel()

if __name__ == '__main__':
    import os
    os.chdir("..")
    from xpy import xUTILS_DB as xdb
    app = wx.App(0)
    ret = GetArticle(xdb.DB(),'',cutend=6)