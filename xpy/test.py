#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------



import wx
import wx.adv
import wx.lib.newevent
import calendar
import datetime

try:
    import psyco; psyco.full()
except:
    pass

SelectDatesEvent, EVT_SELECT_DATES = wx.lib.newevent.NewEvent()


class Calendrier(wx.ScrolledWindow):
    def __init__(self, parent, ID=-1, multiSelections=True, selectionInterdite=False, typeCalendrier="mensuel"):
        wx.ScrolledWindow.__init__(self, parent, ID, style=wx.NO_BORDER)
        self.multiSelections = multiSelections
        self.selectionInterdite = selectionInterdite

        self.SetMinSize((100, 140))

        # Variables � ne surtout pas changer
        self.caseSurvol = None
        self.multiSelect = None
        self.onLeave = True

        # Variables qui peuvent �tre chang�es
        self.listeSelections = []

        self.ecartCases = 2  # Ecart en pixels entre les cases jours d'un mois
        self.ecartMois = 8  # Ecart en pixels entre chaque mois dan un calendrier annuel

        self.couleurFond = (255, 255, 255)  # (255, 255, 255)       # Couleur du fond du calendrier
        self.couleurNormal = (
        255, 255, 255)  # (214, 223, 247) #(175, 225, 251)     # Couleur d'un jour normal du lundi au vendredi
        self.couleurWE = (231, 245, 252)  # (171, 249, 150)         # Couleur des samedis et dimanche
        self.couleurSelect = (55, 228, 9)  # Couleur du fond de la case si celle-ci est s�lectionn�e
        self.couleurSurvol = (0, 0, 0)  # Couleur du bord de la case si celle-ci est survol�e
        self.couleurFontJours = (0, 0, 0)
        self.couleurVacances = (255, 255, 255)  # Couleur des cases dates d'ouverture de la structure
        self.couleurFontJoursAvecPresents = (255, 0, 0)
        self.couleurFerie = (180, 180, 180)  # couleur des jours f�ri�s

        self.headerMois = True
        self.headerJours = True

        self.typeCalendrier = typeCalendrier
        self.moisCalendrier = 2
        self.anneeCalendrier = 2008

        self.selectExclureWE = True  # Inclure les WE quand une p�riode de vacs est s�lectionn�e dans le menu contextuel

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
        self.joursVacances, self.listePeriodesVacs = self.Importation_Vacances(self.anneeCalendrier)
        self.listeFeriesFixes, self.listeFeriesVariables = self.Importation_Feries(self.anneeCalendrier)
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
        try:
            self.joursVacances
        except:
            self.joursVacances, self.listePeriodesVacs = self.Importation_Vacances(self.anneeCalendrier)
        try:
            self.listeFeriesFixes
        except:
            self.listeFeriesFixes, self.listeFeriesVariables = self.Importation_Feries(self.anneeCalendrier)

        self.dictCases = {}
        self.listeCasesJours = []
        largeur, hauteur = self.GetSize()

        annee = self.anneeCalendrier

        if self.typeCalendrier == "mensuel":
            # Cr�ation d'un calendrier mensuel
            mois = self.moisCalendrier
            self.listeJoursAvecPresents = self.Importation_JoursAvecPresents(annee=annee, mois=mois)
            self.DrawMonth(dc, mois, annee, 0, 0, largeur, hauteur)
        else:
            # Cr�ation d'un calendrier annuel
            largeurMois = largeur / 4.0
            hauteurMois = hauteur / 3.0
            numMois = 1
            self.listeJoursAvecPresents = self.Importation_JoursAvecPresents(annee=annee)
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
        """ est utilis� pour �tre s�r que le programme a bien remarqu� les touches press�es """
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
        """ S�lection de la case cliqu�e """
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

                # Si la case est d�j� s�lectionn�e, on la supprime de la liste des s�lections
                if len(self.listeSelections) != 0:
                    if date in self.listeSelections:
                        self.listeSelections.remove(date)
                        self.RedrawCase(IDobjet, survol=True)
                        self.SendDates()
                        return

                # Ajout de la case � la liste des s�lections
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

                    # Si s�lection inverse
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

                        # M�morisation de la date
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
                    # S�lection Unique
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

                    # S�lection par colonne
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

                        # Si tous les jours ont d�j� �t� s�lectionn�s, c'est que l'on doit d�s�lectionner tout le mois :
                        if len(deselect) == nbreSemaines:
                            for date in deselect:
                                self.listeSelections.remove(date)

                    else:
                        # S�lection Unique
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

                        # Si tous les jours ont d�j� �t� s�lectionn�s, c'est que l'on doit d�s�lectionner tout le mois :
                        if len(deselect) == nbreSemaines:
                            self.listeSelections = []
                        else:
                            # S�lection de tout le mois
                            self.listeSelections = []
                            for date in tempSelections:
                                self.listeSelections.append(date)
                            for date in deselect:
                                self.listeSelections.append(date)

            self.SendDates()
            self.MAJAffichage()

        event.Skip()

    def SendDates(self):
        """ Envoie la liste des dates s�lectionn�es """
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
        txt = (u"Restez appuyer sur les touches CONTROL, SHIFT ou ALT pour s�lectionner plusieurs jours � la fois.")
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
        # Redessine uniquement la zone modifi�e
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
            # Si cette case est d�j� actuellement survol�e, on passe...
            if self.caseSurvol != None:
                if self.caseSurvol == IDobjet: return
            # Activation de la case s�lectionn�e
            # Si une case a d�j� �t� survol�e avant, on l'annule
            if self.caseSurvol != None:
                self.RedrawCase(self.caseSurvol, survol=False)
            # Redessine la nouvelle case
            self.caseSurvol = IDobjet
            self.RedrawCase(IDobjet, survol=True)

            # Ecriture d'un texte dans la statutBar
            date = self.IDobjetEnDate(IDobjet)
            listeJours = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
            listeMois = (
            (u"janvier"), (u"f�vrier"), (u"mars"), (u"avril"), (u"mai"), (u"juin"), (u"juillet"), (u"ao�t"),
            (u"septembre"), (u"octobre"), (u"novembre"), (u"d�cembre"))
            dateStr = listeJours[date.weekday()] + " " + str(date.day) + " " + listeMois[date.month - 1] + " " + str(
                date.year)
            texteStatusBar = dateStr

            # Si c'est un jour de vacances
            if date in self.joursVacances:
                texteStatusBar += (u" | Jour de vacances")

            # Si c'est un jour f�ri�
            if (date.day, date.month) in self.listeFeriesFixes:
                texteStatusBar += (u" | Jour f�ri�")
            else:
                if date in self.listeFeriesVariables:
                    texteStatusBar += (u" | Jour f�ri�")

            # Actualisation la statusBar
            try:
                wx.GetApp().GetTopWindow().SetStatusText(texteStatusBar, 0)
            except:
                pass

            return

        # Si on ne survole aucune case : D�sactivation de la case pr�c�demment s�lectionn�e
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

        # Cr�ation de l'entete avec le nom du mois
        if self.headerMois == True:
            hautMois, yMois = self.DrawHeaderMois(dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois)

        # Cr�ation de l'entete avec les noms des jours
        if self.headerJours == True:
            hautMois, yMois = self.DrawHeaderJours(dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois)

        # Calcule la taille d'une case
        largCase = (largMois / 7.0)
        hautCase = (hautMois / float(nbreSemaines))

        # Cr��e les cases jours
        for numSemaine in range(nbreSemaines):
            for numJour in range(7):

                jour = datesMois[numSemaine][numJour]

                if jour != 0:
                    # Cr�e les donn�es de la case
                    x = xMois + (largCase * numJour)
                    y = yMois + (hautCase * numSemaine)
                    l = largCase - self.ecartCases
                    h = hautCase - self.ecartCases
                    texteDate = datetime.date(annee, mois, jour)

                    # Enregistrement des donn�es dans une liste
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
        # R�glage de la police
        dc.SetTextForeground(self.couleurFontJours)
        taille = self.tailleFont(largCase, hautCase)
        font = wx.Font(taille, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        hautHeader = taille * 2
        x = 0
        for jour in range(7):
            texte = listeJours[jour]
            texteComplet = (jour, mois, annee)
            # R�glage du format du texte en fonction de la taille de la case
            if largCase < 50:
                texte = texte[:3]
            if largCase < 25:
                texte = texte[0]
            largTexte, hautTexte = self.GetTextExtent(texte)
            coordX = xMois + x + (largCase / 2) - (largTexte / 2)
            coordY = yMois + (hautHeader / 2) - (hautTexte / 2)
            dc.DrawText(texte, coordX, coordY)
            # M�morisation des jours et de leurs coordonn�es
            self.listeCasesJours.append((coordX, coordY, largTexte, hautTexte, texteComplet))
            x += largCase

        return hautMois - hautHeader, yMois + hautHeader

    def DrawHeaderMois(self, dc, nbreSemaines, mois, annee, xMois, yMois, largMois, hautMois):
        """ Dessine un header comportant le nom du mois """
        listeMois = (
        (u"Janvier"), (u"F�vrier"), (u"Mars"), (u"Avril"), (u"Mai"), (u"Juin"), (u"Juillet"), (u"Ao�t"),
        (u"Septembre"), (u"Octobre"), (u"Novembre"), (u"D�cembre"))
        largCase = (largMois / 7.0)
        hautCase = (hautMois / float(nbreSemaines))
        # R�glage de la police
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

        # Si c'est un jour de vacances
        if texteDate in self.joursVacances:
            dc.SetBrush(wx.Brush(self.couleurVacances))

        # Si c'est un jour de Week-end
        jourSemaine = texteDate.isoweekday()
        if jourSemaine == 6 or jourSemaine == 7:
            dc.SetBrush(wx.Brush(self.couleurWE))

        # Si c'est un jour f�ri�
        if (texteDate.day, texteDate.month) in self.listeFeriesFixes:
            dc.SetBrush(wx.Brush(self.couleurFerie))
        else:
            if texteDate in self.listeFeriesVariables:
                dc.SetBrush(wx.Brush(self.couleurFerie))

        # Si c'est une case survol�e
        if survol == True:
            # dc.SetBrush(wx.Brush('black', wx.TRANSPARENT))
            dc.SetPen(wx.Pen(self.couleurSurvol, 1))

        # Dessine d'une case s�lectionn�e
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

        # On prend le c�t� le plus petit
        if l > h:
            cote = h
        else:
            cote = l
        # On d�finit des ordres de grandeur
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

    def GetTypeCalendrier(self):
        return self.typeCalendrier

    def SetMoisAnneeCalendrier(self, mois=0, annee=0):
        if mois != 0: self.moisCalendrier = mois
        if annee != 0: self.anneeCalendrier = annee
        self.MAJAffichage()

    def GetMoisAnneeCalendrier(self):
        return self.moisCalendrier, self.anneeCalendrier

    def GetTypeCalendrier(self):
        return self.typeCalendrier

    def Importation_Vacances(self, anneeCalendrier=None):
        """ Importation des dates de vacances """
        listeVacances1 = []


        listeVacances2 = []
        listePeriodesVacs = []

        for id, nom, annee, date_debut, date_fin in listeVacances1:
            datedebut = datetime.date(int(date_debut[:4]), int(date_debut[5:7]), int(date_debut[8:10]))
            datefin = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
            listeVacances2.append(datedebut)
            listeTemp = []
            for x in range((datefin - datedebut).days):
                # Ajout � la liste des jours de vacances (qui sert au coloriage de la case)
                datedebut = datedebut + datetime.timedelta(days=1)
                listeVacances2.append(datedebut)
                listeTemp.append(datedebut)
            # Ajout au dictionnaire des vacances (qui sert � s�lectionner une p�riode de vacs dans le calendrier)
            listePeriodesVacs.append((annee, nom, tuple(listeTemp)))

        return listeVacances2, listePeriodesVacs

    def Importation_Feries(self, anneeCalendrier=None):
        """ Importation des dates de vacances """
        listeFeriesTmp = []

        listeFeriesFixes = []
        listeFeriesVariables = []
        for ID, type, nom, jour, mois, annee in listeFeriesTmp:
            if type == "fixe":
                date = (jour, mois)
                listeFeriesFixes.append(date)
            else:
                date = datetime.date(annee, mois, jour)
                listeFeriesVariables.append(date)
        return listeFeriesFixes, listeFeriesVariables

    def Importation_JoursAvecPresents(self, annee=None, mois=None):
        return []
        ###### MODIFIE ICI #############

        if mois == None:
            dateDebut = str(annee) + "-01-01"
            dateFin = str(annee) + "-12-31"
        else:
            strMois = str(mois)
            if len(strMois) == 1: strMois = "0" + strMois
            dateDebut = str(annee) + "-" + strMois + "-01"
            dateFin = str(annee) + "-" + strMois + "-31"

        listeDonnees = []

        # Transformation en bonne liste
        listeDonnees2 = []
        for date in listeDonnees:
            listeDonnees2.append(date[0])

        return listeDonnees2

    def OnContextMenu(self, nomCase):
        """ Menu contextuel du calendrier """
        if self.caseSurvol != None:
            texteDate = self.IDobjetEnDate(self.caseSurvol)
        else:
            texteDate = None

        if self.selectionInterdite == True:
            return

        # Cr�ation du menu
        menu = wx.Menu()

        if self.multiSelections == True:

            # Si une date a bien �t� cliqu�e :
            if texteDate != None:
                # V�rifie si date d�j� s�lectionn�e
                if texteDate in self.listeSelections:
                    select = True
                else:
                    select = False
                # S�lection/d�selection du jour cliqu�
                self.popupID1 = wx.NewId()
                if select == False:
                    texte = (u"S�lectionner le %02d/%02d/%04d") % (texteDate.day, texteDate.month, texteDate.year)
                else:
                    texte = (u"D�s�lectionner le %02d/%02d/%04d") % (texteDate.day, texteDate.month, texteDate.year)
                menu.Append(self.popupID1, texte)
                self.Bind(wx.EVT_MENU, self.OnPopup1, id=self.popupID1)

                menu.AppendSeparator()

        # Choisir la date d'aujourd'hui
        self.popupID4 = wx.NewId()
        menu.Append(self.popupID4, (u"S�lectionner aujourd'hui"))
        self.Bind(wx.EVT_MENU, self.OnPopup4, id=self.popupID4)

        if self.multiSelections == True:

            # Choisir tout le mois
            self.popupID5 = wx.NewId()
            menu.Append(self.popupID5, (u"S�lectionner tout le mois"))
            self.Bind(wx.EVT_MENU, self.OnPopup5, id=self.popupID5)

            # Choisir une p�riode de vacances
            self.popupID3 = wx.NewId()
            if len(self.listePeriodesVacs) != 0:
                sm = wx.Menu()
                index = 0
                self.listePeriodesVacs.reverse()
                # Seules les 20 derni�res p�riodes sont retenues
                for annee, nomPeriode, listeJours in self.listePeriodesVacs[:20]:
                    id = 1000 + index
                    sm.Append(id, nomPeriode + " " + str(annee))
                    self.Bind(wx.EVT_MENU, self.OnPopup3, id=id)
                    index += 1
                # Inclus le sous-menu dans le menu
                menu.AppendMenu(self.popupID3, (u"S�lectionner une p�riode de vacances"), sm)

            # Tout d�s�lectionner
            self.popupID7 = wx.NewId()
            menu.Append(self.popupID7, (u"Tout d�s�lectionner"))
            self.Bind(wx.EVT_MENU, self.OnPopup7, id=self.popupID7)

            # Exclure les jours de week-end dans les s�lections
            self.popupID6 = wx.NewId()
            menu.Append(self.popupID6, (u"Exclure les week-ends des s�lections"),
                        (u"Exclure les week-ends de la s�lection"), wx.ITEM_CHECK)
            if self.selectExclureWE == True:
                menu.Check(self.popupID6, True)
            self.Bind(wx.EVT_MENU, self.OnPopup6, id=self.popupID6)

        # Aide sur le calendrier
        menu.AppendSeparator()
        self.popupID2 = wx.NewId()
        menu.Append(self.popupID2, (u"Aide sur le calendrier"))
        self.Bind(wx.EVT_MENU, self.OnPopup2, id=self.popupID2)

        # make a submenu
        # sm = wx.Menu()
        # sm.Append(self.popupID8, "sub item 1")
        # sm.Append(self.popupID9, "sub item 1")
        # menu.AppendMenu(self.popupID7, "Test Submenu", sm)

        self.onLeave = False
        self.PopupMenu(menu)
        menu.Destroy()
        self.onLeave = True
        # self.RedrawCase(caseSurvol, survol=True)

    def OnPopup1(self, event):
        """ S�lection ou d�s�lection """
        texteDate = self.IDobjetEnDate(self.caseSurvol)

        # V�rifie si date d�j� s�lectionn�e
        if texteDate in self.listeSelections:
            select = True
        else:
            select = False

        # D�s�lection de la date
        if select == True:
            self.listeSelections.remove(texteDate)
            self.SelectJours(self.listeSelections)
            ##            self.RedrawCase(self.caseSurvol, survol=True)
            return

        # S�lection de la date
        else:
            self.listeSelections.append(texteDate)
            self.SelectJours(self.listeSelections)
            ##            self.RedrawCase(self.caseSurvol, survol=True)
            return

    def OnPopup2(self, event):
        """ Aide sur le calendrier """
        print
        "Aide..."
        # FonctionsPerso.Aide(51)

    def OnPopup3(self, event):
        """ S�lection d'une p�riode de vacances """
        index = event.GetId() - 1000
        nomPeriode, annee, listeJours = self.listePeriodesVacs[index]
        # Mets les jours de vacances dans la liste de s�lections

        # Enleve les week-ends si n�cessaires :
        if self.selectExclureWE == True:
            listeJoursTmp = []
            for jour in listeJours:
                jourSemaine = jour.isoweekday()
                if jourSemaine != 6 and jourSemaine != 7:
                    listeJoursTmp.append(jour)
            listeJours = listeJoursTmp

        self.SelectJours(list(listeJours))

    def OnPopup6(self, event):
        """ Inclure ou non les week-ends dans la s�lection """
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
        """ Tout d�s�lectionner """
        self.SelectJours(listeJours=[])

    def SelectJours(self, listeJours=[]):
        """ Met � jour l'affichage du calendrier et le planning en fonction des s�lections """
        self.listeSelections = listeJours
        if len(listeJours) != 0:
            # Se place sur le mois ou l'ann�e du premier jour de la p�riode de vacances s�lectionn�e
            moisDebut, anneeDebut = listeJours[0].month, listeJours[0].year
            self.moisCalendrier = moisDebut
            self.anneeCalendrier = anneeDebut
        # Actualisation de l'affichage
        self.SendDates()
        self.MAJAffichage()
        # Met � jour l'affichage des contr�les de navigation du calendrier
        try:
            self.GetParent().MAJcontrolesNavigation(self.moisCalendrier, self.anneeCalendrier)
        except:
            pass

    def GetSelections(self):
        return self.listeSelections


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class TestFrame(wx.Frame):

    def __init__(self,
                 parent=None,
                 ID=-1,
                 title="BufferedCanvas Test",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)

        ##        self.SetBackgroundColour("BLUE")

        self.tailleRect = (55, 55, 100, 100)
        self.canvas = Calendrier(self)
        # self.panel = CTRL(self)

        self.Bind(wx.EVT_CLOSE, self.onClose)

    ##        self.Bind(wx.EVT_SIZE, self.OnSize)

    def onClose(self, event):
        self.Show(False)
        self.Destroy()


##    def OnSize(self, event):
##        largeur, hauteur = self.GetClientSizeTuple()
##        self.tailleRect = (55, 55, largeur - 80, hauteur - 80)
##        self.canvas.MAJAffichage()
##        event.Skip()


def main():
    app = wx.App()
    frame = TestFrame()
    frame.Show(True)
    frame.Centre()
    app.MainLoop()


if __name__ == '__main__':
    main()

