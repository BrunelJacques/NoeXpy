#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des contrepassations analytiques
# Usage : Ensemble de fonctions pour km, stocks, retrocessions
# Auteur:          Jacques BRUNEL
# Copyright:       (c) 2020-04   Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import srcNoelite.UTILS_Historique      as nuh
import xpy.xGestion_TableauRecherche    as xgtr
import xpy.xUTILS_DB                    as xdb
from xpy.outils             import xformat, xchoixListe
from srcNoelite.DB_schema   import DB_TABLES

def GetClotures(tip='date'):
    noegest = Noegest()
    lClotures = [x for y,x in noegest.GetExercices(tip=tip)]
    del noegest
    return lClotures

def GetDatesFactKm():
    # se lance à l'initialisation des params mais après l'accès à noegest
    noegest = Noegest()
    ldates = noegest.GetDatesFactKm()
    del noegest
    return ldates

class ToComptaKm(object):
    def __init__(self,dicParams,champsIn,noegest):
        addChamps = ['date','compte','noPiece','libelle','montant','contrepartie','qte']
        self.champsIn = champsIn + addChamps
        self.cptVte = dicParams['comptes']['revente'].strip()
        self.cptAch = dicParams['comptes']['achat'].strip()
        self.cptTiers = dicParams['comptes']['tiers'].strip()
        self.forcer = dicParams['compta']['forcer']
        self.dicPrixVte = noegest.GetdicPrixVteKm()
        if dicParams['filtres']['datefact'] > dicParams['filtres']['cloture']:
            self.dateFact = dicParams['filtres']['cloture']
        else:
            self.dateFact = dicParams['filtres']['datefact']
        annee = dicParams['filtres']['cloture'][:4]
        self.piece = 'km' + dicParams['filtres']['cloture'][:4]

    def AddDonnees(self,donnees=[]):
        #add ['date', 'compte', 'noPiece', 'libelle', 'montant', contrepartie,qte]
        tip=donnees[self.champsIn.index('typetiers')]
        typeTiers = tip + ":"
        # libelle écriture
        libTiers = xformat.Supprespaces(donnees[self.champsIn.index('nomtiers')])
        libVehicule = xformat.Supprespaces(donnees[self.champsIn.index('vehicule')])
        libKm = '%dkm'%donnees[self.champsIn.index('conso')]
        lgMax = 30 - (len(typeTiers) + len(libKm) + 2)
        # Tronque un libellé suppérieur à 30 caractères au final
        if len(libTiers + libVehicule) > lgMax:
            libTiers = libTiers[0:min(len(libTiers),int(lgMax / 2))]
        if len(libTiers + libVehicule) > lgMax:
            libVehicule = libVehicule[0:min(len(libVehicule),lgMax-len(libTiers))]

        libelle = "%s%s/%s %s"%(typeTiers, libTiers, libVehicule, libKm)
        # activité cession interne
        if tip == 'A':
            contrepartie = self.cptAch + donnees[self.champsIn.index('idactivite')]
        # partenaire facturé selon une convention
        elif tip == 'P':
            contrepartie = self.cptVte + donnees[self.champsIn.index('idvehicule')]
        # tiers participant au frais en nature
        elif tip == 'T':
            contrepartie = self.cptTiers + donnees[self.champsIn.index('idvehicule')]
        # supporté par la structure
        else:
            contrepartie = self.cptAch + "00"

        donnees.append(self.dateFact)
        donnees.append(self.cptVte + donnees[self.champsIn.index('idvehicule')])
        donnees.append(self.piece)
        donnees.append(libelle)
        donnees.append(donnees[self.champsIn.index('conso')] * self.dicPrixVte[donnees[self.champsIn.index('idvehicule')]])
        donnees.append(contrepartie),
        donnees.append(donnees[self.champsIn.index('conso')])

class Noegest(object):
    def __init__(self,parent=None):
        self.parent = parent
        self.db = xdb.DB()
        self.cloture = None
        self.ltExercices = None

    # ---------------- gestion des immos

    def ValideLigComp(self, track):
        track.valide = True
        track.messageRefus = "Saisie incomplète\n\n"

        # vérification des éléments saisis
        if (not track.libComposant) or (len(track.libComposant)==0):
            track.messageRefus += "Vous devez obligatoirement saisir un libellé !\n"
        if (not track.valeur) or (track.valeur < 1.0):
            track.messageRefus += "Vous devez obligatoirement saisir une valeur positive !\n"
        if track.type == 'L':
            if xformat.Nz(track.tauxLin) == 0.0 :
                track.messageRefus += "Vous devez obligatoirement saisir un taux d'amortissement!\n"
        elif track.type == 'D':
            if xformat.Nz(track.coefDegressif) == 0.0 :
               track.messageRefus += "Vous devez obligatoirement saisir  un taux d'amortissement dégressif !\n"
        elif track.type != 'N':
            track.messageRefus += "Vous devez obligatoirement saisir un type d'amortissement !\n"

        # envoi de l'erreur
        if track.messageRefus != "Saisie incomplète\n\n":
            track.valide = False
        else:
            track.messageRefus = ""
        return

    def SetEnsemble(self,IDimmo,pnlParams):
        # Enregistrement dans la base de l'ensemble
        lstChampsP, lstDonneesP = pnlParams.GetLstValues()
        lstDonnees = [(lstChampsP[x],lstDonneesP[x]) for x in range(len(lstChampsP))]
        if IDimmo:
            ret = self.db.ReqMAJ('immobilisations',lstDonnees[:-1],'IDimmo',IDimmo,mess='UTILS_Noegest.SetEnsemble_maj')
        else:
            ret = self.db.ReqInsert('immobilisations', lstChampsP[:-1], [lstDonneesP[:-1],],
                                    mess='UTILS_Noegest.SetEnsemble_ins')
            if ret == 'ok':
                IDimmo = self.db.newID
        return IDimmo

    def DelEnsemble(self,IDimmo):
        # Suppression dans la base de l'ensemble en mode silentieux
        if IDimmo:
            ret = self.db.ReqDEL('immobilisations','IDimmo',IDimmo,affichError=False)
        return

    def SetComposants(self,IDimmo,lstNews,lstCancels,lstModifs,lstChamps):
        champs = lstChamps + ['dtMaj','user']
        donUser = [xformat.DatetimeToStr(datetime.date.today(), iso=True),
                   self.GetUser()]

        # écriture des composants d'une immo particulière dans la base de donnée
        for donnees in lstNews:
            donnees += donUser
            donnees[1] = IDimmo
            self.db.ReqInsert('immosComposants',champs[1:],[donnees[1:],],mess="U_Noegest.SetComposants_ins")
        for donnees in lstCancels:
            self.db.ReqDEL('immosComposants','IDcomposant',donnees[0],mess="U_Noegest.SetComposants_del")
        for donnees in lstModifs:
            donnees += donUser
            self.db.ReqMAJ('immosComposants',nomChampID='IDcomposant',ID=donnees[0],lstChamps=champs[1:],
                           lstValues=donnees[1:], mess="U_Noegest.SetComposants_maj")
        return

    def GetEnsemble(self,IDimmo, lstChamps,pnlParams):
        # appel du cartouche d'une immo particulière
        req = """   
                SELECT %s
                FROM immobilisations
                WHERE IDimmo = %s;
                """ % (",".join(lstChamps),IDimmo)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetEnsemble')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            if len(recordset) > 0:
                lstDonnees = list(recordset[0])
                pnlParams.SetLstValues(lstChamps,lstDonnees)
        return

    def GetComposants(self,IDimmo, lstChamps):
        # appel des composants d'une immo particulière
        dlg = self.parent
        req = """   
                SELECT %s
                FROM immosComposants
                WHERE IDimmo = %s
                ORDER BY dteAcquisition;
                """ % (",".join(lstChamps),IDimmo)
        lstDonnees = []
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetComposants')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            lstDonnees = [list(x) for x in recordset]
        dlg.ctrlOlv.lstDonnees = lstDonnees
        dlg.ctrlOlv.MAJ()
        dlg.ctrlOlv._FormatAllRows()
        return

    def GetImmosComposants(self,lstChamps):
        # appel des composants dans les tables immos
        self.db.Close()
        self.db = xdb.DB()
        dlg = self.parent
        req = """   
                SELECT %s
                FROM immobilisations
                INNER JOIN immosComposants ON immobilisations.IDimmo = immosComposants.IDimmo;
                """ % (",".join(lstChamps))
        lstDonnees = []
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetImmosComposants')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            lstDonnees = [list(x) for x in recordset]
        dlg.ctrlOlv.lstDonnees = lstDonnees
        dlg.ctrlOlv.MAJ()
        dlg.ctrlOlv._FormatAllRows()
        return

    # ---------------- appels des codes analytiques

    def GetMatriceAnalytiques(self,axe,lstChamps,lstNomsCol,lstTypes,getDonnees):
        # Composition d'un dic matrice permettant de gérer un écran de saisie analytique
        dicBandeau = {'titre': "Choix d'un code analytique: %s"%str(axe),
                      'texte': "les mots clés du champ en bas permettent de filtrer les lignes et d'affiner la recherche",
                      'hauteur': 15, 'nomImage': "xpy/Images/32x32/Matth.png"}

        # Composition de la matrice de l'OLV Analytiques, retourne un dictionnaire

        lstCodesColonnes = [xformat.NoAccents(x).lower() for x in lstNomsCol]
        lstValDefColonnes = xformat.ValeursDefaut(lstNomsCol, lstTypes)
        lstLargeurColonnes = xformat.LargeursDefaut(lstNomsCol, lstTypes,IDcache=False)
        lstColonnes = xformat.DefColonnes(lstNomsCol, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return {
            'lstColonnes': lstColonnes,
            'lstChamps': lstChamps,
            'listeNomsColonnes': lstNomsCol,
            'listeCodesColonnes': lstCodesColonnes,
            'getDonnees': getDonnees,
            'dicBandeau': dicBandeau,
            'sortColumnIndex': 1,
            'sensTri': False,
            'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
        }

    def GetAnalytique(self,**kwd):
        # choix d'un code analytique, retourne un dict,
        # Le mode:'auto' permet un automatisme d'affectation sans un arrêt, pour tous les autres cas =>affichage
        mode = kwd.pop('mode',None)
        axe = kwd.pop('axe',None)
        nbChampsTestes = kwd.pop('axe',3)
        #Pour une recherche sur tous les axes on ne teste que le champ ID pour éviter les ambiguités
        if not axe: nbChampsTestes = 1
        filtre = kwd.pop('filtre',None)
        getAnalytiques = kwd.pop('getAnalytiques', None)
        lstNomsCol = kwd.pop('lstNomsCol',['IDanalytique','abrégé','nom','params','axe'])
        lstChamps = kwd.pop('lstChamps',['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege',
                                         'cpta_analytiques.nom', 'cpta_analytiques.params', 'cpta_analytiques.axe'
                                         ])
        lstTypes = kwd.pop('lstTypes',None)
        if not lstTypes:
            lstTypes = [y for x,y,z in DB_TABLES['cpta_analytiques']]
        lstCodesColonnes = [xformat.NoAccents(x).lower() for x in lstNomsCol]

        if not mode: mode = 'dlg'
        dicAnalytique = None
        nb = 0
        # Test préalable sur début de clé seulement
        if filtre and len(str(filtre))>0:
            # pour recherche sur un seul axre, on déroule les champs progresivement, jusqu'à trouver un item unique
            for ix in range(nbChampsTestes):
                kwd['whereFiltre']  = """
                    AND (%s LIKE '%s%%' )"""%(lstChamps[ix],filtre)
                kwd['lstChamps'] = lstChamps
                kwd['mode'] = mode
                kwd['axe'] = axe
                ltAnalytiques = getAnalytiques(**kwd)
                nb = len(ltAnalytiques)
                if nb == 1:
                    # une seule occurrence trouvée c'est ok dans tous les cas
                    dicAnalytique={}
                    for ix2 in range(len(ltAnalytiques[0])):
                        dicAnalytique[lstCodesColonnes[ix2]] = ltAnalytiques[0][ix2]
                    break
                elif nb > 1 and mode.lower() == 'auto':
                    # Le mode auto prend la première occurrence trouvée même s'il y en a d'autres
                    dicAnalytique={}
                    for ix2 in range(len(ltAnalytiques[0])):
                        dicAnalytique[lstCodesColonnes[ix2]] = ltAnalytiques[0][ix2]
                    break
                elif nb > 1:
                    # dès le premier champ trop d'occurrences, il faut les afficher
                    break
        if mode.lower() == 'auto' or nb == 1:
            return dicAnalytique

        # le filtre semble trop peu sélectif pour un f4 on le supprime
        if nb < 2: filtre = None
        # un item unique n'a pas été trouvé on affiche les choix possibles
        getDonnees = getAnalytiques
        dicOlv = self.GetMatriceAnalytiques(axe,lstChamps,lstNomsCol,lstTypes,getDonnees)
        #dicOlv['lstCodesSup'] = ['axe',]
        dicOlv['size'] = (500,600)

        # appel dee l'écran de saisie
        dlg = xgtr.DLG_tableau(self,dicOlv=dicOlv)

        if dlg.ctrlOlv.Parent.ctrlOutils:
            barreRecherche = dlg.ctrlOlv.Parent.ctrlOutils.barreRecherche
        else:
            barreRecherche = dlg.ctrlOlv.Parent.barreRecherche
        if filtre and len(filtre)>0 and barreRecherche:
            barreRecherche.SetValue(filtre)
            dlg.ctrlOlv.Filtrer(filtre)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            donnees = dlg.GetSelection().donnees
            dicAnalytique = {}
            for ix in range(len(donnees)):
                dicAnalytique[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dlg.Destroy()
        return dicAnalytique

    def GetAnalytiques(self,**kwd):
        # idem GetActivites mais avec axes étendus
        kwd['axe'] = None
        return self.GetActivites(**kwd)

    def SqlAnalytiques(self,**kwd):
        lstChamps = kwd.pop('lstChamps',['*',])
        reqFrom = kwd.pop('reqFrom','')
        reqWhere = kwd.pop('reqWhere','')
        # retourne un recordset de requête (liste de tuples)
        ltAnalytiques = []
        champs = ",".join(lstChamps)
        req = """SELECT %s
                %s
                %s
                """%(champs,reqFrom,reqWhere)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.SqlAnalytiques')
        if retour == "ok":
            ltAnalytiques = self.db.ResultatReq()
        return ltAnalytiques

    # ---------------- gestion des km à refacturer

    def GetDatesFactKm(self):
        ldates = ['{:%Y-%m-%d}'.format(datetime.date.today()),]
        datesNoe = []
        req =   """   
                SELECT vehiculesConsos.dtFact
                FROM vehiculesConsos 
                INNER JOIN cptaExercices ON vehiculesConsos.cloture = cptaExercices.date_fin
                GROUP BY vehiculesConsos.dtFact;
                """
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetDatesFactKm')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            datesNoe = [x[0] for x in recordset]
        return ldates + datesNoe

    def GetdicPrixVteKm(self):
        dicPrix = {}
        req = """   
                SELECT vehiculesCouts.IDanalytique, vehiculesCouts.prixKmVte 
                FROM vehiculesCouts 
                INNER JOIN cpta_analytiques ON vehiculesCouts.IDanalytique = cpta_analytiques.IDanalytique
                WHERE (((vehiculesCouts.cloture) = '%s') AND ((cpta_analytiques.axe)="VEHICULES"))
                ;"""%xformat.DateFrToSql(self.cloture)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetPrixVteKm')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            for ID, cout in recordset:
                dicPrix[ID] = cout
        return dicPrix

    def GetConsosKm(self):
        # appel des consommations de km sur écran Km_saisie
        dlg = self.parent
        box = dlg.pnlParams.GetBox('filtres')
        dateFact = xformat.DateFrToSql(box.GetOneValue('datefact'))
        vehicule = box.GetOneValue('vehicule')
        where =''
        if dateFact and len(dateFact) > 0:
            where += "\n            AND (consos.dtFact = '%s')"%dateFact
        if vehicule and len(vehicule) > 0 and not 'Tous' in vehicule:
            where += "\n            AND ( vehic.abrege = '%s')"%vehicule

        lstChamps = ['consos.'+x[0] for x in DB_TABLES["vehiculesConsos"]]
        lstChamps += ['vehic.abrege','vehic.nom','activ.nom']
        req = """   
            SELECT %s
            FROM (vehiculesConsos AS consos
            INNER JOIN cpta_analytiques AS vehic ON consos.IDanalytique = vehic.IDanalytique) 
            LEFT JOIN cpta_analytiques AS activ ON consos.IDtiers = activ.IDanalytique
            WHERE ((vehic.axe IS NULL OR vehic.axe='VEHICULES')
                    %s)
            ORDER BY consos.IDconso;
            """ % (",".join(lstChamps),where)
        lstDonnees = []
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetConsosKm')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            for record in recordset:
                dicDonnees = xformat.ListToDict(lstChamps,record)
                if dicDonnees["consos.typeTiers"] != 'A':
                    lstObs = dicDonnees["consos.observation"].split(" / ")
                    if len(lstObs) > 1:
                        dicDonnees["activ.nom"] = lstObs[0]
                        dicDonnees["consos.observation"] = ('-').join(lstObs[1:])
                donnees = [
                    dicDonnees["consos.IDconso"],
                    dicDonnees["consos.IDanalytique"],
                    dicDonnees["vehic.abrege"],
                    dicDonnees["consos.typeTiers"],
                    dicDonnees["consos.IDtiers"],
                    dicDonnees["activ.nom"],
                    dicDonnees["consos.dteKmDeb"],
                    dicDonnees["consos.kmDeb"],
                    dicDonnees["consos.dteKmFin"],
                    dicDonnees["consos.kmFin"],
                    dicDonnees["consos.kmFin"]-dicDonnees["consos.kmDeb"],
                    dicDonnees["consos.observation"],
                    ]
                lstDonnees.append(donnees)
        dlg.ctrlOlv.lstDonnees = lstDonnees
        dlg.ctrlOlv.MAJ()
        for object in dlg.ctrlOlv.modelObjects:
            self.ValideLigne(object)
        dlg.ctrlOlv._FormatAllRows()
        return

    def GetVehicule(self,filtre='', mode=None):
        # choix d'une activité et retour de son dict, mute sert pour automatisme d'affectation
        kwd = {
            'axe': 'VEHICULES',
            'mode' : mode,
            'filtre' : filtre,
            'getAnalytiques': self.GetVehicules,
            'lstNomsCol': ['IDanalytique', 'abrégé', 'nom','prix'],
            'lstChamps': ['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom',
                          'vehiculesCouts.prixKmVte'],
            }
        dicVehicule = self.GetAnalytique(**kwd)
        return dicVehicule

    def GetVehicules(self,**kwd):
        lstChamps = kwd.pop('lstChamps',None)
        # matriceOlv et filtre résultent d'une saisie en barre de recherche
        matriceOlv = kwd.pop('dicOlv',{})
        if (not lstChamps) and 'lstChamps' in matriceOlv:
            lstChamps = matriceOlv['lstChamps']
        filtre = kwd.pop('filtre','')
        kwd['filtre'] = filtre
        whereFiltre = kwd.pop('whereFiltre','')
        if len(whereFiltre) == 0 and len(filtre)>0:
            whereFiltre = xformat.ComposeWhereFiltre(filtre,lstChamps,lien='AND')
        kwd['reqWhere'] = """
                WHERE (cpta_analytiques.axe = 'VEHICULES')
                %s"""%(whereFiltre)
        kwd['reqFrom'] = """
                FROM    cpta_analytiques   
                LEFT JOIN vehiculesCouts ON cpta_analytiques.IDanalytique = vehiculesCouts.IDanalytique"""
        kwd['lstChamps'] = lstChamps
        return self.SqlAnalytiques(**kwd)

    def GetActivite(self,filtre='',mode=None,axe='ACTIVITES'):
        # choix d'une activité et retour de son dict, auto sert pour automatisme d'affectation
        kwd = {
            'axe': axe,
            'mode' : mode,
            'filtre' : filtre,
            'getAnalytiques': self.GetActivites}
        # axe = None, cherche pour tous les axes sur le seul champ ID
        if axe == None:
            kwd['getAnalytiques'] = self.GetAnalytiques
        dicActivite = self.GetAnalytique(**kwd)
        return dicActivite

    def GetActivites(self,**kwd):
        lstChamps = kwd.pop('lstChamps',None)
        # matriceOlv et filtre résultent d'une saisie en barre de recherche
        matriceOlv = kwd.pop('dicOlv',{})
        if (not lstChamps) and 'lstChamps' in matriceOlv:
            lstChamps = matriceOlv['lstChamps']
        kwd['lstChamps'] = lstChamps
        axe = kwd.pop('axe','ACTIVITES')
        if (not axe) or len(axe) == 0:
            whereAxe = 'TRUE'
        else:
            whereAxe = "axe = '%s' "%axe
        filtre = kwd.pop('filtre','')
        kwd['filtre'] = filtre
        whereFiltre = kwd.pop('whereFiltre','')
        if len(whereFiltre) == 0 and len(filtre)>0:
            whereFiltre = self.ComposeWhereFiltre(filtre,lstChamps)
        kwd['reqWhere'] = """
            WHERE %s %s
            """%(whereAxe,whereFiltre)
        kwd['reqFrom'] = """
            FROM cpta_analytiques"""
        return self.SqlAnalytiques(**kwd)

    def SetConsoKm(self,track):
        # --- Sauvegarde de la ligne consommation ---
        dteFacturation = self.GetParam('filtres','datefact')
        if track.observation == None: track.observation = ""
        if track.typetiers != 'A' and track.nomtiers and len(track.nomtiers.strip())>0:
            if not (track.nomtiers.strip() in track.observation):
                track.nomtiers = track.nomtiers.replace('/','-')
                track.observation = "%s / %s"%(track.nomtiers.strip(),track.observation.strip())
        if track.idactivite == None: track.idactivite = ''

        lstDonnees = [
            ("IDconso", track.IDconso),
            ("IDanalytique", track.idvehicule),
            ("cloture", xformat.DateFrToSql(self.cloture)),
            ("typeTiers", track.typetiers[:1]),
            ("IDtiers", track.idactivite),
            ("dteKmDeb", xformat.DateFrToSql(track.datekmdeb)),
            ("kmDeb", track.kmdeb),
            ("dteKmFin", xformat.DateFrToSql(track.datekmfin)),
            ("kmFin", track.kmfin),
            ("observation", track.observation),
            ("dtFact", xformat.DateFrToSql(dteFacturation)),
            ("dtMaj", xformat.DatetimeToStr(datetime.date.today(),iso=True)),
            ("user", self.GetUser()),
            ]

        if not track.IDconso or track.IDconso == 0:
            ret = self.db.ReqInsert("vehiculesConsos",lstDonnees= lstDonnees[1:], mess="UTILS_Noegest.SetConsoKm")
            track.IDconso = self.db.newID
            IDcategorie = 6
            categorie = ("Saisie")
        else:
            ret = self.db.ReqMAJ("vehiculesConsos", lstDonnees, "IDconso", track.IDconso)
            IDcategorie = 7
            categorie = "Modification"
        """
        # --- Mémorise l'action dans l'historique ---
        if ret == 'ok':
            nuh.InsertActions([{
                                "IDcategorie": IDcategorie,
                                "action": "Noelite %s de la conso ID%d : %s %s %s" % (
                                categorie, track.IDconso, track.nomvehicule,track.nomtiers,track.observation,),
                                }, ],db=self.db)
        """
        return ret

    def CalculeLigne(self,track):
        # relais lors de former Tracks
        self.ValideLigne(self,track)

    def ValideLigne(self, track):
        track.valide = True
        track.messageRefus = "Saisie incomplète\n\n"
        # vérification des éléments saisis
        try:
            track.conso = int(track.conso)
        except:
            track.conso = None
        if not track.conso or track.conso == 0:
            track.messageRefus += "Le nombre de km consommés est à zéro\n"

        # DateKmFin
        if not xformat.DateFrToSql(track.datekmfin) :
            track.messageRefus += "Vous devez obligatoirement saisir une date de début !\n"

        # véhicule
        if track.idvehicule == None:
            track.messageRefus += "Vous devez obligatoirement sélectionner un véhicle reconnu !\n"

        # activité
        if track.typetiers == 'A' and (not track.idactivite or len(str(track.idactivite))==0):
            track.messageRefus += "Vous devez obligatoirement sélectionner une activité !\n"
        if (not track.nomtiers or len(str(track.nomtiers))==0):
            track.messageRefus += "Vous devez obligatoirement sélectionner un nom de tiers ou d'activité !\n"

        # envoi de l'erreur
        if track.messageRefus != "Saisie incomplète\n\n":
            track.valide = False
        else:
            track.messageRefus = ""
        return

    def SauveLigne(self,track):
        if not track.valide:
            return False
        if not track.conso or int(track.conso) == 0:
            return False
        # gestion de la consommation
        ret = self.SetConsoKm(track)
        if ret != 'ok':
            wx.MessageBox(ret)
        return ret

    def DeleteLigne(self,track):
        db = self.db
        # si l'ID est à zéro il n'y a pas eu d'enregistrements
        if xformat.Nz(track.IDconso) != 0 :
            # suppression  de la consommation
            ret = db.ReqDEL("vehiculesConsos", "IDconso", track.IDconso,affichError=False)
            if track.valide:
                # --- Mémorise l'action dans l'historique ---
                if ret == 'ok':
                    IDcategorie = 8
                    categorie = "Suppression"
                    nuh.InsertActions([{
                        "IDcategorie": IDcategorie,
                        "action": "Noelite %s de conso km véhicule ID%d"%(categorie, track.IDconso),
                        },],db=db)
        return

    # ------------------ fonctions diverses

    def GetExercices(self, where='WHERE  actif = 1',tip='date'):
        if self.ltExercices: return self.ltExercices
        self.ltExercices = []
        lstChamps = ['date_debut', 'date_fin']
        req = """   SELECT %s
                    FROM cptaExercices
                    %s                   
                    """ % (",".join(lstChamps), where)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetExercices')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Aucun exercice n'est paramétré")
            for debut, fin in recordset:
                if tip.lower() in ('date', 'datetime'): debut, fin = xformat.DateSqlToDatetime(debut), \
                                                                     xformat.DateSqlToDatetime(fin)
                elif tip.lower() in ('str','iso','ansi'): debut,fin = xformat.DateSqlToIso(debut),\
                                                                xformat.DateSqlToIso(fin)
                elif tip.lower() == 'fr': debut,fin = xformat.DateSqlToFr(debut),\
                                                      xformat.DateSqlToFr(fin)
                self.ltExercices.append((debut, fin))

        return self.ltExercices

    def ChoixExercice(self):
        lstExercices = self.GetExercices()
        if len(lstExercices) > 0:
            dlg = xchoixListe.DialogAffiche(titre="Choix de l'exercice ",
                     intro="Le choix permettra le calcul des dotations pour cet exercice",
                     lstDonnees=lstExercices,
                     lstColonnes=["Début","Fin"],
                     lstWcol=[150,150],
                     size=(300,500))
            if dlg.ShowModal() == wx.OK:
                return dlg.choix
        return None

    def GetParam(self,cat,name):
        # récup des paramètres stockés sur le disque
        valeur = None
        dicParams = self.parent.pnlParams.GetValues()
        if cat in dicParams:
            if name in dicParams[cat]:
                valeur = dicParams[cat][name]
        return valeur

    def GetUser(self):
        dlg = self.parent
        return dlg.IDutilisateur


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ngest = Noegest()
    ngest.cloture = '2020-09-30'
    print(ngest.GetVehicules(lstChamps=['abrege']))
    app.MainLoop()