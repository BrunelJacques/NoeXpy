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
from xpy.outils.xformat import Nz
from xpy  import xUTILS_DB as xdb

LIMITSQL = 100
# codes repas [ 1,      2,     3,     4       5]
CHOIX_REPAS = ['PtDej','Midi','Soir','5eme','Tous']



# Nouvelle Gestion des inventaires --------------------------------------------
def PostMouvements(champs=[],mouvements=[[],]):
    # uddate des champs d'un mouvement, l'ID en dernière position
    db = xdb.DB()

    retour = True
    for mouvement in mouvements:
        ret = db.ReqMAJ('stMouvements',
                    nomChampID=champs[-1],
                    ID = mouvement[-1],
                    lstChamps=champs[:-1],lstValues=mouvement[:-1],
                    mess="UTILS_Stocks.PostMouvements")
        if ret != 'ok':
            retour = False
    db.Close()
    return retour

def PostInventaire(cloture=datetime.date.today(),inventaire=[[],]):
    # delete puis recrée l'inventaire à la date de cloture
    if cloture == None:
        cloture = datetime.date.today()
    ordi = os.environ['USERDOMAIN']
    dteSaisie = xformat.DatetimeToStr(datetime.date.today(),iso=True)
    # Appelle l'inventaire précédent
    lstChamps = ['IDdate',
                 'IDarticle',
                 'qteStock',
                 'prixMoyen',
                 'prixActuel',
                 'ordi',
                 'dateSaisie',]
    llDonnees = []
    # lignes reçues [date,article,qte,prixMoyen,montant,lastPrix]
    for dte,article,qte,pxMoy,mtt,pxLast in inventaire:
        if dte != str(cloture): raise Exception(
            "cloture = %s diff de inventaire = %s"%(str(cloture),str(dte)))
        llDonnees.append([dte,article,qte,pxMoy,pxLast,ordi,dteSaisie])

    # test présence inventaire
    db = xdb.DB()
    finIso = xformat.DatetimeToStr(cloture,iso=True)
    condition = "stInventaires.IDdate = '%s'"%finIso
    req = """   SELECT *
                FROM stInventaires
                WHERE %s
                ;""" %(condition)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.testPrésenceInventaire')
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) > 0:
            mess = "UTILS_Stoks.PostInventaire.ReqDel"
            ret = db.ReqDEL('stInventaires',condition=condition,mess=mess)

    ret = db.ReqInsert('stInventaires',lstChamps=lstChamps,lstlstDonnees=llDonnees,
                 mess="UTILS_Stocks.PostInventaires")
    db.Close()
    if ret == 'ok':
        return True
    return ret

def GetLastInventaire(dteAnalyse=None,lstChamps=None):
    # retourne l'inventaire précédent la date de dteAnalyse
    if dteAnalyse == None:
        dteAnalyse = datetime.date.today()
    db = xdb.DB()
    # Appelle l'inventaire précédent
    if not lstChamps:
        lstChamps = ['IDdate','IDarticle','qteStock','prixMoyen']
    finIso = xformat.DatetimeToStr(dteAnalyse,iso=True)
    req = """   SELECT %s
                FROM stInventaires
                WHERE   (stInventaires.IDdate = 
                            (SELECT MAX(stInv.IDdate) 
                            FROM stInventaires as stInv
                            WHERE stInv.IDdate < '%s')
                        )
                ;""" % (",".join(lstChamps),finIso)

    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetLastInventaire')
    llInventaire = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            mouvement = []
            for ix  in range(len(lstChamps)):
                mouvement.append(record[ix])
            llInventaire.append(mouvement)
    db.Close()
    return llInventaire

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

def PxUnitInventaire(db, IDarticle, qteStock, dteAnalyse):
    # retourne le prix moyen de la quantité d'articles achetés avant la dteAnalyse
    if Nz(qteStock) == 0:
        return None
    req = """    
        SELECT date, qte, prixUnit
        FROM stMouvements
        WHERE (IDarticle = '%s') AND (origine = 'achat')
        ORDER BY date DESC
        ;""" % IDarticle

    mess = "Echec UTILS_Stocks.PxUnitInventaire"
    ret = db.ExecuterReq(req, mess=mess, affichError=True)
    if ret != 'ok': return None
    recordset = db.ResultatReq()
    pxUn = None
    cumQteAch = 0.0
    cumMttAch = 0.0
    achatsPost = False
    for dte, qteAchat, prixUnit in recordset:
        if dte > dteAnalyse:
            achatsPost = True
            continue
        qteAchat = Nz(qteAchat)
        prixUnit = Nz(prixUnit)
        qteAchat = min(qteStock,qteAchat)
        cumQteAch += qteAchat
        cumMttAch += qteAchat * prixUnit
        qteStock -= qteAchat
        if qteStock < 0.0001:
            break
    if cumQteAch > 0.0:
        pxUn = round(cumMttAch / cumQteAch,4)
        if not achatsPost:
            ltModifs = [('prixMoyen', pxUn),
                        ('ordi', 'PU inventaire'),
                        ('dateSaisie', xformat.DatetimeToStr(datetime.date.today())) ]
            db.ReqMAJ('stArticles',ltModifs,'IDarticle',IDarticle,
                      mess = "UTILS_Stocks.PxUnitInventaire",
                      IDestChaine = True)
    return pxUn

def CalculeInventaire(dlg, *args, **kwd):
    # met à jour les quantités dans article et appelle les données pour OLV
    db = dlg.db
    # préalable MAJ des quantités en stock dans les articles
    req = """
            UPDATE stArticles 
            INNER JOIN (
                SELECT IDarticle, SUM(qte) as qtemvt
                FROM stMouvements
                GROUP BY stMouvements.IDarticle) as stmvt 
            ON stArticles.IDarticle = stmvt.IDarticle 
            SET stArticles.qteStock = stmvt.qtemvt
            WHERE stArticles.qteStock <> stmvt.qtemvt
            ;"""
    mess = "Echec de l'actualisation des qteStocks dans les Articles"
    ret = db.ExecuterReq(req, mess=mess, affichError=True)
    if ret != 'ok': return []

    # Force la mise à jour dans la base avant nouveau select évitant le cache
    del db.cursor
    db.cursor = db.connexion.cursor(buffered=False)
    req = """FLUSH  TABLES stArticles;"""
    ret = db.ExecuterReq(req, mess='SqlInventaires flush')
    if ret != 'ok': return []

    # appel du dernier inventaire
    lstChamps = ['IDdate','IDarticle','qteStock','prixMoyen','qteConstat','prixActuel',]
    llInventaire = GetLastInventaire(dlg.date, lstChamps)
    ddInventaire = {}

    #transforme l'inventaire ll en dd avec 1ère clé: article
    for ligne in llInventaire:
        dLigne = xformat.ListToDict(lstChamps, ligne)
        ddInventaire[ligne[1]] = dLigne

    # limitation à la date d'analyse
    dteFin = xformat.DatetimeToStr(dlg.date,iso=True)
    if len(llInventaire) ==  0:
        dteDeb = llInventaire[0][1]
    else:
        # date des premiers enregistrements si aucun inventaire stocké
        dteDeb = "2020-01-01"
    where = "((stMouvements.date > '%s') AND (stMouvements.date <= '%s'))" % (dteDeb, dteFin)

    # appel de tous les articles et des mouvements de la période
    lstChamps = ['IDarticle',
                 'fournisseur', 'magasin', 'rayon',
                 'qteMini', 'qteSaison',
                 'artRations', 'prixMoyen',
                 'prixActuel','lastBuy',
                 'qteMvts', 'mttMvts',
                 'qteAchats', 'mttAchats',
                 ]
    req = """
        SELECT  stArticles.IDarticle,
                stArticles.fournisseur, magasin, rayon, 
                qteMini, qteSaison, 
                rations, prixMoyen,
                prixActuel, stArticles.dernierAchat,
                Sum(stMouvements.qte), Sum(stMouvements.qte * stMouvements.prixUnit),
                Sum(if (stMouvements.origine = 'achat', stMouvements.qte,0)), 
                Sum(if (stMouvements.origine = 'achat', stMouvements.qte,0) 
                    * stMouvements.prixUnit)
                
        FROM  
            stArticles            
            LEFT JOIN stMouvements 	ON (stArticles.IDarticle = stMouvements.IDarticle)
        WHERE %s
        GROUP BY stArticles.IDarticle,
                stArticles.fournisseur, magasin, rayon, 
                qteMini, qteSaison, 
                rations, prixMoyen, prixActuel
        ;""" % where
    retour = db.ExecuterReq(req, mess="UTILS_Stocks.CalculeInventaire Select")
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    #transforme le recordset en dd avec 1ère clé: article
    ddMouvements = {}
    for ligne in recordset:

        dLigne = xformat.ListToDict(lstChamps, ligne)
        ddMouvements[ligne[0]] = dLigne

    # composition des données du tableau OLV --------------------------------------------
    lstCodes = dlg.dicOlv['lstCodes'] + dlg.dicOlv['lstCodesSup']
    lstDonnees = []

    # fusion des deux dictionnaires mouvements période et inventaire début
    def ComposeLigne(db, dMvts, dInvent=None):
        if dInvent:
            # cumul de l'inventaire dans les mouvements
            """ dInvent['IDdate','IDarticle','qteStock','prixMoyen','qteConstat','prixActuel',]
                dMvts [ 'IDarticle',
                        'fournisseur', 'magasin', 'rayon',
                        'qteMini', 'qteSaison',
                        'artRations', 'prixActuel', 'lastBuy',
                        'qteMvts', 'mttMvts',
                        'qteAchats', 'mttAchats',]"""
            if dInvent['qteConstat']: 
                dInvent['qteStock'] = dInvent['qteConstat']
            dMvts['qteMvts'] += dInvent['qteStock']
            dMvts['mttMvts'] += dInvent['qteStock'] * dInvent['prixMoyen']
            if (not dMvts['prixActuel']) or round(dMvts['prixActuel'],4) == 0.0:
                dMvts['prixActuel'] = dInvent['prixActuel']
            if dMvts['qteAchats'] == 0:
                dMvts['prixActuel'] += dInvent['prixMoyen']
                dMvts['qteAchats'] += dInvent['qteStock']
                dMvts['mttAchats'] += (dInvent['qteStock'] * dInvent['prixMoyen'])

        donnees = [None, ] * len(lstCodes)
        # reprise des champs transposés en l'état (même nom)
        for code in lstCodes:
            if code in lstChamps:
                value = dMvts[code]
                if isinstance(value, decimal.Decimal):
                    value = round(float(value),4)
                donnees[lstCodes.index(code)] = value

        # Les champs lus doivent être assemblés pour certains
        qteMvts = Nz(dMvts['qteMvts'])
        pxUn = Nz(dMvts['prixMoyen'])
        pxAct = dMvts['prixActuel']
        # contrôle du prix moyen
        if qteMvts != 0:
            qteAchats = Nz(dMvts['qteAchats'])
            mttAchats = Nz(dMvts['mttAchats'])
            # il y a eu des achats dans la période
            if qteAchats * mttAchats > 0:
                puAchats = round(mttAchats / qteAchats, 4)
                if puAchats == 0:
                    pass
                if abs(1 - (pxUn / puAchats)) < 0.05:
                    # l'ensemble des achats confirme le prix moyen
                    pass
                elif pxAct > 0 and abs(1 - (pxUn / pxAct)) < 0.05:
                    # le dernier prix à confirmé le prix moyen
                    pass
                else:
                    # prix moyen en distorsion: on recalcule selon les derniers achats
                    pxUn = PxUnitInventaire(db, dMvts['IDarticle'], qteMvts, dteFin)
                    if not pxUn:
                        pxUn = pxAct
        pxUn = max(0.0, pxUn)
        donnees[lstCodes.index('pxUn')] = pxUn
        donnees[lstCodes.index('mttTTC')] = round(qteMvts * pxUn,2)
        donnees[lstCodes.index('qteConstat')] = qteMvts
        donnees[lstCodes.index('qteMvts')] = qteMvts
        donnees[lstCodes.index('rations')] = qteMvts * Nz(dMvts['artRations'])

        if dlg.saisonIx == 0:
            mini = Nz(dMvts['qteMini'])
        elif dlg.saisonIx == 1:
            mini = Nz(dMvts['qteSaison'])
        else:
            mini = 0
        donnees[lstCodes.index('qteMini')] = mini
        return donnees

    # composition des lignes
    db = xdb.DB()
    for key, donnees in ddMouvements.items():
        if key.startswith('BISCUITS B-N'):
            print()
        if key in ddInventaire:
            lstDonnees.append(ComposeLigne(db,donnees, ddInventaire[key]))
        else:
            lstDonnees.append(ComposeLigne(db,donnees))
    db.Close()
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
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    if recordset[0][0] > 0:
        return True
    return False

def GetMvtsOneDate(db, dParams=None):
    lstChamps = xformat.GetLstChampsTable('stMouvements',DB_schema.DB_TABLES)
    lstChamps.append('stArticles.qteStock')
    lstChamps.append('stArticles.prixMoyen')
    sensNum = dParams['sensNum']

    # Appelle les mouvements associés à un dic de choix de param et retour d'une liste de dic
    req = """   SELECT %s
                FROM stMouvements
                LEFT JOIN stArticles ON stMouvements.IDarticle = stArticles.IDarticle 
                WHERE ((date = '%s' )
                        AND (stMouvements.origine = '%s' )
                        AND (stMouvements.fournisseur IS NULL  
                                OR stMouvements.fournisseur = '%s' )
                        AND (stMouvements.IDanalytique IS NULL  
                                OR stMouvements.IDanalytique ='00'  
                                OR stMouvements.IDanalytique = '%s' ))
                ;""" % (",".join(lstChamps),dParams['date'],dParams['origine'],dParams['fournisseur'],dParams['analytique'])

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
        retour = db.ExecuterReq(req, mess="UTILS_Stocks.SqlArticles Flush")

    req = """   SELECT %s 
                FROM stArticles 
                %s
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

def SqlDicArticle(db,olv,IDarticle):
    # retourne les valeurs de l'article sous forme de dict à partir du buffer < fichier starticles
    dicArticle = {}
    dlg = olv.lanceur
    if len(IDarticle)>0:
        if not hasattr(olv, 'buffArticles'):
            olv.buffArticles = {}
        if IDarticle in olv.buffArticles.keys():
            # renvoie l'article présent
            dicArticle = olv.buffArticles[IDarticle]
        else:
            # charge l'article non encore présent
            table = DB_schema.DB_TABLES['stArticles']
            lstChamps = xformat.GetLstChamps(table)
            lstNomsColonnes = xformat.GetLstChamps(table)
            lstSetterValues = xformat.GetValeursDefaut(table)
            req = """   SELECT %s
                            FROM stArticles
                            WHERE IDarticle LIKE '%%%s%%'
                            ;""" % (','.join(lstChamps),IDarticle)
            retour = db.ExecuterReq(req, mess='UTILS_Stocks.SqlOneArticle req1')
            if retour == "ok":
                recordset = db.ResultatReq()
                if len(recordset) > 0:
                    for key in  lstNomsColonnes:
                        ix = lstNomsColonnes.index(key)
                        valeur = recordset[0][ix]
                        if not valeur:
                            valeur = lstSetterValues[ix]
                        dicArticle[key] = valeur
            # bufferisation avec tuple (qteStock,prixMoyen) pour calcul des variations lors des entrées
            olv.buffArticles[IDarticle] =dicArticle

        # vérif taux TVA
        try:
            txTva = dicArticle['txTva']
        except:
            dicArticle['txTva'] = 0.0
    return dicArticle

def SqlFournisseurs(db=None, **kwd):
    lstDonnees = []
    lstMots = []

    def InsFournisseurs(records):
        for record in records:
            # extrait le fournisseur et stocke le mot début
            if not record[0]: continue
            mot = record[0].split()[0]
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

    lstDonnees.append('NONAME')
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

# Appel des mouvements antérieurs
def SqlMvtsAnte(**kwd):
    # ajoute les données à la matrice pour la recherche d'un anterieur
    dicOlv = kwd.get('dicOlv',None)
    db = kwd.get('db',None)
    filtre = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)
    encours = kwd.pop('encours',None)
    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    limit = ''
    if nbreFiltres == 0:
        limit = """
                LIMIT %d""" % LIMITSQL
    origines = dicOlv['codesOrigines']
    where = """
                WHERE origine in ( %s ) """ % str(origines)[1:-1]

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
                        OR IDanalytique LIKE '%%%s%% )'""" % (filtre, filtre, filtre,)

    lstChamps = dicOlv['lstChamps']

    req = """   SELECT %s AS IDM
                FROM stMouvements
                %s 
                GROUP BY origine, date, fournisseur, IDanalytique
                %s
                %s ;""" % (",".join(lstChamps), where,order,limit)
    retour = db.ExecuterReq(req, mess='SqlMvtsAnte')
    lstDonnees = []
    if retour == 'ok':
        recordset = db.ResultatReq()
        for record in recordset:
            lstDonnees.append([x for x in record])
    return lstDonnees

# Appel des inventaires antérieurs
def SqlInvAnte(**kwd):
    return []
    # ajoute les données à la matrice pour la recherche d'un anterieur
    dicOlv = kwd.get('dicOlv',None)
    db = kwd.get('db',None)
    filtre = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    limit = ''
    if nbreFiltres == 0:
        limit = """
                LIMIT %d""" % LIMITSQL
    origines = dicOlv['codesOrigines']
    where = """                    WHERE origine in ( %s ) """ % str(origines)[1:-1]
    if filtre:
        where += """
                AND (date LIKE '%%%s%%'
                        OR fournisseur LIKE '%%%s%%'
                        OR IDanalytique LIKE '%%%s%% )'""" % (filtre, filtre, filtre,)

    lstChamps = dicOlv['lstChamps']

    req = """   SELECT %s
                FROM stMouvements
                %s 
                GROUP BY origine, date, fournisseur, IDanalytique
                ORDER BY date DESC
                %s ;""" % (",".join(lstChamps), where, limit)
    retour = db.ExecuterReq(req, mess='SqlMvtsAnte')
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

def SauveMouvement(db,dlg,track):
    # --- Sauvegarde des différents éléments associés à la ligne de mouvement
    if not track.valide:
        return False
    if not dlg.analytique or len(dlg.analytique.strip()) == 0:
        analytique = '00'
    else: analytique = dlg.analytique
    repas = None
    if dlg.sens == 'sorties' and hasattr(track,'repas'):
        if len(track.repas) > 0:
            repas = CHOIX_REPAS.index(track.repas)+1
    lstDonnees = [
                    ('IDarticle', track.IDarticle),
                    ('repas', repas),
                    ('qte', track.qte * dlg.sensNum),
                    ('prixUnit', track.prixTTC),

                    ('ordi', dlg.ordi),
                    ('dateSaisie', dlg.today),
                    ('modifiable', 1),]

    try: IDmouvement = int(track.IDmouvement)
    except: IDmouvement = None
    MAJarticle(db,dlg,track)

    if IDmouvement :
        ret = db.ReqMAJ("stMouvements", lstDonnees, "IDmouvement", IDmouvement,mess="UTILS_Stocks.SauveLigne Modif: %d"%IDmouvement)
    else:
        lstDonnees += [('origine', dlg.origine),
                       ('date', dlg.date),
                       ('fournisseur', dlg.fournisseur),
                       ('IDanalytique', analytique),
                       ]
        ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="UTILS_Stocks.SauveLigne Insert")
        if ret == 'ok': IDmouvement = db.newID
    if ret == 'ok':
        track.IDmouvement = IDmouvement
        dicMvt = xformat.ListTuplesToDict(lstDonnees)
        track.dicMvt.update(dicMvt)

def DelMouvement(db,olv,track):
    # --- Supprime les différents éléments associés à la ligne --
    if not track.IDmouvement in (None,0, ''):
        if not hasattr(track, 'dicMvt'):
            dicMvt = {'qte': track.qte, 'prixUnit': track.prixTTC}
        track.qte = 0
        MAJarticle(db, olv.lanceur, track)
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
        if not dicArt or Nz(dicArt['prixMoyen']) <= 0:
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
            track.pxMoy = prixMoyen
            if dlg.ht_ttc == 'HT':
                track.pxMoy = prixMoyen / (1 + (dicArt['txTva'] / 100))

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
        if 'achat' in dlg.origine and track.qte != 0:
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

    if hasattr(track, 'dicMvt'):
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
        if hasattr(track,'dicMvt'):
            track.dicMvt.update(newDicMvt)
        else: track.dicMvt = newDicMvt
        track.dicArticle.update(dicArticle)
        track.nbRations = track.qte * dicArticle['rations']

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
    # retourne les effectifs de la table stEffectifs
    db = kwd.get('db',dlg.db)
    nbreFiltres = kwd.get('nbreFiltres', 0)
    periode = kwd.get('periode',dlg.periode)
    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" % LIMITSQL

    where = """
                WHERE (IDdate >= '%s' AND IDdate <= '%s')"""%(periode[0],periode[1])

    if not dlg.analytique: dlg.IDanalytique = '00'
    where += """
                        AND ( IDanalytique = '%s')"""%dlg.analytique

    table = DB_schema.DB_TABLES['stEffectifs']
    lstChamps = xformat.GetLstChamps(table)
    req = """   SELECT %s
                FROM stEffectifs
                %s 
                ORDER BY IDdate DESC
                %s ;""" % (",".join(lstChamps), where, limit)
    retour = db.ExecuterReq(req, mess='GetEffectifs')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # composition des données du tableau à partir du recordset
    lstDonnees = []
    for record in recordset:
        dic = xformat.ListToDict(lstChamps,record)
        ligne = [
            dic['IDdate'],
            dic['midiRepas'],
            dic['soirRepas'],
            dic['midiClients'],
            dic['soirClients'],
            dic['prevuRepas'],
            dic['prevuClients'],
            dic['IDanalytique'],]
        lstDonnees.append(ligne)
    return lstDonnees

def GetPrixJourDetail(dlg,grouper='date',**kwd):
    db = kwd.get('db',dlg.db)
    if not grouper in ('date','article','ensemble'):
        raise Exception("GetPrixJour détail grouper not in ('date','IDarticle','ensemble')")
    periode = dlg.periode
    # filtrage sur la date
    dtFin = xformat.DateSqlToDatetime(periode[1])
    dtDeb = xformat.DateSqlToDatetime(periode[0])
    dtFinJ1 = xformat.DecaleDateTime(dtFin,+1) # pour inclure les ptDèj du lendemain

    # filtrage sur les types de repas demandés
    lstRepasRetenus = []
    if dlg.midi:
        lstRepasRetenus.append(2)
    if dlg.soir:
        lstRepasRetenus.append(3)
    if len(lstRepasRetenus) >0:
        lstRepasRetenus += [0,5,]# ajout des indifinis sauf si matins seuls
    if dlg.matin:
        lstRepasRetenus += [1,4]
    if lstRepasRetenus == []: return []

    # compose le where sur date et analytique
    def getWhere(nomDate, deb,fin):
        wh = """
                WHERE (%s >= '%s' AND %s <= '%s')
                    """%(nomDate,deb,nomDate,fin)

        # filtrage sur le code analytique
        if dlg.cuisine: wh += """
                        AND ( IDanalytique = '00' OR IDanalytique IS NULL )"""
        else: wh += """
                        AND ( IDanalytique = '%s')"""%dlg.analytique
        return wh


    # Recherche des effectifs: ['date', 'nbMidiCli', 'nbMidiRep', 'nbSoirCli', 'nbSoirRep']-------------
    where = getWhere('IDdate', dtDeb,dtFin)

    lstChamps = ['IDdate', 'midiRepas', 'soirRepas', 'midiClients', 'soirClients']
    req = """
            SELECT  %s 
            FROM stEffectifs 
            %s
            ORDER BY IDdate DESC
            ; """%(",".join(lstChamps),where)

    retour = db.ExecuterReq(req, mess='GetPrixJours2')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # composition du dic des effectifs
    dicEffectifs = {}
    for record in recordset:
        dicEff = xformat.ListToDict(lstChamps,record)
        dicEffectifs[dicEff['IDdate']] = dicEff

    # Recherche des mouvements ------------------------------------------------------------------------
    where = getWhere('date', dtDeb, dtFinJ1)
    where += """
                        AND
                        origine in ('repas', 'camp')
                        """

    # ajoute la condition sur les codes repas choisis
    if len(lstRepasRetenus) <5:
        where += """
                        AND (repas in (%s)
                            OR (repas IS NULL))"""%str(lstRepasRetenus)[1:-1]
    lstRepasRetenus.append(None)

    if grouper == 'article':
        lstChamps = ['date', 'repas', 'stMouvements.IDarticle', 'qte', 'prixUnit', 'stArticles.rayon']
        join = "LEFT JOIN stArticles ON stArticles.IDarticle = stMouvements.IDarticle"
    else:
        lstChamps = ['date', 'repas', 'stMouvements.IDarticle', 'qte', 'prixUnit']
        join = ""

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

    # Premier passage : regroupement sur la clé grouper ----------------------------------------------
    for record in lstMouvements:
        date = record[0]
        codeRepas = record[1]
        # on ne retient que les repas à inclure
        if not codeRepas in lstRepasRetenus: continue
        # seuls les pt dej au delà de date fin sont pris
        date = xformat.DateSqlToDatetime(date)
        if codeRepas == 1:
            # Ptit dèj: reculer d'un jour pour se rattacher au soir
            date = xformat.DecaleDateTime(date,-1)
        if date > dtFin or date < dtDeb : continue
        IDarticle = ""
        date, rayon, keyLigne = None, None, None

        if grouper == 'date':
            date, codeRepas, IDarticle, qteConso, prixUnit = record
            date = record[0]
            IDarticle = ""
            keyLigne = date
        elif grouper == 'article':
            date, codeRepas, IDarticle, qteConso, prixUnit, rayon = record
            keyLigne = IDarticle
            date = None
        elif grouper == 'ensemble':
            date, codeRepas, IDarticle, qteConso, prixUnit = record
            date = None
            IDarticle = ""
            keyLigne = 'ensemble'

        if not keyLigne in dicLignes.keys():
            dicLignes[keyLigne] = {'IDarticle': IDarticle,
                                'date': date,
                                'rayon': rayon,
                                'qteConso': 0.0,
                                'cout': {},
                                }
            # on garde le distingo par repas à cause des valeurs unitaires à calculer en final
            for code in lstRepasRetenus:
                dicLignes[keyLigne]['cout'][code] = 0.0
        dicLignes[keyLigne]['cout'][codeRepas] += round(-qteConso * prixUnit,6)
        dicLignes[keyLigne]['qteConso'] -= qteConso

    # Deuxième passage: Calcul des composants de la ligne regroupée -----------------------------------
    lstDonnees = []
    for keyLigne,dic in dicLignes.items():
        # calcul du coût midi et soir
        cout = 0.0
        lstCodRepas = [] # listes des différents repas servis pour cette clé
        for codeRepas, value in dic['cout'].items():
            cout += value
            if value >0 and not codeRepas in lstCodRepas:
                lstCodRepas.append(codeRepas)
        # test présence des différents repas servis
        effSoir = (1 in lstCodRepas or 3 in lstCodRepas or 4 in lstCodRepas) # présence de repas du soir
        effMidi = (2 in lstCodRepas)
        repasIndef = (5 in lstCodRepas or 0 in lstCodRepas or None in lstCodRepas) # présence de repas indéterminés

        # finalisation selon les cases cochées lors de la demande
        if dlg.matin and not (dlg.midi or dlg.soir):
            effSoir = True # le cout matin seul sera divisé par l'effectif du soir seul
            effMidi = False
        if repasIndef:
            # il y a des repas indéfinis, on ne s'occupe que des cases cochées
            effMidi, effSoir = False, False
            if dlg.midi: effMidi = True
            if dlg.soir or dlg.matin: effSoir = True

        nbClientsLigne = 0
        diviseurCli = 0
        nbRepasLigne = 0
        for key, dicEff in dicEffectifs.items():
            # calcul du nombre de client à retenir pour la journée
            if grouper == 'date':
                if key != keyLigne:
                    continue
            nbRepasLigne = xformat.Nz(dicEff['midiRepas']) + xformat.Nz(dicEff['soirRepas'])
            # force le service de repas clients si saisie d'effectifs
            if effMidi or xformat.Nz(dicEff['midiClients']) > 0:
                # service du midi
                nbClientsLigne += xformat.Nz(dicEff['midiClients'])
                if nbClientsLigne > 0: diviseurCli +=1
            if effSoir or xformat.Nz(dicEff['soirClients']) >0:
                #  ajout du service du soir + 5ème et ptdèjJ1
                nbClientsLigne += xformat.Nz(dicEff['soirClients'])
                if nbClientsLigne > 0: diviseurCli +=1

        # le client compte toujours un si présent seulement le midi ou le soir ou toute la journée
        if diviseurCli == 0: diviseurCli = 1
        nbClientsLigne = nbClientsLigne / diviseurCli
        
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
                    prixClient,]

        elif grouper == 'date':
            ligne = [  None,
                    dic['date'],
                    nbRepasLigne,
                    nbClientsLigne,
                    prixRepas,
                    prixClient,
                    cout]
        elif grouper == 'ensemble':
            ligne = [cout,nbRepasLigne,nbClientsLigne] # nombres à regrouper
        lstDonnees.append(ligne)
    return lstDonnees

def GetPrixJours(dlg,**kwd):
    #descriptif des données retournées pour prix de journée
    kwd['grouper'] = 'date'
    """vide, date, nbRepas, nbClients, prixRepas, prixClient, cout"""
    return GetPrixJourDetail(dlg,**kwd)

def GetPrixJourArticle(dlg,**kwd):
    #descriptif des données retournées pour prix de journée
    kwd['grouper'] = 'article'
    """vide, date, nbRepas, nbClients, prixRepas, prixClient, cout"""
    return GetPrixJourDetail(dlg,**kwd)

if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
    print(GetLastInventaire(datetime.date(2021, 6, 30)))