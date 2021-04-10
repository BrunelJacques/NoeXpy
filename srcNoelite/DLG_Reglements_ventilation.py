#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    NoeLITE, ventilation des Reglements
# Usage: affecte des parts de règlements à des prestations
# Auteur:           Ivan LUCAS orgine Noethys CTRL_Ventilation,
#                   Jacques Brunel, adapté aCTRL_Ventilation
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import wx.grid as gridlib
import xpy.xGestion_TableauEditor       as xgte
import xpy.xUTILS_DB                   as xdb
import wx.lib.agw.hyperlink as Hyperlink
import datetime
import decimal
import sys

SYMBOLE = "€"

import xpy.xUTILS_DB as db

COULEUR_FOND_REGROUPEMENT = (200, 200, 200)
COULEUR_TEXTE_REGROUPEMENT = (140, 140, 140)

COULEUR_CASE_MODIFIABLE_ACTIVE = (255, 255, 255)
COULEUR_CASE_MODIFIABLE_INACTIVE = (230, 230, 230)

COULEUR_NUL = (255, 0, 0)
COULEUR_PARTIEL = (255, 193, 37)
COULEUR_TOTAL = (0, 238, 0)


def GetBoutons(dlg):
    return  [
                {'name': 'btnAbort', 'label': "Abandon",
                    'help': "Cliquez ici pour renoncer à affecter le règlement a des prestations",
                    'size': (110, 27), 'image':"xpy/Images/32x32/Annuler.png",'onBtn':dlg.OnAbort},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Validez",'help':"Cliquez ici pour enregistrer la ventilation",
                    'size':(100,30),'image':"xpy/Images/32x32/Valider.png",'onBtn':dlg.OnBoutonOK}
            ]

def DateEngFr(textDate):
    text = str(textDate[8:10]) + u"/" + str(textDate[5:7]) + u"/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (("Lundi"), ("Mardi"), ("Mercredi"), ("Jeudi"), ("Vendredi"), ("Samedi"), ("Dimanche"))
    listeMois = (("janvier"), ("février"), ("mars"), ("avril"), ("mai"), ("juin"), ("juillet"), ("août"), ("septembre"), ("octobre"), ("novembre"), ("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))
        
def PeriodeComplete(mois, annee):
    listeMois = (("Janvier"), ("Février"), ("Mars"), ("Avril"), ("Mai"), ("Juin"), ("Juillet"), ("Août"), ("Septembre"), ("Octobre"), ("Novembre"), ("Décembre"))
    periodeComplete = u"%s %d" % (listeMois[mois-1], annee)
    return periodeComplete

class CTRL_Saisie_euros(wx.TextCtrl):
    def __init__(self, parent, font=None, size=(-1, -1), style=wx.TE_RIGHT):
        wx.TextCtrl.__init__(self, parent, -1, u"0.00", size=size, style=style)
        self.parent = parent
        self.SetToolTip("Saisissez un montant")
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        if font != None:
            self.SetFont(font)

    def OnKillFocus(self, event):
        valide, messageErreur = self.Validation()
        if valide == False:
            wx.MessageBox(messageErreur, "Erreur de saisie")
        else:
            montant = float(self.GetValue())
            self.SetValue(u"%.2f" % montant)
        if event != None: event.Skip()

    def Validation(self):
        # Vérifie si montant vide
        montantStr = self.GetValue()
        try:
            test = float(montantStr)
        except:
            message = "Le montant que vous avez saisi n'est pas valide."
            return False, message
        return True, None

    def SetMontant(self, montant=0.0):
        if montant == None: montant = 0.0
        self.SetValue(u"%.2f" % montant)

    def GetMontant(self):
        validation, erreur = self.Validation()
        if validation == True:
            montant = float(self.GetValue())
            return montant
        else:
            return None

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", listeChoix=[], size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
        
    def OnLeftLink(self, event):
        if self.URL == "automatique" : self.parent.VentilationAuto() 
        if self.URL == "tout" : self.parent.VentilationTout() 
        if self.URL == "rien" : self.parent.VentilationRien() 
        self.UpdateLink()

# ---------------------------------------------------------------------------------------------------------------------

class Ligne_regroupement(object):
    def __init__(self, grid=None, numLigne=0, dictRegroupement={}):
        self.grid = grid
        self.type_ligne = "regroupement"
        self.numLigne = numLigne
        self.dictRegroupement = dictRegroupement
        self.listeLignesPrestations = []
        
        # Init ligne
        hauteurLigne = 20
        grid.SetRowSize(numLigne, hauteurLigne)

        # Attributs communes à toutes les colonnes
        for numColonne in range(0, 8) :
            self.grid.SetCellBackgroundColour(self.numLigne, numColonne, COULEUR_FOND_REGROUPEMENT)
            self.grid.SetReadOnly(self.numLigne, numColonne, True)

        # Case à cocher
        numColonne = 0
        self.grid.SetCellRenderer(self.numLigne, numColonne, gridlib.GridCellBoolRenderer())

        # Label du groupe
        self.grid.SetCellValue(self.numLigne, 1, self.dictRegroupement["label"])
        
        font = self.grid.GetFont() 
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.grid.SetCellFont(self.numLigne, 1, font)
                
        # Montant prestation
        numColonne = 5
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        font = self.grid.GetFont() 
        font.SetPointSize(8)
        self.grid.SetCellFont(self.numLigne, numColonne, font)

        # Montant déjà ventilé
        numColonne = 6
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        font = self.grid.GetFont() 
        font.SetPointSize(8)
        self.grid.SetCellFont(self.numLigne, numColonne, font)

        # Ventilation actuelle
        numColonne = 7
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        font = self.grid.GetFont() 
        font.SetPointSize(8)
        self.grid.SetCellFont(self.numLigne, numColonne, font)
        
    def MAJ(self):
        # Calcul des totaux
        total_prestation = 0.0
        total_aVentiler = 0.0
        total_ventilationActuelle = 0.0
        for ligne in self.listeLignesPrestations :
            total_prestation += ligne.montant
            total_aVentiler += ligne.resteAVentiler
            total_ventilationActuelle += ligne.ventilationActuelle
        
        # Affichage des totaux
        self.grid.SetCellValue(self.numLigne, 5, str(total_prestation))
        self.grid.SetCellValue(self.numLigne, 6, str(total_aVentiler))
        self.grid.SetCellValue(self.numLigne, 7, str(total_ventilationActuelle))

    def GetEtat(self):
        valeur = self.grid.GetCellValue(self.numLigne, 0)
        if valeur == "1" :
            return True
        else :
            return False
    
    def SetEtat(self, etat=False, majTotaux=True):
        self.grid.SetCellValue(self.numLigne, 0, str(int(etat)))

        # Coche ou décoche les prestations du groupe
        for ligne in self.listeLignesPrestations :
            ligne.SetEtat(etat, majTotaux=False)
        
        # MAJ des totaux
        self.grid.MAJtotaux()
        
    def OnCheck(self):
        etat = not self.GetEtat() 
        self.SetEtat(etat)

class Ligne_prestation(object):
    def __init__(self, grid=None, donnees={}):
        self.grid = grid
        self.type_ligne = "prestation"

        # Récupération des données
        self.IDprestation = donnees["IDprestation"]
        self.IDcompte_payeur = donnees["IDcompte_payeur"]
        self.date = donnees["date"]
        self.date_complete = DateComplete(self.date)
        self.mois = self.date.month
        self.annee = self.date.year
        self.periode = (self.annee, self.mois)
        self.periode_complete = PeriodeComplete(self.mois, self.annee)
        self.categorie = donnees["categorie"]
        self.label = donnees["label"]
        self.montant = donnees["montant"]
        self.IDactivite = donnees["IDactivite"]
        self.nomActivite = donnees["nomActivite"]
        self.IDtarif = donnees["IDtarif"]
        self.nomTarif = donnees["nomTarif"]
        self.nomCategorieTarif = donnees["nomCategorieTarif"]
        self.IDfacture = donnees["IDfacture"]
        if self.IDfacture == None or self.IDfacture == "" :
            self.label_facture = ("Non facturé")
        else:
            num_facture = donnees["num_facture"]
            date_facture = donnees["date_facture"]
            if type(num_facture) == int :
                num_facture = str(num_facture)
            self.label_facture = u"n°%s" % num_facture
        self.IDfamille = donnees["IDfamille"]
        self.IDindividu = donnees["IDindividu"]
        self.nomIndividu = donnees["nomIndividu"]
        self.prenomIndividu = donnees["prenomIndividu"]
        if self.prenomIndividu == None :
            self.prenomIndividu = u""
        if self.nomIndividu != None :
            self.nomCompletIndividu = u"%s %s" % (self.nomIndividu, self.prenomIndividu)
        else:
            self.nomCompletIndividu = u""
        self.ventilationPassee = donnees["ventilationPassee"]
        if self.ventilationPassee == None :
            self.ventilationPassee = 0.0
        self.ventilationActuelle = 0.0
        self.resteAVentiler = self.montant - self.ventilationPassee - self.ventilationActuelle
                        
    def Draw(self, numLigne=0, ligneRegroupement=None):
        """ Dessine la ligne dans la grid """
        self.numLigne = numLigne
        self.ligneRegroupement = ligneRegroupement
        
        # Init ligne
        hauteurLigne = 25
        self.grid.SetRowSize(numLigne, hauteurLigne)
        
        # Case à cocher
        numColonne = 0
        self.grid.SetCellRenderer(self.numLigne, numColonne, gridlib.GridCellBoolRenderer())
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        
        # Date
        numColonne = 1
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        # Individu
        numColonne = 2
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        
        # Label prestation
        numColonne = 3
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        # Facture
        numColonne = 4
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_CENTER, wx.ALIGN_CENTRE)
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        
        # Montant prestation
        numColonne = 5
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        
        # Montant déjà ventilé
        numColonne = 6
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        self.grid.SetReadOnly(self.numLigne, numColonne, True)

        # Ventilation actuelle
        numColonne = 7
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        self.grid.SetCellEditor(self.numLigne, numColonne, EditeurMontant(ligne=self))

    def MAJ(self, majTotaux=True):
        """ MAJ les données et l'affichage de la ligne """
        # MAJ des données
        if type(self.ventilationActuelle) != decimal.Decimal :
            self.ventilationActuelle = self.ventilationActuelle

        self.resteAVentiler = self.montant - self.ventilationPassee - self.ventilationActuelle
        
        # Coche
        if self.ventilationActuelle != 0.0 :
            etat = True
        else :
            etat = False
        self.grid.SetCellValue(self.numLigne, 0, str(int(etat)))

        # Label
        self.grid.SetCellValue(self.numLigne, 1, DateComplete(self.date))
        
        # Individu
        self.grid.SetCellValue(self.numLigne, 2, self.prenomIndividu)

        # Label de la prestation
        self.grid.SetCellValue(self.numLigne, 3, self.label)

        # Facture
        self.grid.SetCellValue(self.numLigne, 4, self.label_facture)

        # Montant de la prestation
        self.grid.SetCellValue(self.numLigne, 5, str(self.montant))

        # Montant déjà ventilé
        self.grid.SetCellValue(self.numLigne, 6, str(self.resteAVentiler))
        
        if self.resteAVentiler == 0.0 and self.GetEtat() == True : 
            self.grid.SetCellBackgroundColour(self.numLigne, 6, COULEUR_TOTAL)
        elif self.resteAVentiler == self.montant : 
            self.grid.SetCellBackgroundColour(self.numLigne, 6, COULEUR_NUL)
        else: 
            self.grid.SetCellBackgroundColour(self.numLigne, 6, COULEUR_PARTIEL)

        # Montant ventilé
        self.grid.SetCellValue(self.numLigne, 7, str(self.ventilationActuelle))
        self.grid.SetReadOnly(self.numLigne, 7, not self.GetEtat())

        if self.GetEtat() == True : 
            self.grid.SetCellBackgroundColour(self.numLigne, 7, COULEUR_CASE_MODIFIABLE_ACTIVE)
        else :
            self.grid.SetCellBackgroundColour(self.numLigne, 7, COULEUR_CASE_MODIFIABLE_INACTIVE)
        
        # MAJ de la ligne de regroupement
        if majTotaux == True :
            self.ligneRegroupement.MAJ() 
            self.grid.MAJbarreInfos()
        
    def GetEtat(self):
        valeur = self.grid.GetCellValue(self.numLigne, 0)
        if valeur == "1" :
            return True
        else :
            return False
    
    def SetEtat(self, etat=False, montant=None, majTotaux=True):
        # Coche la case
        self.grid.SetCellValue(self.numLigne, 0, str(int(etat)))
        
        # Attribue le montant
        if etat == False :
            montant = 0.0 
            
        if montant != None :
            # Tout ventiler
            self.ventilationActuelle = montant
        else:
            # Ventiler uniquement le montant donné
            self.ventilationActuelle = self.resteAVentiler
            
        self.MAJ(majTotaux) 
        
    def OnCheck(self):
        etat = not self.GetEtat() 
        montant = None
        
        # Attribue uniquement du crédit encore disponible
        if etat == True :
            montant = self.grid.GetCreditAventiler()
            if self.grid.parent.negatif:
                if montant < self.resteAVentiler or self.grid.bloquer_ventilation == False :
                    montant = self.resteAVentiler
            if not self.grid.parent.negatif:
                if montant > self.resteAVentiler or self.grid.bloquer_ventilation == False :
                    montant = min(montant,self.resteAVentiler)

        # Modifie la ligne
        self.SetEtat(etat, montant)
        
        # Décoche le groupe si aucune prestation cochée dedans
        if etat == False :
            auMoinsUneCochee = False
            for ligne in self.ligneRegroupement.listeLignesPrestations :
                if ligne.GetEtat() == True :
                    auMoinsUneCochee = True
            if auMoinsUneCochee == False :
                self.ligneRegroupement.SetEtat(False)

class RendererCaseMontant(gridlib.GridCellRenderer):
    def __init__(self):
        gridlib.GridCellRenderer.__init__(self)
        self.grid = None

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.grid = grid
            
        # Dessin du fond de couleur
        couleurFond = self.grid.GetCellBackgroundColour(row, col)
        dc.SetBackgroundMode(wx.BRUSHSTYLE_SOLID)
        dc.SetBrush(wx.Brush(couleurFond, wx.BRUSHSTYLE_SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)

        # Ecrit les restrictions
        texte = self.grid.GetCellValue(row, col)
        if texte != "" :
            texte = u"%.2f %s " % (float(texte), SYMBOLE)

        dc.SetBackgroundMode(wx.BRUSHSTYLE_TRANSPARENT)
        dc.SetFont(attr.GetFont())
        hAlign, vAlign = grid.GetCellAlignment(row, col)
        
        # Alignement à droite
        largeur, hauteur = dc.GetTextExtent(texte)
        x = rect[0] + rect[2] - largeur - 2
        y = rect[1] + ((rect[3] - hauteur) / 2.0)
        dc.DrawText(texte, x, y)
        
    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)
        return wx.Size(w, h)

    def Clone(self):
        return RendererCaseMontant()

# ---------------------------------------------------------------------------------------------------------------------

class EditeurMontant(gridlib.GridCellEditor):
    def __init__(self, ligne=None):
        self.ligne = ligne
        gridlib.GridCellEditor.__init__(self)

    def Create(self, parent, id, evtHandler):
        self._tc = CTRL_Saisie_euros(parent, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self._tc.SetInsertionPoint(0)
        self.SetControl(self._tc)
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)
        
    def BeginEdit(self, row, col, grid):
        self.startValue = grid.GetTable().GetValue(row, col)
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()
        self._tc.SetFocus()
        # For this example, select the text
        self._tc.SetSelection(0, self._tc.GetLastPosition())

    def EndEdit(self, row, col, grid, oldVal):
        changed = False
        valeur = self._tc.GetMontant()
        # Validation du montant saisi
        if self._tc.Validation() == False :
            valeur = None
        # Vérifie si montant saisi pas supérieur à montant à ventilé
        if valeur != None :
            resteAVentiler = self.ligne.montant - self.ligne.ventilationPassee - valeur
            if resteAVentiler < 0 :
                dlg = wx.MessageDialog(grid, ("Le montant saisi ne peut pas être supérieur au montant à ventiler !"), ("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                valeur = None
        # Renvoie la valeur
        if valeur != oldVal:  
            return valeur
        else:
            return None
    
    def ApplyEdit(self, row, col, grid):
        valeur = self._tc.GetMontant()
        grid.GetTable().SetValue(row, col, str(valeur))
        self.startValue = ''
        self._tc.SetValue('')
        # MAJ de la ligne
        self.ligne.ventilationActuelle = valeur
        self.ligne.MAJ() 
    
    def Reset(self):
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    def Destroy(self):
        super(EditeurMontant, self).Destroy()

    def Clone(self):
        return EditeurMontant()

# -------------------------------------------------------------------------------------------------------------------

class CTRL_Ventilation(gridlib.Grid): 
    def __init__(self, parent, IDcompte_payeur=None, IDreglement=None): 
        gridlib.Grid.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.lstRequetes = []
        self.parent = parent
        self.IDcompte_payeur = IDcompte_payeur
        self.IDreglement = IDreglement
        self.listeTracks = []
        self.dictVentilation = {}
        self.dictVentilationInitiale = {}
        self.ventilationValide = True
        self.montant_reglement = 0.0
        self.dictLignes = {}
        
        # Options
        self.bloquer_ventilation = False

        # Key de regroupement
        self.KeyRegroupement = "periode" # individu, facture, date, periode
        
        # Binds
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftClick)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.OnMouseOver)
    
    def InitGrid(self):
        """ Création de la grid et importation initiale des données """
        lstColonnes = [
            ( (""), 20),
            ( ("Date"), 175),
            ( ("Individu"), 124),
            ( ("Intitulé"), 185),
            ( ("N° Facture"), 75),
            ( ("Montant"), 65),
            ( ("A ventiler"), 65),
            ( ("Ventilé"), 65),
            ]
        
        # Initialisation de la grid
        self.SetMinSize((10, 10))
        self.moveTo = None
        self.CreateGrid(0, len(lstColonnes))
        self.SetRowLabelSize(1)
        self.DisableDragColSize()
        self.DisableDragRowSize()
        self.modeDisable = False
        
        # Création des colonnes
        self.SetColLabelSize(22)
        numColonne = 0
        for label, largeur in lstColonnes :
            self.SetColLabelValue(numColonne, label)
            self.SetColSize(numColonne, largeur)
            numColonne += 1

        # Importation des données
        self.listeLignesPrestations = self.Importation()

        # MAJ de l'affichage de la grid
        self.MAJ() 
        
        # Importation des ventilations existantes du règlement
        for ligne_prestation in self.listeLignesPrestations :
            if ligne_prestation.IDprestation in self.dictVentilation.keys() :
                montant = self.dictVentilation[ligne_prestation.IDprestation]
                ligne_prestation.SetEtat(True, montant, majTotaux=False)
        self.MAJtotaux() 

    def Importation(self):
        if self.IDreglement == None :
            IDreglement = 0
        else:
            IDreglement = self.IDreglement
        
        # Importation des ventilations de ce règlement
        DB = xdb.DB()
        req = """SELECT IDventilation, IDprestation, montant
        FROM ventilation
        WHERE IDreglement=%d
        ;""" % IDreglement
        DB.ExecuterReq(req)
        lstDonnees = DB.ResultatReq()
        self.dictVentilation = {}
        self.dictVentilationInitiale = {}
        for IDventilation, IDprestation, montant in lstDonnees :
            self.dictVentilation[IDprestation] = montant
            self.dictVentilationInitiale[IDprestation] = IDventilation

        # Importation des prestations de la famille et leurs parts réglées
        req = """
        SELECT prestations.IDprestation, prestations.IDcompte_payeur, date, categorie, label, prestations.montant, 
        prestations.IDactivite, activites.nom,
        prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, 
        prestations.IDfacture, factures.numero, factures.date_edition,
        IDfamille, prestations.IDindividu, 
        individus.nom, individus.prenom,
        SUM(ventilation.montant) AS montant_ventilation
        FROM prestations
        LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
        LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
        LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
        LEFT JOIN categories_tarifs ON tarifs.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture
        WHERE prestations.IDcompte_payeur = %d 
        GROUP BY prestations.IDprestation, prestations.IDcompte_payeur, date, categorie, label, prestations.montant, 
                prestations.IDactivite, activites.nom,
                prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, 
                prestations.IDfacture, factures.numero, factures.date_edition,
                IDfamille, prestations.IDindividu, 
                individus.nom, individus.prenom
        ORDER BY date
        ;""" % self.IDcompte_payeur
        DB.ExecuterReq(req)
        lstDonnees = DB.ResultatReq()
        DB.Close()
        listeLignesPrestations = []
        for IDprestation, IDcompte_payeur, date, categorie, label, montant, IDactivite, nomActivite, IDtarif, nomTarif, \
            nomCategorieTarif, IDfacture, num_facture, date_facture, IDfamille, IDindividu, nomIndividu, prenomIndividu,\
            montantVentilation in lstDonnees :
            montant = montant
            if montantVentilation == None: montantVentilation = 0.0
            if num_facture == None : num_facture = 0
            # Vérif cohérence
            if (montant >= 0.0 and montantVentilation > montant) \
                    or (montant < 0.0 and montantVentilation < montant)\
                    or ((montant * montantVentilation) < 0.0):
                montant,montantVentilation = self.CorrigeVentilation(IDprestation)

            # Composition des données OLV
            if (montant >= 0.0 and montantVentilation < montant) \
                    or (montant < 0.0 and montantVentilation > montant) \
                    or IDprestation in self.dictVentilation.keys() :
                # On garde cette prestation pour pouvoir affecter le règlement
                date = DateEngEnDateDD(date)
                if IDprestation in self.dictVentilation.keys() :
                    montantVentilation = montantVentilation - self.dictVentilation[IDprestation] 

                dictTemp = {
                    "IDprestation" : IDprestation, "IDcompte_payeur" : IDcompte_payeur, "date" : date, "categorie" : categorie,
                    "label" : label, "montant" : montant, "IDactivite" : IDactivite, "nomActivite" : nomActivite, "IDtarif" : IDtarif, "nomTarif" : nomTarif, 
                    "nomCategorieTarif" : nomCategorieTarif, "IDfacture" : IDfacture, "num_facture" : num_facture, "date_facture" : date_facture, 
                    "IDfamille" : IDfamille, "IDindividu" : IDindividu, "nomIndividu" : nomIndividu, "prenomIndividu" : prenomIndividu,
                    "ventilationPassee" : montantVentilation,
                    }
                ligne_prestation = Ligne_prestation(grid=self, donnees=dictTemp)
                listeLignesPrestations.append(ligne_prestation)
        return listeLignesPrestations

    def CorrigeVentilation(self,IDprestation):
        DB = xdb.DB()
        # suppression de ventilations orphelines de leur réglement
        req = """   DELETE ventilation 
                    FROM (ventilation LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement)
                    WHERE ((reglements.IDreglement Is Null) AND (ventilation.IDprestation= %d))
                    ;"""% IDprestation
        DB.ExecuterReq(req,mess="DLG_Reglements_ventilation.CorrigeVentilation")
        self.lstRequetes.append(('ExecuterReq',(req)))

        # appel du détail des ventilations.
        req = """SELECT ventilation.IDventilation,ventilation.montant, prestations.montant, reglements.IDreglement
                FROM (  ventilation 
                        LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement) 
                        INNER JOIN prestations ON ventilation.IDprestation = prestations.IDprestation
                WHERE ventilation.IDprestation=%d
                ORDER BY reglements.date_saisie
                ;""" % IDprestation
        DB.ExecuterReq(req,mess="CTRL_Ventilation.CorrigeVentil2")
        lstDonnees = DB.ResultatReq()
        lstSupprime = []
        mttcum = 0.0
        montant = 0.0
        for IDventilation, ventile, montant, IDreglement in lstDonnees:
            # suppression de ventilation de signe inversé
            if (montant * ventile) < 0:
                lstSupprime.append(IDventilation)
                continue
            # suppression d'excédent d'affectation
            elif abs(montant) < abs(mttcum + ventile):
                lstSupprime.append(IDventilation)
                continue
            mttcum += ventile

        for IDventilation in lstSupprime:
            DB.ReqDEL('ventilation','IDventilation',IDventilation)

        DB.Close()
        return montant,mttcum

    def OnLeftClick(self, event):
        numLigne = event.GetRow()
        numColonne = event.GetCol()
        # Checkbox
        if numLigne in self.dictLignes.keys() :
            ligne = self.dictLignes[numLigne]
            if numColonne == 7 and ligne.GetEtat() == True :
                pass
            else :
                ligne.OnCheck()
        # Case montant modifiable
        if numColonne == 7 and numLigne in self.dictLignes.keys() :
            ligne = self.dictLignes[numLigne]
            if ligne.type_ligne == "prestation" and ligne.GetEtat() == True :
                event.Skip()
    
    def OnMouseOver(self, event):    
        return
        
    def MAJ(self):
        """ Met à jour (redessine) tout le contrôle """
        self.Freeze()
        if self.GetNumberRows() > 0 : 
            self.DeleteRows(0, self.GetNumberRows())
        self.Remplissage()
        self.Thaw()
        nbcol = self.GetNumberCols()
        for ix in range(nbcol-3):
            self.AutoSizeColumn(ix)
        self.Refresh()

    def Remplissage(self):
        # Regroupement
        self.dictRegroupements = {}
        listeKeys = []
        nbreLignes = 0
        for ligne_prestation in self.listeLignesPrestations :
            if self.KeyRegroupement == "individu" : 
                key = ligne_prestation.IDindividu
                if key == 0 or key == None :
                    label = ("Prestations familiales")
                else:
                    label = ligne_prestation.nomCompletIndividu
            if self.KeyRegroupement == "facture" : 
                key = ligne_prestation.IDfacture
                label = ligne_prestation.label_facture
            if self.KeyRegroupement == "date" : 
                key = ligne_prestation.date
                label = ligne_prestation.date_complete
            if self.KeyRegroupement == "periode" : 
                key = ligne_prestation.periode
                label = ligne_prestation.periode_complete
            
            if not key in self.dictRegroupements.keys() :
                self.dictRegroupements[key] = { "label" : label, "total" : 0.0, "prestations" : [], "ligne_regroupement" : None}
                listeKeys.append(key)
                nbreLignes += 1
                
            self.dictRegroupements[key]["prestations"].append(ligne_prestation)
            self.dictRegroupements[key]["total"] += ligne_prestation.montant
            nbreLignes += 1
        
        # Tri des Keys
        listeKeys.sort()
        
        # Création des lignes
        self.AppendRows(nbreLignes)
        
        # Création des branches
        numLigne = 0
        self.dictLignes = {}
        for key in listeKeys :
            
            # Niveau 1 : Regroupement
            dictRegroupement = self.dictRegroupements[key]
            ligne_regroupement = Ligne_regroupement(self, numLigne, dictRegroupement)
            self.dictLignes[numLigne] = ligne_regroupement
            self.dictRegroupements[key]["ligne_regroupement"] = ligne_regroupement
            numLigne += 1
            
            # Niveau 2 : Prestations
            for ligne_prestation in self.dictRegroupements[key]["prestations"] :
                ligne_prestation.Draw(numLigne, ligne_regroupement)
                ligne_prestation.MAJ(majTotaux=False)
                ligne_regroupement.listeLignesPrestations.append(ligne_prestation)
                self.dictLignes[numLigne] = ligne_prestation
                numLigne += 1
        
        # MAJ de tous les totaux
        self.MAJtotaux() 
        
    def MAJtotaux(self):
        """ Mise à jour de tous les totaux regroupements + barreInfos """
        # MAJ de tous les totaux de regroupement
        for key, dictRegroupement in self.dictRegroupements.items() :
            ligne_regroupement = dictRegroupement["ligne_regroupement"]
            ligne_regroupement.MAJ() 
        # MAJ de la barre d'infos
        self.MAJbarreInfos() 
        
    def SetRegroupement(self, key):
        self.KeyRegroupement = key
        self.MAJ() 

    def MAJbarreInfos(self, erreur=None):
        total = 0.0
        for ligne in self.listeLignesPrestations :
            total += ligne.ventilationActuelle
        self.parent.MAJbarreInfos(total, erreur)

    def SelectionneFacture(self, IDfacture=None):
        # Afficher par facture
        self.SetRegroupement("facture")
        # Coche les prestations liées à la facture données
        for key, dictRegroupement in self.dictRegroupements.iteritems():
            if key == IDfacture :
                ligne_regroupement = dictRegroupement["ligne_regroupement"]
                ligne_regroupement.SetEtat(True)

    def GetCreditAventiler(self):
        creditAVentiler = self.montant_reglement - self.GetTotalVentile()
        return creditAVentiler

    def GetTotalVentile(self):
        total = 0.0
        for ligne in self.listeLignesPrestations :
            total += ligne.ventilationActuelle
        return total

    def GetTotalRestePrestationsAVentiler(self):
        total = 0.0
        for ligne in self.listeLignesPrestations :
            total += ligne.resteAVentiler
        return total
    
    def Sauvegarde(self, IDreglement=None):
        """ Sauvegarde des données """
        DB = xdb.DB()
        for ligne in self.listeLignesPrestations :
            IDprestation = ligne.IDprestation
            montant = float(ligne.ventilationActuelle)
            
            if IDprestation in self.dictVentilationInitiale.keys() :
                IDventilation = self.dictVentilationInitiale[IDprestation]
            else:
                IDventilation = None
            
            if ligne.GetEtat() == True :
                # Ajout ou modification
                lstDonnees = [
                        ("IDreglement", IDreglement),
                        ("IDcompte_payeur", self.IDcompte_payeur),
                        ("IDprestation", IDprestation),
                        ("montant", montant),
                    ]
                if IDventilation == None :
                    DB.ReqInsert("ventilation", lstDonnees=lstDonnees,mess="DLG_Reglements_ventilation.Sauvegarde Insert")
                else:
                    DB.ReqMAJ("ventilation",lstDonnees,"IDventilation", IDventilation,
                              mess="DLG_Reglements_ventilation.Sauvegarde Maj")
            else :
                # Suppression
                if IDventilation != None :
                    DB.ReqDEL("ventilation", "IDventilation", IDventilation,mess="DLG_Reglements_ventilation.Sauvegarde Del")
        DB.Close()
        return

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

# ---------------------------------------------------------------------------------------------------------------------

class Panel(wx.Panel):
    def __init__(self, parent, IDcompte_payeur=None, IDreglement=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDcompte_payeur = IDcompte_payeur
        self.IDreglement = IDreglement
        self.montant_reglement = 0.0
        self.total_ventilation = 0.0
        self.validation = True
        
        if "linux" in sys.platform :
            defaultFont = self.GetFont()
            defaultFont.SetPointSize(8)
            self.SetFont(defaultFont)

        # Regroupement
        self.label_regroupement = wx.StaticText(self, -1, ("Regrouper par :"))
        self.radio_periode = wx.RadioButton(self, -1, ("Mois"), style = wx.RB_GROUP)
        self.radio_facture = wx.RadioButton(self, -1, ("Facture"))
        self.radio_individu = wx.RadioButton(self, -1, ("Individu"))
        self.radio_date = wx.RadioButton(self, -1, ("Date"))
        
        # Commandes rapides
        self.label_hyperliens_1 = wx.StaticText(self, -1, ("Ventiler "))
        self.hyper_automatique = Hyperlien(self, label=("automatiquement"), infobulle=("Cliquez ici pour ventiler automatiquement le crédit restant"), URL="automatique")
        self.label_hyperliens_2 = wx.StaticText(self, -1, u" | ")
        self.hyper_tout = Hyperlien(self, label=("tout"), infobulle=("Cliquez ici pour tout ventiler"), URL="tout")
        self.label_hyperliens_3 = wx.StaticText(self, -1, u" | ")
        self.hyper_rien = Hyperlien(self, label=("rien"), infobulle=("Cliquez ici pour ne rien ventiler"), URL="rien")
        
        # Liste de la ventilation
        self.ctrl_ventilation = CTRL_Ventilation(self, IDcompte_payeur, IDreglement)

        # Etat de la ventilation
        self.imgOk = wx.Bitmap("xpy/Images/16x16/Ok4.png", wx.BITMAP_TYPE_PNG)
        self.imgErreur = wx.Bitmap("xpy/Images/16x16/Interdit2.png", wx.BITMAP_TYPE_PNG)
        self.imgAddition = wx.Bitmap("xpy/Images/16x16/Addition.png", wx.BITMAP_TYPE_PNG)
        self.ctrl_image = wx.StaticBitmap(self, -1, self.imgAddition)
        
        self.ctrl_info = wx.StaticText(self, -1, ("Vous pouvez encore ventiler ---- €"))
        self.ctrl_info.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False))
        self.__do_layout()
        
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_periode)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_facture)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_individu)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_date)
        
        # Init
        self.ctrl_ventilation.InitGrid() 

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        
        grid_sizer_barre_haut = wx.FlexGridSizer(rows=1, cols=12, vgap=5, hgap=1)
        grid_sizer_barre_haut.Add(self.label_regroupement, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_barre_haut.Add(self.radio_periode, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add(self.radio_facture, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add(self.radio_individu, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add(self.radio_date, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_barre_haut.Add(self.label_hyperliens_1, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.hyper_automatique, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.label_hyperliens_2, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.hyper_tout, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.label_hyperliens_3, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.hyper_rien, 0, 0, 0)
        grid_sizer_barre_haut.AddGrowableCol(5)
        grid_sizer_base.Add(grid_sizer_barre_haut, 1, wx.EXPAND|wx.BOTTOM, 5)

        grid_sizer_base.Add(self.ctrl_ventilation, 1, wx.EXPAND, 0)
        
        grid_sizer_barre_bas = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_barre_bas.Add( (400, 5), 0, 0, 0)
        grid_sizer_barre_bas.Add(self.ctrl_image, 0, 0, 0)
        grid_sizer_barre_bas.Add(self.ctrl_info, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(grid_sizer_barre_bas, 1, wx.EXPAND|wx.TOP, 5)
        
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
    
    def OnRadioRegroupement(self, event):
        if self.radio_periode.GetValue() == True : key = "periode"
        if self.radio_facture.GetValue() == True : key = "facture"
        if self.radio_individu.GetValue() == True : key = "individu"
        if self.radio_date.GetValue() == True : key = "date"
        self.ctrl_ventilation.SetRegroupement(key)
    
    def MAJ(self):
        self.ctrl_ventilation.MAJ() 
        self.MAJinfos() 
    
    def SetMontantReglement(self, montant=0.0):
        if montant == None : return
        self.montant_reglement = montant
        self.ctrl_ventilation.montant_reglement = montant
        self.MAJinfos() 
    
    def MAJbarreInfos(self, total=0.0, erreur=None):
        self.total_ventilation = total
        self.MAJinfos(erreur) 
    
    def MAJinfos(self, erreur=None):
        self.negatif = False
        if self.montant_reglement < 0.00: self.negatif = True
        """ Recherche l'état """
        if self.montant_reglement == 0.0 :
            self.ctrl_image.SetBitmap(self.imgErreur)
            self.ctrl_info.SetLabel(("Le montant de ce règlement est Nul !"))
            #return

        if erreur == True :
            self.validation = "erreur"
            self.ctrl_image.SetBitmap(self.imgErreur)
            self.ctrl_info.SetLabel(("Vous avez saisi un montant non valide !"))
            return
        
        creditAVentiler = self.montant_reglement - self.total_ventilation
        
        totalRestePrestationsAVentiler = self.ctrl_ventilation.GetTotalRestePrestationsAVentiler()

        # Recherche de l'état
        if self.negatif == False:
            if creditAVentiler > totalRestePrestationsAVentiler :
                creditAVentiler = totalRestePrestationsAVentiler
            if creditAVentiler == 0.0 :
                self.validation = "ok"
                label = ("Ventilation complète !")
            elif creditAVentiler > 0.0 :
                self.validation = "addition"
                label = ("Reste à ventiler %.2f %s !") % (creditAVentiler, SYMBOLE)
            elif creditAVentiler < 0.0 :
                self.validation = "trop"
                label = ("Ventilation de %.2f %s en trop !") % (-creditAVentiler, SYMBOLE)
        else:
            #cas d'un montant négatif
            if creditAVentiler == 0.0 :
                self.validation = "ok"
                label = ("Ventilation complète !")
            elif creditAVentiler > 0.0 :
                self.validation = "addition"
                label = ("Ventilation de %.2f %s en trop !") % (-creditAVentiler, SYMBOLE)
            elif creditAVentiler < 0.0 :
                self.validation = "trop"
                label = ("Reste à ventiler %.2f %s !") % (creditAVentiler, SYMBOLE)
        # Affiche l'image
        if self.validation == "ok" : self.ctrl_image.SetBitmap(self.imgOk)
        if self.validation == "addition" : self.ctrl_image.SetBitmap(self.imgAddition)
        if self.validation == "trop" : self.ctrl_image.SetBitmap(self.imgErreur)
        # MAJ le label d'infos
        if label != self.ctrl_info.GetLabel() :
            self.ctrl_info.SetLabel(label)
        # Colore Label Ventilation Auto
        self.ColoreLabelVentilationAuto() 
        
    def Validation(self):
        creditAVentiler = self.montant_reglement - self.total_ventilation
        if self.validation == "ok" :
            return True
        if self.validation == "addition" :
            totalRestePrestationsAVentiler = self.ctrl_ventilation.GetTotalRestePrestationsAVentiler()
            if creditAVentiler > totalRestePrestationsAVentiler :
                creditAVentiler = totalRestePrestationsAVentiler
            if creditAVentiler > 0.0 :
                dlg = wx.MessageDialog(self, ("Vous devez encore ventiler %.2f %s.\n\nEtes-vous sûr de quand même vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), ("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                if self.negatif: dlg = wx.MessageDialog(self, ("Vous avez ventilé %.2f %s en trop !\n\nEtes-vous sûr de quand même vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), ("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse !=  wx.ID_YES :
                    return False
        if self.validation == "trop" :
            dlg = wx.MessageDialog(self, ("Vous avez ventilé %.2f %s en trop !\n\nEtes-vous sûr de quand même vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), ("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            if self.negatif : dlg = wx.MessageDialog(self, ("Vous devez encore ventiler %.2f %s.\n\nEtes-vous sûr de quand même vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), ("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                return False
        if self.validation == "erreur" :
            dlg = wx.MessageDialog(self, ("La ventilation n'est pas valide. Veuillez la vérifier..."), ("Erreur de saisie"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True

    def Sauvegarde(self, IDreglement=None):
        self.ctrl_ventilation.Sauvegarde(IDreglement)

    def SelectionneFacture(self, IDfacture=None):
        self.radio_facture.SetValue(True)
        self.ctrl_ventilation.SelectionneFacture(IDfacture)
    
    def ColoreLabelVentilationAuto(self):
        aVentiler = 0.0
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
             aVentiler += ligne.montant - ligne.ventilationPassee
        if self.montant_reglement == aVentiler :
            couleur = wx.Colour(0, 200, 0)
        else :
            couleur = "BLUE"
        self.hyper_automatique.SetColours(couleur, couleur, couleur)
        self.hyper_automatique.UpdateLink()

    def VentilationAuto(self):
        """ Procédure de ventilation automatique """
        # Traitement par pointage des prestations négatives
        presenceNegatif = False
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            aVentiler = ligne.resteAVentiler
            if ligne.montant < 0.0 and aVentiler != 0.0:
                presenceNegatif = True
                montant = aVentiler + ligne.ventilationActuelle
                ligne.SetEtat(etat=True, montant=montant, majTotaux=False)
        if presenceNegatif:
                dlg = wx.MessageDialog(None, ("Présence de prestations aux valeurs négatives !\n\nLa ventilation automatique affecte prioritairement tous les montants négatifs !"), ("Information"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
        # Ventilation automatique
        totalVentilation = self.ctrl_ventilation.GetTotalVentile()
        resteVentilation = self.montant_reglement - totalVentilation
        if resteVentilation <= 0.0 :
            dlg = wx.MessageDialog(self, ("Vous avez déjà ventilé tout le crédit disponible !"), ("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            aVentiler = resteVentilation
            if aVentiler > ligne.resteAVentiler :
                aVentiler = ligne.resteAVentiler
            if aVentiler > 0.0 :
                montant = aVentiler + ligne.ventilationActuelle
                ligne.SetEtat(etat=True, montant=montant, majTotaux=False)
                resteVentilation -= aVentiler
        self.ctrl_ventilation.MAJtotaux()
        
    def VentilationTout(self):
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            aVentiler = ligne.montant - ligne.ventilationPassee
            ligne.SetEtat(etat=True, montant=aVentiler, majTotaux=False)
        self.ctrl_ventilation.MAJtotaux()
        
    def VentilationRien(self):
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            ligne.SetEtat(False, majTotaux=False)
        self.ctrl_ventilation.MAJtotaux()

class Dialog(wx.Dialog):
    def __init__(self,parent,ID,titre,IDcompte_payeur=None, IDreglement=None,mttReglement=0.0, **kwds):
        if (not IDcompte_payeur) or IDcompte_payeur == 0: return
        if not ID: ID = -1
        if not titre: titre = "DLG_Reglements_ventilation"
        wx.Dialog.__init__(self, parent,ID,titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,**kwds)

        txtInfos = "Ventilation non obligatoire\nAffectez ce règlement aux prestations auquelles il se rapporte"
        lstInfos = [wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)), txtInfos]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}
        self.pnlPied = PNL_pied(self,dicPied)

        self.panel = Panel(self, IDcompte_payeur=IDcompte_payeur, IDreglement=IDreglement)
        self.panel.SetMontantReglement(mttReglement)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.ALL|wx.EXPAND)
        sizer.Add(self.pnlPied, 0, wx.ALL|wx.EXPAND, 4)

        self.SetSize((1050, 500))
        self.SetSizer(sizer)

        self.Layout()
        self.CenterOnScreen()
        # Décrochement si rien à ventiler
        if len(self.panel.ctrl_ventilation.dictLignes) == 0:
            wx.MessageBox("Pas de prestations non réglées dans Noethys! \nPas d'opération en cours c'est un acompte!",
                          style=wx.ICON_INFORMATION)
            self.ok = False
        else: self.ok = True

    def OnBoutonOK(self, event):
        if self.panel.validation != "ok":
            txt = "Vous n'avez pas ventilé exactement\n\nVous pouvez saisir un montant exact dans la colonne de droite"
            txt += "\nConfirmez-vous la validation?"
            if wx.YES != wx.MessageBox(txt,style=wx.YES_NO):
                return
        self.EndModal(wx.OK)

    def OnAbort(self,event):
        self.EndModal(wx.ID_CANCEL)

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    kwds = {'IDcompte_payeur': 9, 'IDreglement' : 26571, 'mttReglement' :300.00}
    dlg = Dialog(None, None,None,**kwds)
    app.SetTopWindow(dlg)
    if dlg:
        print(dlg.ShowModal())
    app.MainLoop()
