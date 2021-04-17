#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    Projet xpy, gérer des boutons par des paramètres
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx
import wx.adv
import wx.lib.newevent
import wx.lib.masked as masked
import calendar
import datetime
import sys
from xpy.outils import xboutons,xformat
from xpy.outils.xconst          import *

SelectDatesEvent, EVT_SELECT_DATES = wx.lib.newevent.NewEvent()

# -----------------------------------------------------------

class TxtDate(masked.TextCtrl):
    """ Contrôle Date avec mask de saisie """
    def __init__(self, parent):
        masked.TextCtrl.__init__(self, parent, -1, "", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE, mask = "##/##/####")
        self.parent = parent
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnKillFocus(self, event):
        # Envoi un signal de changement de date au panel parent
        try:
            self.parent.OnChoixDate(event)
        except:
            pass
        event.Skip()

# saisie date avec calendrier incorporé
class CTRL_SaisieDate(wx.Panel):
    def __init__(self, parent, **kwds):
        name = kwds.pop("name","CTRL_SaisieDate")
        label = kwds.pop("label","")
        minSize = kwds.pop("minSize",(100 + len(label)*5, 25))
        wx.Panel.__init__(self, parent, id=-1, name=name)
        self.parent = parent
        # kwcal sera adressé au panel calendrier
        self.kwcal = kwds.pop('kwcal',{'typeCalendrier':'mensuel'})
        # kwdlg sera adressé au Dialog d'affichage conteneur fenêtre du calendrier
        self.kwdlg = kwds.pop('kwdlg',{'size':(350,350)})

        self.labelDate = wx.StaticText(self, -1, label)
        #self.ctrlDate = TxtDate(self)
        self.ctrlDate = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
        self.ctrlDate.Bind(wx.EVT_KILL_FOCUS, self.OnChoixDate)
        self.ctrlDate.Bind(wx.EVT_TEXT_ENTER, self.OnChoixDate)

        self.btnDate = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Calendrier.png", wx.BITMAP_TYPE_ANY))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonDate, self.btnDate)

        self.btnDate.SetToolTip("Cliquez ici pour choisir une date à partir du calendrier")
        mess = "Saisissez directement  'jjmmaa', ou choisissez via le calendrier"
        self.ctrlDate.SetToolTip(mess)
        self.labelDate.SetToolTip(mess)
        self.SetMinSize(minSize)

        # Sizer
        grid_sizer_dates = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_dates.Add(self.labelDate, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.ctrlDate, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.btnDate, 0, 0, 0)
        self.SetSizer(grid_sizer_dates)
        grid_sizer_dates.Fit(self)

    def OnChoixDate(self,event):
        # vérification de la validité de la date par passage en datetime et réaffichage
        dtDate = None
        origine = event.EventObject.Parent.Name
        event.Skip()
        try:
            dtDate = xformat.DateToDatetime(self.GetValue())
        except:
            self.SetValue('')
            self.SetFocus()
        if dtDate:
            self.SetValue(xformat.DatetimeToStr(dtDate))
            if hasattr(self.parent,'OnChoixDate'):
                self.parent.OnChoixDate(origine)


    def SetFocus(self):
        self.ctrlDate.SetFocus()

    def OnBoutonDate(self, event):
        dlg = DLG_calendrier(self,kwcal=self.kwcal,kwdlg=self.kwdlg)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrlDate.SetValue(xformat.DatetimeToStr(date))
        dlg.Destroy()

    def SetValue(self,date):
        # affichée en format fr
        self.ctrlDate.SetValue(xformat.DateToFr(date))

    def GetValue(self):
        #date retournée en ansi
        return xformat.DateFrToSql(self.ctrlDate.GetValue())

# saisie de deux dates définissant une période
class CTRL_Periode(wx.Panel):
    def __init__(self, parent, **kwds):
        name = kwds.pop("name","CTRL_Periode")
        label = kwds.pop("label","Période")
        orientation = kwds.pop("orientation",wx.VERTICAL)

        wx.Panel.__init__(self, parent, id=-1, name=name, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.kwcal = kwds.pop('kwcal',{'typeCalendrier':'annuel'})
        self.kwdlg = kwds.pop('kwdlg',{'size':(450,450)})

        self.stboxPeriode = wx.StaticBox(self, wx.ID_ANY, "Période")
        self.ctrlSaisieDu = CTRL_SaisieDate(self,name="date_du",label="du : ",kwcal=self.kwcal,kwdlg=self.kwdlg)
        self.ctrlSaisieAu = CTRL_SaisieDate(self,name="date_au",label="au : ",kwcal=self.kwcal,kwdlg=self.kwdlg)

        # Sizert
        static_sizer_periode = wx.StaticBoxSizer(self.stboxPeriode,orientation)
        static_sizer_periode.Add((1,1), 1, wx.EXPAND, 0)
        static_sizer_periode.Add(self.ctrlSaisieDu, 10, wx.LEFT|wx.EXPAND, 15)
        static_sizer_periode.Add(self.ctrlSaisieAu, 10, wx.LEFT|wx.EXPAND, 15)
        #static_sizer_periode.Add((100,100), 1, wx.EXPAND, 0)
        self.SetSizer(static_sizer_periode)

    def OnChoixDate(self,origine):
        if  origine == 'date_du':
            self.ctrlSaisieAu.SetFocus()
        else:
            debut,fin = self.GetValue()
            if len(fin)>0 and fin < debut:
                wx.MessageBox("La date fin est antérieure au début!!")
            elif hasattr(self.parent,'OnChoixDate'):
                # relais du Bind au parent après saisie de la deuxième date
                self.parent.OnChoixDate()

    def SetValue(self,tplDates):
        # le tuple correspond aux deux dates
        self.ctrlSaisieDu.SetValue(tplDates[0])
        self.ctrlSaisieAu.SetValue(tplDates[1])

    def GetValue(self):
        # retourne tuple deux dates en ansi
        return  (self.ctrlSaisieDu.GetValue(),self.ctrlSaisieAu.GetValue())


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# affiche un caldendrier et les binds
class Calendrier(wx.ScrolledWindow):
    def __init__(self, parent, ID=-1, multiSelections=True, selectionInterdite=False, typeCalendrier="mensuel"):
        super().__init__( parent, ID, style=wx.NO_BORDER)
        self.multiSelections = multiSelections
        self.selectionInterdite = selectionInterdite
        self.listeFeriesFixes = []
        self.joursVacances = []
        self.listeFeriesVariables = []
        self.SetMinSize((100, 140))

        # Variables à ne surtout pas changer
        self.caseSurvol = None
        self.multiSelect = None
        self.onLeave = True

        # Variables qui peuvent être changées
        self.listeSelections = []

        self.ecartCases = 2  # Ecart en pixels entre les cases jours d'un mois
        self.ecartMois = 8  # Ecart en pixels entre chaque mois dan un calendrier annuel

        self.couleurFond = (255, 255, 255)  # (255, 255, 255)       # Couleur du fond du calendrier
        self.couleurNormal = (
        255, 255, 255)  # (214, 223, 247) #(175, 225, 251)     # Couleur d'un jour normal du lundi au vendredi
        self.couleurWE = (231, 245, 252)  # (171, 249, 150)         # Couleur des samedis et dimanche
        self.couleurSelect = (55, 228, 9)  # Couleur du fond de la case si celle-ci est sélectionnée
        self.couleurSurvol = (0, 0, 0)  # Couleur du bord de la case si celle-ci est survolée
        self.couleurFontJours = (0, 0, 0)
        self.couleurVacances = (255, 255, 255)  # Couleur des cases dates d'ouverture de la structure
        self.couleurFontJoursAvecPresents = (255, 0, 0)
        self.couleurFerie = (180, 180, 180)  # couleur des jours fériés

        self.headerMois = True
        self.headerJours = True

        self.typeCalendrier = typeCalendrier
        self.moisCalendrier = 2
        self.anneeCalendrier = 2008

        self.selectExclureWE = True  # Inclure les WE quand une période de vacs est sélectionnée dans le menu contextuel

        # Pour statusBar :
        try:
            self.frameParente = self.GetGrandParent().GetGrandParent().GetParent()
        except:
            pass

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Init DC :
        self.CreatePseudoDC()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)

    def MAJpanel(self):
        self.CreatePseudoDC()
        self.Refresh()

    def CreatePseudoDC(self):
        # create a PseudoDC to record our drawing
        self.pdc = wx.adv.PseudoDC()
        self.DoDrawing(self.pdc)

    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
                event.GetY() + (yView * yDelta))

    def OffsetRect(self, r):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.Offset(-(xView * xDelta), -(yView * yDelta))

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.BufferedPaintDC(self)
        # use PrepateDC to set position correctly
        if wx.VERSION < (2, 9, 0, 0):
            self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        # create a clipping rect from our position and size
        # and the Update Region
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x, y)
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc, r)

    def DoDrawing(self, dc):
        dc.RemoveAll()
        self.caseSurvol = None
        self.Calendrier(dc)

    def MAJAffichage(self):
        self.DoDrawing(self.pdc)
        self.Refresh()

    def OnSize(self, event):
        self.MAJAffichage()
        event.Skip()

    def Calendrier(self, dc):
        self.dictCases = {}
        self.listeCasesJours = []
        largeur, hauteur = self.GetSize()
        annee = self.anneeCalendrier


        if self.typeCalendrier == "mensuel":
            # Création d'un calendrier mensuel
            mois = self.moisCalendrier
            self.listeJoursAvecPresents = []
            self.DrawMonth(dc, mois, annee, 0, 0, largeur, hauteur)
        else:
            # Création d'un calendrier annuel
            largeurMois = largeur / 4.0
            hauteurMois = hauteur / 3.0
            numMois = 1
            self.listeJoursAvecPresents = []
            for colonne in range(3):
                y = colonne * (hauteurMois + (self.ecartMois / 2.0))
                for ligne in range(4):
                    x = ligne * (largeurMois + (self.ecartMois / 3.0))
                    self.DrawMonth(dc, numMois, annee, x, y, largeurMois - self.ecartMois, hauteurMois - self.ecartMois)
                    numMois += 1

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self.multiSelect = "CONTROL"
        if keycode == wx.WXK_SHIFT:
            self.multiSelect = "SHIFT"
            self.multiSelectWE = True
        if keycode == wx.WXK_ALT:
            self.multiSelect = "SHIFT"
            self.multiSelectWE = False
        event.Skip()

    def OnKeyUp(self, event):
        self.multiSelect = None
        self.multiSelectWE = False
        event.Skip()

    def VerifKeyStates(self):
        """ est utilisé pour être sûr que le programme a bien remarqué les touches pressées """
        etat_Control = wx.GetKeyState(wx.WXK_CONTROL)
        etat_Shift = wx.GetKeyState(wx.WXK_SHIFT)
        etat_Alt = wx.GetKeyState(wx.WXK_ALT)

        if etat_Control == True:
            self.multiSelect = "CONTROL"
        if etat_Shift == True:
            self.multiSelect = "SHIFT"
            self.multiSelectWE = True
        if etat_Alt == True:
            self.multiSelect = "SHIFT"
            self.multiSelectWE = False

    def OnLeftDown(self, event):
        """ Sélection de la case cliquée """
        self.VerifKeyStates()
        if self.multiSelections == False:
            self.multiSelect = None
            self.multiSelectWE = False

        if self.selectionInterdite == True:
            return

        x, y = self.ConvertEventCoords(event)
        listeObjets = self.pdc.FindObjectsByBBox(x, y)
        IDobjet = 0
        if len(listeObjets) != 0:
            IDobjet = listeObjets[0]
            date = self.IDobjetEnDate(IDobjet)
            x = 1
            if x == 1:

                # CASES DATES -----------------------------------------------------------------------

                # Si la case est déjà sélectionnée, on la supprime de la liste des sélections
                if len(self.listeSelections) != 0:
                    if date in self.listeSelections:
                        self.listeSelections.remove(date)
                        self.RedrawCase(IDobjet, survol=True)
                        self.SendDates()
                        return

                # Ajout de la case à la liste des sélections
                if self.multiSelect == "CONTROL":
                    # MultiSelections avec la touche CTRL
                    self.listeSelections.append(date)
                    IDobjet = self.DateEnIDobjet(date)
                    self.RedrawCase(IDobjet, survol=True)
                    self.SendDates()

                elif self.multiSelect == "SHIFT":
                    # MultisSelections avec la touche SHIFT
                    self.listeSelections.append(date)
                    self.listeSelections.sort()
                    posTemp = self.listeSelections.index(date) - 1
                    previousDate = self.listeSelections[posTemp]
                    jourDebut = previousDate
                    jourFin = date

                    # Si sélection inverse
                    if jourDebut > jourFin:
                        jourDebut = date
                        jourFin = previousDate

                    nbreJours = (jourFin - jourDebut).days

                    dateEnCours = jourDebut
                    for j in range(nbreJours):
                        dateEnCours = dateEnCours + datetime.timedelta(days=1)

                        # si MultiSelectWE=False, on ne garde ni les samedis ni les dimanches
                        if self.multiSelectWE == False:
                            if dateEnCours.isoweekday() == 6 or dateEnCours.isoweekday() == 7:
                                continue

                        # Mémorisation de la date
                        if not dateEnCours in self.listeSelections:
                            self.listeSelections.append(dateEnCours)

                    # Si le dernier jour est dans le week-end et si MultiSelectWE=False, on le supprime
                    if self.multiSelectWE == False:
                        if dateEnCours.isoweekday() == 6 or dateEnCours.isoweekday() == 7:
                            self.listeSelections.remove(date)

                    self.listeSelections.sort()
                    self.MAJAffichage()
                    self.RedrawCase(IDobjet, survol=True)
                    self.SendDates()

                else:
                    # Sélection Unique
                    self.listeSelections = []
                    self.listeSelections.append(date)
                    self.MAJAffichage()
                    self.RedrawCase(IDobjet, survol=True)
                    self.SendDates()

        else:

            # CASES NOMS DE JOURS -----------------------------------------------------------------
            if self.multiSelections == False:
                return

            for caseJour in self.listeCasesJours:
                if (caseJour[0] <= x <= (caseJour[0] + caseJour[2])) and (
                        caseJour[1] <= y <= (caseJour[1] + caseJour[3])):

                    # Sélection par colonne
                    if self.multiSelect == "CONTROL" or self.multiSelect == "SHIFT":
                        deselect = []
                        nbreSemaines = 0
                        # avec la touche CTRL
                        numJour, mois, annee = caseJour[4]
                        datesMois = calendar.monthcalendar(annee, mois)
                        for semaine in datesMois:
                            selTemp = semaine[numJour]
                            if selTemp != 0:
                                nbreSemaines += 1
                                dateTemp = datetime.date(annee, mois, selTemp)
                                if dateTemp not in self.listeSelections:
                                    self.listeSelections.append(dateTemp)
                                else:
                                    deselect.append(dateTemp)

                        # Si tous les jours ont déjà été sélectionnés, c'est que l'on doit désélectionner tout le mois :
                        if len(deselect) == nbreSemaines:
                            for date in deselect:
                                self.listeSelections.remove(date)

                    else:
                        # Sélection Unique
                        tempSelections = []
                        deselect = []
                        nbreSemaines = 0
                        numJour, mois, annee = caseJour[4]
                        datesMois = calendar.monthcalendar(annee, mois)
                        for semaine in datesMois:
                            selTemp = semaine[numJour]
                            if selTemp != 0:
                                nbreSemaines += 1
                                dateTemp = datetime.date(annee, mois, selTemp)
                                if dateTemp not in self.listeSelections:
                                    tempSelections.append(dateTemp)
                                else:
                                    deselect.append(dateTemp)

                        # Si tous les jours ont déjà été sélectionnés, c'est que l'on doit désélectionner tout le mois :
                        if len(deselect) == nbreSemaines:
                            self.listeSelections = []
                        else:
                            # Sélection de tout le mois
                            self.listeSelections = []
                            for date in tempSelections:
                                self.listeSelections.append(date)
                            for date in deselect:
                                self.listeSelections.append(date)

            self.SendDates()
            self.MAJAffichage()

        event.Skip()

    def SendDates(self):
        """ Envoie la liste des dates sélectionnées """
        event = SelectDatesEvent(selections=self.listeSelections)
        wx.PostEvent(self.GetParent(), event)

    def OnLeave(self, event):
        if self.onLeave == True:
            if self.caseSurvol != None:
                self.RedrawCase(self.caseSurvol, survol=False)
                self.caseSurvol = None
                try:
                    wx.GetApp().GetTopWindow().SetStatusText("", 0)
                except:
                    pass
        try:
            wx.GetApp().GetTopWindow().SetStatusText("", 0)
        except:
            pass
        event.Skip()

    def OnEnter(self, event):
        txt = ("Restez appuyer sur les touches CONTROL, SHIFT ou ALT pour sélectionner plusieurs jours à la fois.")
        try:
            wx.GetApp().GetTopWindow().SetStatusText(txt, 1)
        except:
            pass
        event.Skip()

    def RedrawCase(self, IDobjet, survol=False):
        """ Redessine une case """
        # DC
        dc = self.pdc
        # Efface l'id de la liste des objets du pseudoDC
        dc.ClearId(IDobjet)
        # Redessine la case
        caractCase = self.dictCases[IDobjet]
        self.DrawCase(dc, caractCase[4], caractCase[0], caractCase[1], caractCase[2], caractCase[3], survol=survol)
        # Redessine uniquement la zone modifiée
        r = dc.GetIdBounds(IDobjet)
        self.OffsetRect(r)
        self.RefreshRect(r, False)

    def OnMotion(self, event):
        # Allume la case
        x, y = self.ConvertEventCoords(event)
        listeObjets = self.pdc.FindObjectsByBBox(x, y)
        IDobjet = 0
        if len(listeObjets) != 0:
            IDobjet = listeObjets[0]
            # Si cette case est déjà actuellement survolée, on passe...
            if self.caseSurvol != None:
                if self.caseSurvol == IDobjet: return
            # Activation de la case sélectionnée
            # Si une case a déjà été survolée avant, on l'annule
            if self.caseSurvol != None:
                self.RedrawCase(self.caseSurvol, survol=False)
            # Redessine la nouvelle case
            self.caseSurvol = IDobjet
            self.RedrawCase(IDobjet, survol=True)

            # Ecriture d'un texte dans la statutBar
            date = self.IDobjetEnDate(IDobjet)
            listeJours = LISTE_JOURS
            listeMois = [x.lower() for x in LISTE_MOIS]

            dateStr = listeJours[date.weekday()] + " " + str(date.day) + " " + listeMois[date.month - 1] + " " + str(
                date.year)
            texteStatusBar = dateStr

            # Si c'est un jour de vacances
            if date in self.joursVacances:
                texteStatusBar += (" | Jour de vacances")

            # Si c'est un jour férié
            if (date.day, date.month) in self.listeFeriesFixes:
                texteStatusBar += (" | Jour férié")
            else:
                if date in self.listeFeriesVariables:
                    texteStatusBar += (" | Jour férié")

            # Actualisation la statusBar
            try:
                wx.GetApp().GetTopWindow().SetStatusText(texteStatusBar, 0)
            except:
                pass

            return

        # Si on ne survole aucune case : Désactivation de la case précédemment sélectionnée
        if self.caseSurvol != None:
            self.RedrawCase(self.caseSurvol, survol=False)
            self.caseSurvol = None
            try:
                wx.GetApp().GetTopWindow().SetStatusText("", 0)
            except:
                pass

    def DrawMonth(self, dc, mois, annee, xMois, yMois, largMois, hautMois):
        """ Dessine un mois entier """

        # Recherche une liste des dates du mois
        datesMois = calendar.monthcalendar(annee, mois)
        nbreSemaines = len(datesMois)

        # Création de l'entete avec le nom du mois
        if self.headerMois == True:
            hautMois, yMois = self.DrawHeaderMois(dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois)

        # Création de l'entete avec les noms des jours
        if self.headerJours == True:
            hautMois, yMois = self.DrawHeaderJours(dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois)

        # Calcule la taille d'une case
        largCase = (largMois / 7.0)
        hautCase = (hautMois / float(nbreSemaines))

        # Créée les cases jours
        for numSemaine in range(nbreSemaines):
            for numJour in range(7):

                jour = datesMois[numSemaine][numJour]

                if jour != 0:
                    # Crée les données de la case
                    x = xMois + (largCase * numJour)
                    y = yMois + (hautCase * numSemaine)
                    l = largCase - self.ecartCases
                    h = hautCase - self.ecartCases
                    texteDate = datetime.date(annee, mois, jour)

                    # Enregistrement des données dans une liste
                    caractCase = (x, y, l, h, texteDate)
                    IDcase = self.DateEnIDobjet(texteDate)
                    self.dictCases[IDcase] = caractCase

                    # Dessin de la case
                    self.DrawCase(dc, texteDate, x, y, l, h)

    def DateEnIDobjet(self, date):
        annee = str(date.year)
        mois = str(date.month)
        jour = str(date.day)
        if len(mois) == 1: mois = "0" + mois
        if len(jour) == 1: jour = "0" + jour
        IDobjet = int(annee + mois + jour)
        return IDobjet

    def IDobjetEnDate(self, IDobjet):
        IDobjet = str(IDobjet)
        annee = int(IDobjet[:4])
        mois = int(IDobjet[4:6])
        jour = int(IDobjet[6:8])
        date = datetime.date(annee, mois, jour)
        return date

    def DrawHeaderJours(self, dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois):
        """ Dessine un header comportant les noms des jours """
        # self.listeCasesJours = []
        listeJours = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
        largCase = (largMois / 7.0)
        hautCase = (hautMois / float(nbreSemaines))
        # Réglage de la police
        dc.SetTextForeground(self.couleurFontJours)
        taille = self.tailleFont(largCase, hautCase)
        font = wx.Font(taille, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        hautHeader = taille * 2
        x = 0
        for jour in range(7):
            texte = listeJours[jour]
            texteComplet = (jour, mois, annee)
            # Réglage du format du texte en fonction de la taille de la case
            if largCase < 50:
                texte = texte[:3]
            if largCase < 25:
                texte = texte[0]
            largTexte, hautTexte = self.GetTextExtent(texte)
            coordX = xMois + x + (largCase / 2) - (largTexte / 2)
            coordY = yMois + (hautHeader / 2) - (hautTexte / 2)
            dc.DrawText(texte, coordX, coordY)
            # Mémorisation des jours et de leurs coordonnées
            self.listeCasesJours.append((coordX, coordY, largTexte, hautTexte, texteComplet))
            x += largCase

        return hautMois - hautHeader, yMois + hautHeader

    def DrawHeaderMois(self, dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois):
        """ Dessine un header comportant le nom du mois """
        listeMois = LISTE_MOIS
        largCase = (largMois / 7.0)
        hautCase = (hautMois / float(nbreSemaines))
        # Réglage de la police
        dc.SetTextForeground(self.couleurFontJours)
        taille = self.tailleFont(largCase, hautCase)
        font = wx.Font(taille, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        hautHeader = taille * 3
        # Dessin du texte
        texte = listeMois[mois - 1] + " " + str(annee)
        largTexte, hautTexte = self.GetTextExtent(texte)
        dc.DrawText(texte, xMois + (largMois / 2) - (largTexte / 2), yMois + (hautHeader / 2) - (hautTexte / 2))
        # Dessin de la ligne
        dc.SetPen(wx.Pen((210, 210, 210), 1))
        dc.DrawLine(xMois + 2, yMois + hautHeader - 2, xMois + largMois - 2, yMois + hautHeader - 2)

        return hautMois - hautHeader, yMois + hautHeader

    def DrawCase(self, dc, texteDate, x, y, l, h, survol=False):

        IDobjet = self.DateEnIDobjet(texteDate)
        dc.SetId(IDobjet)

        # Application des couleurs normales
        dc.SetBrush(wx.Brush(self.couleurNormal))
        dc.SetPen(wx.Pen(self.couleurFond, 1))


        # Si c'est un jour de Week-end
        jourSemaine = texteDate.isoweekday()
        if jourSemaine == 6 or jourSemaine == 7:
            dc.SetBrush(wx.Brush(self.couleurWE))

        # Si c'est un jour férié
        if (texteDate.day, texteDate.month) in self.listeFeriesFixes:
            dc.SetBrush(wx.Brush(self.couleurFerie))
        else:
            if texteDate in self.listeFeriesVariables:
                dc.SetBrush(wx.Brush(self.couleurFerie))

        # Si c'est une case survolée
        if survol == True:
            # dc.SetBrush(wx.Brush('black', wx.TRANSPARENT))
            dc.SetPen(wx.Pen(self.couleurSurvol, 1))

        # Dessine d'une case sélectionnée
        if len(self.listeSelections) != 0:
            if texteDate in self.listeSelections:
                dc.SetBrush(wx.Brush(self.couleurSelect))

        # Dessin de la case
        dc.DrawRectangle(x, y, l, h)

        # Dessin du symbole Aujourd'hui
        if texteDate == datetime.date.today():
            dc.SetBrush(wx.Brush((255, 0, 0)))
            dc.SetPen(wx.Pen((255, 0, 0), 0))
            posG = x + l - 2
            posH = y + 1
            tailleTriangle = 5
            dc.DrawPolygon([(posG, posH), (posG - tailleTriangle, posH), (posG, posH + tailleTriangle)])

        # Dessin texte
        if str(texteDate) in self.listeJoursAvecPresents:
            dc.SetTextForeground(self.couleurFontJoursAvecPresents)
        else:
            dc.SetTextForeground(self.couleurFontJours)

        font = self.GetFont()
        font.SetPointSize(self.tailleFont(l, h))
        dc.SetFont(font)
        dc.DrawText(str(texteDate.day), x + 3, y + 2)

        # Traitement pour le PseudoDC
        r = wx.Rect(x, y, l, h)
        dc.SetIdBounds(IDobjet, r)

    def tailleFont(self, l, h):

        # On prend le côté le plus petit
        if l > h:
            cote = h
        else:
            cote = l
        # On définit des ordres de grandeur
        if cote <= 14: return 6
        if cote <= 20: return 7
        if cote <= 40: return 7
        if cote <= 60: return 8
        if cote <= 80: return 9
        if cote <= 120: return 10
        return 12

    def SetTypeCalendrier(self, typeCal):
        self.typeCalendrier = typeCal
        self.MAJAffichage()

    def SetMoisAnneeCalendrier(self, mois=0, annee=0):
        if mois != 0: self.moisCalendrier = mois
        if annee != 0: self.anneeCalendrier = annee
        self.MAJAffichage()

    def GetMoisAnneeCalendrier(self):
        return self.moisCalendrier, self.anneeCalendrier

    def GetTypeCalendrier(self):
        return self.typeCalendrier

    def OnContextMenu(self, nomCase):
        """ Menu contextuel du calendrier """
        if self.caseSurvol != None:
            texteDate = self.IDobjetEnDate(self.caseSurvol)
        else:
            texteDate = None

        if self.selectionInterdite == True:
            return

        # Création du menu
        menu = wx.Menu()

        if self.multiSelections == True:

            # Si une date a bien été cliquée :
            if texteDate != None:
                # Vérifie si date déjà sélectionnée
                if texteDate in self.listeSelections:
                    select = True
                else:
                    select = False
                # Sélection/déselection du jour cliqué
                self.popupID1 = wx.ID_ANY
                if select == False:
                    texte = ("Sélectionner le %02d/%02d/%04d") % (texteDate.day, texteDate.month, texteDate.year)
                else:
                    texte = ("Désélectionner le %02d/%02d/%04d") % (texteDate.day, texteDate.month, texteDate.year)
                menu.Append(self.popupID1, texte)
                self.Bind(wx.EVT_MENU, self.OnPopup1, id=self.popupID1)

                menu.AppendSeparator()

        # Choisir la date d'aujourd'hui
        self.popupID4 = wx.ID_ANY
        menu.Append(self.popupID4, ("Sélectionner aujourd'hui"))
        self.Bind(wx.EVT_MENU, self.OnPopup4, id=self.popupID4)

        if self.multiSelections == True:

            # Choisir tout le mois
            self.popupID5 = wx.ID_ANY
            menu.Append(self.popupID5, ("Sélectionner tout le mois"))
            self.Bind(wx.EVT_MENU, self.OnPopup5, id=self.popupID5)

            # Choisir une période de vacances
            self.popupID3 = wx.ID_ANY
            if len(self.listePeriodesVacs) != 0:
                sm = wx.Menu()
                index = 0
                self.listePeriodesVacs.reverse()
                # Seules les 20 dernières périodes sont retenues
                for annee, nomPeriode, listeJours in self.listePeriodesVacs[:20]:
                    id = 1000 + index
                    sm.Append(id, nomPeriode + " " + str(annee))
                    self.Bind(wx.EVT_MENU, self.OnPopup3, id=id)
                    index += 1
                # Inclus le sous-menu dans le menu
                menu.AppendMenu(self.popupID3, ("Sélectionner une période de vacances"), sm)

            # Tout désélectionner
            self.popupID7 = wx.ID_ANY
            menu.Append(self.popupID7, ("Tout désélectionner"))
            self.Bind(wx.EVT_MENU, self.OnPopup7, id=self.popupID7)

            # Exclure les jours de week-end dans les sélections
            self.popupID6 = wx.ID_ANY
            menu.Append(self.popupID6, ("Exclure les week-ends des sélections"),
                        ("Exclure les week-ends de la sélection"), wx.ITEM_CHECK)
            if self.selectExclureWE == True:
                menu.Check(self.popupID6, True)
            self.Bind(wx.EVT_MENU, self.OnPopup6, id=self.popupID6)

        # Aide sur le calendrier
        menu.AppendSeparator()

        self.onLeave = False
        self.PopupMenu(menu)
        menu.Destroy()
        self.onLeave = True
        # self.RedrawCase(caseSurvol, survol=True)

    def OnPopup1(self, event):
        """ Sélection ou désélection """
        texteDate = self.IDobjetEnDate(self.caseSurvol)

        # Vérifie si date déjà sélectionnée
        if texteDate in self.listeSelections:
            select = True
        else:
            select = False

        # Désélection de la date
        if select == True:
            self.listeSelections.remove(texteDate)
            self.SelectJours(self.listeSelections)
            ##            self.RedrawCase(self.caseSurvol, survol=True)
            return

        # Sélection de la date
        else:
            self.listeSelections.append(texteDate)
            self.SelectJours(self.listeSelections)
            ##            self.RedrawCase(self.caseSurvol, survol=True)
            return

    def OnPopup3(self, event):
        """ Sélection d'une période de vacances """
        index = event.GetId() - 1000
        nomPeriode, annee, listeJours = self.listePeriodesVacs[index]
        # Mets les jours de vacances dans la liste de sélections

        # Enleve les week-ends si nécessaires :
        if self.selectExclureWE == True:
            listeJoursTmp = []
            for jour in listeJours:
                jourSemaine = jour.isoweekday()
                if jourSemaine != 6 and jourSemaine != 7:
                    listeJoursTmp.append(jour)
            listeJours = listeJoursTmp

        self.SelectJours(list(listeJours))

    def OnPopup6(self, event):
        """ Inclure ou non les week-ends dans la sélection """
        self.selectExclureWE = event.IsChecked()

    def OnPopup4(self, event):
        """ Choisir la date d'aujourd'hui """
        self.SelectJours([datetime.date.today(), ])

    def OnPopup5(self, event):
        """ Choisir tout le mois """
        listeJours = []
        datesDuMois = calendar.monthcalendar(self.anneeCalendrier, self.moisCalendrier)
        for semaine in datesDuMois:
            for jour in semaine:
                if jour != 0:
                    jourTmp = datetime.date(year=self.anneeCalendrier, month=self.moisCalendrier, day=jour)
                    if self.selectExclureWE == True:
                        jourSemaine = jourTmp.isoweekday()
                        if jourSemaine != 6 and jourSemaine != 7:
                            listeJours.append(jourTmp)
                    else:
                        listeJours.append(jourTmp)
        self.SelectJours(listeJours)

    def OnPopup7(self, event):
        """ Tout désélectionner """
        self.SelectJours(listeJours=[])

    def SelectJours(self, listeJours=[]):
        """ Met à jour l'affichage du calendrier et le planning en fonction des sélections """
        self.listeSelections = listeJours
        if len(listeJours) != 0:
            # Se place sur le mois ou l'année du premier jour de la période de vacances sélectionnée
            moisDebut, anneeDebut = listeJours[0].month, listeJours[0].year
            self.moisCalendrier = moisDebut
            self.anneeCalendrier = anneeDebut
        # Actualisation de l'affichage
        self.SendDates()
        self.MAJAffichage()
        # Met à jour l'affichage des contrôles de navigation du calendrier
        try:
            self.GetParent().MAJcontrolesNavigation(self.moisCalendrier, self.anneeCalendrier)
        except:
            pass

    def GetSelections(self):
        return self.listeSelections

# calendrier enrigi du choix de mois et année
class PNL_calendrier(wx.Panel):
    def __init__(self, parent, ID=-1,**kwcal):
        afficheBoutonAnnuel = kwcal.pop('afficheBoutonAnnuel',True)
        afficheAujourdhui = kwcal.pop('afficheAujourdhui',True)
        multiSelections = kwcal.pop('multiSelections',True)
        selectionInterdite = kwcal.pop('selectionInterdite',False)
        typeCalendrier = kwcal.pop('typeCalendrier',"mensuel")
        bordHaut = kwcal.pop('bordHaut',0)
        bordBas = kwcal.pop('bordBas',0)
        bordLateral = kwcal.pop('bordLateral',20)

        wx.Panel.__init__(self, parent, ID, name="panel_calendrier")
        self.parent = parent
        self.afficheBoutonAnnuel = afficheBoutonAnnuel
        self.multiSelections = multiSelections
        self.selectionInterdite = selectionInterdite
        self.typeCalendrier = typeCalendrier

        # Création du contrôle calendrier
        self.calendrier = Calendrier(self, -1, multiSelections=multiSelections, selectionInterdite=selectionInterdite,
                                     typeCalendrier=typeCalendrier)

        # Attribution des couleurs au calendrier
        couleurFondPanneau = None
        if couleurFondPanneau != None:
            self.calendrier.SetBackgroundColour(couleurFondPanneau)
        self.calendrier.couleurNormal = (248, 248, 255)
        self.calendrier.couleurWE = (198, 211, 249)
        self.calendrier.couleurSelect = (255, 162, 0)
        self.calendrier.couleurVacances = (255, 255, 187)

        # Création des autres widgets
        self.listeMois = LISTE_MOIS
        if "linux" in sys.platform:
            self.listeMois = LISTE_MOIS_ABREGE
        self.combo_mois = wx.ComboBox(self, -1, "", (-1, -1), (70, -1), self.listeMois, wx.CB_READONLY)

        self.spin = wx.SpinButton(self, -1, size=(17, 20), style=wx.SP_VERTICAL)
        self.spin.SetRange(-1, 1)

        if "linux" in sys.platform:
            largeurMois = 75
        else:
            largeurMois = 55

        self.combo_annee = wx.SpinCtrl(self, -1, "", size=(largeurMois, -1))
        self.combo_annee.SetRange(1970, 2099)

        dateJour = datetime.datetime.today()
        numMois = dateJour.month
        numAnnee = dateJour.year
        self.combo_mois.SetSelection(numMois - 1)
        self.combo_annee.SetValue(numAnnee)

        self.MAJPeriodeCalendrier()

        # Sélection de Aujourdh'ui
        if afficheAujourdhui == True and self.selectionInterdite == False:
            self.calendrier.SelectJours([datetime.date.today(), ])

        self.bouton_CalendrierAnnuel = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Calendrier.png",
                                                                           wx.BITMAP_TYPE_PNG), size=(28, 21))
        self.bouton_CalendrierAnnuel.SetToolTip("Cliquez ici pour afficher le calendrier annuel")

        # Layout
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizerOptions = wx.FlexGridSizer(rows=1, cols=8, vgap=0, hgap=0)
        sizerOptions.Add(self.bouton_CalendrierAnnuel, 0, wx.EXPAND | wx.RIGHT, 5)
        sizerOptions.Add(self.combo_mois, 0, wx.EXPAND, 0)
        sizerOptions.Add(self.spin, 0, wx.EXPAND, 0)
        sizerOptions.Add((5, 5), 0, wx.EXPAND, 0)
        sizerOptions.Add(self.combo_annee, 0, wx.EXPAND, 0)
        sizerOptions.AddGrowableCol(1)

        sizer.Add((0, bordHaut), 0, wx.EXPAND|wx.ALL, 0) # Espace haut
        sizer.Add(sizerOptions, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, bordLateral)
        sizer.Add(self.calendrier, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, bordLateral)
        sizer.Add((0, bordBas), 0, wx.EXPAND | wx.ALL, 0)  # espace Bas
        self.SetSizer(sizer)

        # Bind
        self.Bind(wx.EVT_SPIN, self.OnSpin, self.spin)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuel, self.bouton_CalendrierAnnuel)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboMois, self.combo_mois)
        self.Bind(wx.EVT_SPINCTRL, self.OnComboAnnee, self.combo_annee)
        self.Bind(wx.EVT_TEXT, self.OnComboAnnee, self.combo_annee)

        # Affiche ou non le bouton Annuel
        if self.afficheBoutonAnnuel == False:
            self.bouton_CalendrierAnnuel.Show(False)
        else:
            self.bouton_CalendrierAnnuel.Show(True)
        if self.typeCalendrier == "annuel":
            self.combo_mois.Enable(False)
            self.spin.Enable(False)
            self.bouton_CalendrierAnnuel.SetToolTip("Cliquez ici pour afficher le calendrier mensuel")
        else:
            self.combo_mois.Enable(True)
            self.spin.Enable(True)
            self.bouton_CalendrierAnnuel.SetToolTip("Cliquez ici pour afficher le calendrier annuel")

    def SetMultiSelection(self, etat=False):
        self.multiSelections = etat
        self.calendrier.multiSelections = etat
        listeSelections = self.GetSelections()
        if len(listeSelections) > 1:
            self.SelectJours((min(listeSelections),))

    def GetSelections(self):
        listeSelections = self.calendrier.GetSelections()
        if listeSelections != None:
            listeSelections = list(listeSelections)
            listeSelections.sort()
        return listeSelections

    def SelectJours(self, listeDates=[]):
        self.calendrier.SelectJours(listeDates)

    def MAJselectionDates(self, listeDates):
        """ Envoie les dates sélectionnée au module Presences """
        self.SetSelectionDates(listeDates)
        self.GetGrandParent().GetParent().MAJpanelPlanning()
        self.GetGrandParent().GetParent().panelPersonnes.listCtrlPersonnes.CreateCouleurs()

    def OnSpin(self, event):
        x = event.GetPosition()
        if self.combo_mois.IsEnabled() == True:
            # Changement du mois
            mois = self.combo_mois.GetSelection() + 1
            annee = int(self.combo_annee.GetValue())
            mois = mois + x
            if mois == 0:
                mois = 12
                annee = annee - 1
            if mois == 13:
                mois = 1
                annee = annee + 1
            self.combo_mois.SetSelection(mois - 1)
            self.combo_annee.SetValue(annee)
        else:
            # Changement de l'année uniquement
            annee = int(self.combo_annee.GetValue()) + x
            self.combo_annee.SetValue(annee)
        self.spin.SetValue(0)
        self.MAJPeriodeCalendrier()

    def OnBoutonAnnuel(self, event):
        if self.calendrier.GetTypeCalendrier() == "mensuel":
            self.calendrier.SetTypeCalendrier("annuel")
            self.combo_mois.Enable(False)
            self.spin.Enable(False)
            self.bouton_CalendrierAnnuel.SetToolTip("Cliquez ici pour afficher le calendrier mensuel")
            self.parent.SetSize((700, 600))
        else:
            self.calendrier.SetTypeCalendrier("mensuel")
            self.combo_mois.Enable(True)
            self.spin.Enable(True)
            self.bouton_CalendrierAnnuel.SetToolTip("Cliquez ici pour afficher le calendrier annuel")
            self.parent.SetSize((300, 300))

    def MAJPeriodeCalendrier(self):
        mois = self.combo_mois.GetSelection() + 1
        annee = int(self.combo_annee.GetValue())
        self.calendrier.SetMoisAnneeCalendrier(mois, annee)

    def OnComboMois(self, event):
        self.MAJPeriodeCalendrier()

    def OnComboAnnee(self, event):
        self.MAJPeriodeCalendrier()

    def MAJpanel(self):
        self.calendrier.MAJpanel()

    def MAJcontrolesNavigation(self, mois, annee):
        self.combo_mois.SetSelection(mois - 1)
        self.combo_annee.SetValue(annee)


    def onClose(self, event):
        self.Show(False)
        self.Destroy()

# Enrichi de validation
class DLG_calendrier(wx.Dialog):
    def __init__(self, parent,kwcal={},kwdlg={}):
        kwCalOut = {'afficheAujourdhui' : False,
                    'typeCalendrier' : "mensuel",
                    'afficheBoutonAnnuel' : True,
                    'multiSelections' : False,
                    'selectionInterdite' : False,
                    'bordHaut' : 0,
                    'bordBas' : 0,
                    'bordLateral' : 20}
        kwCalOut.update(kwcal)

        kwDlgOut = {'name':"DLG_Calendrier",
                    'style':wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX}
        kwDlgOut.update(kwdlg)


        wx.Dialog.__init__(self, parent, -1, **kwDlgOut )
        self.parent = parent
        minSize = (320, 350)
        if kwCalOut['typeCalendrier'] == 'annuel':
            minSize = (500,400)
        self.ctrl_calendrier = PNL_calendrier(self,**kwCalOut)
        self.ctrl_calendrier.Bind(EVT_SELECT_DATES, self.OnDateSelected)

        self.bouton_ok = xboutons.BTN_fermer(self,onBtn=self.OnBoutonOk)
        self.bouton_ok.Show(False)
        self.bouton_annuler = xboutons.Bouton(self, id=wx.ID_CANCEL, label=("Annuler"),
                                                     image="xpy/Images/32x32/Annuler.png")

        self.SetTitle("Cliquez sur une date pour la sélectionner...")
        self.SetMinSize(minSize)
        self.bouton_annuler.SetToolTip("Cliquez ici pour fermer")

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)

        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu.Add(self.ctrl_calendrier, 0, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.ALL | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((1, 1), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        #grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.Layout()
        self.CenterOnScreen()

    def OnDateSelected(self, event):
        self.OnBoutonOk(event)

    def GetDate(self):
        selections = self.ctrl_calendrier.GetSelections()
        if len(selections) > 0:
            return selections[0]
        else:
            return None

    def SetDate(self, date=None):
        self.ctrl_calendrier.SelectJours([date, ])

    def OnBoutonOk(self, event):
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else: self.Close()

# -Pour test--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class TestFrame(wx.Frame):

    def __init__(self, **kwd):
        wx.Frame.__init__(self, None, -1, **kwd)

    def OnChoixDate(self):
        self.Close()

if __name__ == '__main__':
    import os
    os.chdir("..")
    os.chdir("..")
    app = wx.App(0)

    """
    frame = DLG_calendrier(None)
    frame.Show()
    frame.Centre()
    frame_2 = TestFrame(title='PNL_calendrier', pos=(800,300))
    frame_2.pnlCalendrier = Calendrier(frame_2)
    frame_2.Show()
    """

    frame_3 = TestFrame(title='CTRL_SaisieDate', pos=(100,300),size=(300,150))
    frame_3.ctrl = CTRL_Periode(frame_3)
    #frame_3.ctrl = CTRL_SaisieDate(frame_3,label="Du:")
    frame_3.Show()


    app.MainLoop()

