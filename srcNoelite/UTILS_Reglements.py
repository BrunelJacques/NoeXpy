#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Usage : Ensemble de fonctions acompagnant DLG_Reglements_gestion
# Auteur:          Jacques BRUNEL
# Copyright:       (c) 2020-04   Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import srcNoelite.UTILS_Historique  as nuh
import xpy.xGestion_TableauEditor   as xgte
import xpy.xGestion_TableauRecherche as xgtr
import xpy.xUTILS_SaisieParams      as xusp
from xpy.outils import xformat

SYMBOLE = "€"

def GetMatriceFamilles():
    dicBandeau = {'titre':"Recherche d'une famille",
                  'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

    # Composition de la matrice de l'OLV familles, retourne un dictionnaire

    lstChamps = ['0','familles.IDfamille','familles.adresse_intitule','individus_1.cp_resid','individus_1.ville_resid',
                 'individus.nom','individus.prenom']

    lstNomsColonnes = ["0","IDfam","désignation","cp","ville","noms","prénoms"]

    lstTypes = ['INTEGER','INTEGER','VARCHAR(80)','VARCHAR(30)','VARCHAR(100)',
                'VARCHAR(90)','VARCHAR(120)']
    lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return   {
                'listeColonnes': lstColonnes,
                'listeChamps':lstChamps,
                'listeNomsColonnes':lstNomsColonnes,
                'listeCodesColonnes':lstCodesColonnes,
                'getDonnees': GetFamilles,
                'dicBandeau': dicBandeau,
                'colonneTri': 2,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetFamilles(db,matriceOlv={}, filtre = None, limit=100):
    # ajoute les données à la matrice pour la recherche d'une famille
    where = ""
    if filtre:
        where = """WHERE familles.adresse_intitule LIKE '%%%s%%'
                        OR individus_1.ville_resid LIKE '%%%s%%'
                        OR individus.nom LIKE '%%%s%%'
                        OR individus.prenom LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,)

    lstChamps = matriceOlv['listeChamps']
    lstCodesColonnes = matriceOlv['listeCodesColonnes']

    req = """   SELECT %s 
                FROM ((familles 
                LEFT JOIN rattachements ON familles.IDfamille = rattachements.IDfamille) 
                LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu) 
                LEFT JOIN individus AS individus_1 ON familles.adresse_individu = individus_1.IDindividu
                %s
                LIMIT %d ;""" % (",".join(lstChamps),where,limit)
    retour = db.ExecuterReq(req, mess='GetFamilles' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    # composition des données du tableau à partir du recordset, regroupement par famille
    dicFamilles = {}
    # zero,IDfamille,designation,cp,ville,categ,nom,prenom
    ixID = lstCodesColonnes.index('idfam')
    for record in recordset:
        if not record[ixID] in dicFamilles.keys():
            dicFamilles[record[ixID]] = {}
            for ix in range(len(lstCodesColonnes)):
                dicFamilles[record[ixID]][lstCodesColonnes[ix]] = record[ix]
        else:
            # ajout de noms et prénoms si non encore présents
            if not record[-2] in dicFamilles[record[ixID]]['noms']:
                dicFamilles[record[ixID]]['noms'] += "," + record[-2]
            if not record[-1] in dicFamilles[record[ixID]]['prenoms']:
                dicFamilles[record[ixID]]['prenoms'] += "," + record[-1]

    lstDonnees = []
    for key, dic in dicFamilles.items():
        ligne = []
        for code in lstCodesColonnes:
            ligne.append(dic[code])
        lstDonnees.append(ligne)
    dicOlv =  matriceOlv
    dicOlv['listeDonnees']=lstDonnees
    return lstDonnees

def GetFamille(db):
    dicOlv = GetMatriceFamilles()
    dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv,db=db)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        IDfamille = dlg.GetSelection().donnees[1]
    else: IDfamille = None
    dlg.Destroy()
    return IDfamille

def GetMatriceDepots():
    dicBandeau = {'titre':"Rappel d'un depot existant",
                  'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

    # Composition de la matrice de l'OLV depots, retourne un dictionnaire

    lstChamps = ['0','IDdepot', 'depots.date', 'depots.nom',
                    'comptes_bancaires.nom', 'observations']

    lstNomsColonnes = ['0','numéro', 'date', 'nomDépôt', 'banque', 'nbre', 'total', 'détail', 'observations']

    lstTypes = ['INTEGER','INTEGER','VARCHAR(10)','VARCHAR(80)','VARCHAR(130)','VARCHAR(10)','VARCHAR(10)','VARCHAR(170)','VARCHAR(170)']
    lstCodesColonnes = [xformat.SupprimeAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return   {
                'listeColonnes': lstColonnes,
                'listeChamps':lstChamps,
                'listeNomsColonnes':lstNomsColonnes,
                'listeCodesColonnes':lstCodesColonnes,
                'getDonnees': GetDepots,
                'dicBandeau': dicBandeau,
                'colonneTri': 2,
                'sensTri' : False,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetDepots(db=None,matriceOlv={}, filtre = None, limit=100):
    # ajoute les données à la matrice pour la recherche d'un depot
    where = ""
    if filtre:
        where = """WHERE IDdepot LIKE '%%%s%%'
                        OR depots.date LIKE '%%%s%%'
                        OR depots.nom LIKE '%%%s%%'
                        OR comptes_bancaires.nom LIKE '%%%s%%'
                        OR observations LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,filtre)

    lstChamps = matriceOlv['listeChamps']
    lstCodesColonnes = matriceOlv['listeCodesColonnes']

    req = """   SELECT %s
                FROM depots
                LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = depots.IDcompte
                %s 
                ORDER BY depots.date DESC
                LIMIT %d ;""" % (",".join(lstChamps),where,limit)
    retour = db.ExecuterReq(req, mess='GetDepots' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # composition des données du tableau à partir du recordset
    dicDepots = {}
    ixID = lstCodesColonnes.index('numero')
    for record in recordset:
        if not record[ixID]: continue
        dicDepots[record[ixID]] = {}
        for ix in range(len(lstChamps)-1):
            dicDepots[record[ixID]][lstCodesColonnes[ix]] = record[ix]
        # champ observation relégué en fin
        dicDepots[record[ixID]][lstCodesColonnes[-1]] = record[-1]
        dicDepots[record[ixID]]['lstModes'] = []

    # appel des compléments d'informations sur les règlements associés au dépôt
    lstIDdepot = [x for x in dicDepots.keys()]
    recordset = ()
    if len(lstIDdepot)>0:
        where = "WHERE reglements.IDdepot IN (%s)"% str(lstIDdepot)[1:-1]
        req = """SELECT reglements.IDdepot, reglements.IDmode, modes_reglements.label,
                    SUM(reglements.montant), COUNT(reglements.IDreglement)
                    FROM reglements 
                    LEFT JOIN modes_reglements ON modes_reglements.IDmode = reglements.IDmode
                    %s                
                    GROUP BY reglements.IDdepot, reglements.IDmode, modes_reglements.label
                    ;"""%where
        retour = db.ExecuterReq(req, mess='GetDepots' )
        recordset = ()
        if retour == "ok":
            recordset = db.ResultatReq()

        # Ajout des compléments au dictionnaire
        for IDdepot, IDmode, label, somme, nombre in recordset:
            if not 'nbre' in dicDepots[IDdepot]:
                dicDepots[IDdepot]['nbre'] = 0
                dicDepots[IDdepot]['total'] = 0.0
            dicDepots[IDdepot]['nbre'] += nombre
            dicDepots[IDdepot]['total'] += somme
            dicDepots[IDdepot][IDmode] = {}
            dicDepots[IDdepot][IDmode]['nbre'] = nombre
            dicDepots[IDdepot][IDmode]['label'] = label
            dicDepots[IDdepot]['lstModes'].append(IDmode)

    # composition des données
    lstDonnees = []
    for IDdepot, dic in dicDepots.items():
        if not 'nbre' in dic.keys(): continue
        ligne = []
        dic['detail'] = ""
        for IDmode in dic['lstModes']:
            dic['detail'] += "%d %s, "%(dic[IDmode]["nbre"], dic[IDmode]["label"])
        for code in lstCodesColonnes:
            ligne.append(dic[code])
        lstDonnees.append(ligne)
    dicOlv =  matriceOlv
    dicOlv['listeDonnees']=lstDonnees
    return lstDonnees

def GetBanquesNne(db,where = 'code_nne IS NOT NULL'):
    ldBanques = []
    lstChamps = ['IDcompte','nom','defaut','code_nne','iban','bic']
    req = """   SELECT %s
                FROM comptes_bancaires
                WHERE %s
                """ % (",".join(lstChamps),where)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetBanquesNne' )
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            wx.MessageBox("Aucun banque n'a de compte destination (code Nne) paramétré")
    for record in recordset:
        dicBanque = {}
        for ix in range(len(lstChamps)):
            dicBanque[lstChamps[ix]] = record[ix]
        ldBanques.append(dicBanque)
    return ldBanques

def GetModesReglements(db):
    if db.echec == 1:
        wx.MessageBox("ECHEC accès Noethys!\n\nabandon...")
        return wx.ID_ABORT
    ldModesRegls = []
    lstChamps = ['IDmode','label','numero_piece','nbre_chiffres','type_comptable','code_compta']
    req = """   SELECT %s
                FROM modes_reglements
                ;"""%",".join(lstChamps)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetModesReglements' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            wx.MessageBox("Aucun mode de règlements")
    else: return wx.ID_ABORT
    for record in recordset:
        dicModeRegl = {}
        for ix in range(len(lstChamps)):
            dicModeRegl[lstChamps[ix]] = record[ix]
        ldModesRegls.append(dicModeRegl)
    return ldModesRegls

def GetDesignationFamille(db,IDfamille):
    if not isinstance(IDfamille,int): return ""
    req = """   SELECT adresse_intitule
                FROM familles
                WHERE IDfamille = %d
                """ % (IDfamille)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetDesignationFamille' )
    recordset = []
    if retour == "ok":
        recordset = db.ResultatReq()
    designation = ''
    for record in recordset:
        designation = record[0]
    return designation

def GetPayeurs(db,IDfamille):
    ldPayeurs = []
    lstChamps = ['IDpayeur','IDcompte_payeur','nom']
    req = """   SELECT %s
                FROM payeurs
                WHERE IDcompte_payeur = %d and nom IS NOT NULL
                """ % (",".join(lstChamps),IDfamille)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetPayeurs')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    for record in recordset:
        dicPayeur = {}
        for ix in range(len(lstChamps)):
            dicPayeur[lstChamps[ix]] = record[ix]
        ldPayeurs.append(dicPayeur)
    return ldPayeurs

def SetPayeur(db,IDcompte_payeur,nom):
    listeDonnees = [('IDcompte_payeur',IDcompte_payeur),
                    ('nom',nom)]
    db.ReqInsert("payeurs", lstDonnees=listeDonnees,mess="UTILS_Reglements.SetPayeur")
    ID = db.newID
    return ID

def GetReglements(db,IDdepot):
    listeDonnees = []
    #            IDreglement,date,IDfamille,designation,payeur,labelmode,numero,libelle,montant,IDpiece in recordset
    lstChamps = ['reglements.IDreglement', 'reglements.date', 'reglements.IDcompte_payeur', 'familles.adresse_intitule',
                 'payeurs.nom', 'modes_reglements.label', 'reglements.numero_piece', 'reglements.observations', 
                 'reglements.montant', 'reglements.IDpiece','prestations.compta','reglements.compta']

    req = """   SELECT %s
                FROM ((( reglements 
                        LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode) 
                        LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur) 
                        LEFT JOIN familles ON reglements.IDcompte_payeur = familles.IDfamille)
                        LEFT JOIN prestations ON reglements.IDpiece = prestations.IDprestation
                WHERE ((reglements.IDdepot = %d))
                ;""" % (",".join(lstChamps),IDdepot)

    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetReglements')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    for IDreglement,date,IDfamille,designation,payeur,labelmode,numero,libelle,montant,IDpiece,prestcpta,compta in recordset:
        creer = "N"
        # la reprise force la non création car déjà potentiellement fait. IDpiece contient l'ID de la prestation créée
        lstDonneesTrack = [IDreglement, date, IDfamille, designation,payeur, labelmode, numero, "", "", libelle,
                           montant,creer,IDpiece,prestcpta,compta]
        listeDonnees.append(lstDonneesTrack)
    return listeDonnees

def GetNewIDreglement(db,lstID):
    # Recherche le prochain ID reglement après ceux de la base et éventuellement déjà dans la liste ID préaffectés
    req = """SELECT MAX(IDreglement) 
            FROM reglements;"""
    db.ExecuterReq(req)
    recordset = db.ResultatReq()
    ID = recordset[0][0] + 1
    while ID in lstID:
        ID += 1
    return ID

def ValideLigne(db,track):
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"

    # vérification des éléments saisis
    if not len(GetDesignationFamille(db,track.IDfamille)) > 0:
        track.messageRefus += "La famille n'est pas identifiée\n"

    # montant null
    try:
        track.montant = float(track.montant)
    except:
        track.montant = None
    if not track.montant or track.montant == 0.0:
        track.messageRefus += "Le montant est à zéro\n"

    # IDreglement manquant
    if track.IDreglement in (None,0) :
        track.messageRefus += "L'ID reglement n'est pas été déterminé à l'entrée du montant\n"

    # Date
    if not track.date or not isinstance(track.date,(wx.DateTime,datetime.date)):
        track.messageRefus += "Vous devez obligatoirement saisir une date d'émission du règlement !\n"

    # Mode
    if not track.mode or len(track.mode) == 0:
        track.messageRefus += "Vous devez obligatoirement sélectionner un mode de règlement !\n"

    # Numero de piece
    if track.mode[:3].upper() == 'CHQ':
        if not track.numero or len(track.numero)<4:
            track.messageRefus += "Vous devez saisir un numéro de chèque 4 chiffres mini!\n"
        # libelle pour chèques
        if track.libelle == '':
            track.messageRefus += "Veuillez saisir la banque émettrice du chèque dans le libellé !\n"

    # Payeur
    if track.payeur == None:
        track.messageRefus += "Vous devez obligatoirement sélectionner un payeur dans la liste !\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.valide = False
    else: track.messageRefus = ""
    return

def SetPrestation(track,db):
    # --- Sauvegarde de la prestation ---
    listeDonnees = [
        ("date", xformat.DatetimeToStr(datetime.date.today(),iso=True)),
        ("categorie", track.nature),
        ("label", track.libelle),
        ("montant_initial", track.montant),
        ("montant", track.montant),
        ("IDcompte_payeur", track.IDfamille),
        ("code_compta", track.article),
        ("IDfamille", track.IDfamille),
        ("IDindividu", 0),
    ]

    if (not hasattr(track,"IDpiece")) or (not track.IDpiece):
        ret = db.ReqInsert("prestations",lstDonnees= listeDonnees, mess="UTILS_Reglements.SetPrestation",)
        IDcategorie = 6
        categorie = ("Saisie")
        if ret == 'ok':
           track.IDpiece = db.newID
    else:
        ret = db.ReqMAJ("prestations", listeDonnees, "IDprestation", track.IDpiece)
        IDcategorie = 7
        categorie = "Modification"

    # mise à jour du règlement sur son numéro de pièce (ID de la prestation
    listeDonnees = [("IDpiece",track.IDpiece)]
    ret = db.ReqMAJ("reglements", listeDonnees, "IDreglement", track.IDreglement)

    # --- Mémorise l'action dans l'historique ---
    if ret == 'ok':
        texteMode = track.mode
        montant = u"%.2f %s" % (track.montant, SYMBOLE)
        if not track.IDpiece: IDprest = 0
        else: IDprest = track.IDpiece
        nuh.InsertActions([{
            "IDfamille": track.IDfamille,
            "IDcategorie": IDcategorie,
            "action": "Noelite %s de prestation associée regl ID%d : %s en %s "%(categorie, IDprest,
                                                                                 montant, track.libelle),
            },],db=db)
    return True

def DelPrestation(track,db):
    ret = db.ReqDEL("prestations", "IDprestation", track.IDpiece)
    IDcategorie = 8
    categorie = "Suppression"
    # --- Mémorise l'action dans l'historique ---
    if ret == 'ok':
        # mise à jour du règlement sur son numéro de pièce (ID de la prestation
        listeDonnees = [("IDpiece", None)]
        db.ReqMAJ("reglements", listeDonnees, "IDreglement", track.IDreglement)

        montant = u"%.2f %s" % (track.montant, SYMBOLE)
        if not track.IDpiece: IDprest = 0
        else: IDprest = track.IDpiece
        nuh.InsertActions([{
            "IDfamille": track.IDfamille,
            "IDcategorie": IDcategorie,
            "action": "Noelite %s de prestation associée regl ID%d : %s en %s "%(categorie, IDprest,
                                                                                 montant, track.libelle),
            }, ],db=db)
        track.IDpiece = None
    return True

def SauveLigne(db,dlg,track):
    if not track.valide:
        return False
    if not track.montant or not isinstance(track.montant,float):
        return False
    # --- Sauvegarde des différents éléments associés à la ligne ---
    # gestion de l'ID depot si withDepot
    if not hasattr(dlg,"IDdepot") and dlg.withDepot:
        dlg.IDdepot = SetDepot(dlg,db)

    # gestion du réglement
    ret = SetReglement(dlg,track,db)

    if not hasattr(track,'IDpiece'): track.IDpiece = None
    # gestion de la prestation associée
    if ret and track.creer:
        ret = SetPrestation(track,db)
    elif ret and track.IDpiece:
        ret = DelPrestation(track,db)

    # Vérif Prestation
    message = ''
    if not hasattr(track,'IDpiece'): track.IDpiece = None
    if track.creer == True  and not track.IDpiece:
        message = "La prestation associée n'est pas créée!\n"
    if track.creer == False and track.IDpiece:
        message = "La prestation associée au règlement n'est pas supprimée!\n"
    if len(message)>0: wx.MessageBox(message)
    return ret

def DeleteLigne(db,track):
    # --- Supprime les différents éléments associés à la ligne ---
    # si le montant est à zéro il n'y a pas eu d'enregistrements
    if track.montant != 0.0:
        # suppression  du réglement et des ventilations
        ret = db.ReqDEL("reglements", "IDreglement", track.IDreglement,affichError=False)
        if track.valide:
            # --- Mémorise l'action dans l'historique ---
            if ret == 'ok':
                IDcategorie = 8
                categorie = "Suppression"
                nuh.InsertActions([{
                    "IDfamille": track.IDfamille,
                    "IDcategorie": IDcategorie,
                    "action": "Noelite %s du règlement ID%d"%(categorie, track.IDreglement),
                    },],db=db)

        db.ReqDEL("ventilation", "IDreglement", track.IDreglement)

        # gestion de la prestation associée
        if ret == 'ok' and track.IDpiece:
            DelPrestation(track, db)
    return

def SetReglement(dlg,track,db):
    # --- Sauvegarde du règlement ---
    IDmode = dlg.dicModesRegl[track.mode]['IDmode']
    IDpayeur = None
    if not hasattr(dlg.pnlOlv,'ldPayeurs'):
        dlg.pnlOlv.ldPayeurs = GetPayeurs(db,track.IDfamille)
    for dicPayeur in dlg.pnlOlv.ldPayeurs:
        if track.payeur in dicPayeur['nom']:
            IDpayeur = dicPayeur['IDpayeur']
            break
    if not IDpayeur:
        IDpayeur = SetPayeur(db,track.IDfamille,track.payeur)

    listeDonnees = [
        ("IDreglement", track.IDreglement),
        ("IDcompte_payeur", track.IDfamille),
        ("date", xformat.DatetimeToStr(track.date,iso=True)),
        ("IDmode", IDmode),
        ("numero_piece", track.numero),
        ("montant", track.montant),
        ("IDpayeur", IDpayeur),
        ("observations", track.libelle),
        ("IDcompte", dlg.GetIDbanque()),
        ("date_saisie", xformat.DatetimeToStr(datetime.date.today(),iso=True)),
        ("IDutilisateur", dlg.IDutilisateur),
    ]
    if dlg.withDepot:
        listeDonnees.append(("IDdepot",dlg.IDdepot))
    attente = 0
    if hasattr(track,'differe'):
        listeDonnees.append(("date_differe", xformat.DatetimeToStr(track.differe,iso=True)))
        if len(track.differe) > 0:
            attente = 1
    listeDonnees.append(("encaissement_attente",attente))

    if track.IDreglement in dlg.pnlOlv.lstNewReglements:
        nouveauReglement = True
        ret = db.ReqInsert("reglements",lstDonnees= listeDonnees, mess="UTILS_Reglements.SetReglement")
        dlg.pnlOlv.lstNewReglements.remove(track.IDreglement)
    else:
        nouveauReglement = False
        ret = db.ReqMAJ("reglements", listeDonnees, "IDreglement", track.IDreglement)

    # --- Mémorise l'action dans l'historique ---
    if ret == 'ok':
        if nouveauReglement == True:
            IDcategorie = 6
            categorie = ("Saisie")
        else:
            IDcategorie = 7
            categorie = "Modification"
        texteMode = track.mode
        if track.numero != "":
            texteNumpiece = u" n°%s" % track.numero
        else:
            texteNumpiece = u""
        if texteNumpiece == "":
            texteDetail = u""
        else:
            texteDetail = u"- %s - " % (texteNumpiece)

        montant = u"%.2f %s" % (track.montant, SYMBOLE)
        textePayeur = track.payeur
        nuh.InsertActions([{
            "IDfamille": track.IDfamille,
            "IDcategorie": IDcategorie,
            "action": "Noelite %s du règlement ID%d : %s en %s %spayé par %s" % (
            categorie, track.IDreglement, montant, texteMode, texteDetail, textePayeur),
        }, ],db=db)
    return True

class Article(object):
    def __init__(self,db,nature):
        self.nature = nature
        self.db = db

    def GetMatriceArticles(self):
        dicBandeau = {'titre':"Recherche d'un article prestation",
                      'texte':"l'article choisi détermine le code du plan comptable de la prestation générée",
                      'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

        # Composition de la matrice de l'OLV articles, retourne un dictionnaire

        lstChamps = ['0','matPlanComptable.pctCompte','matPlanComptable.pctCodeComptable','matPlanComptable.pctLibelle',]

        lstNomsColonnes = ["0","compte","code","libellé"]

        lstTypes = ['INTEGER','VARCHAR(8)','VARCHAR(16)','VARCHAR(100)']
        lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
        lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
        lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
        lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return   {
                    'listeColonnes': lstColonnes,
                    'listeChamps':lstChamps,
                    'listeNomsColonnes':lstNomsColonnes,
                    'listeCodesColonnes':lstCodesColonnes,
                    'getDonnees': self.GetArticles,
                    'dicBandeau': dicBandeau,
                    'colonneTri': 2,
                    'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                    'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                    }

    def GetArticles(self,matriceOlv,filtre = None):
        # le pointeur de cette fonction est dans le dic généré par GetMatriceArticles,

        nature = self.nature
        if nature: nature = nature.lower()
        if nature == 'don':
            rad1 = 'DON'
            rad2 = 'PRET'
        else:
            rad1 = 'RBT'
            rad2 = 'DEB'

        where = """ ((pctLibelle Like '%s%%')
                        OR (pctLibelle Like '%s%%')
                        OR (pctCodeComptable Like '%s%%')
                        OR (pctCodeComptable Like '%s%%'))
                """%(rad1,rad2,rad1,rad2)
        if filtre:
            where += """AND (pctLibelle LIKE '%%%s%%'
                            OR pctCodeComptable LIKE '%%%s%%'
                            OR pctCompte LIKE '%%%s%%')"""%(filtre,filtre,filtre)

        lstChamps = matriceOlv['listeChamps']
        lstCodesColonnes = matriceOlv['listeCodesColonnes']
        req = """SELECT %s
                FROM matPlanComptable
                WHERE %s;
                """ % (",".join(lstChamps),where)
        retour = self.db.ExecuterReq(req, mess='UTILS_Reglements.GetArticles' )
        recordset = ()
        if retour == "ok":
            recordset = self.db.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Aucun article paramétré contenant '%s' ou '%s' dans le code ou le libellé"%(rad1,rad2))

        # composition des données du tableau à partir du recordset, regroupement par article
        dicArticles = {}
        ixID = lstCodesColonnes.index('code')
        for record in recordset:
            if not record[ixID] in dicArticles.keys():
                dicArticles[record[ixID]] = {}
                for ix in range(len(lstCodesColonnes)):
                    dicArticles[record[ixID]][lstCodesColonnes[ix]] = record[ix]
            else:
                # ajout de noms et prénoms si non encore présents
                if not record[-2] in dicArticles[record[ixID]]['noms']:
                    dicArticles[record[ixID]]['noms'] += "," + record[-2]
                if not record[-1] in dicArticles[record[ixID]]['prenoms']:
                    dicArticles[record[ixID]]['prenoms'] += "," + record[-1]

        lstDonnees = []
        for key, dic in dicArticles.items():
            ligne = []
            for code in lstCodesColonnes:
                ligne.append(dic[code])
            lstDonnees.append(ligne)
        dicOlv =  matriceOlv
        dicOlv['listeDonnees']=lstDonnees
        return lstDonnees

    def GetArticle(self,db=None):
        dicOlv = self.GetMatriceArticles()
        dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv,db=db)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            article = dlg.GetSelection().donnees[1]
        else: article = None
        dlg.Destroy()
        return article

def SetDepot(dlg,db):
    # cas d'un nouveau depot à créer, retourne l'IDdepot
    IDdepot = None
    listeDonnees = [
        ("date", xformat.DatetimeToStr(datetime.date.today(), iso=True)),
        ("nom", "Saisie règlements via Noelite"),
        ("IDcompte", dlg.GetIDbanque()),
    ]
    if not hasattr(dlg, "IDdepot"):
        ret = db.ReqInsert("depots", lstDonnees=listeDonnees, mess="UTILS_Reglements.SetDepot", )
        if ret == 'ok':
            IDdepot = db.newID

    # affichage de l'IDdepot créé
    dlg.pnlParams.ctrlRef.SetValue(str(IDdepot))
    return IDdepot

def GetDepot(db=None):
    # appel des dépots existants pour reprise d'un dépot
    dicDepot = {}
    dicOlv = GetMatriceDepots()
    dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv,db=db)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        donnees = dlg.GetSelection().donnees
        for ix in range(len(donnees)):
            dicDepot[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
    dlg.Destroy()
    return dicDepot

#------------------------ Lanceur de test  -------------------------------------------
def OnClick(event):
    print("on click")
    #mydialog.Close()

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #print(GetBanquesNne())
    #print(GetFamille(None))
    #print(GetPayeurs(1))
    #art = Article('debour')
    #print(art.GetArticle())
    print(GetDepot())
    app.MainLoop()