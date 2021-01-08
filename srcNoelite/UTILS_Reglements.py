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
LIMITSQL =100

def GetMatriceFamilles():
    dicBandeau = {'titre':"Recherche d'une famille",
                  'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

    # Composition de la matrice de l'OLV familles, retourne un dictionnaire

    lstChamps = ['0','familles.IDfamille','familles.adresse_intitule','individus_1.cp_resid','individus_1.ville_resid',
                 'individus.nom','individus.prenom']

    lstNomsColonnes = ["0","IDfam","désignation","cp","ville","noms","prénoms"]

    lstTypes = ['INTEGER','INTEGER','VARCHAR(80)','VARCHAR(10)','VARCHAR(100)',
                'VARCHAR(90)','VARCHAR(120)']
    lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return   {
                'lstColonnes': lstColonnes,
                'lstChamps':lstChamps,
                'listeNomsColonnes':lstNomsColonnes,
                'listeCodesColonnes':lstCodesColonnes,
                'getDonnees': GetFamilles,
                'size':(800,400),
                'dicBandeau': dicBandeau,
                'sortColumnIndex': 2,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetFamilles(db,dicOlv={}, **kwd):
    # ajoute les données à la matrice pour la recherche d'une famille

    # appel des données à afficher
    filtreTxt = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" %LIMITSQL

    where = ""
    if filtreTxt and len(filtreTxt) > 0:
        where = """WHERE familles.adresse_intitule LIKE '%%%s%%'
                        OR individus_1.ville_resid LIKE '%%%s%%'
                        OR individus.nom LIKE '%%%s%%'
                        OR individus.prenom LIKE '%%%s%%' """%(filtreTxt,filtreTxt,filtreTxt,filtreTxt,)

    lstChamps = dicOlv['lstChamps']
    lstCodesColonnes = [x.valueGetter for x in dicOlv['lstColonnes']]

    req = """   SELECT %s 
                FROM ((familles 
                LEFT JOIN rattachements ON familles.IDfamille = rattachements.IDfamille) 
                LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu) 
                LEFT JOIN individus AS individus_1 ON familles.adresse_individu = individus_1.IDindividu
                %s
                %s ;""" % (",".join(lstChamps),where,limit)

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
    dicOlv =  dicOlv
    dicOlv['lstDonnees']=lstDonnees
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

    lstTypes = ['INTEGER','INTEGER','DATE','VARCHAR(80)','VARCHAR(130)','VARCHAR(10)','VARCHAR(10)','VARCHAR(170)','VARCHAR(170)']
    lstCodesColonnes = [xformat.SupprimeAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return   {
                'lstColonnes': lstColonnes,
                'lstChamps':lstChamps,
                'listeNomsColonnes':lstNomsColonnes,
                'listeCodesColonnes':lstCodesColonnes,
                'getDonnees': GetDepots,
                'dicBandeau': dicBandeau,
                'sortColumnIndex': 2,
                'sensTri' : False,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'size':(900, 400)                }

def GetDepots(db=None,dicOlv={}, limit=100,**kwd):
    # ajoute les données à la matrice pour la recherche d'un depot
    filtre = kwd.pop('filtreTxt', '')
    nbreFiltres = kwd.pop('nbreFiltres', 0)

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" %LIMITSQL


    where = ""
    if filtre:
        where = """WHERE IDdepot LIKE '%%%s%%'
                        OR depots.date LIKE '%%%s%%'
                        OR depots.nom LIKE '%%%s%%'
                        OR comptes_bancaires.nom LIKE '%%%s%%'
                        OR observations LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,filtre)

    lstChamps = dicOlv['lstChamps']
    lstCodesColonnes = [x.valueGetter for x in dicOlv['lstColonnes']]

    req = """   SELECT %s
                FROM depots
                LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = depots.IDcompte
                %s 
                ORDER BY depots.date DESC
                %s ;""" % (",".join(lstChamps),where,limit)
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
    dicOlv =  dicOlv
    dicOlv['lstDonnees']=lstDonnees
    return lstDonnees

def GetBanquesNne(db,where = 'code_nne IS NOT NULL',**kwd):
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

def GetModesReglements(db,**kwd):
    if db.echec == 1:
        wx.MessageBox("ECHEC accès Noethys!\n\nabandon...")
        return wx.ID_ABORT
    ddModesRegls = {}
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
        ddModesRegls[dicModeRegl['IDmode']] = dicModeRegl
    return ddModesRegls

def GetEmetteurs(db,lstModes,**kwd):
    if db.echec == 1:
        wx.MessageBox("ECHEC accès Noethys!\n\nabandon...")
        return wx.ID_ABORT
    dlEmetteurs = {}
    dlIDemetteurs = {}
    
    for mode in lstModes:
        dlEmetteurs[mode] = []
        dlIDemetteurs[mode] = []
    lstChamps = ['IDemetteur','IDmode','nom']
    modes = [str(x) for x in lstModes]
    req = """   SELECT %s
                FROM emetteurs
                WHERE IDmode IN (%s)
                ;"""%(",".join(lstChamps),",".join(modes))
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetEmetteurs' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    else: return wx.ID_ABORT
    for IDemetteur,IDmode,nom in recordset:
        dlEmetteurs[IDmode].append(nom)
        dlIDemetteurs[IDmode].append(IDemetteur)
    return dlEmetteurs, dlIDemetteurs

def GetDesignationFamille(db,IDfamille,**kwd):
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

def GetPayeurs(db,IDfamille,**kwd):
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

def SetPayeurs(pnl,track):
    pnl.ldPayeurs = GetPayeurs(pnl.parent.db, track.IDfamille)
    payeurs = [x['nom'] for x in pnl.ldPayeurs]
    if len(payeurs) == 0: payeurs.append(track.designation)
    ix = 0
    if track.payeur in payeurs:
        ix = payeurs.index(track.payeur)
    track.payeur = payeurs[ix]
    pnl.ctrlOlv.dicChoices[pnl.ctrlOlv.lstCodesColonnes.index('payeur')] = payeurs

def SetPayeur(db,IDcompte_payeur,nom,**kwd):
    lstDonnees = [('IDcompte_payeur',IDcompte_payeur),
                    ('nom',nom)]
    db.ReqInsert("payeurs", lstDonnees=lstDonnees,mess="UTILS_Reglements.SetPayeur")
    ID = db.newID
    return ID

def TransposeDonnees(dlg,recordset,lstCodesChamps,lstCodesDonnees):
    # ajustement des choix possibles selon le contenu du règlement et de la prestation associée
    ixnat = lstCodesDonnees.index('nature')
    ixdat = lstCodesDonnees.index('date')
    ixmode = lstCodesDonnees.index('mode')
    ixcreer = lstCodesDonnees.index('creer')
    ixcompte = lstCodesDonnees.index('compte')

    # les derniers champs ne sont pas dans la grille à afficher, mais tous dans les données
    lstDonnees = []
    # chaque ligne du recordset crée une ligne de données
    for record in recordset:
        donnees = [None, ] * len(lstCodesDonnees)

        # alimente tous les champs de données présents dans le recordset en l'état
        for ixdon in range(len(lstCodesDonnees)):
            if lstCodesDonnees[ixdon] in lstCodesChamps:
                ixch = lstCodesChamps.index(lstCodesDonnees[ixdon])
                donnees[ixdon]= record[ixch]

        # recherche du mode de règlement
        IDmode = record[lstCodesChamps.index('IDmode')]
        donnees[ixmode] = dlg.ddModesRegl[IDmode]['choice']

        # détermination de la nature 'Règlement','Acompte','Don','Debour','Libre'
        compte = record[lstCodesChamps.index('prestcompte')]
        nature = record[lstCodesChamps.index('prestcateg')]
        nbVentil = record[lstCodesChamps.index('nbventil')]
        if nature and nature.lower() == 'don':
            donnees[ixnat] = 'Don'
            donnees[ixcompte] = compte
            creer = 'O'
        elif nature and nature.lower() == 'donsscerfa':
            donnees[ixnat] = 'DonSsCerfa'
            donnees[ixcompte] = compte
            creer = 'O'
        elif nature and nature.lower() == 'debour':
            donnees[ixnat] = 'Debour'
            donnees[ixcompte] = compte
            creer = 'O'
        elif nbVentil and nbVentil > 0:
            donnees[ixnat] = 'Règlement'
            creer = 'N'
        else:
            donnees[ixnat] = 'Acompte'
            creer = 'N'
        donnees[ixcreer] = creer

        # date remise en format français
        donnees[ixdat] = xformat.DateSqlToDatetime(donnees[ixdat])
        lstDonnees.append(donnees)
    return lstDonnees

def GetReglements(dlg,IDdepot):
    # Appelle les règlements associés à un dépôt
    db = dlg.db
    lstChamps = ['reglements.IDreglement','reglements.date','reglements.IDcompte_payeur','familles.adresse_intitule',
            'payeurs.nom','reglements.IDmode','emetteurs.nom','reglements.numero_piece','reglements.observations',
            'reglements.montant','Null','reglements.IDpiece','prestations.categorie','prestations.code_compta',
            'prestations.compta','reglements.compta', 'COUNT(ventilation.IDventilation)']
    
    lstCodesChamps = ['IDreglement','date','IDfamille','designation',
                      'payeur','IDmode','emetteur','numero','libelle',
                      'montant','creer','IDprestation','prestcateg','prestcompte',
                      'prestcpta','reglcompta','nbventil']

    #            IDreglement,date,IDfamille,designation,payeur,labelmode,numero,libelle,montant,IDpiece in recordset
    req = """   SELECT %s
                FROM (((( reglements 
                        LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur) 
                        LEFT JOIN emetteurs ON reglements.IDemetteur = emetteurs.IDemetteur) 
                        LEFT JOIN familles ON reglements.IDcompte_payeur = familles.IDfamille)
                        LEFT JOIN prestations ON reglements.IDpiece = prestations.IDprestation)
                        LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement
                WHERE ((reglements.IDdepot = %d))
                GROUP BY %s
                ;""" % (",".join(lstChamps),IDdepot,",".join(lstChamps[:-1]))

    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetReglements')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    lstCodesDonnees = dlg.ctrlOlv.lstCodesColonnes + dlg.ctrlOlv.lstCodesSup

    return TransposeDonnees(dlg,recordset,lstCodesChamps,lstCodesDonnees)

def GetNewIDreglement(db,lstID,**kwd):
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
    if  track.mode and track.mode[:3].upper() == 'CHQ':
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
    if not track.nature.lower() in ('don','donsscerfa','debour'):
        raise Exception("UTILS_Reglements.SetPrestation ni don ni debour!!")
    lstDonnees = [
        ("date", xformat.DatetimeToStr(datetime.date.today(),iso=True)),
        ("categorie", track.nature),
        ("label", track.libelle),
        ("montant_initial", track.montant),
        ("montant", track.montant),
        ("IDcompte_payeur", track.IDfamille),
        ("code_compta", track.compte),
        ("IDfamille", track.IDfamille),
        ("IDindividu", 0),
    ]

    if (not hasattr(track,"IDprestation")) or (not track.IDprestation):
        ret = db.ReqInsert("prestations",lstDonnees= lstDonnees, mess="UTILS_Reglements.SetPrestation",)
        IDcategorie = 6
        categorie = ("Saisie")
        if ret == 'ok':
           track.IDprestation = db.newID
    else:
        ret = db.ReqMAJ("prestations", lstDonnees, "IDprestation", track.IDprestation)
        IDcategorie = 7
        categorie = "Modification"
    IDprestation = track.IDprestation

    # supprime les ventilations du règlement
    ret = db.ReqDEL("ventilation","IDreglement",track.IDreglement)

    # création d'une ventilation
    lstDonnees = [('IDprestation',IDprestation),
                  ('IDreglement',track.IDreglement),
                  ('montant',track.montant),
                  ('IDcompte_payeur',track.IDfamille)]
    ret = db.ReqInsert("ventilation", lstDonnees=lstDonnees, mess="UTILS_Reglements.SetPrestation.ventilation", )

    # mise à jour du règlement sur son numéro de pièce (ID de la prestation
    lstDonnees = [("IDpiece",IDprestation)]
    ret = db.ReqMAJ("reglements", lstDonnees, "IDreglement", track.IDreglement)

    # --- Mémorise l'action dans l'historique ---
    if ret == 'ok':
        texteMode = track.mode
        montant = u"%.2f %s" % (track.montant, SYMBOLE)
        if not IDprestation: IDprest = 0
        else: IDprest = IDprestation
        nuh.InsertActions([{
            "IDfamille": track.IDfamille,
            "IDcategorie": IDcategorie,
            "action": "Noelite %s de prestation associée regl ID%d : %s en %s "%(categorie, IDprest,
                                                                                 montant, track.libelle),
            },],db=db)
    return IDprestation

def DelPrestation(track,db,idPrest=None):
    # supprime une prestation et ses ventilations
    if not idPrest:
        idPrest = track.IDprestation
    if not idPrest: return False
    ret = db.ReqDEL("prestations", "IDprestation", idPrest)
    db.ReqDEL('ventilation','IDprestation',idPrest,afficheError=False)
    IDcategorie = 8
    categorie = "Suppression"
    # mise à jour du règlement sur son numéro de pièce (ID de la prestation) et historisation
    if ret == 'ok':
        lstDonnees = [("IDprestation", None)]
        db.ReqMAJ("reglements", lstDonnees, "IDreglement", track.IDreglement)
        track.IDprestation = None
        # --- Mémorise l'action dans l'historique ---
        montant = u"%.2f %s" % (track.montant, SYMBOLE)
        if not track.IDprestation: IDprest = 0
        else: IDprest = track.IDprestation
        nuh.InsertActions([{
            "IDfamille": track.IDfamille,
            "IDcategorie": IDcategorie,
            "action": "Noelite %s de prestation associée regl ID%d : %s en %s "%(categorie, IDprest,
                                                                                 montant, track.libelle),
            }, ],db=db)
    return True

def SauveLigne(db,dlg,track):
    # --- Sauvegarde des différents éléments associés à la ligne ---
    if not track.valide:
        return False
    if not track.montant or not isinstance(track.montant,float):
        return False

    # gestion de l'ID depot si withDepot
    if not hasattr(dlg,"IDdepot") and dlg.withDepot:
        dlg.IDdepot = SetDepot(dlg,db)
    elif dlg.withDepot:
        dlg.IDdepot = dlg.pnlParams.ctrlRef.GetValue()
        MajDepot(dlg,db,dlg.IDdepot)

    # annulations des prestations associées antérieurement et de leurs ventilations
    ixnat = dlg.ctrlOlv.lstCodesColonnes.index('nature')
    ixprest = dlg.ctrlOlv.lstCodesColonnes.index('IDprestation')
    if track.oldDonnees[ixnat] and track.oldDonnees[ixnat].lower() in ('don','donsscerfa','debour'):
        DelPrestation(track, db,idPrest=track.oldDonnees[ixprest])

    # création  de la prestation associée et sa ventilation
    if track.nature and track.nature.lower() in ('don','donsscerfa','debour'):
        IDprestation = SetPrestation(track,db)
    else:
        IDprestation = None
    track.donnees[ixprest] = IDprestation
    track.IDprestation = IDprestation

    # Vérif Prestation
    message = ''
    if track.creer == True  and not IDprestation:
        message = "La prestation associée n'est pas créée!\n"
    if track.creer == False and IDprestation:
        message = "La prestation associée au règlement n'est pas supprimée!\n"
    if len(message)>0: wx.MessageBox(message,"UTIL_Reglements.SauveLigne.verif")

    # gestion du réglement insertion ou modif
    ret = SetReglement(dlg,track,db)

    # stockage pour les prochaines modifs
    track.oldDonnees = track.donnees

    return ret

def DeleteLigne(db,track):
    # --- Supprime les différents éléments associés à la ligne ---
    if not track.IDreglement in (0, ''):
        # suppression  du réglement et des ventilations
        ret = db.ReqDEL("reglements", "IDreglement", track.IDreglement,affichError=True)
        if hasattr(track,'valide') and track.valide:
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
        if ret == 'ok' and track.IDprestation:
            DelPrestation(track, db)
    return

def SetReglement(dlg,track,db):
    # --- Sauvegarde du règlement ---
    IDemetteur = None
    IDpayeur = None
    if not hasattr(track,'IDprestation'):track.IDprestation = None

    # transposition du payeur en son ID
    if not hasattr(dlg.pnlOlv,'ldPayeurs'):
        dlg.pnlOlv.ldPayeurs = GetPayeurs(db,track.IDfamille)
    for dicPayeur in dlg.pnlOlv.ldPayeurs:
        if track.payeur in dicPayeur['nom']:
            IDpayeur = dicPayeur['IDpayeur']
            break
    if not IDpayeur:
        IDpayeur = SetPayeur(db,track.IDfamille,track.payeur)
        dlg.pnlOlv.ldPayeurs = GetPayeurs(db,track.IDfamille)

    IDmode = dlg.dicModesChoices[track.mode]['IDmode']

    # transposition de l'émetteur en son ID
    lstEmetteurs = dlg.dlEmetteurs[IDmode]
    if len(lstEmetteurs) >= 0 and track.emetteur and track.emetteur in lstEmetteurs:
        IDemetteur = dlg.dlIDemetteurs[IDmode][lstEmetteurs.index(track.emetteur)]
    else:
        track.emetteur = None
        ixem = dlg.ctrlOlv.lstCodesColonnes.index('emetteur')
        track.donnees[ixem]
    if not track.libelle: track.libelle = ""
    if not track.numero: track.numero = ""

    lstDonnees = [
        ("IDreglement", track.IDreglement),
        ("IDcompte_payeur", track.IDfamille),
        ("date", xformat.DatetimeToStr(track.date,iso=True)),
        ("IDmode", IDmode),
        ("IDemetteur", IDemetteur),
        ("numero_piece", track.numero),
        ("montant", track.montant),
        ("IDpayeur", IDpayeur),
        ("observations", track.libelle),
        ("IDcompte", dlg.GetIDbanque()),
        ("date_saisie", xformat.DatetimeToStr(datetime.date.today(),iso=True)),
        ("IDutilisateur", dlg.IDutilisateur),
        ("IDpiece",track.IDprestation),
    ]
    if dlg.withDepot:
        lstDonnees.append(("IDdepot",dlg.IDdepot))
    if hasattr(track,'differe'):
        lstDonnees.append(("date_differe", xformat.DatetimeToStr(track.differe,iso=True)))

    if track.IDreglement in dlg.pnlOlv.lstNewReglements:
        nouveauReglement = True
        ret = db.ReqInsert("reglements",lstDonnees= lstDonnees, mess="UTILS_Reglements.SetReglement")
        dlg.pnlOlv.lstNewReglements.remove(track.IDreglement)
    else:
        nouveauReglement = False
        ret = db.ReqMAJ("reglements", lstDonnees, "IDreglement", track.IDreglement)

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
        if not isinstance(track.IDreglement, int):
            print('anomalie: ',track.IDreglement)
        nuh.InsertActions([{
            "IDfamille": track.IDfamille,
            "IDcategorie": IDcategorie,
            "action": "Noelite %s du règlement ID%d : %s en %s %spayé par %s" % (
            categorie, track.IDreglement, montant, texteMode, texteDetail, textePayeur),
        }, ],db=db)
    return True

class Compte(object):
    def __init__(self,db,nature):
        self.nature = nature
        self.db = db

    def GetMatriceComptes(self):
        dicBandeau = {'titre':"Recherche d'un compte prestation",
                      'texte':"le compte choisi détermine le code du plan comptable de la prestation générée",
                      'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

        # Composition de la matrice de l'OLV comptes, retourne un dictionnaire

        lstChamps = ['0','matPlanComptable.pctCompte','matPlanComptable.pctCodeComptable','matPlanComptable.pctLibelle',]

        lstNomsColonnes = ["0","compte","code","libellé"]

        lstTypes = ['INTEGER','VARCHAR(8)','VARCHAR(16)','VARCHAR(100)']
        lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
        lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
        lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
        lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return   {
                    'lstColonnes': lstColonnes,
                    'lstChamps':lstChamps,
                    'listeNomsColonnes':lstNomsColonnes,
                    'listeCodesColonnes':lstCodesColonnes,
                    'getDonnees': self.GetComptes,
                    'dicBandeau': dicBandeau,
                    'sortColumnIndex': 2,
                    'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                    'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                    }

    def GetComptes(self,dicOlv,**kwd):
        # le pointeur de cette fonction est dans le dic généré par GetMatriceComptes,
        filtre = kwd.pop('filtreTxt', '')
        nbreFiltres = kwd.pop('nbreFiltres', 0)

        # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
        # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
        limit = ''
        if nbreFiltres == 0:
            limit = "LIMIT %d" % LIMITSQL

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

        lstChamps = dicOlv['lstChamps']
        lstCodesColonnes = [x.valueGetter for x in dicOlv['lstColonnes']]
        req = """SELECT %s
                FROM matPlanComptable
                WHERE %s
                %s;
                """ % (",".join(lstChamps),where,limit)
        retour = self.db.ExecuterReq(req, mess='UTILS_Reglements.GetComptes' )
        recordset = ()
        if retour == "ok":
            recordset = self.db.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Aucun compte paramétré contenant '%s' ou '%s' dans le code ou le libellé"%(rad1,rad2))

        # composition des données du tableau à partir du recordset, regroupement par compte
        dicComptes = {}
        ixID = lstCodesColonnes.index('code')
        for record in recordset:
            if not record[ixID] in dicComptes.keys():
                dicComptes[record[ixID]] = {}
                for ix in range(len(lstCodesColonnes)):
                    dicComptes[record[ixID]][lstCodesColonnes[ix]] = record[ix]
            else:
                # ajout de noms et prénoms si non encore présents
                if not record[-2] in dicComptes[record[ixID]]['noms']:
                    dicComptes[record[ixID]]['noms'] += "," + record[-2]
                if not record[-1] in dicComptes[record[ixID]]['prenoms']:
                    dicComptes[record[ixID]]['prenoms'] += "," + record[-1]

        lstDonnees = []
        for key, dic in dicComptes.items():
            ligne = []
            for code in lstCodesColonnes:
                ligne.append(dic[code])
            lstDonnees.append(ligne)
        dicOlv =  dicOlv
        dicOlv['lstDonnees']=lstDonnees
        return lstDonnees

    def GetCompte(self,db=None):
        dicOlv = self.GetMatriceComptes()
        dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv,db=db)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            retour = dlg.GetSelection().donnees
            compte, libelle = retour[1],retour[3]
        else:
            compte, libelle = None, None
        dlg.Destroy()
        return compte, libelle

def DeleteDepot(IDdepot,db):
    # cas d'un depot vidé de ses lignes
    db.ReqDEL("depots", "IDdepot", IDdepot, affichError=True)
    return

def SetDateDepot(db,IDdepot,date):
    # cas d'un changement de la date du dépot après sa création
    db.ReqMAJ('depots', [('date',date),],'IDdepot', IDdepot, affichError=True)
    return

def MajDepot(dlg,db,IDdepot):
    modes = ""
    mindte, maxdte = datetime.date(2999,12,31), datetime.date(2000,1,1)

    nb = len(dlg.ctrlOlv.modelObjects)
    for track in dlg.ctrlOlv.modelObjects:
        if track.mode and len(track.mode) > 0:
            if not track.mode[:3] in modes: modes += track.mode[:3]+', '
        mindte = min(mindte,track.date)
        maxdte = max(maxdte, track.date)
    if mindte == maxdte:
        dates = "le %s"%(xformat.DatetimeToStr(mindte,iso=False))
    else: dates = "du %s au %s"%(xformat.DatetimeToStr(mindte,iso=False),xformat.DatetimeToStr(maxdte,iso=False))
    label = "Noelite: %d %s datés %s"%(nb,modes,dates)

    lstDonnees = [
        ("date", xformat.DateFrToSql(dlg.pnlParams.ctrlDate.GetValue())),
        ("nom", label),
        ("IDcompte", dlg.GetIDbanque()),
        ]
    # Mise à jour du libellé dépôt
    db.ReqMAJ('depots', lstDonnees,'IDdepot', IDdepot, affichError=True)
    return

def SetDepot(dlg,db):
    # cas d'un nouveau depot à créer, retourne l'IDdepot
    IDdepot = None
    today = xformat.DatetimeToStr(datetime.date.today(),iso=False)
    label = "saisie '%s' sur '%s' via '%s' le %s"%(dlg.dictUtilisateur['utilisateur'],dlg.dictUtilisateur['userdomain'],
                                                    dlg.dictUtilisateur['config'],today)
    lstDonnees = [
        ("date", xformat.DateFrToSql(dlg.pnlParams.ctrlDate.GetValue())),
        ("nom", "Saisie règlements via Noelite"),
        ("verrouillage",0),
        ("IDcompte", dlg.GetIDbanque()),
        ("observations",label)
        ]
    if not hasattr(dlg, "IDdepot"):
        ret = db.ReqInsert("depots", lstDonnees=lstDonnees, mess="UTILS_Reglements.SetDepot", )
        if ret == 'ok':
            IDdepot = db.newID

    # affichage de l'IDdepot créé
    dlg.pnlParams.ctrlRef.SetValue(str(IDdepot))
    return IDdepot

def GetDepot(db=None,**kwd):
    # lancement de l'appel des dépots existants pour reprise
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
    #art = Compte('debour')
    #print(art.GetCompte())
    print(GetDepot())
    app.MainLoop()