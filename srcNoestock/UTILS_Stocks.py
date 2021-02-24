#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des stocks et prix de journée
# Usage : Ensemble de fonctions acompagnant les DLG
# Auteur:          Jacques BRUNEL 2020-04 Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import xpy.xGestion_TableauRecherche as xgtr
from xpy.outils import xformat

def ValideLigne(db,track):
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"

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

def GetFournisseurs(db):
    # appel des composants d'une immo particulière
    dlg = self.parent
    req = """   
            SELECT %s
            FROM immosComposants
            WHERE IDimmo = %s
            ORDER BY dteAcquisition;
            """ % (",".join(lstChamps), IDimmo)
    lstDonnees = []
    retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetComposants')
    if retour == "ok":
        recordset = self.db.ResultatReq()
        lstDonnees = [list(x) for x in recordset]
    dlg.ctrlOlv.lstDonnees = lstDonnees
    dlg.ctrlOlv.MAJ()
    dlg.ctrlOlv._FormatAllRows()
    return []

def GetAnalytiques(db):
    return []