#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    NoeLITE, gestion des stocks et prix de journée
# Usage : Ensemble de fonctions acompagnant les DLG
# Auteur:          Jacques BRUNEL 2021-01 Matthania
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx, decimal, datetime
from srcNoelite     import DB_schema
from xpy.outils     import xformat
from xpy.outils.xformat import Nz,DateSqlToDatetime
from xpy  import xUTILS_DB as xdb

LIMITSQL = 1000
# codes repas [ 1,      2,     3,     4       5]
CHOIX_REPAS = ['PtDej','Midi','Soir','5eme','Tous']

class SetAttrDicToTrack:
    #  Pour créer les attributs de tracks par un dict de données
    def __init__(self,codesTrack,codesDic, dicDon):
        for ix in range(len(codesTrack)):
            self.__setattr__(codesTrack[ix],dicDon[codesDic[ix]])

# Nouvelle Gestion des inventaires --------------------------------------------

def InsertInventaire(dlg):
    lstTracks = dlg.ctrlOlv.GetObjects()
    lstFields = [
        'IDdate', 'IDarticle', 'qteStock','qteConstat', 'prixMoyen','prixActuel',
        'ordi','dateSaisie','modifiable']
    today = str(datetime.date.today())

    # Compose les données à intégrer dans la table inventaires
    llDonnees = []
    for track in lstTracks:
        llDonnees.append([
            str(dlg.date),track.IDarticle,track.qteStock,0,track.pxUn,track.prixActuel,
            dlg.ordi,today,0])

    # Ecriture dans la base de donnée
    mess = "UTILS_Stocks.PostInventaire"
    ret = dlg.db.ReqInsert('stInventaires', lstFields,llDonnees,mess=mess)
    if ret == 'ok':
        mess = "Archivage terminé avec succés au %s"% llDonnees[0][0]
        wx.MessageBox(mess,"succés")

def GetDateLastInventaire(db,dteAnalyse=None):
    # return: date du dernier inventaire précédant la date d'analyse
    whereDate = ""
    if dteAnalyse:
        dteIso = xformat.DatetimeToStr(dteAnalyse, iso=True)
        whereDate = "WHERE stInventaires.IDdate <= '%s' " % dteIso
    req = """   
            SELECT MAX(IDdate)
            FROM stInventaires
            %s
            GROUP BY IDdate    
            ;""" % (whereDate)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetDateLastInventaire')
    dteLast = '2000-01-01'
    if retour == 'ok':
        recordset = db.ResultatReq()
        if len(recordset) > 0:
            dteLast = recordset[-1][0]
    return DateSqlToDatetime(dteLast)

def GetLastInventaire(dteAnalyse=None,lstChamps=None,oneArticle=None):
    # return: lignes de l'inventaire précédant dteAnalyse ou seulement une ligne article
    db = xdb.DB()
    if not lstChamps:
        lstChamps = ['IDdate','IDarticle','qteStock','prixMoyen','IDmouvement']
    lstChampsSql = []
    for champ in lstChamps:
        lchampSplit = champ.split('.')
        if len(lchampSplit) == 1:
            if champ.lower() == 'idarticle':
                lstChampsSql.append('stArticles.IDarticle')
            elif 'IDmouvement' in champ:
                lstChampsSql.append('0')
            else:
                lstChampsSql.append('stInventaires.%s'%lchampSplit[-1])
        else:
            lstChampsSql.append(champ)
    condArticle = ""
    if oneArticle:
        condArticle = "AND (stArticles.IDarticle = '%s')" % oneArticle
    whereDate = "1"
    dteIso = xformat.DatetimeToStr(dteAnalyse, iso=True)
    if dteIso and len(dteIso)>0:
        whereDate = "stInv.IDdate <= '%s' " % dteIso

    req = """   
        SELECT %s
        FROM stArticles 
        LEFT JOIN stInventaires ON stArticles.IDarticle = stInventaires.IDarticle
        WHERE   (   (stInventaires.IDdate = 
                        (   SELECT MAX(stInv.IDdate) 
                            FROM stInventaires as stInv
                            WHERE (%s)
                        )
                    )
                    OR (stInventaires.IDdate IS NULL)
                )
                %s;""" % (",".join(lstChampsSql),whereDate,condArticle)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetLastInventaire')
    llInventaire = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            mouvement = []
            for ix  in range(len(lstChamps)):
                value = record[ix]
                if value == None:
                    if lstChamps[ix][:3] in ('qte', 'pxU', 'pri'):
                        value = 0.0
                    else:
                        value = ''
                mouvement.append(value)
            # ajout d'un ID mouvement virtuel
            mouvement.append(0)
            llInventaire.append(mouvement)
    db.Close()
    return llInventaire

def GetLastInventForMvts(dlg, dParams):
    # retourne ld de pseudos mouvements pour enrichir  des lignes 'reprise à Nouveau'
    oneArticle = None
    lstChampsInvent = ['IDdate','IDarticle','qteStock','prixMoyen','dateSaisie','ordi','IDmouvement']
    champsTransposes = ['date','IDarticle','qte','prixUnit','dateSaisie','ordi','IDmouvement']
    if 'lstChamps' in dParams:
        lstChampsMvt = dParams['lstChamps']

    else:
        lstChampsMvt = champsTransposes

    if dParams['article'] and len(dParams['article']) > 0:
        oneArticle = dParams['article']
    if oneArticle.lower() == "tous":
        oneArticle = None
    kwd = {'dteAnalyse': dParams['anteDate'],
           'lstChamps': lstChampsInvent,
           'oneArticle': oneArticle}
    llInventaire = GetLastInventaire(**kwd)
    ldMouvements = []
    for ligne in llInventaire:
        dicMvt = {}
        for champ  in lstChampsMvt:
            if '.' in champ:
                champ = champ.split('.')[1]
            valeur = None
            # les champs renseignés seront ceux présents dans stInventaires ou composés
            if champ in champsTransposes:
                valeur = ligne[champsTransposes.index(champ)]
            elif champ == 'origine':  valeur = 'inventaire'
            elif champ == 'IDmouvement':  valeur = 0
            elif champ == 'IDanalytique':  valeur = '00'
            elif champ == 'modifiable':  valeur = 0
            dicMvt[champ] = valeur
        ldMouvements.append(dicMvt)
    return ldMouvements

def GetMvtsPeriode(debut=None, fin=None):
    # retourne une  liste de mouvements en forme de liste
    lstChamps = ['date','origine','stMouvements.IDarticle','qte','prixUnit','IDmouvement']
    if fin == None: fin = datetime.date.today()
    if debut == None: debut = fin - datetime.timedelta(days=180)
    finIso = xformat.DatetimeToStr(fin,iso=True)
    debutIso = xformat.DatetimeToStr(debut,iso=True)
    db = xdb.DB()
    # Appelle les mouvements de la période
    req = """   SELECT %s
                FROM stMouvements
                WHERE   (   (date > '%s' ) 
                            AND (date <= '%s' ))
                ;""" % (",".join(lstChamps),debutIso,finIso)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetMvtsPeriode')
    llMouvements = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            mouvement = []
            for ix  in range(len(lstChamps)):
                mouvement.append(record[ix])
            llMouvements.append(mouvement)
    db.Close()
    return llMouvements

def GetDateLastMvt(db):
    # retourne la date de la dernière écriture de mouvement
    req = """    
        SELECT MAX(date)
        FROM stMouvements
        ;"""
    mess = "Echec UTILS_Stocks.GetLastMouvement"
    ret = db.ExecuterReq(req, mess=mess, affichError=True)
    if ret != 'ok':
        return str(datetime.date.today())
    recordset = db.ResultatReq()
    return recordset[0][0]

def PxAchatsStock(modelObjects):
    # retourne px moyens achetés du stock restant dans modelObjects: méthode FIFO
    lstArticles = []
    dQtesFin = {}
    # calcul des quantités en stock, crée liste articles présents, attribution d'index
    for track in modelObjects:
        if track.IDarticle not in lstArticles:
            lstArticles.append(track.IDarticle)
            dQtesFin[track.IDarticle] = 0
        dQtesFin[track.IDarticle] += Nz(track.qte)

        if isinstance(track.date,str):
                track.date = xformat.DateSqlToDatetime(track.date)
        if not track.date:
                track.date = datetime.date(2000,1,1)

    lastArticle = None
    qteAchatsTous = 0.0
    mttAchatsTous = 0.0
    finiPourArticle = False
    qteAchatsArt = 0.0
    mttAchatsArt = 0.0

    # recherche des prix d'achat sur liste triée dates décroissantes après articles
    fnSort = lambda trk: (trk.IDarticle,trk.date,trk.IDmouvement)
    for track in sorted(modelObjects, key=fnSort,reverse=True):
        article = track.IDarticle
        if not lastArticle:
            # seulement pour le premier item pas de rupture article à faire
            lastArticle = article
        if track.origine not in ('achat','inventaire'):
            # on ne s'occupe que des achats pour le prix moyen d'achat du stock fin
            continue
        # rupture article,
        if lastArticle != article:
            finiPourArticle = False
            qteAchatsArt = 0.0
            mttAchatsArt = 0.0
        # purge des lignes non nécessaires
        if finiPourArticle:
            continue # jusqu'à changement article pour rupture
        # progression dans le suivi des achats
        qteAchat = Nz(track.qte)
        prixUnit = Nz(track.pxUn)
        qteAchat = min(dQtesFin[article],qteAchat)
        qteAchatsTous += qteAchat
        mttAchatsTous += qteAchat * prixUnit
        qteAchatsArt += qteAchat
        mttAchatsArt += qteAchat * prixUnit
        dQtesFin[article] -= qteAchat
        if dQtesFin[article] < 0.0001:
            # Les achats retenus couvrent le stock restant, on ignore l'antérieur
            finiPourArticle = True

    if Nz(qteAchatsTous) != 0:
        prixMoyen = round(mttAchatsTous / qteAchatsTous,4)
    else: prixMoyen = None
    return prixMoyen

def CalculeInventaire(dlg, dParams):
    # nouveau calcul
    db = dlg.db
    endDate = dParams['date']
    anteDate = GetDateLastInventaire(db,endDate)

    # écritures postérieures à la date d'analyse, pas de maj PU et qte de l'article
    majArticles = True
    if endDate < GetDateLastMvt(db):
        majArticles = False

    # complète les paramètres façon DLG_MvtOneArticle
    lstChampsMvts = ['IDarticle', 'date', 'qte', 'prixUnit','origine','IDmouvement']
    # appel des mouvements de la période
    dParams['lstChamps'] = lstChampsMvts
    dParams['article'] = 'tous'
    dParams['lstOrigines'] = ['tous',]
    dParams['anteDate'] = anteDate
    dParams['endDate'] = endDate

    # appel de l'inventaire précédent et des mouvements
    ldMouvements = [x for x in GetLastInventForMvts(db, dParams)]
    ldMouvements += [x for x in GetMvtsByArticles(db, dParams)]

    # fractionnement en dictionnaire par article de listes des mouvements
    dldArtMouvements = {}
    for dMvt in ldMouvements:
        if not dMvt['IDarticle'] in dldArtMouvements:
            dldArtMouvements[dMvt['IDarticle']] = []
        dldArtMouvements[dMvt['IDarticle']].append(dMvt)

    # appel du détail des articles présents dans les mouvements
    lstIDarticles = [x for x in dldArtMouvements]
    lstChampsArt = ['IDarticle','fournisseur', 'magasin', 'rayon','qteMini', 'qteSaison',
                    'qteStock','rations', 'prixMoyen','prixActuel', 'dernierAchat']
    where = ""
    if len(lstIDarticles) == 1:
        where = "IDarticle = '%s'" % lstIDarticles[0]
    elif len(lstIDarticles) > 0:
        where = "IDarticle in (%s)" % str(lstIDarticles)[1:-1]
    req = """
        SELECT  %s
        FROM  stArticles            
        WHERE %s
        ;""" % (','.join(lstChampsArt), where)
    retour = db.ExecuterReq(req, mess="UTILS_Stocks.CalculeInventaire articles")
    ddArticles = {}
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            ddArticles[record[0]] = {}
            for ix in range(len(lstChampsArt)):
                ddArticles[record[0]][lstChampsArt[ix]] = record[ix]

    # composition des données du tableau OLV --------------------------------------------
    lstCodes = dlg.dicOlv['lstCodes'] + dlg.dicOlv['lstCodesSup']
    codesDic = ['date','IDarticle','qte','prixUnit','origine','IDmouvement']
    codesTrack = ['date','IDarticle','qte','pxUn','origine','IDmouvement']
    lstDonnees = []
    ldMajArticles = []

    # Composition de la ligne olv sur un article selon les colonnes  ---------------------
    def ComposeLigne(dArt, ldMvts):
        dl = dParams["endDate"]
        # calcul le prix du stock sur derniers achats
        lstObjects = [SetAttrDicToTrack(codesTrack,codesDic,x) for x in ldMvts if x["date"] <= dl]
        pxAchatsStock = PxAchatsStock(lstObjects)

        # choix du prix unitaire retenu pour valoriser le stock, priorité FIFO
        pxUnArt = Nz(dArt['prixMoyen']) # c'est le prix dans l'article
        pxUn = Nz(dArt['prixActuel'])
        if pxUn == 0:
            pxUn = pxUnArt
        if pxAchatsStock:
            # est prioritaire et non null si présence d'achats
            pxUn = pxAchatsStock

        # regroupe les mouvements en une seule ligne
        qteMvts = 0.0
        mttMvts = 0.0
        lastBuy = datetime.date(2000,1,1)
        for track in lstObjects:
            qteMvts += track.qte
            mttMvts += (track.qte * track.pxUn)
            if track.date > lastBuy and track.origine == "achat":
                lastBuy = track.date
        deltaValoAchats= abs(mttMvts - (pxUn * qteMvts))

        # controle article
        if majArticles:
            pbQteArt = True
            if dArt['qteStock'] == qteMvts:
                pbQteArt = False
            elif Nz(dArt['qteStock']) != 0:
                if abs(1 - (qteMvts / dArt['qteStock'])) <= 0.02:
                    pbQteArt = False
            pbPxArt = True
            if dArt['prixMoyen'] == pxUn:
                pbPxArt = False
            elif Nz(dArt['prixMoyen']) != 0:
                if abs(1 - (pxUn / dArt['prixMoyen'])) <= 0.02:
                    pbPxArt = False
            if pbQteArt or pbPxArt:
                ldMajArticles.append({'ID': dArt['IDarticle'],
                                      'values':[qteMvts,pxUn]})

        donnees = [None, ] * len(lstCodes)
        # reprise des champs articles transposés en l'état (même nom)
        for code in lstCodes:
            if code in lstChampsArt:
                value = dArt[code]
                if isinstance(value, decimal.Decimal):
                    value = round(float(value),4)
                donnees[lstCodes.index(code)] = value

        # compléments des autres champs
        #'qteMvts','qteAchats','mttAchats','artRations'
        donnees[lstCodes.index('pxUn')] = pxUn
        donnees[lstCodes.index('mttTTC')] = round(qteMvts * pxUn,2)
        donnees[lstCodes.index('qteStock')] = qteMvts # peut faire l'objet de corrections
        donnees[lstCodes.index('qteMvts')] = qteMvts # reste fixe
        donnees[lstCodes.index('rations')] = qteMvts * Nz(dArt['rations'])
        donnees[lstCodes.index('artRations')] = Nz(dArt['rations'])
        donnees[lstCodes.index('deltaValo')] = deltaValoAchats

        if lastBuy != datetime.date(2000,1,1):
            donnees[lstCodes.index('lastBuy')] = lastBuy
            donnees[lstCodes.index('prixActuel')] = round(pxUnArt,4)
        else:
            donnees[lstCodes.index('lastBuy')] = None

        if dlg.saisonIx == 0:
            mini = Nz(dArt['qteMini'])
        elif dlg.saisonIx == 1:
            mini = Nz(dArt['qteSaison'])
        else:
            mini = 0
        donnees[lstCodes.index('qteMini')] = mini
        return donnees
    # fin de ComposeLigne --------------------------------------------------------------

    for key, donnees in ddArticles.items():
        lstDonnees.append(ComposeLigne(donnees, dldArtMouvements[key]))

    # mise à jour éventuelle du fichier articles
    if majArticles and len(ldMajArticles) > 0:
        mess = 'UTILS_Stocks.CalculeInventaire.MajArticles'
        lstChamps = ['qteStock','prixMoyen']
        for dMaj in ldMajArticles:
            lstValues = dMaj['values']
            db.ReqMAJ('stArticles',None,'IDarticle',dMaj['ID'],lstValues=lstValues,
                      lstChamps=lstChamps,IDestChaine=True,
                      mess = mess)
        # Force la mise à jour dans la base avant nouveau select évitant le cache
        del db.cursor
        db.cursor = db.connexion.cursor(buffered=False)

        req = """FLUSH  TABLES individus;"""
        ret = db.ExecuterReq(req, mess='SqlInventaires flush',affichError=True)
        if retour != "ok":
            return []
    return lstDonnees

# Select de données  ----------------------------------------------------------

def MouvementsPosterieurs(dlg):
    db = dlg.db
    # limitation à la date d'analyse, mais art.qte est l'ensemble des mouvements
    where = "WHERE (stMouvements.date > '%s') " % dlg.date

    req = """
        SELECT  Count(stMouvements.qte)        
        FROM stMouvements
        %s ;""" % (where)

    retour = db.ExecuterReq(req, mess="UTILS_Stocks.MouvementsPosterieurs Select" )
    if retour == "ok":
        recordset = db.ResultatReq()
        if recordset[0][0] > 0:
            return True
    return False

def GetMvtsByDate(db, dParams=None):
    if hasattr(db.connexion,'connection_id') and db.connexion.connection_id == None:
        wx.MessageBox('db closed!!','INFO programmation')
        return []
    # retourne l'ensemble des mouvements pour une date donnée et d'autres params
    lstChamps = xformat.GetLstChampsTable('stMouvements',DB_schema.DB_TABLES)
    lstChamps.append('stArticles.qteStock')
    lstChamps.append('stArticles.prixMoyen')
    andOrigine = "AND (stMouvements.origine in (%s) )"%str(dParams['lstOrigines'])[1:-1]
    if len(dParams['fournisseur'])>0:
        andFournisseur = "AND (stMouvements.fournisseur = '%s' )"%dParams['fournisseur']
    else: andFournisseur = """AND ((stMouvements.fournisseur = '') 
                    OR (stMouvements.fournisseur IS NULL))"""
    if len(dParams['analytique'])>0 and dParams['analytique'] != '00':
        andAnalytique = """AND (stMouvements.IDanalytique = '%s')""" % dParams['analytique']
    else:
        andAnalytique = """AND ((stMouvements.IDanalytique IS NULL)
                    OR (stMouvements.IDanalytique ='00'))"""
    andWhere = """%s
                %s
                %s"""%(andOrigine,andFournisseur,andAnalytique)
    # Appelle les mouvements associés à un dic de choix de param et retour d'une liste de dic
    req = """
            SELECT %s
            FROM stMouvements
            LEFT JOIN stArticles ON stMouvements.IDarticle = stArticles.IDarticle 
            WHERE ((date = '%s')
                %s);""" % (",".join(lstChamps),dParams['date'],andWhere)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetMouvements')
    ldMouvements = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            dMouvement = {}
            for ix  in range(len(lstChamps)):
                champ = lstChamps[ix].split('.')[1]
                # transposition du code repas en libellé
                if champ == 'repas' and record[ix]:
                    dMouvement[champ] = CHOIX_REPAS[record[ix]-1]
                # transposition du sens du nombre pour les quantités
                #elif champ == 'qte' and record[ix]:
                #    dMouvement[champ] = record[ix] * sensNum
                else:
                    dMouvement[champ] = record[ix]
            ldMouvements.append(dMouvement)
    return ldMouvements

def GetMvtsByArticles(db, dParams=None):
    # Retourne une liste de dictionnaires d'articles selon autres params
    if not 'lstChamps' in dParams:
        lstChamps = xformat.GetLstChampsTable('stMouvements',DB_schema.DB_TABLES)
    else:
        lstChamps = dParams['lstChamps']

    # composition des filtres
    article = dParams.get('article','')
    if article .lower() == 'tous' :
        condArticle = ""
    else:
        condArticle = "stMouvements.IDarticle = '%s'" % article

    lstOrigines = dParams.get('lstOrigines',['tous',])
    firstOrigine = lstOrigines[0]
    if firstOrigine == 'tous':
        condOrigine = ""
    else:
        condOrigine = "origine in (%s)" % str(lstOrigines)[1:-1]

    anteDate = dParams.get('anteDate',None)
    endDate = dParams.get('endDate',None)

    if not anteDate:
        condDate = ''
    else:
        condDate = "(date > '%s')" % anteDate

    if not endDate:
        condDate += ''
    else:
        if not condDate == '':
            condDate += " AND "
        condDate += "(date <= '%s')" % endDate

    where = "WHERE %s" % condDate
    lstCond = [condArticle,condOrigine,]
    where = xformat.AppendConditionWhere(where,lstCond)

    # Appelle les mouvements selon dic param et retour d'une liste de dic
    req = """   
                SELECT %s
                FROM stMouvements
                %s
                ;""" % (",".join(lstChamps),where)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetMvtsByArticles')
    ldMouvements = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            dMouvement = {}
            for ix  in range(len(lstChamps)):
                champ = lstChamps[ix]
                if '.' in champ:
                    champ = champ.split('.')[1]
                # transposition du code repas en libellé
                if champ == 'repas' and record[ix]:
                    dMouvement[champ] = CHOIX_REPAS[record[ix]-1]
                else:
                    dMouvement[champ] = record[ix]
            ldMouvements.append(dMouvement)
    return ldMouvements

def SqlArticles(**kwd):
    db = kwd.get('db',None)
    # appel des données d'un olv
    filtreTxt = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)
    dicOlv = kwd.pop('dicOlv',{})
    lstChamps = dicOlv['lstChamps']
    lstColonnes = dicOlv['lstColonnes']
    withObsoletes = dicOlv.get('withObsoletes',True)

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" %LIMITSQL

    # intégration du filtre recherche via le where dans tous les champs
    if withObsoletes:
        where = ''
        if filtreTxt and len(filtreTxt) > 0:
            where = xformat.ComposeWhereFiltre(filtreTxt, lstChamps, lstColonnes=lstColonnes, lien='WHERE')
    else:
        where = 'WHERE ((obsolete IS NULL) OR (obsolete = 0))'
        if filtreTxt and len(filtreTxt) >0:
                where += xformat.ComposeWhereFiltre(filtreTxt,lstChamps, lstColonnes = lstColonnes,lien='AND')

    if not db.typeDB == 'sqlite':
        req = """FLUSH TABLES stArticles;"""
        #retour = db.ExecuterReq(req, mess="UTILS_Stocks.SqlArticles Flush")

    req = """   SELECT %s 
                FROM stArticles 
                %s
                ORDER BY IDarticle
                %s ;""" % (",".join(lstChamps),where,limit)

    retour = db.ExecuterReq(req, mess="UTILS_Stocks.SqlArticles Select" )
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

def SqlOneArticle(db,value,flou=True):
    # test de présence de l'article
    recordset = []
    if flou:
        match = "LIKE '%%%s%%'"%value
    else: match = "= '%s'"%value
    if value and len(value)>0:
        req = """   SELECT IDarticle
                    FROM stArticles
                    WHERE IDarticle %s
                    ;""" % (match)
        retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlOneArticle req1')
        if retour == "ok":
            recordset = db.ResultatReq()
    return recordset

def SqlDicArticles(db, olv, lstArticles):
    # retourne les valeurs de l'article sous forme de dict à partir du buffer < fichier starticles
    if not hasattr(olv, 'buffArticles'):
        olv.buffArticles = {}
    lstManquants = [x for x in lstArticles if not x in olv.buffArticles]

    # compléter buffArticles
    if len(lstManquants) == 1:
        condArticle = "IDarticle LIKE '%%%s%%'" % lstManquants[0]
    elif len(lstManquants) >1:
        condArticle = "IDarticle in (%s)" % str(lstManquants)[1:-1]
    else: condArticle = None

    # appelle les articles non encore présent dans le buffer
    if condArticle:
        table = DB_schema.DB_TABLES['stArticles']
        lstChamps = xformat.GetLstChamps(table)
        lstNomsColonnes = xformat.GetLstChamps(table)
        lstSetterValues = xformat.GetValeursDefaut(table)
        req = """   SELECT %s
                        FROM stArticles
                        WHERE %s
                        ;""" % (','.join(lstChamps),condArticle)
        retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlDicArticle req1')
        if retour == "ok":
            recordset = db.ResultatReq()
            for record in recordset:
                dicArticle = {}
                for key in  lstNomsColonnes:
                    ix = lstNomsColonnes.index(key)
                    valeur = record[ix]
                    if not valeur:
                        valeur = lstSetterValues[ix]
                    dicArticle[key] = valeur
                IDarticle = dicArticle['IDarticle']
                olv.buffArticles[IDarticle] = dicArticle
                # vérif taux TVA
                if not dicArticle['txTva']:
                    dicArticle['txTva'] = 5.5

    # composition du retour à partir du buffer
    ddArticles = {}
    for article in lstArticles:
        ddArticles[article] = olv.buffArticles[article]
    return ddArticles

def SqlFournisseurs(db=None, **kwd):
    lstDonnees = []
    lstMots = []

    def InsFournisseurs(records):
        for record in records:
            # extrait le fournisseur et stocke le mot début
            if not record[0]: continue
            mot = record[0].split()[0].upper()
            if len(mot) > 7: mot = mot[:7]
            if mot in lstMots: continue
            lstMots.append(mot)
            lstDonnees.append(record[0].upper())
        return

    # liste des fournisseurs utilisés dans les articles, non approximativement présent (7 caractères)
    req = """   
            SELECT fournisseur
            FROM stArticles
            GROUP BY fournisseur
            """
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlFournisseurs1')

    if retour == "ok":
        recordset = db.ResultatReq()
        InsFournisseurs(recordset)

    # appel des noms de fournisseurs déjà utilisés par le passé
    req = """   
            SELECT stMouvements.fournisseur
            FROM stMouvements
            GROUP BY stMouvements.fournisseur
            """
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlFournisseurs2')
    if retour == "ok":
        recordset = db.ResultatReq()
        InsFournisseurs(recordset)
    lstDonnees.sort()
    return lstDonnees

def SqlAnalytiques(db, axe="%%"):
    # appel des items Analytiques de l'axe précisé
    req = """   
            SELECT cpta_analytiques.IDanalytique, cpta_analytiques.abrege, cpta_analytiques.nom
            FROM cpta_analytiques
            WHERE (((cpta_analytiques.axe) Like '%s'))
            GROUP BY cpta_analytiques.IDanalytique, cpta_analytiques.abrege, cpta_analytiques.nom
            ORDER BY cpta_analytiques.IDanalytique;
            """ % axe
    lstDonnees = []
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlFournisseurs')
    if retour == "ok":
        recordset = db.ResultatReq()
        lstDonnees = [list(x) for x in recordset]
    return lstDonnees

def SqlRayons(db):
    # appel des items utilisés
    req = """   
            SELECT rayon
            FROM stArticles
            GROUP BY rayon
            ORDER BY rayon;
            """
    lstDonnees = []
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlMagasins')
    if retour == "ok":
        recordset = db.ResultatReq()
        lstDonnees = [x[0].capitalize() for x in recordset]
    lstDonnees = ["",] + lstDonnees
    return lstDonnees

def SqlMagasins(db):
    # appel des items utilisés
    req = """   
            SELECT magasin
            FROM stArticles
            GROUP BY magasin
            ORDER BY magasin;
            """
    lstDonnees = []
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlMagasins')
    if retour == "ok":
        recordset = db.ResultatReq()
        lstDonnees = [x[0].capitalize() for x in recordset]
    lstDonnees = ["",] + lstDonnees
    return lstDonnees

def SqlMvtsAnte(**kwd):
    # retourne les mouvements anterieurs pour un écran DLG_Mouvements
    dicOlv = kwd.get('dicOlv',None)
    db = kwd.get('db',None)
    filtre = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)
    encours = kwd.pop('encours',None)
    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    if nbreFiltres == 0:
        limit = """
                LIMIT %d""" % LIMITSQL
    codesOrigines = dicOlv['codesOrigines']

    dateEnCours = GetDateLastInventaire(db)
    where = """
                WHERE ( date >= '%s' )
                        AND (origine in ( %s ) )""" % (dateEnCours, str(codesOrigines)[1:-1])

    order = "ORDER BY date DESC"
    if encours:
        # limite à la date encours
        where += """
                AND dateSaisie = '%s' """%(encours)
        order = "ORDER BY IDM DESC"

    if filtre:
        where += """
                AND (date LIKE '%%%s%%'
                        OR fournisseur LIKE '%%%s%%'
                        OR IDanalytique LIKE '%%%s%% ')""" % (filtre, filtre,filtre)

    lstChamps = dicOlv['lstChamps']
    lstGroupBy  = [ x for x in lstChamps if '(' not in x ]
    groupBy = ",".join(lstGroupBy)
    req = """   SELECT %s AS IDM
                FROM stMouvements
                %s 
                GROUP BY %s
                ;""" % (",".join(lstChamps), where,groupBy)
    retour = db.ExecuterReq(req, mess='SqlMvtsAnte')
    lstDonnees = []
    if retour == 'ok':
        recordset = db.ResultatReq()
        for record in recordset:
            lstDonnees.append([x for x in record])
    return lstDonnees

def SqlTable(**kwd):
    # retourne les données pour une liste des  anterieurs
    dicOlv = kwd.get('dicOlv',None)
    db = kwd.get('db',None)
    table = dicOlv.get('table',None)
    groupby = dicOlv.get('groupby',"")
    where = dicOlv.get('where',"LIMIT 100")
    lstChamps = dicOlv['lstChamps']
    if where != "": where = "WHERE %s"%where
    if groupby != "": groupby = "GROUP BY %s"%groupby
    req = """   SELECT %s
                FROM %s
                    %s
                    %s
                ;""" % (",".join(lstChamps),table,where,groupby)
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlTable')
    lstDonnees = []
    if retour == 'ok':
        recordset = db.ResultatReq()
        for record in recordset:
            lstDonnees.append([x for x in record])
    return lstDonnees

def MakeChoiceActivite(analytique):
    if not analytique:
        return "???"
    if isinstance(analytique,(list,tuple)):
        choice = "%s %s"%(analytique[0],analytique[1])
    else:
        choice = "%s %s"%(analytique['idanalytique'],analytique['abrege'])
    return choice

# Gestion des lignes de l'olv mouvements --------------------------------------------------------------------------
def MajMouvements(champs=(), llMvts=[[],]):
    # uddate des champs d'un mouvement, l'ID en première position
    db = xdb.DB()
    retour = True
    for values in llMvts:
        ret = db.ReqMAJ('stMouvements',
                    nomChampID=champs[0],
                    ID = values[0],
                    lstChamps=champs[1:],lstValues=values[1:],
                    mess="UTILS_Stocks.MajMouvements"),
        if ret != 'ok':
            retour = False
    db.Close()
    return retour

def SauveMouvement(db,dlg,track):
    # --- Sauvegarde des différents éléments associés à la ligne de mouvement
    if not track.valide:
        return False

    if hasattr(track,'analytique') and track.analytique:
        analytique = track.analytique
    elif not dlg.analytique or len(dlg.analytique.strip()) == 0:
        analytique = '00'
    else: analytique = dlg.analytique

    if hasattr(track,'repas') and track.repas:
        repas = CHOIX_REPAS.index(track.repas)+1
    else:
        repas = None

    if hasattr(track,'date') and track.date:
        date = track.date
    else: date = dlg.date
    if hasattr(track,'origine') and track.origine:
        origine = track.origine
    else: origine = dlg.origine
    if hasattr(track,'fournisseur') and track.fournisseur:
        fournisseur = track.fournisseur
    else: fournisseur = dlg.fournisseur

    lstDonnees = [
                ('IDarticle', track.IDarticle),
                ('repas', repas),
                ('qte', track.qte * dlg.sensNum),
                ('prixUnit', track.prixTTC),
                ('ordi', dlg.ordi),
                ('dateSaisie', dlg.today),
                ('modifiable', 1),
                ('origine', origine),
                ('date', date),
                ('fournisseur', fournisseur),
                ('IDanalytique', analytique),
    ]

    try: IDmouvement = int(track.IDmouvement)
    except: IDmouvement = None
    MAJarticle(db,dlg,track)

    if IDmouvement :
        ret = db.ReqMAJ("stMouvements", lstDonnees, "IDmouvement", IDmouvement,mess="UTILS_Stocks.SauveLigne Modif: %d"%IDmouvement)
    else:
        ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="UTILS_Stocks.SauveLigne Insert")
        if ret == 'ok': IDmouvement = db.newID
    if ret == 'ok':
        track.IDmouvement = IDmouvement
        dicMvt = xformat.ListTuplesToDict(lstDonnees)
        track.dicMvt.update(dicMvt)

def DelMouvement(db,olv,track):
    # --- Supprime les différents éléments associés à la ligne --
    if not track.IDmouvement in (None,0, ''):
        if track.valide and  not hasattr(track, 'dicMvt'):
            dicMvt = {'qte': track.qte, 'prixUnit': track.prixTTC}
        track.qte = 0
        MAJarticle(db, olv.lanceur, track)
        if track.valide:
            ret = db.ReqDEL("stMouvements", "IDmouvement", track.IDmouvement,affichError=True)
            if ret == 'ok':
                del track.dicMvt
    return

def MAJarticle(db,dlg,track):
    # sauve dicArticle bufférisé dans ctrlOlv.bffArticles, pointé par les track.dicArticle)
    if not track.IDarticle or track.IDarticle in ('',0): return
    if hasattr(track,'valide)') and track.valide == False: return
    if track.qte in (None,''): return

    # Maj dicArt
    def majArticle(dicArt,dicMvt):
        # calcul de la correction quantités stock
        deltaQte = (track.qte * dlg.sensNum) - dicMvt['qte']
        oldQteStock = dicArt['qteStock']
        dicArt['qteStock'] += deltaQte
        # calcul du nouveau prix moyen
        if dicArt and (dlg.sens == 'article'):
            # cas des corrections oMvtOneArticle, on recalcule
            prixMoyen = PxAchatsStock(dlg.ctrlOlv.modelObjects)
        elif not dicArt or Nz(dicArt['prixMoyen']) <= 0:
            # non renseigné en double, pas de moyenne nécessaire
            prixMoyen = abs(track.prixTTC)
        elif dlg.sens == 'sorties' or track.qte < 0:
            # les sorties ou correctifs ne modifient pas la valeur unitaire du stock
            prixMoyen = dicArt['prixMoyen']
        else:
            # Nouvelle entrée en stock, il faut faire la moyenne geométrique
            oldValSt = oldQteStock * dicArt['prixMoyen']
            oldValMvt = dicMvt['qte'] * dicMvt['prixUnit']
            newValMvt = track.qte * track.prixTTC
            newValSt = oldValSt + newValMvt - oldValMvt
            if xformat.Nz(dicArt['qteStock']) == 0:
                prixMoyen = dicArticle['prixMoyen']
            else:
                prixMoyen = (newValSt / dicArt['qteStock'] )
            track.pxMoyen = prixMoyen
            if dlg.ht_ttc == 'HT':
                track.pxMoyen = prixMoyen / (1 + (dicArt['txTva'] / 100))

        # Maj dicMvt
        newDicMvt['IDmouvement'] = track.IDmouvement
        newDicMvt['prixUnit'] = track.pxUn
        newDicMvt['IDarticle'] = track.IDarticle
        dicArt['prixMoyen'] = prixMoyen
        lstDonnees = [('qteStock', dicArt['qteStock']),
                      ('prixMoyen', dicArt['prixMoyen']),
                      ('ordi', dlg.ordi),
                      ('dateSaisie', dlg.today), ]

        # prix actuel changé uniquement sur nouvelles entrées
        if 'achat' in dlg.origine and Nz(track.qte) != 0:
            dicArt['prixActuel'] = track.prixTTC
            lstDonnees += [
                ('dernierAchat', xformat.DateFrToSql(dlg.date)),
                ('prixActuel', dicArt['prixActuel']), ]

        # enregistre l' article dans la bd
        ret = db.ReqMAJ("stArticles", lstDonnees, "IDarticle", dicArt['IDarticle'],
                        mess="UTILS_Stocks.MAJarticle Modif: %s" % dicArt['IDarticle'])
        return ret

    #IDarticle = track.IDarticle
    newDicMvt = {}
    dicArticle = xformat.CopyDic(track.dicArticle)

    oldIDarticle = track.IDarticle
    if hasattr(track, 'oldIDarticle'):
        oldIDarticle = track.oldIDarticle

    if hasattr(track, 'dicMvt') and track.dicMvt:
        dicMvt = track.dicMvt
        oldIDarticle = dicMvt['IDarticle']
    else:
        dicMvt = {'IDarticle':oldIDarticle,'qte': 0, 'prixUnit': 0}

    newQte = track.qte

    ret = None
    # différents cas lancés

    if oldIDarticle != dicArticle['IDarticle']:
        # article changé, gestion de la suppression virutelle de la ligne puis recréation
        # suppression, de l'ancien mouvement et mis sa nouvelle quantité à zéro
        track.qte = 0
        ret = majArticle(track.oldDicArticle,dicMvt)

        # recréation, sans ancien mouvement mais nouvelle quantité
        track.qte = newQte
        newDicMvt = {}
        ret = majArticle(dicArticle, {'qte': 0, 'prixUnit': dicArticle['prixMoyen']})
    else:
        # modif du mouvement sur le même article
        ret = majArticle(dicArticle,dicMvt)

    if ret == 'ok':
        if hasattr(track,'dicMvt') and track.dicMvt:
            track.dicMvt.update(newDicMvt)
        else: track.dicMvt = newDicMvt
        track.dicArticle.update(dicArticle)
        track.nbRations = track.qte * dicArticle['rations']
    if 'DLG_MvtOneArticle' in dlg.Name:
        dlg.ctrlOlv.MAJ_calculs(dlg)

def RenameArticle(db,dlg,oldID,newID):
    lstDonnees = [('IDarticle',newID)]

    ret = db.ReqMAJ('stArticles',lstDonnees,'IDarticle',oldID, mess="RenameArticle / Articles",affichError=True)
    if ret == 'ok':
        condition = "IDarticle = '%s'"%oldID
        ret = db.ReqMAJ('stMouvements',lstDonnees,condition=condition, mess="RenameArticle / Mouvements",affichError=True)
        ret = db.ReqMAJ('stInventaires',lstDonnees,condition=condition, mess="RenameArticle / Inventaires",affichError=True)
    return

def SauveEffectif(dlg,**kwd):
    # Appelé en retour de saisie, gère l'enregistrement
    mode = kwd.pop('mode',None)
    donnees = kwd.pop('donnees',None)
    if donnees and dlg and 'lstCodesSup' in dlg.dicOlv:
        # pour aligner le nbre de données sur le nbre de colonnes de l'olv décrit dans dicOlv
        donnees += ['']*len(dlg.dicOlv['lstCodesSup'])

    db = kwd.pop('db',None)
    lstDonnees = []
    IDdate = None

    condPK = 'IDanalytique = %s' % dlg.analytique

    ixLigne = kwd.pop('ixLigne',None)
    if hasattr(dlg,'ctrlOlv'):
        donneesOlv = dlg.ctrlOlv.lstDonnees
        if ixLigne != None and len(donneesOlv) > 0:
            ixLigne = min(ixLigne,len(donneesOlv))
            IDdate = donneesOlv[ixLigne][0]

    if mode == 'suppr':
        ret = db.ReqDEL('stEffectifs','IDdate',IDdate,condPK, mess="Suppression Effectifs")
        if ret == 'ok' and ixLigne:
            del donneesOlv[ixLigne]
    else:
        lstDonnees = [('IDdate',donnees[0]),
                    ('IDanalytique',dlg.analytique),
                    ('midiRepas',donnees[1]),
                    ('soirRepas',donnees[2]),
                    ('midiClients', donnees[3]),
                    ('soirClients', donnees[4]),
                    ('prevuRepas',donnees[5]),
                    ('prevuClients', donnees[6]),
                    ('ordi', dlg.ordi),
                    ('dateSaisie', dlg.today),]

    if mode == 'ajout':
        ret = db.ReqInsert('stEffectifs',lstDonnees=lstDonnees,mess="Insert Effectifs",affichError=True)
        if ret == 'ok' and hasattr(dlg,'ctrlOlv'):
            if ixLigne and ixLigne < len(donneesOlv):
                dlg.ctrlOlv.lstDonnees = donneesOlv[:ixLigne] + [donnees,] + donneesOlv[ixLigne:]
            else: dlg.ctrlOlv.lstDonnees.append(donnees)

    elif mode == 'modif':
        ret = db.ReqMAJ('stEffectifs',lstDonnees[2:],'IDdate',IDdate,condPK, mess="MAJ Effectifs")
        if ret == 'ok' and ixLigne:
            donneesOlv[ixLigne] = donnees

def SauveArticle(dlg,**kwd):
    # Appelé en retour de saisie, gère l'enregistrement
    mode = kwd.pop('mode',None)
    donnees = kwd.pop('donnees',None)
    dicOlv = kwd.get('dicOlv',{})
    if donnees and dlg and 'lstCodesSup' in dlg.dicOlv:
        # pour aligner le nbre de données sur le nbre de colonnes de l'olv décrit dans dicOlv
        donnees += ['']*len(dlg.dicOlv['lstCodesSup'])

    db = kwd.pop('db',None)
    lstDonnees = []

    # récup des liste de champs dans l'écran de saisie
    lstChamps = []
    for partie,lignes in dicOlv['matriceSaisie'].items():
        lstChamps += [x['name'] for x in lignes]

    # mis à jour des données OLV et enregistremetn db
    ixLigne = kwd.pop('ixLigne',None)
    if ixLigne != None:
        donneesOlv = dlg.ctrlOlv.lstDonnees
        ixLigne = min(ixLigne,len(donneesOlv))
        if mode in ('modif', 'suppr'):
            IDarticle = donneesOlv[ixLigne][0]
    else:
        if mode in ('modif','suppr'):
            wx.MessageBox('Impossible de pointer la ligne sans ixLigne')
            return

    if mode == 'suppr':
        ret = db.ReqDEL('stArticles','IDarticle',IDarticle, mess="Suppression Article")
        if ret == 'ok' and ixLigne:
            del donneesOlv[ixLigne]
    else:
        # récup des données saisies pour constituer les ajouts ou modif
        lstDonnees = []
        for ix in range(len(donnees)):
            lstDonnees.append((lstChamps[ix],donnees[ix]))
        lstDonnees +=    [('ordi', dlg.ordi),
                        ('dateSaisie', dlg.today),]

    if mode == 'ajout':
        ret = db.ReqInsert('stArticles',lstDonnees=lstDonnees,mess="Insert Article",affichError=True)
        if ret == 'ok':
            if ixLigne and ixLigne < len(donneesOlv):
                dlg.ctrlOlv.lstDonnees = donneesOlv[:ixLigne] + [donnees,] + donneesOlv[ixLigne:]
            else: dlg.ctrlOlv.lstDonnees.append(donnees)

    elif mode == 'modif':
        ret = db.ReqMAJ('stArticles',lstDonnees[1:],'IDarticle',IDarticle, mess="MAJ Article")
        if ret == 'ok' and ixLigne:
            donneesOlv[ixLigne] = donnees

def GetEffectifs(dlg,**kwd):
    # retourne une liste valeurs de la table stEffectifs selon lstChamps et période
    lstChampsDef = ['IDdate', 'midiRepas', 'soirRepas', 'midiClients', 'soirClients',
                    'prevuRepas', 'prevuClients', 'IDanalytique']
    db = kwd.get('db',dlg.db)
    periode = kwd.get('periode',dlg.periode)
    limit = kwd.get('limit','')
    nbreFiltres = kwd.get('nbreFiltres', 0)
    lstChamps = kwd.get('lstChamps',lstChampsDef)

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    if nbreFiltres == 0 and limit == '':
        limit = "LIMIT %d" % LIMITSQL
    dtFin = xformat.DateSqlToDatetime(periode[1])
    dtDeb = xformat.DateSqlToDatetime(periode[0])

    # compose le where sur date et analytique
    def getWhere(deb,fin):
        wh = """
                WHERE (IDdate >= '%s' AND IDdate <= '%s')
                    """%(deb,fin)

        # filtrage sur le code analytique
        if dlg.cuisine == 1: wh += """
                        AND ( IDanalytique = '00' OR IDanalytique IS NULL )"""
        else: wh += """
                        AND ( IDanalytique = '%s')"""%dlg.analytique
        return wh

    # Recherche des effectifs:'date', 'nbMidiCli', 'nbMidiRep', 'nbSoirCli', 'nbSoirRep'
    where = getWhere(dtDeb,dtFin)
    table = DB_schema.DB_TABLES['stEffectifs']
    champsReq = xformat.GetLstChamps(table)
    req = """   SELECT %s
                FROM stEffectifs
                %s 
                ORDER BY IDdate DESC
                %s ;""" % (",".join(champsReq), where, limit)

    retour = db.ExecuterReq(req, mess='GetEffectifs')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # composition des données à partir du recordset
    lstDonnees = []
    for record in recordset:
        dic = xformat.ListToDict(champsReq,record)
        ligne = []
        for ix in range(len(lstChamps)):
            ligne.append(dic[lstChamps[ix]])
        lstDonnees.append(ligne)
    return lstDonnees

def QuelsEffectifs(dlg,decalJ1=False):
    # retourne la prise en compte des effectifs quotidiens
    if dlg.midi: effMidi = True
    if dlg.soir: effSoir = True
    if dlg.matin and not (dlg.midi or dlg.soir):
        if decalJ1:
            effSoir = True # le cout matin seul sera divisé par l'effectif du soir seul
        else:
            effMidi = True # le cout matin seul sera divisé par l'effectif du midi seul
    return effMidi,effSoir

def GetEffectifPeriode(dlg):
    # retourne nb repas et clients sur la période
    effMidi, effSoir = QuelsEffectifs(dlg)
    lstChamps = ['IDdate', 'midiRepas', 'soirRepas', 'midiClients', 'soirClients']
    lstEffectifs = GetEffectifs(dlg,lstChamps=lstChamps)
    Nz = xformat.Nz
    nbRepas, nbClients = 0, 0
    for IDdate, midiRepas, soirRepas, midiClients, soirClients in lstEffectifs:
        # calcul repas et cients
        nbcl = 0
        if effMidi:
            nbRepas += Nz(midiRepas)
            nbcl += Nz(midiClients)
        if effSoir:
            nbRepas += Nz(soirRepas)
            nbcl += Nz(soirClients)
        if effMidi and effSoir:
            # les clients ne comptent qu'une fois, moyenne midi-soir
            nbcl = nbcl / 2
        nbClients += nbcl
    return nbRepas, nbClients

def GetPrixJourLignes(dlg, grouper='date', **kwd):
    # renvoie une liste de données pour les lignes de l'olv, champ1 = key
    db = kwd.get('db',dlg.db)
    if not grouper in ('date','article'):
        # le champ 1 regroupement est soit la date soit l'article
        raise Exception("GetPrixJour détail grouper not in ('date','IDarticle')")

    # si non repas en cuisine il faut un code analytique de camp
    if dlg.cuisine == 0 and dlg.analytique == '':
        return []

    # filtrage sur la date
    periode = dlg.periode
    dtFin = xformat.DateSqlToDatetime(periode[1])
    dtDeb = xformat.DateSqlToDatetime(periode[0])
    if dlg.matinj1:
        decalJ1 = 1
    else: decalJ1 = 0
    dtFinJ1 = xformat.DecaleDateTime(dtFin,decalJ1) # pour inclure les ptDèj du lendemain

    # filtrage sur les types de repas demandés
    lstRepasRetenus = []
    if dlg.midi:
        lstRepasRetenus.append(2)
    if dlg.soir:
        lstRepasRetenus.append(3)
    if len(lstRepasRetenus) >0:
        lstRepasRetenus += [5,]# ajout des indifinis sauf si matins seuls
    if dlg.matin:
        lstRepasRetenus += [1,4]
    if lstRepasRetenus == []: return []

    lstChamps = ['IDdate', 'midiRepas', 'soirRepas', 'midiClients', 'soirClients']
    lstEffectifs = GetEffectifs(dlg,lstChamps=lstChamps,periode = (dtDeb, dtFinJ1))

    # composition du dic des effectifs
    dicEffectifs = {}
    for effectif in lstEffectifs:
        dicEff = xformat.ListToDict(lstChamps,effectif)
        dicEffectifs[dicEff['IDdate']] = dicEff
    initDicEff = xformat.ListToDict( lstChamps,(0,) * len(lstChamps) )

    # quels effectifs selon les repas retenus?
    nbRepasPeriode, nbClientsPeriode = GetEffectifPeriode(dlg)

    # Recherche des mouvements -----------------------------------------------------------
    # compose le where sur date et analytique
    def getWhere(deb,fin):
        wh = """
                WHERE (date >= '%s' AND date <= '%s')
                    """%(deb,fin)

        # filtrage sur le code analytique
        if dlg.cuisine == 1: wh += """
                        AND ( IDanalytique = '00' OR IDanalytique IS NULL )"""
        else: wh += """
                        AND ( IDanalytique = '%s')"""%dlg.analytique
        return wh

    where = getWhere(dtDeb, dtFinJ1)

    # condition sur l'origine
    if dlg.cuisine == 1:
        origine = " AND origine in ('repas','od_in','od_out')"
    else:
        origine = " AND origine in ('camp')"
    where += origine

    # définition des paramètres de la requête
    lstChamps = ['date', 'repas', 'stMouvements.IDarticle', 'qte', 'prixUnit',
                 'rayon','origine']
    join = "LEFT JOIN stArticles ON stArticles.IDarticle = stMouvements.IDarticle"

    # appel des mouvements
    req = """
            SELECT  %s
            FROM stMouvements
            %s
            %s
            ORDER BY stMouvements.Date DESC , stMouvements.repas
            ; """%(", ".join(lstChamps), join, where)
    retour = db.ExecuterReq(req, mess='GetPxJoursDetail')
    lstMouvements = ()
    if retour == "ok": lstMouvements = db.ResultatReq()

    # création de dictionnaires de données à partir du lstMouvements
    dicLignes = {}

    # Premier passage : regroupement sur la clé regroupement -----------------------------
    lstManqueEffectifs = []
    for dteStr,repas,IDarticle,qteConso,prixUnit,rayon,origine in lstMouvements:
        # liminaire
        if not dteStr in dicEffectifs:
            dicEffectifs[dteStr] = initDicEff
            if not dteStr in lstManqueEffectifs:
                lstManqueEffectifs.append(dteStr)
        if not repas: repas = 5
        # on ne retient que les repas à inclure
        if not repas in lstRepasRetenus: continue
        # on ne prend que les od négative assimilées en sorties
        if origine.startswith('od') and qteConso >= 0: continue
        # si décalage: ptdej ramenés au jour j-1 pour les rattacher à effectifs soir
        date = xformat.DateSqlToDatetime(dteStr)
        if repas == 1 and decalJ1 == 1:
            date = xformat.DecaleDateTime(date,-1)
        if date > dtFin or date < dtDeb : continue

        keyLigne = None
        if grouper == 'date':
            keyLigne = date
            IDarticle = ""
        elif grouper == 'article':
            keyLigne = IDarticle
            date = None
        if not keyLigne in dicLignes:
            dicLignes[keyLigne] = {'IDarticle': IDarticle,
                                'date': date,
                                'rayon': rayon,
                                'qteConso': 0.0,
                                'cout': {},
                                'dontOD': {}
                                }
            # on garde le distingo par repas à cause des valeurs unitaires à calculer en final
            for code in lstRepasRetenus:
                dicLignes[keyLigne]['cout'][code] = 0.0
                dicLignes[keyLigne]['dontOD'][code] = 0.0
        # répartition des repas 'tous' sur midi et soir
        if repas == 5:
            nbrepas = dicEffectifs[dteStr]['midiRepas'] + dicEffectifs[dteStr]['soirRepas']
            if nbrepas > 0 and not dlg.midi:
                # retire la part du midi
                qteConso -= qteConso * dicEffectifs[dteStr]['midiRepas'] / nbrepas
            if nbrepas >0 and not dlg.soir:
                # retire la part du soir
                qteConso -= qteConso * dicEffectifs[dteStr]['midiSoir'] / nbrepas

        dicLignes[keyLigne]['qteConso'] -= qteConso
        dicLignes[keyLigne]['cout'][repas] += round(-qteConso * prixUnit,6)
        if origine.startswith('od'):
            dicLignes[keyLigne]['dontOD'][repas] += round(-qteConso * prixUnit, 6)

    # Deuxième passage: Calcul des composants de la ligne regroupée ---------------------
    lstDonnees = []

    for keyLigne,dic in dicLignes.items():
        # calcul du coût
        cout = 0.0
        dontOD = 0.0
        for codeRepas, value in dic['cout'].items():
            cout += value
        for codeRepas, value in dic['dontOD'].items():
            dontOD += value

        # lignes par article
        nbRepasLigne = nbRepasPeriode
        nbClientsLigne = nbClientsPeriode

        if grouper == 'date':
            # calcul du nombre de clients repas à retenir pour la journée
            effMidi, effSoir = QuelsEffectifs(dlg)
            key = str(keyLigne)
            dicEff = dicEffectifs[key]
            nbRepasLigne = xformat.Nz(dicEff['midiRepas']) + xformat.Nz(
                dicEff['soirRepas'])
            # nombre de clients
            nbcl = 0
            if effMidi:
                # service du midi
                nbcl += xformat.Nz(dicEff['midiClients'])
            if effSoir:
                #  ajout du service du soir
                nbcl += xformat.Nz(dicEff['soirClients'])
            if effMidi and effSoir:
                # les clients ne comptent qu'une fois, moyenne midi-soir
                nbcl = nbcl / 2
            nbClientsLigne = nbcl

        prixRepas = cout
        prixClient = cout
        if nbRepasLigne > 0:
            prixRepas = cout / nbRepasLigne
        if nbClientsLigne > 0:
            prixClient = cout / nbClientsLigne
        if abs(dic['qteConso']) > 0:
            prixUn = cout / dic['qteConso']
        else:
            prixUn = cout

        ligne = []
        if grouper == 'article':
            ligne = [   None,
                    dic['IDarticle'],
                    dic['rayon'],
                    dic['qteConso'],
                    prixUn,
                    cout,
                    nbRepasLigne,
                    prixRepas,
                    nbClientsLigne,
                    prixClient,
                    dontOD]
        elif grouper == 'date':
            ligne = [  None,
                    dic['date'],
                    nbRepasLigne,
                    nbClientsLigne,
                    prixRepas,
                    prixClient,
                    cout,
                    dontOD]
        lstDonnees.append(ligne)

    if len(lstManqueEffectifs) > 0:
        mess = "%d jours sans effectifs renseignés\n\n"%len(lstManqueEffectifs)
        mess += "Jours: %s"%str(lstManqueEffectifs[:5])
        if len(lstManqueEffectifs) > 5: mess += "..."
        wx.MessageBox(mess,"Prix rations faux",style=wx.ICON_ERROR)
    return lstDonnees

def GetPrixJours(dlg,**kwd):
    #descriptif des données retournées pour prix de journée
    kwd['grouper'] = 'date'
    return GetPrixJourLignes(dlg, **kwd)

def GetPrixJourArticle(dlg,**kwd):
    #descriptif des données retournées pour prix de journée
    kwd['grouper'] = 'article'
    return GetPrixJourLignes(dlg, **kwd)

if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
    print(GetLastInventaire(datetime.date(2021, 6, 30)))