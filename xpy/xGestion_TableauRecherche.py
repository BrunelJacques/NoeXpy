#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - évolution surcouche OLV ne reçoit pas les données mais une requête avec filtre qui s'actualise
#  permet d'interroger les tables volumineuses avec l'option LIMIT
#  Le double clic lance une action sur la ligne
#  2020/06/02

import wx
import os
import datetime
import xpy.xUTILS_DB            as xdb
import xpy.xUTILS_SaisieParams  as xusp
from xpy.outils import xbandeau,xformat,xboutons
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, CTRL_Outils
from xpy.outils.xconst import *

# ------------------------------------------------------------------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, donnees,codesColonnes, nomsColonnes, setterValues,codesSup=[]):
        # il peut y avoir plus de données que le nombre de colonnes, elles sont non gérées par le tableau
        if not (len(donnees)-len(codesSup) == len(codesColonnes) == len(nomsColonnes) == len(setterValues) ):
            lst = [str(codesColonnes),str(nomsColonnes),str(setterValues),str(donnees)]
            mess = "Problème de nombre d'occurences!\n\n"
            mess += "%d - %d donnees, %d codes, %d colonnes et %d valeurs défaut"%(len(donnees),len(codesSup),
                                                        len(codesColonnes), len(nomsColonnes), len(setterValues))
            mess += '\n\n'+'\n\n'.join(lst)
            wx.MessageBox(mess,caption="xGestion_TableauEditor.TrackGeneral")
        self.donnees = donnees
        for ix in range(len(codesColonnes + codesSup)):
            donnee = donnees[ix]
            if setterValues[ix]:
                # prise de la valeur par défaut si pas de donnée
                if (donnee is None):
                    donnee = setterValues[ix]
                # le type de la donnée n'est pas celui attendu
                else:
                    if not isinstance(donnee,type(setterValues[ix])):
                        try:
                            if type(setterValues[ix]) in (int,float):
                                donnee = float(donnee)
                            elif type(setterValues[ix]) == str:
                                donnee = str(donnee)
                            elif isinstance(setterValues[ix],(wx.DateTime,datetime.date,datetime.datetime,datetime.time)):
                                donnee = xformat.DateSqlToDatetime(donnee)
                        except : pass
            self.__setattr__((codesColonnes + codesSup)[ix], donnee)

class ListView(FastObjectListView):
    """
    Lors de l'instanciation de cette classe vous pouvez y passer plusieurs parametres :

    lstColonnes : censé être une liste d'objets ColumndeFn
    lstDonnees : est alimenté par la fonction getDonnees

    msgIfEmpty : une chaine de caractères à envoyer si le tableau est vide

    sortColumnIndex : Permet d'indiquer le numéro de la colonne selon laquelle on veut trier
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
        self.parent = args[0]
        self.filtre = ''
        self.dicOlv = kwds.copy()
        #self.pnlFooter = kwds.pop('pnlFooter', None) - pas implementé
        style = kwds.pop('style', wx.LC_SINGLE_SEL)
        self.checkColonne = kwds.pop('checkColonne',False)
        self.lstColonnes = kwds.pop('lstColonnes', [])
        self.lstCodesSup = kwds.pop('lstCodesSup', [])
        self.msgIfEmpty = kwds.pop('msgIfEmpty', 'Tableau vide')
        self.sortColumnIndex = kwds.pop('sortColumnIndex', None)
        self.sensTri = kwds.pop('sensTri', True)
        self.menuPersonnel = kwds.pop('menuPersonnel', False)
        self.getDonnees = kwds.pop('getDonnees', None)

        # Choix des options du 'tronc commun' du menu contextuel
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
        self.titreImpression = kwds.pop('titreImpression', "Tableau récapitulatif")
        self.orientationImpression = kwds.pop('orientationImpression', True)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1

        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args,style=style,**kwds)
        self.InitObjectListView()
        self.InitModel()

    def formerCodeColonnes(self):
        codeColonnes = list()
        for colonne in self.lstColonnes:
            code = colonne.valueGetter
            codeColonnes.append(code)
        return codeColonnes

    def formerNomsColonnes(self):
        nomColonnes = list()
        for colonne in self.lstColonnes:
            nom = colonne.title
            nomColonnes.append(nom)
        return nomColonnes

    def formerSetterValues(self):
        setterValues = list()
        for colonne in self.lstColonnes:
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

    def formerTracks(self,**kwd):
        kwd['dicOlv'] = self.dicOlv
        self.lstDonnees = self.getDonnees(**kwd)

        tracks = list()
        if self.lstDonnees is None:
            return tracks
        for ligneDonnees in self.lstDonnees:
            tracks.append(TrackGeneral(ligneDonnees,self.lstCodesColonnes,self.lstNomsColonnes,self.lstSetterValues,
                                        codesSup=self.lstCodesSup))
        return tracks

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = '#F0FBED'
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        # On définit les colonnes0
        self.SetColumns(self.lstColonnes)
        if self.checkColonne:
            self.CreateCheckStateColumn(0)
        self.lstCodesColonnes = self.formerCodeColonnes()
        self.lstNomsColonnes = self.formerNomsColonnes()
        self.lstSetterValues = self.formerSetterValues()
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.FONTFAMILY_DEFAULT))
        # Si la colonne à trier n'est pas précisée on trie selon la première par défaut
        if self.ColumnCount > 1:
            if self.sortColumnIndex == None:
                self.SortBy(1, self.sensTri)
            else:
                self.SortBy(self.sortColumnIndex, self.sensTri)

    def InitModel(self,**kwd):
        #kwd peut contenir  filtretxt et lstfiltres
        if hasattr(self.Parent.Parent,'db'):
            kwd['db'] = self.Parent.Parent.db
        self.SetObjects(self.formerTracks(**kwd))
        if len(self.innerList) >0:
            self.SelectObject(self.innerList[0])

    def MAJ(self, ID=None):
        self.selectionID = ID
        self.InitModel()
        # Rappel de la sélection d'un item
        if self.selectionID != None and len(self.innerList) > 0:
            self.SelectObject(self.innerList[ID], deselectOthers=True, ensureVisible=True)

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        # Création du menu contextuel
        if self.menuPersonnel:
            menuPop = self.Parent.GetMenuPersonnel()
            # On met un separateur
            menuPop.AppendSeparator()
        else:
            menuPop = wx.Menu()

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

        if self.parent.ctrlOutils:
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
        return self.exportExcel or self.exportTexte or self.apercuAvantImpression or self.imprimer or self.menuPersonnel

    def GetOrientationImpression(self):
        if self.orientationImpression:
            return wx.PORTRAIT
        return wx.LANDSCAPE

    def Apercu(self, event):
        import xpy.outils.ObjectListView.Printer as printer
        # Je viens de voir dans la fonction concernée, le format n'est pas utilisé et il vaut 'A' par défaut donc rien ne change
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

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def OnBoutonFiltrer(self, event=None):
        self.parent.ctrlOutils.OnBoutonFiltrer(event)

    def SupprimerFiltres(self, event=None):
        self.parent.ctrlOutils.SupprimerFiltres()

# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(wx.Panel):
    #panel olv avec habillage optionnel pour des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        self.parent = parent
        self.avecRecherche = dicOlv.pop('recherche',True)
        dicBandeau = dicOlv.pop('dicBandeau',None)
        autoSizer = dicOlv.pop('autoSizer',True)
        self.lstBtns = kwds.pop('lstBtns',None)
        if self.lstBtns == None:
            self.lstBtns = dicOlv.pop('lstBtns', None)
        self.lstBtnActions = kwds.pop('lstBtnActions',None)
        self.dicOnClick = kwds.pop('dicOnClick',None)
        if self.lstBtns == None :
            #force la présence d'un pied d'écran par défaut
            self.lstBtns =  [
                ('BtnPrec', wx.ID_CANCEL, wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (32, 32)),
                "Abandon, Cliquez ici pour retourner à l'écran précédent"),
               ('BtnOK', wx.ID_OK, wx.Bitmap('xpy/Images/32x32/Valider.png', wx.BITMAP_TYPE_ANY),
                "Cliquez ici pour Choisir l'item sélectionné"),
            ]

        wx.Panel.__init__(self, parent, *args,  **kwds)
        #ci dessous l'ensemble des autres paramètres possibles pour OLV
        if dicBandeau:
            self.bandeau = xbandeau.Bandeau(self,**dicBandeau)
        else:self.bandeau = None

        #récup des seules clés possibles pour dicOLV
        lstParamsOlv = ['id',
                        'style',
                        'lstColonnes',
                        'lstCodesSup',
                        'lstChamps',
                        'sortColumnIndex',
                        'getDonnees',
                        'getDonneesObj',
                        'msgIfEmpty',
                        'sensTri',
                        'exportExcel',
                        'exportTexte',
                        'apercuAvantImpression',
                        'imprimer',
                        'titreImpression',
                        'orientationImpression',
                        'cellEditMode',
                        'useAlternateBackColors',
                        'menuPersonnel',
                        'checkColonne'
                        ]
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur
        self.ctrlOlv = ListView(self,**dicOlvOut)

        # choix  barre de recherche ou pas
        if self.avecRecherche:
            afficherCocher = False
            if self.ctrlOlv.checkStateColumn: afficherCocher = True
            self.ctrlOutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=afficherCocher)
            self.ctrlOutils.Bind(wx.EVT_CHAR,self.OnRechercheChar)
            self.pnlPied = (10,10)
        else:
            self.ctrlOutils = False
            # Le pnlPied est un spécifique alimenté par les descendants
            self.pnlPied = (200,10)

        # Sizer différé pour les descendants avec spécificités modifiant le panel
        if autoSizer:
            self.ProprietesOlv()
            self.Sizer()

    def Sizer(self):
        #composition de l'écran selon les composants
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        if self.bandeau:
            sizerhaut = wx.BoxSizer(wx.VERTICAL)
            sizerhaut.Add(self.bandeau,0,wx.ALL|wx.EXPAND,3)
            sizerbase.Add(sizerhaut, 0, wx.EXPAND, 5)

        sizercentre = wx.BoxSizer(wx.HORIZONTAL)
        sizercentre.Add(self.ctrlOlv,10,wx.ALL|wx.EXPAND,3)
        if self.lstBtnActions:
            sizeractions = wx.StaticBoxSizer(wx.VERTICAL, self, label='Gestion')
            self.itemsActions = self.GetItemsBtn(self.lstBtnActions)
            sizeractions.AddMany(self.itemsActions)
            sizercentre.Add(sizeractions,0,wx.ALL|wx.EXPAND,3)
        sizerbase.Add(sizercentre, 10, wx.EXPAND, 0)

        sizerbase.Add(wx.StaticLine(self), 0, wx.TOP| wx.EXPAND, 3)

        sizerpied = wx.FlexGridSizer(rows=1, cols=10, vgap=0, hgap=0)
        if self.avecRecherche:
            sizerpied.Add(self.ctrlOutils, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, 3)

        sizerpied.Add(self.pnlPied, 0, wx.EXPAND|wx.ALIGN_LEFT, 0)

        if self.lstBtns:
            self.itemsBtns = self.GetItemsBtn(self.lstBtns)
            sizerpied.AddMany(self.itemsBtns)
        sizerpied.AddGrowableCol(0)
        sizerbase.Add(sizerpied,0,wx.EXPAND,5)
        self.SetSizerAndFit(sizerbase)
        if self.avecRecherche:
            self.ctrlOutils.SetFocus()

    def ProprietesOlv(self):
        self.ctrlOlv.Bind(wx.EVT_CONTEXT_MENU, self.ctrlOlv.OnContextMenu)
        self.ctrlOlv.Bind(wx.EVT_LEFT_DCLICK, self.OnDblClick)
        self.ctrlOlv.Bind(wx.EVT_COMMAND_ENTER, self.OnBoutonOK)

    def GetItemsBtn(self,lstBtns):
        # décompactage des paramètres de type bouton
        lstBtn = []
        for btn in lstBtns:
            if isinstance(btn,wx.Button):
                bouton = btn
            else:
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
                except:
                    bouton = wx.Button(self, wx.ID_ANY, 'Erreur!')
            lstBtn.append((bouton, 0, wx.ALL | wx.ALIGN_RIGHT, 5))
        return lstBtn

    def OnDblClick(self,event):
        # a écraser par homonyme dans l'instance
        self.OnBoutonOK(None)

    def OnBoutonOK(self,event):
        if not self.ctrlOlv.GetSelectedObject():
            wx.MessageBox("Aucun choix n'a été fait\n\nIl vous faut sélectionner une ligne ou abandonner!")
            return
        self.parent.Close()

    def OnRechercheChar(self,evt):
        if evt.GetKeyCode() in (wx.WXK_UP,wx.WXK_DOWN,wx.WXK_PAGEDOWN,wx.WXK_PAGEUP):
            self.ctrlOlv.Filtrer(self.ctrlOutils.GetValue())
            self.ctrlOlv.SetFocus()
            return
        evt.Skip()

class DLG_tableau(wx.Dialog):
    # minimum fonctionnel affiche un tableau de recherche sans gestion des lignes tout est dans pnl
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        # inutile si SetSizerAndFit qui ajuste
        size = dicOlv.pop('size', (600,300))
        self.db = kwds.pop('db',xdb.DB())
        pnlTableau = dicOlv.pop('pnlTableau',PNL_tableau )
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,None, title=titre, size=size,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        self.pnl = pnlTableau(self, dicOlv,  **kwds )
        self.ctrlOlv = self.pnl.ctrlOlv
        self.CenterOnScreen()

    def GetSelection(self):
        return self.pnl.ctrlOlv.GetSelectedObject()

    def Close(self):
        if self.IsModal():
            self.EndModal(wx.OK)
        else:
            self.Close()

class DLG_gestion(wx.Dialog):
    # Lanceur de pnl_Tableau qui gére les fonctions classique de gestion des lignes
    """ En plus du dicOlv indspensable à la définition du tableau, des fonctions permettent de gérer:
            - lstBtnActions qui défini les boutons de gestion à droite du tableau
            - lstBtns qui défini les boutons d'application de bas d'écran"""
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        # inutile si SetSizerAndFit qui ajuste
        size = dicOlv.pop('size', (600,300))
        self.db = kwds.pop('db',None)
        if self.db == None:
            self.db = xdb.DB()
        self.lblList = kwds.pop('lblList', None )
        lstBtns = kwds.pop('lstBtns', None )
        self.lstBtnActions = kwds.pop('lstBtnActions', None)
        pnlTableau = dicOlv.pop('pnlTableau',PNL_tableau )


        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,None, title=titre, size=size,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        if self.lstBtnActions == None:
            kwds['lstBtnActions'] = self.GetBtnsActions()
        else: kwds['lstBtnActions'] = self.lstBtnActions
        self.pnl = pnlTableau(self, dicOlv,  **kwds )
        self.ctrlOlv = self.pnl.ctrlOlv
        self.CenterOnScreen()

        #if lstBtns == None: kwds['lstBtns'] = self.GetBtns()
        #else: kwds['lstBtns'] = lstBtns
        #PNL_tableau(self, dicOlv,  **kwds )
        #self.ctrlOlv = self.pnl.ctrlOlv


    def InitMatrice(self, ltColonnes=[]):
        # Compose la grille de saisie des paramètres selon la liste colonnes
        for (name, label, format) in ltColonnes:
            format = eval("wx.LIST_FORMAT_%s" % format.upper())
            self.ctrlOlv.AppendColumn( label, format, width=100)
        return 'fin matrice'

    # série de boutons de gestion standards
    def GetBtnsActions(self):
        lstBtnActions = [('Action1', wx.ID_COPY, 'Choix un', "Cliquez pour l'action 1"),
                      ('Action2', wx.ID_CUT, 'Choix deux', "Cliquez pour l'action 2")]
        return [xboutons.BTN_action(self,name='creer',
                           image=wx.Bitmap("xpy/Images/16x16/Ajouter.png"),
                           help="Créer une nouvelle ligne",
                           onBtn=self.OnAjouter ),
                xboutons.BTN_action(self,name='modifier',
                           image=wx.Bitmap("xpy/Images/16x16/Modifier.png"),
                           help="Modifier la ligne selectionnée",
                           onBtn=self.OnModifier ),
                xboutons.BTN_action(self,name='dupliquer',
                           image=wx.Bitmap("xpy/Images/16x16/Dupliquer.png"),
                           help="Dupliquer la ligne selectionée",
                           onBtn=self.OnDupliquer ),
                xboutons.BTN_action(self,name='supprimer',
                           image=wx.Bitmap("xpy/Images/16x16/Supprimer.png"),
                           help="Supprimer les lignes selectionées",
                           onBtn=self.OnSupprimer )]

    # bouton bas d'écran ajoutés
    def GetBtns(self):
        return [xboutons.BTN_esc(self),
                xboutons.BTN_fermer(self)]

    def SetValues(self, llItems=[], ltColonnes=[]):
        # Alimente les valeurs dans la grille
        self.ctrlOlv.DeleteAllItems()
        for items in llItems:
            self.ctrlOlv.Append(items)
        for i in range(len(ltColonnes)):
            self.ctrlOlv.SetColumnWidth(i,wx.LIST_AUTOSIZE_USEHEADER)

    def GetValues(self,ixLigne=None):
        # réciproque de Set valeur  ou choix d'une seule ligne d'items-----------------------------------------------
        """ wx!!!: un item est une ligne dans la fonction Insert, mais un seul element dans les fonctions Set et Get
            la fonction Append permet de remplir la ligne, je n'ai pas trouve une fonction inverse il faut boucler
        """
        llItems=[]
        nblig = self.ctrlOlv.GetItemCount()
        cols = self.ctrlOlv.GetColumnCount()
        dep = 0
        fin = nblig
        if ixLigne:
            dep = max(ixLigne,0)
            fin = min(ixLigne+1, nblig)
        for row in range(nblig)[dep:fin]:
            lItems = []
            for col in range(cols):
                lItems.append(self.ctrlOlv.GetItem(row,col).GetText())
            llItems.append(lItems)
        return llItems

    def OnAjouter(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnAjouter(event)

    def OnModifier(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        if self.ctrlOlv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de modification possible !" ,
                                'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        items = self.ctrlOlv.GetFirstSelected()
        # documentation dans dupliquer
        ddDonnees = self.lddDonnees[items]
        self.pnl.SetValues(ddDonnees)
        self.EnableID(enable=False)
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            ddDonnees = self.Calcul(self.dlgGest.pnl.GetValues())
            self.lddDonnees[items] = ddDonnees
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValues(self.llItems, self.ltColonnes)
        self.pnl.ctrl.Select(items)
        #self.dlgGest.Destroy()

    def OnSupprimer(self, event):
        if self.ctrlOlv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de suppression possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnSupprimer(event,self.ctrlOlv.GetFirstSelected())

    def OnDupliquer(self, event):
        if self.ctrlOlv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de duplication possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnDupliquer(event,self.ctrlOlv.GetFirstSelected())

    def GetSelection(self):
        return self.pnl.ctrlOlv.GetSelectedObject()

    def OnFermer(self):
        if self.IsModal():
            self.EndModal(wx.OK)
        else:
            self.Close()

    def OnEsc(self):
        if self.IsModal():
            self.EndModal(wx.ID_ABORT)
        else:
            self.Close()


# -- pour tests -----------------------------------------------------------------------------------------------------

def GetDonnees(db=None,**kwds):
    filtre = kwds.pop('filtre',"")
    donnees = [[1,False, 'Bonjour', -1230.05939, -1230.05939, None,'deux'],
                     [2,None, 'Bonsoir', 57.5, 208.99,datetime.date.today(),None],
                     [3,'', 'Jonbour', 0, 'remisé', datetime.date(2018, 11, 20), 'mon item'],
                     [4,29, 'Salut', 57.082, 209, wx.DateTime.FromDMY(28, 1, 2019),"Gérer l'entrée dans la cellule"],
                     [None,None, 'Salutation', 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), '2019-10-24'],
                     [None,2, 'Python', 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), '2000-12-25'],
                     [None,3, 'Java', 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), None],
                     [None,98, 'langage C', 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                     ]
    donneesFiltrees = [x for x in donnees if filtre in x[2] ]
    return donneesFiltrees

liste_Colonnes = [
    ColumnDefn("null", 'centre', 0, 'IX', valueSetter=''),
    ColumnDefn("clé", 'centre', 60, 'cle', valueSetter=True, isSpaceFilling=False,),
    ColumnDefn("mot d'ici", 'left', 200, 'mot',valueSetter=''),
    ColumnDefn("nbre", 'right', -1, 'nombre',isSpaceFilling = True, valueSetter=0.0, stringConverter=xformat.FmtDecimal),
    ColumnDefn("prix", 'left', 80, 'prix',valueSetter=0.0,isSpaceFilling = True, stringConverter=xformat.FmtMontant),
    ColumnDefn("date", 'center', 80, 'date',valueSetter=wx.DateTime.FromDMY(1,0,1900),isSpaceFilling = True,
               stringConverter=xformat.FmtDate),
    ColumnDefn("txt", 'center', 12, 'txt', valueSetter='',isSpaceFilling = True,)
]

# params d'actions: ce sont des boutons placés à droite et non en bas
lstBtnActions = [('Action1',wx.ID_COPY,'Choix un',"Cliquez pour l'action 1"),
              ('Action2',wx.ID_CUT,'Choix deux',"Cliquez pour l'action 2")]
# params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
dicOnClick = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                'Action2': 'self.parent.Close()',}
dicOlv = {'lstColonnes':liste_Colonnes,
                'getDonnees':GetDonnees,
                'recherche':True,
                'checkColonne': True,
                'msgIfEmpty':"Aucune donnée ne correspond à votre recherche",
        }

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dicBandeau = {'titre':"MON TITRE", 'texte':"mon introduction", 'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}
    dicOlv['dicBandeau'] = dicBandeau
    #exempleframe = DLG_tableau(None,dicOlv=dicOlv,lstBtnActions=lstBtnActions,lstBtns= None,dicOnClick=dicOnClick)
    exempleframe = DLG_gestion(None,dicOlv=dicOlv,lstBtnActions=lstBtnActions,lstBtns= None)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    if exempleframe.GetSelection():
        print(exempleframe.GetSelection().donnees)
    else: print(None)
    app.MainLoop()
