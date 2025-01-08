#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - Projet XPY -Evolution surcouche OLV permettant la saisie sur la ligne)
# module xGTE remplace xGTR qui permet la saisie dans un nouvel écran
#  2022-08-01 appelle OLV façon Noethys
#

import wx
import os
import datetime
import xpy.xUTILS_SaisieParams as xusp
from xpy.outils import xbandeau, xformat, xboutons,xexport, xchemins

from xpy.ObjectListView.ObjectListView import FastObjectListView
from xpy.ObjectListView.ObjectListView  import  ColumnDefn
import xpy.ObjectListView.Footer as Footer
from xpy.ObjectListView.ObjectListView import CTRL_Outils
import xpy.ObjectListView.OLVEvent as OLVEvent
import xpy.ObjectListView.CellEditor as CellEditor
from xpy.outils.xconst import *

# ----------  Objets  ObjectListView --------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, olv, donnees=None):
        codesColonnes = olv.lstCodesColonnes
        nomsColonnes = olv.lstNomsColonnes
        setterValues = olv.lstSetterValues
        ok = True
        self.donnees = []
        if not hasattr(olv,'lstCodesSup'):
            codesSup = []
        else: codesSup = olv.lstCodesSup
        if donnees == None:
            donnees = [None,] * (len(codesColonnes)+ len(codesSup))
        self.vierge = None
        self.valide = None
        # les données suplémentaires au nbre de colonnes, sont présentes dans les tracks et définies par codesSup
        if not (len(donnees)-len(codesSup) == len(codesColonnes) == len(nomsColonnes) == len(setterValues)):
            lst = [str(codesColonnes),str(nomsColonnes),str(setterValues),str(donnees)]
            mess = "Problème de nombre d'occurences!\n\n"
            mess += "%d codesCol, %d nomsCol, %d valDéfaut, (%d donnees - %d codes_sup) = %d"%(
                                    len(codesColonnes),
                                    len(nomsColonnes), len(setterValues),
                                    len(donnees),len(codesSup),
                                    (len(donnees)-len(codesSup)))
            mess += '\n\n'+'\n\n'.join(lst)
            wx.MessageBox(mess,caption="xGTE.TrackGeneral")
            ok = False
        # instanciation proprement dite
        if ok:
            # pour chaque donnée affichée, attribut et ctrl setter value
            for ix in range(len(codesColonnes)):
                donnee = donnees[ix]
                if setterValues[ix] != None:
                    # prise de la valeur par défaut si pas de donnée
                    if donnee in (None,""):
                        donnee = setterValues[ix]
                    # le type de la donnée n'est pas celui attendu
                    else:
                        self.vierge = False
                        if not isinstance(donnee,type(setterValues[ix])):
                            try:
                                if type(setterValues[ix]) == int:
                                    donnee = int(donnee)
                                elif type(setterValues[ix]) == float:
                                    donnee = float(donnee)
                                elif type(setterValues[ix]) == str:
                                    donnee = str(donnee)
                                elif isinstance(setterValues[ix],(wx.DateTime,
                                                                      datetime.date,
                                                                      datetime.datetime,
                                                                      datetime.time)):
                                    donnee = xformat.DateSqlToDatetime(donnee)
                            except : pass
                self.__setattr__((codesColonnes + codesSup)[ix], donnee)
            # complément des autres données hors colonnes affichées
            for ixrel in range(len(codesSup)):
                ixabs = len(codesColonnes) + ixrel
                self.__setattr__((codesSup)[ixrel],donnees[ixabs])
            self.donnees = donnees
            # ce stockage des oldDonnees de l'existant permet de gérer la saisies invalides
            self.oldDonnees = [x for x in self.donnees]

class TrackVierge(TrackGeneral):
    #    Cette classe initialise une ligne avec les valeurs par défaut définies dans les colonnes
    def __init__(self,olv):
        TrackGeneral.__init__(self, olv)
        self.vierge = True
        self.valide = False
        return

class ListView( FastObjectListView):
    """
    Lors de l'instanciation de cette classe vous pouvez y passer plusieurs parametres :

    lstColonnes : censé être une liste d'objets ColumndeFn
    lstDonnees : liste de listes ayant la même longueur que le nombre de colonnes.

    msgIfEmpty : une chaine de caractères à envoyer si le tableau est vide

    sortColumnIndex : Permet d'indiquer le numéro de la colonne selon laquelle on veut trier
    sensTri : True ou False indique le sens de tri

    exportExcel : True par défaut, False permet d'enlever l'option 'Exporter au format Excel'
    exportTexte : idem
    apercuAvantImpression : idem
    imprimer : idem
    toutCocher : idem
    toutDecocher : idem
    menuPersonnel : On peut avoir déjà créé un "pré" menu contextuel auquel
                    viendra s'ajouter le tronc commun

    Pour cette surcouche de OLV j'ai décidé de ne pas laisser la fonction
    OnItemActivated car ça peut changer selon le tableau
    donc ce sera le role de la classe parent (qui appelle ListView) de définir
    une fonction OnItemActivated qui sera utilisée lors du double clic sur une ligne

    Dictionnaire optionnel ou on indique si on veut faire le bilan
                (exemple somme des valeurs)
    """

    def __init__(self, *args, **kwds):
        self.parent = args[0].parent
        self.lanceur = self.parent.lanceur
        self.dicOlv = xformat.CopyDic(kwds)
        self.pnlFooter = kwds.pop('pnlFooter', None)
        self.checkColonne = kwds.pop('checkColonne',True)
        self.lstColonnes = kwds.pop('lstColonnes', [])
        self.lstCodesSup = kwds.pop('lstCodesSup', [])
        self.editMode = kwds.pop('editMode', True)
        self.msgIfEmpty = kwds.pop('msgIfEmpty', 'Tableau vide')
        self.sortColumnIndex = kwds.pop('sortColumnIndex', None)
        self.sensTri = kwds.pop('sensTri', True)
        self.menuPersonnel = kwds.pop('menuPersonnel', False)
        self.lstDonnees = kwds.pop('lstDonnees', None)
        self.getDonnees = kwds.pop('getDonnees', None)
        self.dictColFooter = kwds.pop('dictColFooter', {})
        self.buffertracks = None

        # Choix des options du 'tronc commun' du menu contextuel
        self.copier = kwds.pop('copier', True)
        self.couper = kwds.pop('couper', True)
        self.coller = kwds.pop('coller', True)
        self.supprimer = kwds.pop('supprimer', True)
        self.inserer = kwds.pop('inserer', True)
        self.exportExcel = kwds.pop('exportExcel', True)
        self.exportTexte = kwds.pop('exportTexte', True)
        self.apercuAvantImpression = kwds.pop('apercuAvantImpression', True)
        self.imprimer = kwds.pop('imprimer', True)
        self.toutCocher = kwds.pop('toutCocher', True)
        self.toutDecocher = kwds.pop('toutDecocher', True)
        self.inverserSelection = kwds.pop('inverserSelection', True)
        if not self.checkColonne:
            self.toutCocher = False
            self.toutDecocher = False
            self.inverserSelection = False

        # Choix du mode d'impression
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []

        # Initialisation du listCtrl
        if not 'autoAddRow' in kwds: kwds['autoAddRow']=True
        if not 'sortable' in kwds: kwds['sortable']=True
        FastObjectListView.__init__(self, *args,**kwds)
        self.InitObjectListView()
        self.Proprietes()

    def Proprietes(self):
        # Binds perso
        self.Bind(OLVEvent.EVT_ITEM_CHECKED, self.MAJ_footer)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        if self.editMode:
            self.cellEditMode =  FastObjectListView.CELLEDIT_SINGLECLICK
        self.Bind(wx.EVT_SET_FOCUS,self.OnSetFocus)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.flagSkipEdit = False

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.useExpansionColumn = True
        # On définit les colonnes
        self.SetColumns(self.lstColonnes)
        if self.checkColonne:
            self.CreateCheckStateColumn(0)
        self.lstCodesColonnes = self.GetLstCodesColonnes()
        self.lstNomsColonnes = self.GetLstNomsColonnes()
        self.lstSetterValues = self.GetLstSetterValues()
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.FONTFAMILY_DEFAULT))

    def MAJ(self, ID=None, ):
        self.selectionID = ID
        self.SetObjects(self.formerTracks(self.dicOlv))
        if self.pnlFooter:
            self.MAJ_footer(None)
        # Rappel de la sélection d'un item
        if self.selectionID != None and len(self.innerList) > 0:
            self.SelectObject(self.innerList[ID], deselectOthers=True, ensureVisible=True)

    def formerTracks(self,dicOlv=None):
        tracks = list()
        if self.lstDonnees is None and self.getDonnees :
            self.lstDonnees = self.getDonnees(**dicOlv)
        if self.lstDonnees is None:
            return []

        for ligneDonnees in self.lstDonnees:
            tracks.append(TrackGeneral(self,ligneDonnees))
        if hasattr(self.parent,"CalculeLigne"):
            for track in tracks:
                self.parent.CalculeLigne(self,track)
        for track in tracks:
            # les lignes remontées sont sensées être valides
            track.valide = True
        self._FormatAllRows()
        return tracks

    def OnItemDeselected(self,event):
        if not event.EventObject.cellBeingEdited:
            return
        (ixLig, ixCol) = event.EventObject.cellBeingEdited
        track = self.innerList[ixLig]
        if track.valide == False:
            track = TrackGeneral(self,track.oldDonnees)
            track.valide = True
            self.innerList[ixLig] = track

    def OnSetFocus(self,evt):
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        valide = True
        # SetFocus sur le corps d'écran pour récupérer le KillFocus sur les params
        if hasattr(self.parent,'ValideParams'):
            valide = self.parent.ValideParams()
        elif hasattr(self.parent.parent,'ValideParams'):
            valide = self.parent.parent.ValideParams()
        self.flagSkipEdit = False
        evt.Skip()

    def SetFooter(self, ctrl=None, dictColFooter={}):
        self.ctrl_footer = ctrl
        self.ctrl_footer.listview = self
        self.ctrl_footer.dictColFooter = dictColFooter

    def MAJ_footer(self,evt):
        if self.ctrl_footer and self.pnlFooter:
            self.ctrl_footer.MAJ_totaux()
            self.ctrl_footer.MAJ_affichage()
        if hasattr(self,'MAJ_calculs'):
            self.MAJ_calculs(self.lanceur)

    def GetTrackVierge(self,row = None):
        track = TrackVierge(self)
        if hasattr(self.Parent,'InitTrackVierge'):
            self.Parent.InitTrackVierge(track,self.modelObjects)
        return track

    def AddTracks(self,lstDonnees):
        tracks = []
        for ligneDonnees in lstDonnees:
            tracks.append(TrackGeneral( self,ligneDonnees))
        self.AddObjects(tracks)

    def GetLstCodesColonnes(self):
        lstCodes = list()
        for colonne in self.lstColonnes:
            code = colonne.valueGetter
            lstCodes.append(code)
        return lstCodes

    def GetLstNomsColonnes(self):
        nomColonnes = list()
        for colonne in self.lstColonnes:
            nom = colonne.title
            nomColonnes.append(nom)
        return nomColonnes

    def GetLstSetterValues(self):
        setterValues = list()
        for colonne in self.lstColonnes:
            fmt = colonne.stringConverter
            tip = None
            if colonne.valueSetter != None:
                tip = colonne.valueSetter
            if tip == None:
                if fmt:
                    fmt = colonne.stringConverter.__name__
                    if fmt[3:] in ('Montant','Solde','Decimal'):
                        tip = 0.0
                    elif fmt[3:] == 'Date':
                        tip = wx.DateTime.FromDMY(1,0,1900)
                    elif fmt[3:] == 'Entier':
                        tip = 0
                elif colonne == self.lstColonnes[0]:
                    tip = 0
            setterValues.append(tip)
        return setterValues

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
       # Création du menu contextuel
        if self.menuPersonnel:
            if hasattr(self.Parent,'GetMenuPersonnel'):
                menuPop = self.Parent.GetMenuPersonnel()
                # On ajoute un séparateur ici ou dans la classe parent ?
            menuPop.AppendSeparator()
        else:
            menuPop = wx.Menu()

        # Item Insérer Ligne
        if self.inserer  and self.cellEditMode != 0:
            item = wx.MenuItem(menuPop, 21, INSERER_LIGNE)
            bmp = wx.Bitmap(MAGIQUE_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.OnInsert, id=21)

        # Item copier Ligne
        if self.copier and self.cellEditMode != 0:
            item = wx.MenuItem(menuPop, 16, COPIER_LIGNE)
            bmp = wx.Bitmap(COPIER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.OnCopier, id=16)

        # Item couper Ligne
        if self.couper and self.cellEditMode != 0:
            item = wx.MenuItem(menuPop, 17, COUPER_LIGNE)
            bmp = wx.Bitmap(COUPER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.OnCouper, id=17)
        # Item coller Ligne
        if self.coller and self.cellEditMode != 0:
            item = wx.MenuItem(menuPop, 18, COLLER_LIGNE)
            bmp = wx.Bitmap(COLLER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.OnColler, id=18)

        # Item Supprimer Ligne
        if self.supprimer and self.cellEditMode != 0:
            item = wx.MenuItem(menuPop, 22, SUPPRIMER_LIGNE)
            bmp = wx.Bitmap(ABANDON_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.OnDelete, id=22)

        # On met le separateur
        menuPop.AppendSeparator()

        # Item Tout cocher
        if self.toutCocher:
            item = wx.MenuItem(menuPop, 70, TOUT_COCHER_TXT)
            bmp = wx.Bitmap(COCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheListeTout, id=70)

        # Item Tout décocher
        if self.toutDecocher:
            item = wx.MenuItem(menuPop, 80, TOUT_DECOCHER_TXT)
            bmp = wx.Bitmap(DECOCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheListeRien, id=80)

        if self.inverserSelection and self.GetSelectedObject() is not None:
            item = wx.MenuItem(menuPop, 90, INVERSER_SELECTION_TXT)
            bmp = wx.Bitmap(DECOCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheInvJusqua, id=90)

        # On met le separateur seulement si un des deux menus est present
        if self.toutDecocher or self.toutCocher:
            menuPop.AppendSeparator()
        if self.parent.avecRecherche:
            # Item filtres
            item = wx.MenuItem(menuPop, 81, UN_FILTRE)
            bmp = wx.Bitmap(FILTRE_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.OnBoutonFiltrer, id=81)

            item = wx.MenuItem(menuPop, 83, SUPPRIMER_FILTRES)
            bmp = wx.Bitmap(FILTREOUT_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.SupprimerFiltres, id=83)

            # On met le separateur
            menuPop.AppendSeparator()

        # Item Apercu avant impression
        if self.apercuAvantImpression:
            item = wx.MenuItem(menuPop, 40, APERCU_IMP_TXT)
            item.SetBitmap(wx.Bitmap(APERCU_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Apercu, id=40)

        # Item Imprimer
        if self.imprimer:
            item = wx.MenuItem(menuPop, 50, IMPRIMER_TXT)
            item.SetBitmap(wx.Bitmap(IMPRIMANTE_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Imprimer, id=50)

        # On vérifie la présence d'un des menus précédents pour mettre un séparateur
        if self.imprimer or self.apercuAvantImpression:
            menuPop.AppendSeparator()

        # Item Export Texte
        if self.exportTexte:
            item = wx.MenuItem(menuPop, 600, EXPORT_TEXTE_TXT)
            item.SetBitmap(wx.Bitmap(TEXTE2_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)

        # Item Export Excel
        if self.exportExcel:
            item = wx.MenuItem(menuPop, 700, EXPORT_EXCEL_TXT)
            item.SetBitmap(wx.Bitmap(EXCEL_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        # On vérifie que menuPop n'est pas vide
        if self.MenuNonVide():
            self.PopupMenu(menuPop)
        menuPop.Destroy()

    def MenuNonVide(self):  # Permet de vérifier si le menu créé est vide
        return self.exportExcel or self.exportTexte \
               or self.apercuAvantImpression or self.imprimer \
               or self.toutCocher or self.toutDecocher or self.menuPersonnel

    def Apercu(self, event):
        if hasattr(self.lanceur,"ValideImpress"):
            if not self.lanceur.ValideImpress():
                return
                print("Impress non valide")
        import xpy.ObjectListView.Printer as printer
        prt = printer.ObjectListViewPrinter(self, titre=self.GetTitreImpression(),
                                                        orientation=self.GetOrientationImpression())
        prt.Preview()

    def Imprimer(self, event):
        if hasattr(self.lanceur,"ValideImpress"):
            if not self.lanceur.ValideImpress():
                return
        import xpy.ObjectListView.Printer as printer
        prt = printer.ObjectListViewPrinter(self, titre=self.GetTitreImpression(),
                                                    orientation=self.GetOrientationImpression())
        prt.Preview()

    def ExportTexte(self, event):
        xexport.ExportTexte(self, titre=self.GetTitreImpression())

    def ExportExcel(self, event):
        titre = self.GetTitreImpression()
        xexport.ExportExcel(self, titre=titre[:31], autoriseSelections=False)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def OnBoutonFiltrer(self, event=None):
        self.parent.ctrlOutils.OnBoutonFiltrer(event)

    def SupprimerFiltres(self, event=None):
        self.parent.ctrlOutils.SupprimerFiltres()

    def SpareCouper(self,nomFichier="LignesPerdues.txt"):
        # Sauvegarde avant suppression
        lstColonnes, llData = xexport.GetValeursListview(self)
        xexport.ExportTemp(lstColonnes,llData,nomFichier=nomFichier)

    def OnCopier(self,event=None):
        # action copier
        self.buffertracks = self.GetSelectedObjects()

        if len(self.buffertracks) == 0:
            mess = "Pas de sélection faite"
            wx.MessageBox(mess)
        else:
            mess = "lignes mémorisées pour prochain coller ou <ctrl> V"
            wx.MessageBox(" %d %s"%(len(self.buffertracks),mess))
            for track in self.buffertracks:
                track.set = True
        return

    def OnCouper(self,event=None):
        # action copier
        self.buffertracks = self.GetSelectedObjects()
        if len(self.buffertracks) == 0:
            mess = "Pas de sélection faite"
            wx.MessageBox(mess)
            return

        # Sauvegarde des lignes
        nomFichier = "CutLines.txt"
        self.SpareCouper(nomFichier)
        for track in self.buffertracks:
            track.set = False

        # suppression
        for track in self.buffertracks:
            ix = self.lastGetObjectIndex
            if hasattr(self.parent, 'OnDeleteTrack'):
                self.parent.OnDeleteTrack(track)
            self.modelObjects.remove(track)
        self.RepopulateList()
        self._SelectAndFocus(ix)
        wx.MessageBox(" %d lignes supprimées et mémorisées pour prochain <ctrl V>"%len(self.buffertracks))
        return

    def OnColler(self,event=None):
        # action coller
        if self.buffertracks and len(self.buffertracks) >0:
            ix = self.lastGetObjectIndex
            if len(self.GetSelectedObjects()) > 0:
                ix = self.modelObjects.index(self.GetSelectedObjects()[0])
            for track in self.buffertracks:
                track.valide = False
                track.vierge = True
                if hasattr(self.parent,'OnCollerTrack'):
                    self.parent.OnCollerTrack(track)
                else:
                    # avant de coller une track, raz du champs ID
                    track.donnees[0] = None
                    track.vierge = True
                    track.oldDonnees = [None,] * len(track.donnees)
                    if hasattr(self.parent,'ValideLigne'):
                        self.parent.ValideLigne(None, track)
                    if hasattr(self.parent, 'SauveLigne'):
                        self.parent.SauveLigne(track)
                self.modelObjects.insert(ix,track)
                if self.buffertracks:
                    for track in self.buffertracks:
                        track.set = True
                ix += 1
            self.RepopulateList()
            self._SelectAndFocus(ix)
        else:
            mess = "Rien en copier ou coller, refaites le <ctrl> C ou <ctrl> X"
            wx.MessageBox(mess)
        return

    def OnDelete(self,event):
        nb = len(self.GetSelectedObjects())
        # avertissements
        path = xchemins.GetRepTemp()
        mess2 = "\n\ncopie de sécurité en %s" % path
        if self.checkStateColumn and len(self.GetCheckedObjects()) > 0:
            mot = "coch"
        else:
            mot = "sélectionn"
        if nb == 0: mess = "Pas de lignes %sées pour suppression"%mot
        elif nb == 1 : mess = "Confirmation: suppression de la ligne %sée!"%mot + mess2
        else:  mess = "Confirmation: suppression des %d lignes %sées!%s"%(nb,mot,mess2)
        dlg = wx.MessageDialog(self,
                               mess,"Suppresion demandée",
                               style=wx.YES_NO|wx.ICON_INFORMATION,)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return True

        # Sauvegarde des lignes
        nomFichier = "DeletedLines.txt"
        self.SpareCouper(nomFichier)

        # suppression proprement dite
        ix = 0
        for obj in self.GetSelectedObjects():
            # suppression des lignes pour la saisie
            ix = self.lastGetObjectIndex
            # appel des éventuels spécifiques sur OnDelete
            if hasattr(self.parent, 'OnDeleteTrack'):
                self.parent.OnDeleteTrack(obj)
            event.Skip()
            #Suppression dans l'OLV
            self.modelObjects.remove(obj)
        self.RepopulateList()
        self._SelectAndFocus(ix)
        return True

    # def OnInsert() est géré dans la classe mère ObjectListView

    def GetTitreImpression(self):
        if hasattr(self.lanceur,'GetTitreImpression'):
            return self.lanceur.GetTitreImpression()
        elif hasattr(self, 'titreImpression') and self.titreImpression:
            return self.titreImpression
        return "Tableau récapitulatif"

class PanelListView(wx.Panel):
    # Panel pour listView et le footer, attention il crée un niveau généalogique supplémentaire (parent.parent)
    def __init__(self, parent, **dicOlv):
        id = -1
        self.parent = parent
        self.lanceur = parent
        if hasattr(parent,'lanceur'): self.lanceur = parent.lanceur
        self.oldRow = None
        stylePanel = wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, id=id, style=stylePanel)
        self.dictColFooter = dicOlv.pop('dictColFooter', {})
        if not 'id' in dicOlv: dicOlv['id'] = wx.ID_ANY
        if not 'style' in dicOlv:
            dicOlv['style'] = wx.LC_REPORT|wx.NO_BORDER|wx.LC_HRULES|wx.LC_VRULES
        if self.dictColFooter and len(self.dictColFooter.keys())>0:
            dicOlv['pnlFooter']=True

        self.ctrlOlv = ListView(self,**dicOlv)
        self.ctrl_footer = None
        self.SetFooter(reinit=False)
        self.ctrlOlv.Bind(wx.EVT_CHAR,self.OnChar)
        self.ctrlOlv.Bind(OLVEvent.EVT_CELL_EDIT_FINISHING,self.OnEditFinishing)
        self.ctrlOlv.Bind(OLVEvent.EVT_CELL_EDIT_FINISHED,self.OnEditFinished)
        self.ctrlOlv.Bind(OLVEvent.EVT_CELL_EDIT_STARTED,self.OnEditStarted)
        # Layout

    def Sizer(self):
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.ctrlOlv, 1, wx.ALL | wx.EXPAND, 0)
        sizerbase.Add(self.ctrl_footer, 0, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizerbase)
        self.Layout()

    def SetFooter(self,reinit=False):
        if reinit:
            del self.ctrl_footer
        self.ctrl_footer = Footer.Footer(self)
        self.ctrlOlv.SetFooter(ctrl=self.ctrl_footer, dictColFooter=self.dictColFooter)
        self.Sizer()

    def MAJ(self):
        self.ctrlOlv.MAJ()
        self.ctrl_footer.MAJ_totaux()
        self.ctrl_footer.MAJ_affichage()

    def GetListview(self):
        return self.ctrlOlv

    # Handler niveau OLV
    def OnChar(self, event):
        # GetUnicode renvoie 0 pour les touches spéciales, cf event.GetKeyCode() == wx.WXK_LEFT
        keycode = event.GetUnicodeKey()
        if keycode == 3: self.ctrlOlv.OnCopier(event) # ctrl C
        if keycode == 24: self.ctrlOlv.OnCouper(event) # ctrl X
        if keycode == 22: self.ctrlOlv.OnColler(event) # ctrl V
        event.Skip()

    # Handlers niveau cell Editor
    def OnEditStarted(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if self.ctrlOlv.checkColonne:
            code = self.ctrlOlv.lstCodesColonnes[col-1]
        track = self.ctrlOlv.GetObjectAt(row)
        # conservation des données de la ligne en cours
        if track.valide:
            track.oldDonnees = [x for x in track.donnees]

        # conservation de la valeur qui peut être modifiée
        if not (hasattr(track,'oldValue')):
            track.oldValue = None
        if not (hasattr(self.ctrlOlv,'error')):
            self.ctrlOlv.error = None
        if not self.ctrlOlv.error and hasattr(track,"%s" % code):
            track.oldValue = eval("track.%s"%code)
        else: track.oldValue = None

        # appel des éventuels spécifiques
        if hasattr(self.parent, 'OnEditStarted'):
            self.parent.OnEditStarted(code,track,editor=event.editor)
        event.Skip()

    def OnEditFinishing(self, event):
        self.event = event
        # gestion des actions de sortie
        row, col = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)
        value = self.ctrlOlv.cellEditor.GetValue()
        code = self.ctrlOlv.lstCodesColonnes[col]
        if self.ctrlOlv.checkColonne:
            code = self.ctrlOlv.lstCodesColonnes[col-1]

        # si pas de saisie on passe
        valueIdem = False
        if hasattr(track,"oldValue") and track.oldValue == value:
            valueIdem = True
        if (value == None) or valueIdem:
            track.noSaisie = True
            event.Skip()
            return
        track.noSaisie = False

        # appel des éventuels spécifiques
        if hasattr(self.parent, 'OnEditFinishing'):
            ret = self.parent.OnEditFinishing(code,value,event)
            if ret: value = ret
        # stockage de la nouvelle saisie
        track.__setattr__(code, value)
        track.donnees[col] = value
        event.Skip()

    def OnEditFinished(self, event):
        if self.ctrlOlv.cellBeingEdited:
            row, col = self.ctrlOlv.cellBeingEdited
            track = self.ctrlOlv.GetObjectAt(row)
            self.oldRow = row
            # si pas de saisie on passe
            if hasattr(track, 'noSaisie') and track.noSaisie:
                event.Skip()
                return

            # appel des éventuels spécifiques
            code = self.ctrlOlv.lstCodesColonnes[col]
            if self.ctrlOlv.checkColonne:
                code = self.ctrlOlv.lstCodesColonnes[col-1]

            if hasattr(self.parent, 'OnEditFinished'):
                ret = self.parent.OnEditFinished(code, track, editor=event.editor)

            # lance l'enregistrement de la ligne
            self.ValideLigne(code,track)
            if hasattr(track,'valide') and track.valide:
                self.SauveLigne(track)

            self.ctrl_footer.MAJ_totaux()
            self.ctrl_footer.MAJ_affichage()
        event.Skip()

    def OnEditFunctionKeys(self, event):
        # Fonction appelée par CellEditor.Validator lors de l'activation d'une touche de fonction
        if self.ctrlOlv.cellBeingEdited:
            self.parent.OnEditFunctionKeys(event)
            event.Skip()

    def ValideLigne(self,code,track):
        # Cette procédure peut générer deux attributs track.valide track.message interceptés par CellEditor.
        if hasattr(self.parent, 'ValideLigne'):
            self.parent.ValideLigne(code,track)

    def CalculeLigne(self,code,track):
        if hasattr(self.parent, 'CalculeLigne'):
            self.parent.CalculeLigne(code,track)

    def SauveLigne(self,track):
        # teste old donnees % en cas de modif lance le sauve ligne du parent
        if hasattr(self.parent, 'SauveLigne'):
            self.parent.SauveLigne(track)
        else:
            wx.MessageBox("Fonction Enregistrement de ligne non trouvé!!!","Erreur du programme",style = wx.ICON_ERROR)

    # Initialisation d'une nouvelle track
    def InitTrackVierge(self,track,modelObject):

        # appel des éventuels spécifiques
        if hasattr(self.parent, 'InitTrackVierge'):
            self.parent.InitTrackVierge(track,modelObject)
        track.oldDonnees = [x for x in track.donnees]

# ----------- Composition de l'écran -------------------------------------------------------
class PNL_params(xusp.TopBoxPanel):
    def __init__(self, parent, *args, **kwds):
        kwdsTopBox = {}
        for key in xusp.OPTIONS_TOPBOX:
            if key in kwds.keys(): kwdsTopBox[key] = kwds[key]
        super().__init__(parent, *args, **kwdsTopBox)
        self.parent = parent

class PNL_corps(wx.Panel):
    #panel olv avec habillage optionnel pour recherche (en bas), boutons actions (à droite)
    def __init__(self, parent, dicOlv,*args, **kwds):
        # size inutile car SizerAndFit l'ajustera
        minSize =       dicOlv.pop('minSize',(400,150))
        getBtnActions =    dicOlv.pop('getBtnActions',None)
        self.db = kwds.pop('db',None) #d'éventuels arguments db seront envoyés à olv pour les get données
        self.avecRecherche= dicOlv.pop('recherche',True)
        self.parent = parent
        self.lanceur = parent
        self.flagSkipEdit = False
        if hasattr(parent,'lanceur'): self.lanceur = parent.lanceur
        # récupére les éventuels boutons d'actions
        if getBtnActions:
            self.lstBtnActions = getBtnActions(self)
        else: self.lstBtnActions = None

        # init du super()
        wx.Panel.__init__(self, parent, *args)

        #ci dessous l'ensemble des autres paramètres possibles pour OLV
        lstParamsOlv = ['id',
                        'style',
                        'lstColonnes',
                        'lstCodesSup',
                        'lstDonnees',
                        'getDonnees',
                        'msgIfEmpty',
                        'sensTri',
                        'exportExcel',
                        'exportTexte',
                        'checkColonne',
                        'apercuAvantImpression',
                        'imprimer',
                        'saisie',
                        'inserer',
                        'supprimer',
                        'copier',
                        'coller',
                        'couper',
                        'toutCocher',
                        'toutDecocher',
                        'inverserSelection',
                        'dictColFooter',
                        'editMode',
                        'autoAddRow',
                        'sortable',
                        'sortColumnIndex',
                        'sortAscending',
                        ]

        # le footer éventuel doit passer au niveau panel suivant, sinon on ne cherche pas à le transférer
        self.avecFooter = ('dictColFooter'  in dicOlv)
        if not self.avecFooter : lstParamsOlv.remove('dictColFooter')

        #récup des seules clés possibles pour dicOLV
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur

        self.olv = PanelListView(self,**dicOlvOut)
        self.ctrlOlv = self.olv.ctrlOlv

        # choix  barre de recherche ou pas
        if self.avecRecherche:
            afficherCocher = False
            if self.ctrlOlv.checkStateColumn: afficherCocher = True
            self.ctrlOutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=afficherCocher)
            self.olv.ctrlOutils = self.ctrlOutils
        self.ctrlOlv.SetMinSize(minSize)
        self.ctrlOlv.MAJ()
        self.Sizer()

    def Sizer(self):
        #composition de l'écran selon les composants
        sizerbase = wx.BoxSizer(wx.HORIZONTAL)
        sizercorps = wx.BoxSizer(wx.VERTICAL)
        sizercorps.Add(self.olv, 10, wx.EXPAND, 10)
        if self.avecRecherche:
            sizercorps.Add(self.ctrlOutils, 0, wx.EXPAND, 10)
        sizerbase.Add(sizercorps, 10, wx.EXPAND, 10)
        # ajout des boutons d'actions
        if self.lstBtnActions:
            sizeractions = wx.BoxSizer(wx.VERTICAL)
            sizeractions.AddMany(xboutons.GetAddManyBtns(self,self.lstBtnActions))
            sizerbase.Add(sizeractions, 0, wx.TOP, 10)
        self.SetSizerAndFit(sizerbase)

class PNL_pied(wx.Panel):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, *args, **kwds):
        self.lanceur = dicPied.pop('lanceur',None)
        self.lstInfos = dicPied.pop('lstInfos',None)
        self.lstBtns = dicPied.pop('lstBtns',None)
        if (not self.lstBtns) and (not self.lstInfos):
            #force la présence d'un pied d'écran par défaut
            self.lstBtns = [('BtnOK', wx.OK, wx.Bitmap('xpy/Images/100x30/Bouton_ok.png', wx.BITMAP_TYPE_ANY),
                           "Cliquez ici pour fermer la fenêtre et quitter")]
        wx.Panel.__init__(self, parent, *args)
        self.parent = parent
        self.Sizer()

    def Sizer(self):
        self.itemsBtns = xboutons.GetAddManyBtns(self,self.lstBtns)
        self.itemsInfos = self.CreateItemsInfos(self.lstInfos)
        nbinfos = len(self.itemsInfos)
        nbcol=(len(self.itemsBtns)+len(self.itemsInfos)+1)
        #composition de l'écran selon les composants
        sizerpied = wx.FlexGridSizer(rows=1, cols=nbcol, vgap=0, hgap=0)
        if self.lstInfos:
            sizerpied.AddMany(self.itemsInfos)
        sizerpied.Add((10,10),1,wx.ALL|wx.EXPAND,5)
        if self.lstBtns:
            sizerpied.AddMany(self.itemsBtns)
        sizerpied.AddGrowableCol(nbinfos)
        self.SetSizer(sizerpied)

    def CreateItemsInfos(self,lstInfos):
        # images ou texte sont retenus
        self.infosImage = None
        self.infosTexte = None
        lstItems = [(7,7)]
        if not lstInfos: lstInfos = []
        for item in lstInfos:
            if isinstance(item,wx.Bitmap):
                self.infosImage = wx.StaticBitmap(self, wx.ID_ANY, item)
                lstItems.append((self.infosImage,0,wx.ALIGN_LEFT|wx.TOP,10))
            elif isinstance(item,str):
                self.infosTexte = wx.StaticText(self,wx.ID_ANY,item)
                lstItems.append((self.infosTexte,10,wx.ALIGN_LEFT|wx.ALL|wx.EXPAND,5))
            lstItems.append((7,7))
        return lstItems

    def SetItemsInfos(self,text=None,image=None,):
        # après create  permet de modifier l'info du pied pour dernière image et dernier texte
        if image:
            self.infosImage.SetBitmap(image)
        if text:
            self.infosTexte.SetLabelText(text)

    def OnBoutonOK(self,event):
        self.parent.OnFermer(None)

# ------------- Lancement ------------------------------------------------------------------
class DLG_tableau(xusp.DLG_vide):
    # minimum fonctionnel dans dialog tout est dans les trois pnl
    def __init__(self,parent,dicParams={},dicOlv={},dicPied={}, **kwds):
        #purge d'éventuels arguments db à ne pas envoyer à super()
        self.db = kwds.pop('db',None)
        autoSizer =     kwds.pop('autoSizer', True)
        size = kwds.get('size',None)
        if not 'style' in kwds.keys():
            kwds['style'] = wx.DEFAULT_FRAME_STYLE

        # recherche éventuelle base de donnée
        if not self.db and hasattr(parent,'db'):
            self.db = parent.db
        if not self.db:
            self.db = dicOlv.get('db',None)
        if not self.db:
            self.db = dicParams.get('db',None)

        # si size pas dans kwds, on pique celle de l'olv qui serait contrainte donc inutile
        if not size and dicOlv.get('size',None):
            kwds['size'] = dicOlv.pop('size',None)
        # recherche d'un dicBandeau
        for dic in (kwds, dicParams, dicOlv):
            dicBandeau = dic.pop('dicBandeau',None)
            if dicBandeau != None:
                break

        super().__init__(parent,**kwds)
        if dicBandeau:
            self.bandeau = xbandeau.Bandeau(self,**dicBandeau)
        else: self.bandeau = None

        # Création des différentes parties de l'écran
        self.pnlParams = PNL_params(self, **dicParams)
        kwds['db'] = self.db
        if dicOlv == {}:
            autoSizer = False
        else:
            if not hasattr(self, 'dicOlv'):
                self.dicOlv = xformat.CopyDic(dicOlv)
            self.pnlOlv = PNL_corps(self, self.dicOlv, **kwds)
            self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.pnlPied = PNL_pied(self, dicPied,  **kwds )

        # permet un Sizer de substitution différé après l'init propre à l'instance
        if autoSizer:
            self.ctrlOlv.MAJ()
            self.Sizer()

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        # haut d'écran
        growRow = 1
        if self.bandeau:
            growRow += 1
            sizer_base.Add(self.bandeau, 0, wx.EXPAND, 0)
        sizer_base.Add(self.pnlParams, 1, wx.TOP| wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP| wx.EXPAND, 3)
        sizer_base.Add(wx.StaticLine(self),1,wx.EXPAND,0)
        sizer_base.Add(self.pnlPied, 0,wx.EXPAND, 0)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(growRow)
        self.CenterOnScreen()
        self.SetSizer(sizer_base)

    def OnFermer(self, event):
        #wx.MessageBox("Traitement de sortie")
        if self.ctrlOlv.buffertracks:
            lstNoSet = [x for x in self.ctrlOlv.buffertracks if x.set != True]
            if len(lstNoSet) > 0:
                mess = "%d lignes ont été coupées sans être collées\n\n"%len(lstNoSet)
                mess += "La sortie de ce programme en fera disparaître la mémoire,"
                mess += "confirmez-vous la sortie?"
                ret = wx.MessageBox(mess, "Confirmation", style = wx.YES_NO)
                if ret != wx.YES:
                    return
        if event:
            event.Skip()
        if self.IsModal():
            self.EndModal(wx.ID_CANCEL)
        else:
            self.Close()

# ------------ Pour tests ------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    os.chdir('..')
    os.chdir('..')
    # tableau OLV central de l'écran ,
    #                    stringConverter=xpy.outils.xformat.FmtMontant
    liste_Colonnes = [
        ColumnDefn("null", 'centre', 0, 'IX', valueSetter=''),
        ColumnDefn("clé", 'centre', 60, 'cle', valueSetter=True,
                   isSpaceFilling=False ,cellEditorCreator = CellEditor.BooleanEditor),
        ColumnDefn("mot d'ici", 'left', 200, 'mot', valueSetter='A saisir', isEditable=True),
        ColumnDefn("nbre", 'right', -1, 'nombre', isSpaceFilling=True, valueSetter=0.0,
                   stringConverter=xformat.FmtDecimal),
        ColumnDefn("prix", 'left', 80, 'prix', valueSetter=0.0, isSpaceFilling=True,cellEditorCreator = CellEditor.ComboEditor),
        ColumnDefn("date", 'center', 80, 'date', valueSetter=wx.DateTime.FromDMY(1, 0, 1900), isSpaceFilling=True,
                   stringConverter=xformat.FmtDate),
        ColumnDefn("choice", 'center', 40, 'choice', valueSetter='mon item',choices=['CHQ','VRT','ESP'], isSpaceFilling=True,
                   cellEditorCreator = CellEditor.ChoiceEditor,)
    ]
    lstDonnees = [[1,False, 'Bonjour', -1230.05939, -1230.05939, None,'deux'],
                     [2,None, 'Bonsoir', 57.5, 208.99,datetime.date.today(),None],
                     [3,'', 'Jonbour', 0, 'remisé', datetime.date(2018, 11, 20), 'mon item'],
                     [4,29, 'Salut', 57.082, 209, wx.DateTime.FromDMY(28, 1, 2019),"Gérer l'entrée dans la cellule"],
                     [None,None, 'Salutation', 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), '2019-10-24'],
                     [None,2, 'Python', 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), '2000-12-25'],
                     [None,3, 'Java', 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), None],
                     [None,98, 'langage C', 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                     ]
    dicOlv = {'lstColonnes': liste_Colonnes,
              'lstDonnees': lstDonnees,
              'checkColonne': True,
              'recherche': True,
              'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
              'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
              }

    # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
    lstBtns = [('BtnPrec',-1, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (42, 22)),"Cliquez ici pour test info"),
               ('BtnPrec2',-1, "Ecran\nprécédent", "Retour à l'écran précédent next"),
               ('BtnOK', -1, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),"Cliquez ici pour fermer la fenêtre")
               ]
    lstInfos = [wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, ),
                wx.Bitmap('xpy/Images/16x16/Magique.png', wx.BITMAP_TYPE_PNG),
                "Autre\nInfo"]

    # l'info se compmose d'une imgae et d'un texte
    dicPied = {'lstBtns': lstBtns, 'lstInfos': lstInfos}

    # cadre des paramètres
    import datetime
    dicParams = {'matrice':{
            ('ident',"Vos paramètres"):[
            {'name': 'date', 'genre': 'Date', 'label': 'Début de période', 'value': datetime.date.today(),
                                    'help': 'Ce préfixe à votre nom permet de vous identifier'},
            {'name': 'utilisateur', 'genre': 'String', 'label': 'Votre identifiant', 'value': "NomSession",
                                    'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
                ],
            }}
    exempleframe = DLG_tableau(None,dicParams,dicOlv=dicOlv,dicPied=dicPied)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    app.MainLoop()
