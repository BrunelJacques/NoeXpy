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
    lblOrigine = pnlOrigine.GetValue()
    pnlFournisseur = pnl.GetPnlCtrl('fournisseur', codebox='param2')
    fournisseur = pnlFournisseur.GetValue()
    pnlAnalytique = pnl.GetPnlCtrl('analytique', codebox='param2')
    analytique = pnlAnalytique.GetValue()

    if 'achat' in lblOrigine:
        if (not fournisseur) or (len(fournisseur) == 0):
            wx.MessageBox("Veuillez saisir un fournisseur!")
            pnlFournisseur.SetFocus()
    elif 'retour' in lblOrigine:
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
    lstChamps = xformat.GetLstChamps(DB_schema.DB_TABLES[table])
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

def GetDonneesEntrees(dlg, dParams):
    # retourne la liste des données de l'OLv de DlgEntree
    ctrlOlv = dlg.ctrlOlv
    # appel des données des mouvements selon les params
    ldMouvements = GetLdMouvements(dlg.db,dParams)
    # appel des dicArticles des mouvements
    ddArticles = {}
    for dMvt in ldMouvements:
        ddArticles[dMvt['IDarticle']] = GetDicArticle(dlg.db,dMvt['IDarticle'])

    # composition des données
    lstDonnees = []
    lstCodesCol = ctrlOlv.GetLstCodesColonnes()
    lstCodesSup = dlg.dicOlv['lstCodesSup']

    # autant de lignes dans l'olv que de mouvements remontés
    for dMvt in ldMouvements:
        donnees = []
        dArticle = ddArticles[dMvt['IDarticle']]
        # alimente les premières données des colonnes
        for code in lstCodesCol:
            # présence de la donnée dans le mouvement
            if code in dMvt.keys():
                donnees.append(dMvt[code])
                continue
            # présence dans l'article associé
            if code in dArticle.keys():
                donnees.append(dArticle)
                continue
            if code in ('pxUn','mttHT','mttTTC','nbRations'):
                convTva = (1+(dArticle['txTva'] / 100))
                if code == 'pxUn':
                    if dlg.ht_ttc == 'HT':
                        donnees.append(round( dMvt['prixUnit'] / convTva,6))
                    else:
                        donnees.append(dMvt['prixUnit'])
                elif code == 'mttHT':
                    donnees.append(round(dMvt['prixUnit'] * dMvt['qte'] / convTva ,2))
                elif code == 'mttTTC':
                    donnees.append(dMvt['prixUnit'] * dMvt['qte'])
                elif code == 'nbRations':
                    donnees.append(dArticle['rations'] * dMvt['qte'])
                else:
                    raise("code: %s Erreur de programmation en UTILS_Stocks.GetDonneesEntrees"%code)
                continue

        # alimeente les codes supplémentaires 'prixTTC','IDmouvement','dicArticle'
        donnees += [dMvt['prixUnit'],
                    dMvt['IDmouvement'],
                    dArticle]
        lstDonnees.append(donnees)
    return lstDonnees

def GetLdMouvements(db,dParams=None):
    lstChamps = xformat.GetLstChamps(DB_schema.DB_TABLES['stMouvements'])
    # Appelle les mouvements associés à un dic de choix de param et retour d'une liste de dic
    req = """   SELECT %s
                FROM stMouvements 
                WHERE ((date = '%s' )
                        AND (origine = '%s' )
                        AND (fournisseur = '%s' )
                        AND (analytique = '%s' ))
                ;""" % (",".join(lstChamps),dParams['date'],dParams['origine'],dParams['fournisseur'],dParams['analytique'])
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetMouvements')
    ldMouvements = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            dMouvement = {}
            for ix  in range(len(lstChamps)):
                dMouvement[lstChamps[ix]] = record[ix]
            ldMouvements.append(dMouvement)            
    return ldMouvements

def GetArticles(**kwd):
    db = kwd.get('db',None)
    # appel des données d'un olv
    filtreTxt = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)
    dicOlv = kwd.pop('dicOlv',{})
    lstChamps = dicOlv['lstChamps']
    lstColonnes = dicOlv['lstColonnes']

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
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
    lstDonnees = []
    for record in recordset:
        ligne = []
        for val in record:
            ligne.append(val)
        lstDonnees.append(ligne)
    return lstDonnees

def GetArticle(db,value,**kwds):
    # test de présence de l'article
    if len(value)>0:
        req = """   SELECT IDarticle
                    FROM stArticles
                    WHERE IDarticle LIKE '%%%s%%'
                    ;""" % (value)
        retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetArticle req1')
        if retour == "ok":
            recordset = db.ResultatReq()
            if len(recordset) == 1:
                return recordset[0][0]

    # article non trouvé, on lance la gestion des articles pour un choix filtré sur value
    cutend = kwds.pop('cutend',6)
    dicOlv = GetMatriceArticles(cutend=cutend)
    dlg = DLG_articles(db=db,value=value,dicOlv=dicOlv)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        IDarticle = dlg.GetSelection().IDarticle
    else: IDarticle = None
    dlg.Destroy()
    return IDarticle

def GetDicArticle(db,value):
    # retourne les valeurs de l'article sous forme de dict
    dicArticle = {}
    if len(value)>0:
        table = DB_schema.DB_TABLES['stArticles']
        lstChamps = xformat.GetLstChamps(table)
        lstNomsColonnes = xformat.GetLstNomsColonnes(table)
        req = """   SELECT %s
                        FROM stArticles
                        WHERE IDarticle LIKE '%%%s%%'
                        ;""" % (','.join(lstChamps),value)
        retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetArticle req1')
        if retour == "ok":
            recordset = db.ResultatReq()
            if len(recordset) > 0:
                for key in  lstNomsColonnes:
                    valeur = recordset[0][lstNomsColonnes.index(key)]
                    dicArticle[key] = valeur
    return dicArticle

def CalculeLigne(dlg,track):
    try: qte = float(track.qte)
    except: qte = 0.0
    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0
    try: txTva = track.dicArticle['txTva']
    except: txTva = 0.0
    try: rations = track.dicArticle['rations']
    except: rations = 1
    if dlg.ht_ttc == 'HT':
        mttHT = qte * pxUn
        mttTTC = round(mttHT * (1 + (txTva / 100)),2)
        prixTTC = round(pxUn * (1 + (txTva / 100)),6)
    elif dlg.ht_ttc == 'TTC':
        mttTTC = qte * pxUn
        mttHT = round(mttTTC / (1 + (txTva / 100)),2)
        prixTTC = pxUn
    else: raise("Taux de tva non renseigné")
    track.mttHT = mttHT
    track.mttTTC = mttTTC
    track.prixTTC = prixTTC
    track.nbRations = track.qte * rations

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

    lstDonnees = [  ('date',dlg.date),
                    ('fournisseur',dlg.fournisseur),
                    ('origine',dlg.origine),
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
        ret = db.ReqMAJ("stMouvements", lstDonnees, "IDmouvement", IDmouvement,mess="UTILS_Stocks.SauveLigne Modif: %d"%IDmouvement)
    else:
        ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="UTILS_Stocks.SauveLigne Insert")
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
        lstDonnees = [x[0] for x in recordset]
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

class Anterieur(object):
    def __init__(self,db, origines=['achat',]):
        self.origines = origines
        self.db = db

    def GetMatriceAnterieurs(self):
        dicBandeau = {'titre': "Rappel d'un anterieur existant",
                      'texte': "les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                      'hauteur': 15, 'nomImage': "xpy/Images/32x32/Zoom_plus.png"}

        # Composition de la matrice de l'OLV anterieurs, retourne un dictionnaire

        lstChamps = ['origine', 'date', 'fournisseur', 'analytique', 'COUNT(IDmouvement)']

        lstNomsColonnes = ['origine', 'date', 'fournisseur', 'analytique', 'nbLignes']

        lstTypes = ['VARCHAR(8)', 'DATE', 'VARCHAR(32)', 'VARCHAR(32)', 'INT']
        lstCodesColonnes = [xformat.SupprimeAccents(x).lower() for x in lstNomsColonnes]
        lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
        lstLargeurColonnes = [100,100,180,180,200]
        lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return {
            'lstColonnes': lstColonnes,
            'lstChamps': lstChamps,
            'listeNomsColonnes': lstNomsColonnes,
            'listeCodesColonnes': lstCodesColonnes,
            'getDonnees': self.GetAnterieurs,
            'dicBandeau': dicBandeau,
            'sortColumnIndex': 2,
            'sensTri': False,
            'style': wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
            'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
            'size': (650, 400)}

    def GetAnterieurs(self,db=None, dicOlv={}, **kwd):
        # ajoute les données à la matrice pour la recherche d'un anterieur
        filtre = kwd.pop('filtreTxt', '')
        nbreFiltres = kwd.pop('nbreFiltres', 0)

        # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
        # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
        limit = ''
        if nbreFiltres == 0:
            limit = """
                    LIMIT %d""" % LIMITSQL

        where = """                    WHERE origine in ( %s ) """ % str(self.origines)[1:-1]
        if filtre:
            where += """
                    AND (date LIKE '%%%s%%'
                            OR fournisseur LIKE '%%%s%%'
                            OR analystique LIKE '%%%s%% )'""" % (filtre, filtre, filtre,)

        lstChamps = dicOlv['lstChamps']

        req = """   SELECT %s
                    FROM stMouvements
                    %s 
                    GROUP BY origine, date, fournisseur, analytique
                    ORDER BY date DESC
                    %s ;""" % (",".join(lstChamps), where, limit)
        retour = db.ExecuterReq(req, mess='GetAnterieurs')
        lstDonnees = []
        if retour == 'ok':
            recordset = db.ResultatReq()
            for record in recordset:
                lstDonnees.append([x for x in record])
        return lstDonnees

    def GetDic(self,db=None):
        # lancement de l'appel des mouvements antérieurs existants pour reprise
        dicAnterieur = {}
        dicOlv = self.GetMatriceAnterieurs()
        dlg = xgtr.DLG_tableau(None, dicOlv=dicOlv, db=db)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            donnees = dlg.GetSelection().donnees
            for ix in range(len(donnees)):
                dicAnterieur[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dlg.Destroy()
        return dicAnterieur

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
        lstChamps = xformat.GetLstChamps(DB_schema.DB_TABLES[table])
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
            ret = self.db.ReqMAJ('stArticles',lstDonnees,nomChampID=lstDonnees[0][0],ID=lstDonnees[0][1],mess=mess)
            if ret != 'ok':
                pass

        elif mode == 'suppr':
            del self.donnees[ixligne]
            mess="DLG_articles.GereDonnees Suppr"
            self.db.ReqDel()

if __name__ == '__main__':
    import os
    os.chdir("..")
    from xpy import xUTILS_DB as xdb
    app = wx.App(0)
    obj = Anterieur(xdb.DB)
    ret = obj.GetDic()
    print(ret)