#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - Projet XPY - xTableau.py (implémentation d'une gestion de tableau paramétrable)
#  2019/04/18
# note l'appel des fonctions 2.7 passent par le chargement de la bibliothèque future (vue comme past)
# ce module reprend les fonctions de xUTILS_Tableau sans y faire appel
# matrice OLV

import wx
import os
import xpy.outils.xformat
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, Filter, Footer, CTRL_Outils, OLVEvent
from xpy.outils.xconst import *

# ------------------------------------------------------------------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, donnees,codesColonnes, nomsColonnes, setterValues):
        self.donnees = donnees
        if not(len(donnees) == len(codesColonnes)== len(nomsColonnes) == len(setterValues)):
            wx.MessageBox("Problème de nombre d'occurences!\n%d donnees, %d codes, %d colonnes et %d valeurs défaut"
                          %(len(donnees), len(codesColonnes), len(nomsColonnes), len(setterValues)))
        for ix in range(len(donnees)):
            donnee = donnees[ix]
            if setterValues[ix]:
                if (donnee is None):
                    donnee = setterValues[ix]
                else:
                    if not isinstance(donnee,type(setterValues[ix])):
                        try:
                            if type(setterValues[ix]) in (int,float):
                                donnee = float(donnee)
                            elif type(setterValues[ix]) == str:
                                donnee = str(donnee)
                        except : pass
            self.__setattr__(codesColonnes[ix], donnee)

class ListView(FastObjectListView):
    """
    Lors de l'instanciation de cette classe vous pouvez y passer plusieurs parametres :

    listeColonnes : censé être une liste d'objets ColumndeFn
    listeDonnees : liste de listes ayant la même longueur que le nombre de colonnes.

    msgIfEmpty : une chaine de caractères à envoyer si le tableau est vide

    colonneTri : Permet d'indiquer le numéro de la colonne selon laquelle on veut trier
    sensTri : True ou False indique le sens de tri

    exportExcel : True par défaut, False permet d'enlever l'option 'Exporter au format Excel'
    exportTexte : idem
    apercuAvantImpression : idem
    imprimer : idem
    toutCocher : idem
    toutDecocher : idem
    menuPersonnel : On peut avoir déjà créé un "pré" menu contextuel auquel viendra s'ajouter le tronc commun

    titreImpression : Le titre qu'on veut donner à la page en cas d'impression par exemple "Titre")
    orientationImpression : L'orientation de l'impression, True pour portrait et False pour paysage

    Pour cette surcouche de OLV j'ai décidé de ne pas laisser la fonction OnItemActivated car ça peut changer selon le tableau
    donc ce sera le role de la classe parent (qui appelle ListView) de définir une fonction OnItemActivated qui sera utilisée
    lors du double clic sur une ligne

    Dictionnaire optionnel ou on indique si on veut faire le bilan (exemple somme des valeurs)
    """

    def __init__(self, *args, **kwds):
        self.ctrl_footer = None
        self.parent = args[0].parent
        self.pnlfooter = kwds.pop("pnlfooter", None)
        self.checkColonne = kwds.pop("checkColonne",True)
        self.listeColonnes = kwds.pop("listeColonnes", [])
        self.msgIfEmpty = kwds.pop("msgIfEmpty", "Tableau vide")
        self.colonneTri = kwds.pop("colonneTri", None)
        self.sensTri = kwds.pop("sensTri", True)
        self.menuPersonnel = kwds.pop("menuPersonnel", None)
        self.listeDonnees = kwds.pop("listeDonnees", None)
        self.lstCodesColonnes = self.formerCodeColonnes()
        self.lstNomsColonnes = self.formerNomsColonnes()
        self.lstSetterValues = self.formerSetterValues()
        self.dictColFooter = kwds.pop("dictColFooter", {})

        # Choix des options du 'tronc commun' du menu contextuel
        self.exportExcel = kwds.pop("exportExcel", True)
        self.exportTexte = kwds.pop("exportTexte", True)
        self.apercuAvantImpression = kwds.pop("apercuAvantImpression", True)
        self.imprimer = kwds.pop("imprimer", True)
        self.toutCocher = kwds.pop("toutCocher", True)
        self.toutDecocher = kwds.pop("toutDecocher", True)
        self.inverserSelection = kwds.pop("inverserSelection", True)
        if not self.checkColonne:
            self.toutCocher = False
            self.toutDecocher = False
            self.inverserSelection = False

        # Choix du mode d'impression
        self.titreImpression = kwds.pop("titreImpression", "Tableau récapitulatif")
        self.orientationImpression = kwds.pop("orientationImpression", True)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []

        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args,**kwds)
        # Binds perso
        self.Bind(OLVEvent.EVT_ITEM_CHECKED, self.OnItemChecked)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def SetFooter(self, ctrl=None, dictColFooter={}):
        self.ctrl_footer = ctrl
        self.ctrl_footer.listview = self
        self.ctrl_footer.dictColFooter = dictColFooter

    def MAJ_footer(self):
        if self.ctrl_footer != None:
            self.ctrl_footer.MAJ_totaux()
            self.ctrl_footer.MAJ_affichage()

    def formerTracks(self):
        #self.tracks = list() faisait double emploi avec 'self.modelObjects'
        tracks = list()
        if self.listeDonnees is None:
            return tracks

        for ligneDonnees in self.listeDonnees:
            tracks.append(TrackGeneral(donnees=ligneDonnees,codesColonnes=self.lstCodesColonnes,
                                            nomsColonnes=self.lstNomsColonnes,setterValues=self.lstSetterValues))
        return tracks

    def formerCodeColonnes(self):
        codeColonnes = list()
        for colonne in self.listeColonnes:
            code = colonne.valueGetter
            codeColonnes.append(code)
        return codeColonnes

    def formerNomsColonnes(self):
        nomColonnes = list()
        for colonne in self.listeColonnes:
            nom = colonne.title
            nomColonnes.append(nom)
        return nomColonnes

    def formerSetterValues(self):
        setterValues = list()
        for colonne in self.listeColonnes:
            fmt = colonne.stringConverter
            tip = None
            if colonne.valueSetter != None:
                tip = colonne.valueSetter
            if tip == None:
                tip = ''
                if fmt:
                    fmt = colonne.stringConverter.__name__
                    if fmt[3:] in ('Montant','Solde','Decimal','Entier'):
                        tip = 0.0
                    elif fmt[3:] == 'Date':
                        tip = wx.DateTime.FromDMY(1,0,1900)
            setterValues.append(tip)
        return setterValues

    def InitModel(self):
        #self.donnees = self.GetTracks()
        self.donnees = self.formerTracks()

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        # On définit les colonnes
        self.SetColumns(self.listeColonnes)
        if self.checkColonne:
            self.CreateCheckStateColumn(0)
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT))
        # Si la colonne à trier n'est pas précisée on trie selon la première par défaut
        if self.ColumnCount > 1:
            if self.colonneTri == None:
                self.SortBy(1, self.sensTri)
            else:
                self.SortBy(self.colonneTri, self.sensTri)
        self.SetObjects(self.formerTracks())

    def MAJ(self, ID=None):
        self.selectionID = ID
        #self.InitModel()
        self.InitObjectListView()
        # Rappel de la sélection d'un item
        if self.selectionID != None and len(self.innerList) > 0:
            self.SelectObject(self.innerList[ID], deselectOthers=True, ensureVisible=True)

    def Selection(self):
        return self.GetSelectedObjects()

    """def GetTracks(self):
        # Récupération des données
        return self.tracks"""

    def OnItemChecked(self, event):
        if self.pnlfooter:
            self.pnlfooter.SetFooter(reinit=True)

    def OnContextMenu(self, event):
        """
        Ouverture du menu contextuel

        L'idée serait de créer dans ce menu tout le 'tronc commun' c'est à dire Aperçu avant impression, Imprimer,
        Exporter au format texte , Exporter au format Excel, et pourquoi pas ajouter une option copier (la ligne ou tout le tableau)

        Ensuite on pourrait passer en paramètre une partie du menu qui sera simplement ajoutée au début.

        Par exemple les options 'tout cocher' et 'tout décocher' pourraient être activées de base et paramétrables lors de l'initialisation

        """
        if len(self.Selection()):  # equivalent a !=0
            noSelection = False
        else:
            noSelection = True

        # Création du menu contextuel ou alors récupération du menu donné en paramètre
        if self.menuPersonnel:
            menuPop = self.menuPersonnel
            # On ajoute un séparateur ici ou dans la classe parent ?
            menuPop.AppendSeparator()
        else:
            menuPop = wx.Menu()

        # Item Tout cocher
        if self.toutCocher:
            item = wx.MenuItem(menuPop, 70, TOUT_COCHER_TXT)
            bmp = wx.Bitmap(COCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout décocher
        if self.toutDecocher:
            item = wx.MenuItem(menuPop, 80, TOUT_DECOCHER_TXT)
            bmp = wx.Bitmap(DECOCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        if self.inverserSelection and self.GetSelectedObject() is not None:
            item = wx.MenuItem(menuPop, 90, INVERSER_SELECTION_TXT)
            bmp = wx.Bitmap(DECOCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.InverserCocheSelection, id=90)

        # On met le separateur seulement si un des deux menus est present
        if self.toutDecocher or self.toutCocher:
            menuPop.AppendSeparator()
        if self.parent.barreRecherche:
            # Item filtres
            item = wx.MenuItem(menuPop, 81, UN_FILTRE)
            bmp = wx.Bitmap(FILTRE_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.UnFiltre, id=81)

            item = wx.MenuItem(menuPop, 82, AJOUT_FILTRE)
            bmp = wx.Bitmap(FILTRE_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.AjoutFiltre, id=82)

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
        return self.exportExcel or self.exportTexte or self.apercuAvantImpression or self.toutCocher or self.toutDecocher or self.imprimer or self.menuPersonnel

    def GetOrientationImpression(self):
        if self.orientationImpression:
            return wx.PORTRAIT
        return wx.LANDSCAPE

    def Apercu(self, event):
        import xpy.outils.ObjectListView.Printer as printer
        # Je viens de voir dans la fonction concernée, le format n'est pas utilisé et il vaut "A" par défaut donc rien ne change
        prt = printer.ObjectListViewPrinter(self, titre=self.titreImpression,
                                                        orientation=self.GetOrientationImpression())
        prt.Preview()

    def Imprimer(self, event):
        import xpy.outils.ObjectListView.Printer as printer
        prt = printer.ObjectListViewPrinter(self, titre=self.titreImpression,
                                                        orientation=self.GetOrientationImpression())
        prt.Print()

    def ExportTexte(self, event):
        import xpy.outils.xexport
        xpy.outils.xexport.ExportTexte(self, titre=self.titreImpression, autoriseSelections=False)

    def ExportExcel(self, event):
        import xpy.outils.xexport
        xpy.outils.xexport.ExportExcel(self, titre=self.titreImpression, autoriseSelections=False)

    def CocheTout(self, event=None):
        if self.GetFilter() is not None:
            listeObjets = self.GetFilteredObjects()
        else:
            listeObjets = self.GetObjects()
        for track in listeObjets:
            self.Check(track)
            self.RefreshObject(track)
        return

    def CocheRien(self, event=None):
        if self.GetFilter() is not None:
            listeObjets = self.GetFilteredObjects()
        else:
            listeObjets = self.GetObjects()
        for track in listeObjets:
            self.Uncheck(track)
            self.RefreshObject(track)
        return

    def InverserCocheSelection(self, event=None):
        if self.GetFilter() is not None:
            listeObjets = self.GetFilteredObjects()
        else:
            listeObjets = self.GetObjects()

        if self.GetSelectedObject() is not None:
            for track in listeObjets:
                if self.IsChecked(track):
                    self.Uncheck(track)
                else:
                    self.Check(track)
                self.RefreshObject(track)
                if track == self.GetSelectedObject():
                    return

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def UnFiltre(self, event=None):
        self.parent.ctrloutils.UnFiltre()

    def AjoutFiltre(self, event=None):
        self.parent.ctrloutils.AjoutFiltre()

    def SupprimerFiltres(self, event=None):
        self.parent.ctrloutils.SupprimerFiltres()

class PanelListView(wx.Panel):
    # Le Panel contiendra le listView et le footer, attention à l'étape généalogique supplémentaire
    def __init__(self, parent, **kwargs):
        id = -1
        self.parent = parent
        stylePanel = wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, id=id, style=stylePanel)
        self.dictColFooter = kwargs.pop("dictColFooter", {})
        if not "id" in kwargs: kwargs["id"] = wx.ID_ANY
        if not "style" in kwargs: kwargs["style"] = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES
        kwargs["pnlfooter"]=self
        listview = ListView(self,**kwargs)

        self.ctrl_listview = listview
        self.ctrl_footer = None
        self.SetFooter(reinit=False)

        # Layout

    def Sizer(self):
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.ctrl_listview, 1, wx.ALL | wx.EXPAND, 0)
        sizerbase.Add(self.ctrl_footer, 0, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizerbase)
        self.Layout()

    def SetFooter(self,reinit=False):
        if reinit:
            del self.ctrl_footer
        self.ctrl_footer = Footer.Footer(self)
        self.ctrl_listview.SetFooter(ctrl=self.ctrl_footer, dictColFooter=self.dictColFooter)
        self.Sizer()

    def MAJ(self):
        self.ctrl_listview.MAJ()
        self.ctrl_footer.MAJ()

    def GetListview(self):
        return self.ctrl_listview

# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(wx.Panel):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        self.lanceur = dicOlv.pop('lanceur',None)
        self.lstActions = kwds.pop('lstActions',None)
        self.lstInfos = kwds.pop('lstInfos',None)
        self.lstBtns = kwds.pop('lstBtns',None)
        self.dicOnClick = kwds.pop('dicOnClick',None)
        if (not self.lstBtns) and (not self.lstInfos):
            #force la présence d'un pied d'écran par défaut
            self.lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY),
                           "Cliquez ici pour fermer la fenêtre")]

        wx.Panel.__init__(self, parent, *args,  **kwds)
        #ci dessous l'ensemble des autres paramètres possibles pour OLV
        lstParamsOlv = ['id',
                        'style',
                        'listeColonnes',
                        'listeDonnees',
                        'msgIfEmpty',
                        'sensTri',
                        'exportExcel',
                        'exportTexte',
                        'checkColonne',
                        'apercuAvantImpression',
                        'imprimer',
                        'toutCocher',
                        'toutDecocher',
                        'inverserSelection',
                        'titreImpression',
                        'orientationImpression',
                        'dictColFooter']
        self.avecFooter = "dictColFooter" in dicOlv
        if not self.avecFooter : lstParamsOlv.remove('dictColFooter')
        if 'recherche' in dicOlv: self.barreRecherche = dicOlv['recherche']
        else : self.barreRecherche = True
        self.parent = parent
        #récup des seules clés possibles pour dicOLV
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur

        # choix footer ou pas
        pnlOlv = PanelListView(self,**dicOlvOut)
        if self.avecFooter:
            self.ctrlOlv = pnlOlv.ctrl_listview
            self.olv = pnlOlv
        else:
            self.ctrlOlv = ListView(self,**dicOlvOut)
            self.olv = self.ctrlOlv
            self.ctrlOlv.parent = self.ctrlOlv.Parent
        if self.barreRecherche:
            self.ctrloutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=False)
        self.ctrlOlv.MAJ()
        self.Sizer()

    def Sizer(self):
        #composition de l'écran selon les composants
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerhaut = wx.BoxSizer(wx.HORIZONTAL)
        sizerolv = wx.BoxSizer(wx.VERTICAL)
        sizerolv.Add(self.olv, 10, wx.EXPAND, 10)
        if self.barreRecherche:
            sizerolv.Add(self.ctrloutils, 0, wx.EXPAND, 10)
        sizerhaut.Add(sizerolv,10,wx.ALL|wx.EXPAND,3)
        if self.lstActions:
            sizeractions = wx.StaticBoxSizer(wx.VERTICAL, self, label='Actions')
            self.itemsActions = self.GetItemsBtn(self.lstActions)
            sizeractions.AddMany(self.itemsActions)
            sizerhaut.Add(sizeractions,0,wx.ALL|wx.EXPAND,3)

        sizerbase.Add(sizerhaut, 10, wx.EXPAND, 10)
        sizerbase.Add(wx.StaticLine(self), 0, wx.TOP| wx.EXPAND, 3)
        sizerpied = wx.BoxSizer(wx.HORIZONTAL)
        if self.lstInfos:
            sizerinfos = wx.StaticBoxSizer(wx.HORIZONTAL,self,label='infos')
            self.itemsInfos = self.GetItemsInfos(self.lstInfos)
            sizerinfos.AddMany(self.itemsInfos)
            sizerpied.Add(sizerinfos,10,wx.BOTTOM|wx.LEFT|wx.EXPAND,3)
        else: sizerpied.Add((10,10),10,wx.BOTTOM|wx.LEFT|wx.EXPAND,3)
        if self.lstBtns:
            self.itemsBtns = self.GetItemsBtn(self.lstBtns)
            sizerpied.AddMany(self.itemsBtns)
        sizerbase.Add(sizerpied,0,wx.EXPAND,5)
        self.SetSizerAndFit(sizerbase)

    def GetItemsBtn(self,lstBtns):
        # décompactage des paramètres de type bouton
        lstBtn = []
        for btn in lstBtns:
            try:
                (code,ID,label,tooltip) = btn
                if isinstance(label,wx.Bitmap):
                    bouton = wx.BitmapButton(self,ID,label)
                elif isinstance(label,str):
                    bouton = wx.Button(self,ID,label)
                else: bouton = wx.Button(self,ID,'Erreur!')
                bouton.SetToolTip(tooltip)
                bouton.name = code
                #le bouton OK est par défaut, il ferme l'écran DLG
                if code == 'BtnOK':
                    bouton.Bind(wx.EVT_BUTTON, self.OnBoutonOK)
                #implémente les fonctions bind transmises, soit par le pointeur soit par eval du texte
                if self.dicOnClick and code in self.dicOnClick:
                    if isinstance(self.dicOnClick[code],str):
                        fonction = lambda evt,code=code: eval(self.dicOnClick[code])
                    else: fonction = self.dicOnClick[code]
                    bouton.Bind(wx.EVT_BUTTON, fonction)
                lstBtn.append((bouton, 0, wx.ALL , 5))

            except:
                bouton = wx.Button(self, wx.ID_ANY, 'Erreur!')
                lstBtn.append((bouton, 0, wx.ALL, 5))
        return lstBtn

    def GetItemsInfos(self,lstInfos):
        lstInfo = []
        for label in lstInfos:
            if isinstance(label,wx.Bitmap):
                info = wx.StaticBitmap(self, wx.ID_ANY, label)
            elif isinstance(label,str):
                info = wx.StaticText(self,wx.ID_ANY,label)
            else: info = wx.Button(self,wx.ID_OK,'Erreur!')
            lstInfo.append((info,0,wx.RIGHT|wx.ALIGN_LEFT,10))
        return lstInfo

    def OnBoutonOK(self,event):
        self.parent.Close()

class DLG_tableau(wx.Dialog):
    # minimum fonctionnel dans dialog tout est dans pnl
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        largeur = dicOlv.pop("largeur", 800)
        hauteur = dicOlv.pop("hauteur", 700)
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,None, title=titre, size=(largeur,hauteur),style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        self.pnl = PNL_tableau(self, dicOlv,  **kwds )
        self.ctrlOlv = self.pnl.ctrlOlv
        self.CenterOnScreen()
        self.Layout()

    def Close(self):
        self.EndModal(wx.OK)

    def Validation(self,param=None):
        # pour test avec appel de xGestion_Ligne
        self.pnl.ctrlOlv.MAJ()
        return True

# -- pour tests -----------------------------------------------------------------------------------------------------
liste_Colonnes = [
    ColumnDefn("clé", 'left', 10, "cle",valueSetter=1,isSpaceFilling = True,),
    ColumnDefn("mot d'ici", 'left', 200, "mot",valueSetter='',isEditable=False),
    ColumnDefn("nbre", 'right', -1, "nombre",isSpaceFilling = True, valueSetter=0.0, stringConverter=xpy.outils.xformat.FmtDecimal),
    ColumnDefn("prix", 'left', 80, "prix",valueSetter=0.0,isSpaceFilling = True, stringConverter=xpy.outils.xformat.FmtMontant),
    ColumnDefn("date", 'center', 80, "date",valueSetter=wx.DateTime.FromDMY(1,0,1900),isSpaceFilling = True,  stringConverter=xpy.outils.xformat.FmtDate),
    ColumnDefn("date SQL", 'center', 80, "datesql", valueSetter='2000-01-01',isSpaceFilling = True,
               stringConverter=xpy.outils.xformat.FmtDate)
]
liste_Donnees = [[18, "Bonjour", -1230.05939,-1230.05939,None,None],
                 [19, "Bonsoir", 57.5, 208.99,wx.DateTime.FromDMY(15,11,2018),'2019-03-29'],
                 [1, "Jonbour", 0 , 209,wx.DateTime.FromDMY(6,11,2018),'2019-03-01'],
                 [29, "Salut", 57.082, 209,wx.DateTime.FromDMY(28,1,2019),'2019-11-23'],
                 [None, "Salutation", 57.08, 0,wx.DateTime.FromDMY(1,7,1997),'2019-10-24'],
                 [2, "Python", 1557.08, 29,wx.DateTime.FromDMY(7,1,1997),'2000-12-25'],
                 [3, "Java", 57.08, 219,wx.DateTime.FromDMY(1,0,1900),''],
                 [98, "langage C", 10000, 209,wx.DateTime.FromDMY(1,0,1900),''],
                 ]
dicOlv = {'listeColonnes':liste_Colonnes,
                'listeDonnees':liste_Donnees,
                'hauteur':650,
                'largeur':850,
                'recherche':True,
                'msgIfEmpty':"Aucune donnée ne correspond à votre recherche",
                'dictColFooter':{"nombre" : {"mode" : "total",  "alignement" : wx.ALIGN_RIGHT},
                                 "mot" : {"mode" : "nombre",  "alignement" : wx.ALIGN_CENTER},
                                 "prix": {"mode": "total", "alignement": wx.ALIGN_RIGHT},}
        }
# params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
lstActions = [('Action1',wx.ID_COPY,'Choix un',"Cliquez pour l'action 1"),
              ('Action2',wx.ID_CUT,'Choix deux',"Cliquez pour l'action 2")]
# params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
dicOnClick = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                'Action2': 'self.parent.Validation()',
                'BtnPrec' : 'self.parent.Close()'}

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    lstBtns = [('BtnPrec', wx.ID_FORWARD, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (42, 22)),
                "Cliquez ici pour retourner à l'écran précédent"),
               ('BtnPrec2', wx.ID_PREVIEW_NEXT, "Ecran\nprécédent", "Retour à l'écran précédent next"),
               ('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                "Cliquez ici pour fermer la fenêtre")
               ]
    # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
    lstInfos = ['Première', "Voici", wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),
                "Autre\nInfo"]

    exempleframe = DLG_tableau(None,dicOlv=dicOlv,lstBtns= lstBtns,lstActions=lstActions,lstInfos=lstInfos,dicOnClick=dicOnClick)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    print(ret)
    app.MainLoop()
