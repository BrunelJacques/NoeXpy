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
from xpy.outils import xbandeau,xformat,xboutons,xshelve
from xpy.outils.ObjectListView import ObjectListView, ColumnDefn, CTRL_Outils
from xpy.outils.xconst import *

# ------------------------------------------------------------------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, donnees,codesColonnes, setterValues,codesSup=[]):
        # il peut y avoir plus de données que le nombre de colonnes, elles sont non gérées par le tableau
        if not (len(donnees)-len(codesSup) == len(codesColonnes) == len(setterValues) ):
            lst = [str(codesColonnes),str(setterValues),str(donnees)]
            mess = "Problème de nombre d'occurences!\n\n"
            mess += "%d - %d donnees, %d codes, %d colonnes et %d valeurs défaut"%(len(donnees),len(codesSup),
                                                        len(codesColonnes), len(setterValues))
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

class ListView(ObjectListView):
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
        style = kwds.pop('style', wx.LC_SINGLE_SEL)| wx.LC_REPORT
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
        ObjectListView.__init__(self, *args,style=style,**kwds)
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
            tracks.append(TrackGeneral(ligneDonnees,self.lstCodesColonnes,self.lstSetterValues,
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
        else:
            kwd['db'] = xdb.DB()
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

# Saisie d'une ligne de l'olv
class DLG_saisie(xusp.DLG_vide):
    def __init__(self,parent,dicOlv,mode='creation',**kwds):
        # récup de la matrice servant à la gestion des données
        matrice = dicOlv.pop('matriceSaisie',None)
        if not matrice:
            key = ("saisie","")
            matrice = xformat.DicOlvToMatrice(key,dicOlv)
        sizeSaisie = dicOlv.pop('sizeSaisie',None)
        if not sizeSaisie:
            nblignes = 0
            for key, lst in matrice.items():
                nblignes += len(lst)
            sizeSaisie = (200,max(60 + nblignes * 50,400))
        kwds['size'] = sizeSaisie
        super().__init__(parent, **kwds)

        # construction de l'écran de saisie
        self.pnl = xusp.TopBoxPanel(self, matrice=matrice, lblTopBox=None)

        # grise le champ ID
        ctrlID = self.pnl.GetPnlCtrl('ID')
        if mode == 'creation' :
            titre = "Création d'une nouvelle ligne"
        else:
            titre = "Modification de la base de données"
        texte = "Définissez les valeurs souhaitées pour la ligne"

        # personnalisation des éléments de l'écran
        self.bandeau = xbandeau.Bandeau(self,titre=titre,texte=texte,
                                        nomImage='xpy/images/32x32/Configuration.png')
        self.btn = self.Boutons(self)

        # layout
        self.Sizer(self.pnl)

    def Boutons(self,dlg):
        btnEsc = xboutons.BTN_esc(dlg,label='',size=(35,35))
        btnOK = xboutons.BTN_fermer(dlg,label='',onBtn=dlg.OnFermer,size=(35,35))
        boxBoutons = wx.BoxSizer(wx.HORIZONTAL)
        boxBoutons.Add(btnEsc, 0,  wx.RIGHT,5)
        boxBoutons.Add(btnOK, 0,  wx.RIGHT,5)
        return boxBoutons

# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(wx.Panel):
    #panel olv avec habillage optionnel pour des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        self.parent = parent
        self.db = kwds.pop('db',None)
        self.avecRecherche = dicOlv.pop('recherche',True)
        dicBandeau = dicOlv.pop('dicBandeau',None)
        autoSizer = dicOlv.pop('autoSizer',True)
        self.lstBtns = kwds.pop('lstBtns', None)
        if self.lstBtns == None:
            self.lstBtns = dicOlv.pop('lstBtns', None)
        self.lstBtnActions = kwds.pop('lstBtnActions',None)
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
        else:
            self.ctrlOutils = False
            # Le pnlPied est un spécifique alimenté par les descendants

        # Sizer différé pour les descendants avec spécificités modifiant le panel
        if autoSizer:
            self.ProprietesOlv()
            self.Sizer()

    def Sizer(self):
        # force la présence d'un pied d'écran par défaut
        if self.lstBtns == None :
            self.lstBtns =  [
                ('BtnPrec', wx.ID_CANCEL, wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (32, 32)),
                "Abandon, Cliquez ici pour retourner à l'écran précédent"),
               ('BtnOK', wx.OK, wx.Bitmap('xpy/Images/32x32/Valider.png', wx.BITMAP_TYPE_ANY),
                "Cliquez ici pour Choisir l'item sélectionné"),
            ]
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
            sizerpied.Add(self.ctrlOutils, 1, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, 3)
        sizerpied.Add((10,10), 1, wx.EXPAND|wx.ALIGN_LEFT, 0)

        if len(self.lstBtns) > 0:
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
        self.ctrlOlv.Bind(wx.EVT_COMMAND_ENTER, self.OnFermer)

    def GetItemsBtn(self,lstBtns):
        # décompactage des paramètres de type bouton
        lstBtn = []
        for btn in lstBtns:
            if isinstance(btn,wx.Button):
                bouton = btn
            else:
                # cas de paramètres bouton sous forme de tuple
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
                        bouton.Bind(wx.EVT_BUTTON, self.OnFermer)
                except:
                    bouton = wx.Button(self, wx.ID_ANY, 'Erreur!')
            lstBtn.append((bouton, 0, wx.ALL | wx.ALIGN_RIGHT, 5))
        return lstBtn

    def OnDblClick(self,event):
        # a écraser par homonyme dans l'instance
        self.OnFermer(None)

    def OnFermer(self,event):
        if not self.ctrlOlv.GetSelectedObject():
            wx.MessageBox("Aucun choix n'a été fait\n\nIl vous faut sélectionner une ligne ou abandonner!")
            return
        self.parent.OnFermer()

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

    def OnFermer(self, end=wx.OK):
        if self.IsModal():
            self.EndModal(end)
        else:
            self.Close()

class DLG_gestion(wx.Dialog):
    # Lanceur de pnl_Tableau qui gére les fonctions classique de gestion des lignes
    """ En plus du dicOlv indspensable à la définition du tableau, des fonctions permettent de gérer:
            - lstBtnActions qui défini les boutons de gestion à droite du tableau
            - lstBtns qui défini les boutons d'application de bas d'écran"""
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        self.dicOlv = dicOlv
        # inutile si SetSizerAndFit qui ajuste
        size = dicOlv.pop('size', (700,400))
        pnlTableau = dicOlv.pop('pnlTableau',PNL_tableau )
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,None, title=titre, size=size,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        self.estAdmin = None
        self.donnees = None
        #relais local pour pouvoir intercepter le getDonnees
        self.getDonnees = dicOlv.pop('getDonnees',None)
        dicOlv['getDonnees'] = self.GetDonnees

        self.lblList = kwds.pop('lblList', None )

        dicOlv['autoSizer'] = False
        self.pnl = pnlTableau(self, dicOlv,  **kwds )
        # Boutons en pied d'écran
        if self.pnl.lstBtns == None:
            self.pnl.lstBtns = self.GetBtns(self.pnl)
        # Boutons à droite  pouvant être transmis par kwds ou par la fonction GetBtnsActions
        if self.pnl.lstBtnActions == None:
            self.pnl.lstBtnActions = self.GetBtnActions(self.pnl)

        self.pnl.ProprietesOlv()
        self.pnl.Sizer()
        self.ctrlOlv = self.pnl.ctrlOlv
        self.CenterOnScreen()

    # série de boutons de gestion standards
    def GetBtnActions(self,pnl):
        lstBtnActions =  [xboutons.BTN_action(pnl,name='creer',
                           image=wx.Bitmap("xpy/Images/16x16/Ajouter.png"),
                           help="Créer une nouvelle ligne",
                           onBtn=self.OnAjouter ),
                xboutons.BTN_action(pnl,name='modifier',
                           image=wx.Bitmap("xpy/Images/16x16/Modifier.png"),
                           help="Modifier la ligne selectionnée",
                           onBtn=self.OnModifier ),
                xboutons.BTN_action(pnl,name='supprimer',
                           image=wx.Bitmap("xpy/Images/16x16/Supprimer.png"),
                           help="Supprimer les lignes selectionées",
                           onBtn=self.OnSupprimer )]
        return lstBtnActions

    # bouton bas d'écran ajoutés
    def GetBtns(self,pnl):
        return [xboutons.BTN_esc(pnl,label='',size=(35,35)),
                xboutons.BTN_fermer(pnl,label='',size=(35,35))]

    def EnableID(self,pnl,enable=True):
        ctrlID = pnl.GetPnlCtrl('ID')
        if ctrlID:
            ctrlID.Enable(enable)

    def EstAdmin(self):
        if self.estAdmin == None:
            # récup info de l'utilisateur de la session
            cfg = xshelve.ParamUser()
            dicUser = cfg.GetDict(dictDemande=None, groupe='USER')
            self.estAdmin =  dicUser['profil'] == 'administrateur'
        if not self.estAdmin:
            mess = "Echec de la vérification des droits administateur"
            mess += "\n\n%s de profil %s n'est pas administrateur!"%(dicUser['utilisateur'],dicUser['profil'])
            wx.MessageBox(mess,"Verif droits d'accès")
        return self.estAdmin

    def GetDonnees(self,**kwds):
        # fonctionne en tandem avec GereDonnees
        if not self.donnees:
            self.donnees = [x for x in self.getDonnees(**kwds)]
        return  self.donnees

    def ValideSaisie(self,dlgSaisie):
        # Appelé lors de fermeture de saisie finalisation de l'enregistrement
        ddDonnees = dlgSaisie.pnl.GetValues()

        # vérifie la saisie du premier champ de la première box (censé être l'ID)
        donneesBox = ddDonnees[next(iter(ddDonnees.keys()))]
        firstcle = next(iter(donneesBox.keys()))
        txtId = donneesBox[firstcle]
        if len(txtId) > 0 and txtId != '0':
            return wx.OK
        else:
            dlgSaisie.pnl.SetOneValue(firstcle,txtId)
            wx.MessageBox("Le premier champ doit être non null et dans le format souhaité!","Rejet saisie",style=wx.ICON_WARNING)
            return wx.ID_ABORT

    def GereDonnees(self, mode=None, nomsCol=[], donnees=[], ixligne=0):
        # Appelé en retour de saisie, à vocation a être substitué par des accès base de données
        if mode == 'ajout':
            self.donnees = self.donnees[:ixligne] + [donnees,] + self.donnees[ixligne:]
        elif mode == 'modif':
            self.donnees[ixligne] = donnees
        elif mode == 'suppr':
            del self.donnees[ixligne]

    def OnAjouter(self, event):
        if not self.EstAdmin(): return
        # l'ajout d'une ligne nécessite d'appeler un écran avec les champs en lignes
        olv = self.ctrlOlv
        ligne = olv.GetSelectedObject()
        ixLigne = 0
        if ligne:
            ixLigne = olv.modelObjects.index(ligne)
        else: ixLigne = len(self.donnees)
        dlgSaisie = DLG_saisie(self,self.dicOlv)
        ret = dlgSaisie.ShowModal()
        if ret == wx.OK:
            #récupération des valeurs saisies puis ajout dans les données avant reinit olv
            ddDonnees = dlgSaisie.pnl.GetValues()
            nomsCol, donnees = xformat.DictToList(ddDonnees)
            self.GereDonnees('ajout',nomsCol, donnees, ixLigne)
            self.pnl.ctrlOutils.barreRecherche.SetValue('')
            olv.Filtrer('')
        olv.Select(ixLigne)


    def OnModifier(self, event):
        if not self.EstAdmin(): return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        olv = self.ctrlOlv
        if olv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de modification possible !" ,
                                'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return

        ligne = olv.GetSelectedObject()
        ixLigne = olv.modelObjects.index(ligne)

        dDonnees = xformat.TrackToDdonnees(ligne,olv)
        dlgSaisie = DLG_saisie(self,self.dicOlv)
        dlgSaisie.pnl.SetValues(dDonnees,)
        self.EnableID(dlgSaisie.pnl, enable=False)
        ret = dlgSaisie.ShowModal()
        if ret == wx.OK:
            #récupération des valeurs saisies puis ajout dans les données avant reinit olv
            ddDonnees = dlgSaisie.pnl.GetValues()
            nomsCol, donnees = xformat.DictToList(ddDonnees)
            self.GereDonnees('modif',nomsCol, donnees, ixLigne)
            olv.Filtrer()
        olv.Select(ixLigne)

    def OnSupprimer(self, event):
        if not self.EstAdmin(): return
        olv = self.ctrlOlv
        if olv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de suppression possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        ligne = olv.GetSelectedObject()
        ixLigne = olv.modelObjects.index(ligne)
        olv.modelObjects.remove(ligne)
        self.GereDonnees(mode='suppr', ixligne=ixLigne)
        olv.RepopulateList()

    def OnFermer(self, end=wx.OK):
        if self.IsModal():
            self.EndModal(end)
        else:
            self.Close()

    def OnEsc(self,end):
        if self.IsModal():
            self.EndModal(wx.ID_ABORT)
        else:
            self.Close()

    def GetSelection(self):
        # appellé depuis parent
        return self.ctrlOlv.GetSelectedObject()


# -- pour tests -----------------------------------------------------------------------------------------------------

def GetDonnees(**kwds):
    filtre = kwds.pop('filtre',"")
    donnees = [[1,False, 'Bonjour', -1230.05939, -1230.05939, None,'deux'],
                     [2,None, 'Bonsoir', 57.5, 208.99,datetime.date.today(),None],
                     [9,'', 'Jonbour', 0, 'remisé', datetime.date(2018, 11, 20), 'mon item'],
                     [14,29, 'Salut', 57.082, 209, wx.DateTime.FromDMY(28, 1, 2019),"Gérer l'entrée dans la cellule"],
                     [5,None, 'Salutation', 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), '2019-10-24'],
                     [6,2, 'Python', 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), '2000-12-25'],
                     [12,3, 'Java', 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), None],
                     [13,98, 'langage C', 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                     ]
    donneesFiltrees = [x for x in donnees if filtre in x[2] ]
    return donneesFiltrees

liste_Colonnes = [
    ColumnDefn("IDix", 'centre', 0, 'IDxx', valueSetter=0),
    ColumnDefn("clé", 'centre', 60, 'cle', valueSetter=True, isSpaceFilling=False,),
    ColumnDefn("mot d'ici", 'left', 200, 'mot',valueSetter=''),
    ColumnDefn("nbre", 'right', -1, 'nombre',isSpaceFilling = True, valueSetter=0.0, stringConverter=xformat.FmtDecimal),
    ColumnDefn("prix", 'left', 80, 'prix',valueSetter=0.0,isSpaceFilling = True, stringConverter=xformat.FmtMontant),
    ColumnDefn("date", 'center', 80, 'date',valueSetter=wx.DateTime.FromDMY(1,0,1900),isSpaceFilling = True,
               stringConverter=xformat.FmtDate),
    ColumnDefn("txt", 'center', 12, 'txt', valueSetter='',isSpaceFilling = True,)
]

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
    #exempleframe = DLG_tableau(None,dicOlv=dicOlv,lstBtns= None)
    exempleframe = DLG_gestion(None,dicOlv=dicOlv,lstBtns= None)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    print("retour: ",ret)
    if ret == wx.OK :
        print(exempleframe.GetSelection().donnees)
    else: print(None)
    app.MainLoop()
