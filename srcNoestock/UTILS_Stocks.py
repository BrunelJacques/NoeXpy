#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des stocks et prix de journée
# Usage : Ensemble de fonctions acompagnant les DLG
# Auteur:          Jacques BRUNEL 2021-01 Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
from srcNoestock    import DLG_Mouvements
from srcNoelite     import DB_schema
from xpy.outils     import xformat

LIMITSQL =100
CHOIX_REPAS = ['PtDej','Midi','Soir','Tous']

# Select de données  ------------------------------------------------------------------

def SqlMouvements(db,dParams=None):
    lstChamps = xformat.GetLstChamps(DB_schema.DB_TABLES['stMouvements'])
    # Appelle les mouvements associés à un dic de choix de param et retour d'une liste de dic
    req = """   SELECT %s
                FROM stMouvements 
                WHERE ((date = '%s' )
                        AND (origine = '%s' )
                        AND (fournisseur IS NULL  OR fournisseur = '%s' )
                        AND (IDanalytique IS NULL  OR IDanalytique = '%s' ))
                ;""" % (",".join(lstChamps),dParams['date'],dParams['origine'],dParams['fournisseur'],dParams['analytique'])
    retour = db.ExecuterReq(req, mess='UTILS_Stocks.GetMouvements')
    ldMouvements = []
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            dMouvement = {}
            for ix  in range(len(lstChamps)):
                if lstChamps[ix] == 'repas' and record[ix]:
                    dMouvement[lstChamps[ix]] = CHOIX_REPAS[record[ix]]
                else:
                    dMouvement[lstChamps[ix]] = record[ix]
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

def SqlOneArticle(db,value,**kwds):
    # test de présence de l'article
    recordset = []
    if value and len(value)>0:
        req = """   SELECT IDarticle
                    FROM stArticles
                    WHERE IDarticle LIKE '%%%s%%'
                    ;""" % (value)
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
def SqlAnterieurs(**kwd):
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
    retour = db.ExecuterReq(req, mess='SqlAnterieurs')
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
    if not track.valide:
        return False
    if not dlg.analytique or len(dlg.analytique.strip()) == 0:
        dlg.analytique = ''
    repas = None
    if dlg.sens == 'sorties' and hasattr(track,'repas'):
        if len(track.repas) > 0:
            repas = CHOIX_REPAS.index(track.repas)
    lstDonnees = [  ('date',dlg.date),
                    ('fournisseur',dlg.fournisseur),
                    ('origine',dlg.origine),
                    ('repas', repas),
                    ('IDarticle', track.IDarticle),
                    ('qte', track.qte),
                    ('prixUnit', track.prixTTC),
                    ('IDanalytique', dlg.analytique),
                    ('ordi', dlg.ordi),
                    ('dateSaisie', dlg.today),
                    ('modifiable', 1),]

    try: IDmouvement = int(track.IDmouvement)
    except: IDmouvement = None
    SauveArticle(db,dlg,track)

    if IDmouvement :
        ret = db.ReqMAJ("stMouvements", lstDonnees, "IDmouvement", IDmouvement,mess="UTILS_Stocks.SauveLigne Modif: %d"%IDmouvement)
    else:
        ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="UTILS_Stocks.SauveLigne Insert")
        if ret == 'ok':
            track.IDmouvement = db.newID
  
def SauveArticle(db,dlg,track):
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
                    ('prixActuel', dicArticle['prixActuel']),]
    ret = db.ReqMAJ("stArticles", lstDonnees, "IDarticle", IDarticle,mess="UTILS_Stocks.SauveArticle Modif: %s"%IDarticle)
    if ret == 'ok':
        track.oldQte = track.qte
        track.qteStock = dicArticle['qteStock']
        track.oldPu = track.prixTTC

def DeleteLigne(db,olv,track):
    # --- Supprime les différents éléments associés à la ligne --
    if not track.IDmouvement in (None,0, ''):
        track.qte = 0
        SauveArticle(db, olv.lanceur, track)
        ret = db.ReqDEL("stMouvements", "IDmouvement", track.IDmouvement,affichError=True)
    return

def SetEffectifs(dlg,**kwd):
    # Appelé en retour de saisie, gère l'enregistrement
    mode = kwd.pop('mode',None)
    donnees = kwd.pop('donnees',None)
    if dlg and 'lstCodesSup' in dlg.dicOlv:
        # pour aligner le nbre de données sur le nbre de colonnes de l'olv décrit dans dicOlv
        donnees += ['']*len(dlg.dicOlv['lstCodesSup'])
    ixLigne = kwd.pop('ixLigne',None)
    db = kwd.pop('db',None)
    donneesOlv = dlg.ctrlOlv.lstDonnees

    lstDonnees = [('IDdate',donnees[0]),
                  ('IDanalytique',dlg.analytique),
                  ('midiRepas',donnees[1]),
                  ('midiClients', donnees[2]),
                  ('soirRepas',donnees[3]),
                  ('soirClients', donnees[4]),
                  ('prevuRepas',donnees[5]),
                  ('prevuClients', donnees[6]),
                  ]
    if mode == 'ajout':
        ret = db.ReqInsert('stEffectifs',lstDonnees=lstDonnees,mess="Insert Effectifs")
        if ret == 'ok':
            if ixLigne and ixLigne < len(donneesOlv):
                dlg.ctrlOlv.lstDonnees = donneesOlv[:ixLigne] + [donnees,] + donneesOlv[ixLigne:]
            else: dlg.ctrlOlv.lstDonnees.append(donnees)

    elif mode == 'modif':
        ret = db.ReqMAJ('stEffectifs',lstDonnees[1:],'IDdate',donnees[0],mess="MAJ Effectifs")
        if ret == 'ok':
            donneesOlv[ixLigne] = donnees

    elif mode == 'suppr':
        ret = db.ReqDEL('stEffectifs','IDdate',donnees[0],mess="Suppression Effectifs")
        if ret == 'ok':
            del donneesOlv[ixLigne]

def GetEffectifs(dlg,**kwd):
    # retourne les effectifs dans la table stEffectifs
    db = kwd.get('db',None)
    nbreFiltres = kwd.get('nbreFiltres', 0)
    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" % LIMITSQL

    where = """
                WHERE (IDdate >= '%s' AND IDdate <= '%s')"""%(dlg.periode[0],dlg.periode[1])
    if dlg.repas: where += """
                        AND ( IDanalytique = '00' )"""
    else: where += """
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
            dic['midiClients'],
            dic['soirRepas'],
            dic['soirClients'],
            dic['prevuRepas'],
            dic['prevuClients'],
            dic['IDanalytique'],
            dic['modifiable'],]
        lstDonnees.append(ligne)
    return lstDonnees


if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
