#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des stocks et prix de journée
# Usage : Ensemble de fonctions acompagnant les DLG
# Auteur:          Jacques BRUNEL 2021-01 Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx, datetime
from srcNoestock    import DLG_Mouvements
from srcNoelite     import DB_schema
from xpy.outils     import xformat

LIMITSQL =100
CHOIX_REPAS = ['PtDej','Midi','Soir','Tous']

# Select de données  ------------------------------------------------------------------


def SqlInventaire(dlg,*args,**kwd):
    db = dlg.db

    where = ''
    if not dlg.qteZero:
        where += '(stArticles.qteStock > 0) '
    if not dlg.qteMini :
        if len(where) > 0 :
            where += 'AND '
        if dlg.saisonIx == 1:
            mini = 'stArticles.qteMini'
        else: mini = 'stArticles.qteSaison'
        where += '(stArticlesqteStock > %s) '%mini
        if len(where) > 0 :
            where = 'WHERE %s'%where

    whereMvt = "WHERE stMouvements.date <= '%s' OR (stMouvements.date IS NULL) "%dlg.date

    lstChamps = ['IDarticle', 'IDdate',
                 'qteConstat', 'qteInv','pxActInv', 'pxMoyInv',
                 'qteMvt','mttMvt',
                 'fournisseur','magasin','rayon','qteArt','qteMini','qteSaison','pxMoyArt','rations']
    lstChamps += ['qteStock','pxUnit','mttTTC']
    req = """
        SELECT  art.artArt, art.dte, 
                stInventaires.qteConstat, stInventaires.qteStock, stInventaires.prixActuel, stInventaires.prixMoyen,
                Sum(stMouvements.qte) AS qteMvt, Sum(stMouvements.qte * stMouvements.prixUnit) AS mttMvt,
                art.fournisseur, art.magasin, art.rayon, art.artQte, art.qteMini, art.qteSaison, art.prixMoyen, 
                (art.rations * art.artQte)
        
        FROM (
            (	SELECT stArticles.IDarticle AS artArt, max(if( IDdate is NULL, '2021-01-01', IDdate)) AS dte, 
                        stArticles.fournisseur, stArticles.magasin, stArticles.rayon, stArticles.qteStock AS artQte, 
                        stArticles.qteMini, stArticles.qteSaison, stArticles.prixMoyen, stArticles.dernierAchat, 
                        stArticles.rations
                FROM stArticles 
                LEFT JOIN stInventaires ON stArticles.IDarticle = stInventaires.IDarticle
                %s
                GROUP BY stArticles.IDarticle, stArticles.fournisseur, stArticles.magasin, stArticles.rayon, 
                        stArticles.qteStock, stArticles.qteMini, stArticles.qteSaison, stArticles.prixMoyen, 
                        stArticles.dernierAchat, stArticles.rations
             ) 
            AS art
        
            LEFT JOIN stInventaires ON (art.artArt = stInventaires.IDarticle) 
                                        AND (art.dte = stInventaires.IDdate)
            ) 
        LEFT JOIN stMouvements 	ON ( art.dte < stMouvements.date) 
                                    AND (art.artArt = stMouvements.IDarticle)
        %s
        GROUP BY art.artArt, art.dte, stInventaires.qteConstat, stInventaires.qteStock, stInventaires.prixActuel,
            stInventaires.prixMoyen, art.fournisseur, art.magasin, art.rayon, art.artQte, art.qteMini, art.qteSaison, 
            art.prixMoyen, art.rations;            
            """ %(where,whereMvt)

    retour = db.ExecuterReq(req, mess="UTILS_Stocks.SqlArticles Select" )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    # composition des données du tableau à partir du recordset
    Nz = xformat.Nz
    def CalculChamps(rec):
        qteMvt = Nz(rec[lstChamps.index('qteMvt')])
        mttMvt = Nz(rec[lstChamps.index('mttMvt')])
        qteInv = Nz(rec[lstChamps.index('qteInv')])
        pxActInv = Nz(rec[lstChamps.index('pxActInv')]) # prix forcé dans l'inventaire
        if pxActInv <= 0.0: pxActInv = Nz(rec[lstChamps.index('pxMoyInv')]) # prix résultant d'un calcul antérieur dans l'inventaire
        if (qteInv + qteMvt) == 0.0 : qteInv, qteMvt = (0,1)
        qteStock = Nz(rec[lstChamps.index('qteConstat')]) + Nz(qteMvt)
        pxUnit = ((qteInv * pxActInv) + mttMvt) / (qteInv + qteMvt)
        mttTTC = qteStock * pxUnit
        return (qteStock,pxUnit,mttTTC)

    lstDonnees = []
    lstCodes = dlg.dicOlv['lstCodes'] + dlg.dicOlv['lstCodesSup']
    for record in recordset:
        ligne = []
        for code in lstCodes:
            donnees = record + CalculChamps(record)
            ligne.append(donnees[lstChamps.index(code)])
        lstDonnees.append(ligne)
    return lstDonnees

def SqlMouvements(db,dParams=None):
    lstChamps = xformat.GetLstChampsTable('stMouvements',DB_schema.DB_TABLES)
    lstChamps.append('stArticles.qteStock')
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
                elif champ == 'qte' and record[ix]:
                    dMouvement[champ] = record[ix] * sensNum
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
        where = 'WHERE (obsolete IS NULL)'
        if filtreTxt and len(filtreTxt) >0:
                where += xformat.ComposeWhereFiltre(filtreTxt,lstChamps, lstColonnes = lstColonnes,lien='AND')

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
            # bufferisation avec tuple QstPmoy pour calcul des variations lors des entrées
            #dicArticle['oldQstPmoy'] = (dicArticle['qteStock',dicArticle['prixMoyen']])
            olv.buffArticles[IDarticle] =dicArticle
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

# Appel des mouvements antérieurs
def SqlMvtsAnte(**kwd):
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

# Appel des inventaires antérieurs
def SqlInvAnte(**kwd):
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
    if isinstance(analytique,(list,tuple)):
        choice = "%s %s"%(analytique[0],analytique[1])
    else:
        choice = "%s %s"%(analytique['idanalytique'],analytique['abrege'])
    return choice

# Gestion des lignes de l'olv mouvements --------------------------------------------------------------------------

def SauveMouvement(db,dlg,track):
    # --- Sauvegarde des différents éléments associés à la ligne de mouvement
    sensNum = dlg.sensNum
    if not track.valide:
        return False
    if not dlg.analytique or len(dlg.analytique.strip()) == 0:
        analytique = '00'
    else: analytique = dlg.analytique
    repas = None
    if dlg.sens == 'sorties' and hasattr(track,'repas'):
        if len(track.repas) > 0:
            repas = CHOIX_REPAS.index(track.repas)+1
    lstDonnees = [  ('date',dlg.date),
                    ('fournisseur',dlg.fournisseur),
                    ('origine',dlg.origine),
                    ('repas', repas),
                    ('IDarticle', track.IDarticle),
                    ('qte', track.qte * sensNum),
                    ('prixUnit', track.prixTTC),
                    ('IDanalytique', analytique),
                    ('ordi', dlg.ordi),
                    ('dateSaisie', dlg.today),
                    ('modifiable', 1),]

    try: IDmouvement = int(track.IDmouvement)
    except: IDmouvement = None
    MAJarticle(db,dlg,track)

    if IDmouvement :
        ret = db.ReqMAJ("stMouvements", lstDonnees, "IDmouvement", IDmouvement,mess="UTILS_Stocks.SauveLigne Modif: %d"%IDmouvement)
    else:
        ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="UTILS_Stocks.SauveLigne Insert")
        if ret == 'ok':
            track.IDmouvement = db.newID

def DelMouvement(db,olv,track):
    # --- Supprime les différents éléments associés à la ligne --
    if not track.IDmouvement in (None,0, ''):
        track.qte = 0
        MAJarticle(db, olv.lanceur, track)
        ret = db.ReqDEL("stMouvements", "IDmouvement", track.IDmouvement,affichError=True)
    return

def MAJarticle(db,dlg,track):
    # sauve dicArticle bufférisé dans ctrlOlv.bffArticles, pointé par les track.dicArticle)
    if not track.IDarticle or track.IDarticle in ('',0): return
    if not track.valide: return
    if track.qte in (None,''): return

    IDarticle = track.IDarticle
    dicArticle = track.dicArticle

    # variation des quantités saisies % antérieur
    if hasattr(track,'oldQte'):
        deltaQte = track.qte - track.oldQte
    else:
        track.oldQte = track.qte
        deltaQte = 0.0
    if dlg.sens == 'sorties':
        deltaQte = -deltaQte

    # variation du prix Unitaire saisies % antérieur
    if not hasattr(track,'prixTTC'): DLG_Mouvements.CalculeLigne(dlg,track)
    if not hasattr(track,'oldPu'):
        track.oldPu = track.prixTTC

    # Nouvelles valeurs en stock
    oldValSt = dicArticle['qteStock'] * dicArticle['prixMoyen']
    oldValMvt = track.oldQte * track.oldPu
    newValMvt = track.qte * track.prixTTC
    newValSt = oldValSt + newValMvt - oldValMvt
    dicArticle['qteStock'] += deltaQte

    # sauve dicArticle
    lstDonnees = [('qteStock', dicArticle['qteStock']), ]

    # prix moyen changé uniquement sur nouvelles entrées achetées avec prix actuel
    if 'achat' in dlg.origine:
        dicArticle['prixMoyen'] = round((newValSt / (dicArticle['qteStock'])),2)
        dicArticle['prixActuel'] = track.prixTTC
        lstDonnees += [
                    ('dernierAchat', xformat.DateFrToSql(dlg.date)),
                    ('prixMoyen', dicArticle['prixMoyen']),
                    ('prixActuel', dicArticle['prixActuel']),
                    ('ordi', dlg.ordi),
                    ('dateSaisie', dlg.today),]

    ret = db.ReqMAJ("stArticles", lstDonnees, "IDarticle", IDarticle,mess="UTILS_Stocks.MAJarticle Modif: %s"%IDarticle)
    if ret == 'ok':
        track.oldQte = track.qte
        track.qteStock = dicArticle['qteStock']
        track.oldPu = track.prixTTC

def SauveEffectif(dlg,**kwd):
    # Appelé en retour de saisie, gère l'enregistrement
    mode = kwd.pop('mode',None)
    donnees = kwd.pop('donnees',None)
    if donnees and dlg and 'lstCodesSup' in dlg.dicOlv:
        # pour aligner le nbre de données sur le nbre de colonnes de l'olv décrit dans dicOlv
        donnees += ['']*len(dlg.dicOlv['lstCodesSup'])

    db = kwd.pop('db',None)
    lstDonnees = []
    if hasattr(dlg,'date'):
        IDdate = dlg.date

    condPK = 'IDanalytique = %s' % dlg.analytique

    ixLigne = kwd.pop('ixLigne',None)
    if ixLigne != None:
        donneesOlv = dlg.ctrlOlv.lstDonnees
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
        if ret == 'ok':
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
        lstDonnees = []
        for ix in range(len(donnees)-2):
            lstDonnees.append((dicOlv['lstChamps'][ix],donnees[ix]))
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
    # retourne les effectifs dans la table stEffectifs
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

def GetPrixJours(dlg,**kwd):
    # retourne les effectifs dans la table stEffectifs
    db = kwd.get('db',dlg.db)

    # filtrage sur la date
    dtFin = xformat.DateSqlToDatetime(dlg.periode[1])
    dtDeb = xformat.DateSqlToDatetime(dlg.periode[0])
    dtFinJ1 = xformat.DecaleDateTime(dtFin,+1) # pour inclure les ptDèj du lendemain

    # filtrage sur les types de repas
    lstRepasRetenus = []
    if dlg.midi:
        lstRepasRetenus.append(2)
    if dlg.soir:
        lstRepasRetenus.append(3)
    if len(lstRepasRetenus) >0:
        lstRepasRetenus += [0,4,]
    if dlg.matin:   
        lstRepasRetenus.append(1)
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


    #lstChamps = ['date', 'codeRepas', 'IDarticle', 'qteConso', 'prixUnit']
    req = """
            SELECT  Date, repas, IDarticle, qte, prixUnit
            FROM stMouvements 
            %s
            ORDER BY stMouvements.Date DESC , stMouvements.repas
            ; """%(where)

    retour = db.ExecuterReq(req, mess='GetPrixJours')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # création de dictionnaires de données à partir du recordset
    dicLignes = {}
    # Premier passage :Cumul des couts
    for date, codeRepas, IDarticle, qteConso, prixUnit in recordset:
        # on ne retient que les repas à inclure
        if not codeRepas in lstRepasRetenus: continue
        # seuls les pt dej au delà de date fin sont pris
        if codeRepas == 1:
            # Ptit dèj: reculer d'un jour pour se rattacher au soir
            date = xformat.DecaleDateTime(date,-1)
        if date > dtFin or date < dtDeb : continue

        if not date in dicLignes.keys():
            dicLignes[date] = {'IDdate': date, 
                               'cout': {},
                               }
            # on garde le distingo par repas à cause des valeurs unitaires à calculer en final
            for code in lstRepasRetenus:
                dicLignes[date]['cout'][code] = 0.0
        dicLignes[date]['cout'][codeRepas] += round(qteConso * prixUnit,2)

    # Recherche des effectifs: ['date', 'nbMidiCli', 'nbMidiRep', 'nbSoirCli', 'nbSoirRep']
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

    # Deuxième passage: Calcul des composants de la ligne regroupée par date
    lstDonnees = []
    for date,dic in dicLignes.items():
        nbRepas = 0
        nbClients = 0
        cout = 0.0
        for code, value in dic['cout'].items():
            cout += value
        # choix du diviseur
        lstCodes = [x for x in dic['cout'].keys()]
        soir = (1 in lstCodes or 3 in lstCodes) 
        midi = (2 in lstCodes) 
        tous = (4 in lstCodes or 0 in lstCodes or None in lstCodes)
        if dlg.matin and not (soir or midi):
            soir = True
        if tous and not (soir or midi):
            midi = True
        diviseur = soir + midi
        if diviseur == 0: diviseur = 1
        if date in dicEffectifs.keys():
            dicEff = dicEffectifs[date]
            if midi:
                nbRepas += xformat.Nz(dicEff['midiRepas'])
                nbClients += xformat.Nz(dicEff['midiClients'])
            if soir:
                nbRepas += xformat.Nz(dicEff['soirRepas'])
                nbClients += xformat.Nz(dicEff['soirClients'])
        nbClients = nbClients / diviseur 
        prixRepas = cout
        prixClient = cout
        if nbRepas > 0:
            prixRepas = prixRepas / nbRepas
        if nbClients > 0:
            prixClient = prixClient / nbClients
        ligne = [   date,
                    nbRepas,
                    nbClients,
                    prixRepas,
                    prixClient,
                    cout]
        lstDonnees.append(ligne)        
    return lstDonnees


if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
