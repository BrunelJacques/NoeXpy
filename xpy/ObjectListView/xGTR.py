#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - évolution surcouche OLV ne reçoit pas les données mais une requête avec filtre qui s'actualise
#  permet d'interroger les tables volumineuses avec l'option LIMIT
#  Le double clic lance une action sur la ligne
#  2020/06/02

import wx
import os
import xpy.xUTILS_SaisieParams  as xusp
from xpy.outils import xbandeau,xformat,xboutons,xshelve
import xpy.ObjectListView.Footer as Footer
from xpy.ObjectListView.ObjectListView import FastObjectListView
from xpy.ObjectListView.ObjectListView  import  ColumnDefn
from xpy.ObjectListView.ObjectListView import CTRL_Outils
from xpy.outils.xconst import *

OPTIONS_OLV = ('f.rowFormatter', 'rowFormatter','useAlternateBackColors', 'useAlternateBackColorsTrue',
                'sortColumnIndex','sortAscending','sortable',
                'cellEditMode','autoAddRow','typingSearchesSortColumn',
               'pos','size','style','validator','name')


def GetBtnsPied(pnl):
    return  [
            ('BtnPrec', wx.ID_CANCEL, wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (32, 32)),
                    "Abandon, Cliquez ici pour retourner"),
           ('BtnOK', wx.OK, wx.Bitmap('xpy/Images/32x32/Valider.png', wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour Choisir l'item sélectionné"),
            ]

# série de boutons de gestion standards
def GetBtnActions(self,lstNomsBtns):
    dicParamsBtns =  {
                'creer': {'name':'creer',
                       'image':wx.Bitmap("xpy/Images/16x16/Ajouter.png"),
                       'help':"Créer une nouvelle ligne",
                       'onBtn':"OnAjouter" },
                'modifier': {'name':'modifier',
                       'image':wx.Bitmap("xpy/Images/16x16/Modifier.png"),
                       'help':"Modifier la ligne selectionnée",
                       'onBtn':"OnModifier" },
                'dupliquer': {'name':'dupliquer',
                       'image':wx.Bitmap("xpy/Images/16x16/Copier.png"),
                       'help':"Dupliquer la ligne selectionnée",
                       'onBtn':"OnDupliquer" },
                'supprimer': {'name':'supprimer',
                       'image':wx.Bitmap("xpy/Images/16x16/Supprimer.png"),
                       'help':"Supprimer les lignes selectionnées",
                       'onBtn':"OnSupprimer" },}
    lstBtns = [dicParamsBtns[x] for x in lstNomsBtns]
    return lstBtns

# ------------ Gestion de l'OLV  -----------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, donnees,codesColonnes, setterValues,codesSup=list):
        # il peut y avoir plus de données que le nombre de colonnes, elles sont non gérées par le tableau
        if not (len(donnees)-len(codesSup) == len(codesColonnes) == len(setterValues) ):
            lst = [str(codesColonnes),str(setterValues),str(donnees)]
            mess = "Problème de nombre d'occurences!\n\n"
            mess += "(%d - %d) donnees, %d codes, %d colonnes"%(len(donnees),len(codesSup),
                                                        len(codesColonnes), len(setterValues))
            mess += '\n\n'+'\n\n'.join(lst)
            wx.MessageBox(mess,caption="xGestion_TableauRecherche.TrackGeneral")
            raise("echec Track général")
        self.donnees = donnees
        for ix in range(len(codesColonnes + codesSup)):
            donnee = donnees[ix]
            if ix < len(codesColonnes):
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
    sortAscending : True ou False indique le sens de tri

    exportExcel : True par défaut, False permet d'enlever l'option 'Exporter au format Excel'
    exportTexte : idem
    apercuAvantImpression : idem
    imprimer : idem
    toutCocher : idem
    toutDecocher : idem
    menuPersonnel : On peut avoir déjà créé un "pré" menu contextuel auquel viendra s'ajouter le tronc commun

    Pour cette surcouche de OLV j'ai décidé de ne pas laisser la fonction OnItemActivated car ça peut changer selon le tableau
    donc ce sera le role de la classe parent (qui appelle ListView) de définir une fonction OnItemActivated qui sera utilisée
    lors du double clic sur une ligne

    Dictionnaire optionnel ou on indique si on veut faire le bilan (exemple somme des valeurs)
    """

    def __init__(self, *args, **kwds):
        self.parent = args[0]
        self.lanceur = self.parent.lanceur
        self.filtre = ''
        self.lstDonnees = []
        self.avecFooter = False
        self.dicOlv = xformat.CopyDic(kwds)

        # récup des arguments à transmettre à l'OLV
        kwdsOLV = {}
        for arg in OPTIONS_OLV:
            valarg = kwds.get(arg,None)
            if valarg:
                kwdsOLV[arg] = valarg

        if not 'style' in kwdsOLV:
            kwdsOLV['style'] = (wx.LC_SINGLE_SEL| wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)

        # arguments propres à cette instance
        self.checkColonne = kwds.pop('checkColonne',False)
        self.lstColonnes = kwds.pop('lstColonnes', [])
        self.lstCodesSup = kwds.pop('lstCodesSup', [])
        self.msgIfEmpty = kwds.pop('msgIfEmpty', 'Tableau vide')
        self.sortColumnIndex = kwds.pop('sortColumnIndex', None)
        self.sortAscending = kwds.pop('sortAscending', True)
        self.menuPersonnel = kwds.pop('menuPersonnel', False)
        self.getDonnees = kwds.pop('getDonnees', None)
        if isinstance(self.getDonnees,str):
            self.getDonnees = eval(self.getDonnees)
        self.db  = kwds.pop('db', None)

        # Choix des options du 'tronc commun' du menu contextuel
        self.exportExcel = kwds.pop('exportExcel', True)
        self.exportTexte = kwds.pop('exportTexte', True)
        self.apercuAvantImpression = kwds.pop('apercuAvantImpression', True)
        self.orientationImpression = kwds.pop('orientationImpression', True)
        self.titreImpression = kwds.pop('titreImpression', None)
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

        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args,**kwdsOLV)
        self.InitObjectListView()
        self.Proprietes()

    def Proprietes(self):
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LEFT_DCLICK, self.parent.OnDblClick)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def OnChar(self,event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.parent.OnDblClick(event)
        else: event.Skip()

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.useExpansionColumn = True
        self.oddRowsBackColor = '#F0FBED'
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        # On définit les colonnes0
        self.SetColumns(self.lstColonnes)
        if self.checkColonne:
            self.CreateCheckStateColumn(0)
        self.lstCodesColonnes = self.GetLstCodesColonnes()
        self.lstNomsColonnes = self.GetLstNomsColonnes()
        self.lstSetterValues = self.GetLstSetterValues()
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.FONTFAMILY_DEFAULT))

        # Si la colonne à trier n'est pas précisée on trie selon la première par défaut
        if self.ColumnCount > 1:
            if self.sortColumnIndex == None:
                self.SortBy(1, self.sortAscending)
            else:
                self.SortBy(self.sortColumnIndex, self.sortAscending)

    def InitModel(self,**kwd):
        #kwd peut contenir  filtretxt et lstfiltres
        if self.db:
            kwd['db'] = self.db
        elif hasattr(self.parent,'db'):
            kwd['db'] = self.parent.db
        elif hasattr(self.lanceur,'db'):
            kwd['db'] = self.lanceur.db
        lstDonnees = self.FormerTracks(**kwd)
        self.SetObjects(lstDonnees)
        if len(self.innerList) >0:
            self.SelectObject(self.innerList[0])
        if self.avecFooter:
            self.ctrlFooter.MAJ_totaux()
            self.ctrlFooter.Refresh()

    def MAJ(self, ID=None):
        self.selectionID = ID
        self.InitModel()
        self.Refresh()
        # Rappel de la sélection d'un item
        if self.selectionID != None and len(self.innerList) > 0:
            self.SelectObject(self.innerList[ID], deselectOthers=True, ensureVisible=True)

    def GetLstCodesColonnes(self):
        codeColonnes = list()
        for colonne in self.lstColonnes:
            code = colonne.valueGetter
            codeColonnes.append(code)
        return codeColonnes

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
                tip = ''
                if fmt:
                    fmt = colonne.stringConverter.__name__
                    if fmt[3:] in ('Montant','Solde','Decimal','Entier'):
                        tip = 0.0
                    elif fmt[3:] == 'Date':
                        tip = wx.DateTime.FromDMY(1,0,1900)
            setterValues.append(tip)
        return setterValues

    def FormerTracks(self,**kwd):
        kwd['dicOlv'] = self.parent.dicOlv
        if hasattr(self,'getDonnees') and self.getDonnees :
            self.lstDonnees = self.getDonnees(**kwd)
        else: self.lstDonnees = []
        tracks = list()
        if self.lstDonnees is None:
            return tracks
        for ligneDonnees in self.lstDonnees:
            tracks.append(TrackGeneral(ligneDonnees,self.lstCodesColonnes,self.lstSetterValues,
                                        codesSup=self.lstCodesSup))
        return tracks

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

        if hasattr(self.parent,'ctrlOutils'):
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

    def Apercu(self, event):
        import xpy.ObjectListView.Printer as printer
        # L'orientation par défaut est donnée par l'attribut 'orientationImpression' de l'olv
        prt = printer.ObjectListViewPrinter(self, titre=self.GetTitreImpression(),
                                            intro=self.GetIntroImpression(),
                                            total=self.GetTotalImpression(),
                                            orientation=self.GetOrientationImpression())
        prt.Preview()

    def Imprimer(self, event):
        import xpy.ObjectListView.Printer as printer
        prt = printer.ObjectListViewPrinter(self, titre=self.GetTitreImpression(),
                                                intro=self.GetIntroImpression(),
                                                total=self.GetTotalImpression(),
                                                orientation=self.GetOrientationImpression())
        prt.Print()

    def ExportTexte(self, event):
        import xpy.outils.xexport
        xpy.outils.xexport.ExportTexte(self, titre=self.GetTitreImpression())

    def ExportExcel(self, event):
        import xpy.outils.xexport
        xpy.outils.xexport.ExportExcel(self, titre=self.GetTitreImpression())

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def OnBoutonFiltrer(self, event=None):
        self.parent.ctrlOutils.OnBoutonFiltrer(event)

    def SupprimerFiltres(self, event=None):
        self.parent.ctrlOutils.SupprimerFiltres()

    def GetTitreImpression(self):
        if hasattr(self.lanceur,'GetTitreImpression'):
            return self.lanceur.GetTitreImpression()
        elif hasattr(self, 'titreImpression') and self.titreImpression:
            return self.titreImpression
        return "Tableau récapitulatif"

    def GetIntroImpression(self):
        if hasattr(self.lanceur,'GetIntroImpression'):
            return self.lanceur.GetIntroImpression()
        elif hasattr(self, 'introImpression') and self.introImpression:
            return self.introImpression
        return ""

    def GetTotalImpression(self):
        if hasattr(self.lanceur,'GetTotalImpression'):
            return self.lanceur.GetTotalImpression()
        elif hasattr(self, 'introImpression') and self.introImpression:
            return self.introImpression
        return ""

# Saisie ou gestion d'une ligne de l'olv dans un nouvel écran
class DLG_saisie(xusp.DLG_vide):
    def __init__(self,parent,dicOlv,**kwds):
        # récup de la matrice servant à la gestion des données, si non fournie elle est composée automatiquemetn
        matrice = dicOlv.get('matriceSaisie',None)
        mode = dicOlv.get('mode','ajout')
        if not matrice:
            key = ("saisie","")
            matrice = xformat.DicOlvToMatrice(key,dicOlv)
        sizeSaisie = dicOlv.get('sizeSaisie',None)

        # Size de l'écran de saisie
        if not sizeSaisie:
            nblignes = 0
            for key, lst in matrice.items():
                nblignes += len(lst)
            sizeSaisie = (200,max(80 + nblignes * 50,400))
        kwds['size'] = sizeSaisie
        kwds['kwValideSaisie'] = dicOlv
        super().__init__(parent, **kwds)

        # construction de l'écran de saisie
        self.pnl = xusp.TopBoxPanel(self, matrice=matrice, lblTopBox=None)

        # grise le champ ID
        if mode in 'ajout' :
            titre = "Création d'une nouvelle ligne"
        else:
            titre = "Modification de la base de données"
            ctrl = self.pnl.GetPnlCtrl('ID')
            if ctrl:
                self.pnl.GetPnlCtrl('ID').Enable(False)
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

# ----------- Composition de l'écran -------------------------------------------------------

class PNL_params(xusp.TopBoxPanel):
    def __init__(self, parent, *args, **kwds):
        kwdsTopBox = {}
        for key in xusp.OPTIONS_TOPBOX:
            if key in kwds.keys(): kwdsTopBox[key] = kwds[key]
        super().__init__(parent, *args, **kwdsTopBox)
        self.parent = parent
        self.lanceur = parent.lanceur

class PNL_corps(wx.Panel):
    #panel olv avec habillage optionnel pour recherche (en bas), boutons actions (à droite)
    def __init__(self, parent, dicOlv,*args, **kwds):
        # size est inutile si SizerAndFit ajuste derrière le constructeur
        minSize =       dicOlv.pop('minSize',(400,150))
        lstNomsBtns =  dicOlv.pop('lstNomsBtns',None)
        getBtnActions =    dicOlv.pop('getBtnActions',None)
        self.db = kwds.pop('db',None) #d'éventuels arguments db seront envoyés à olv pour les get données
        self.dictColFooter = dicOlv.pop('dictColFooter',None)
        self.avecFooter = isinstance(self.dictColFooter,dict)
        self.avecRecherche= dicOlv.pop('recherche',True)
        self.parent = parent
        self.lanceur = parent
        self.estAdmin = None
        self.dicOlv = xformat.CopyDic(dicOlv)

        # init du super()
        wx.Panel.__init__(self, parent, *args)

        # récupére les éventuels boutons d'actions
        if getBtnActions:
            self.lstBtnActions = getBtnActions(self)
        elif lstNomsBtns:
            self.lstBtnActions = GetBtnActions(self,lstNomsBtns)
        else: self.lstBtnActions = None

        #ci dessous l'ensemble des autres paramètres possibles pour OLV pour les transmettre exclusivement
        lstKwdsOlv = ['id',
                        'style',
                        'lstColonnes',
                        'lstCodesSup',
                        'lstChamps',
                        'getDonnees',
                        'cellEditMode',
                        'useAlternateBackColors',
                        'menuPersonnel',
                        'msgIfEmpty',
                        'sortAscending',
                        'exportExcel',
                        'exportTexte',
                        'checkColonne',
                        'apercuAvantImpression',
                        'orientationImpression',
                        'titreImpression',
                        'imprimer',
                        'saisie',
                        'toutCocher',
                        'toutDecocher',
                        'inverserSelection',
                        'editMode',
                        'autoAddRow',
                        'sortable',
                        'sortColumnIndex',
                        'sortAscending',
                        ]

        #récup des seules clés possibles pour dicOLV
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstKwdsOlv:
                 dicOlvOut[key] = valeur

        # création de l'olv
        self.ctrlOlv = ListView(self,**dicOlvOut)
        self.olv = self.ctrlOlv

        # éventuel footer
        if self.avecFooter: self.SetFooter()
        
        # choix  barre de recherche ou pas
        if self.avecRecherche:
            afficherCocher = False
            if self.ctrlOlv.checkStateColumn: afficherCocher = True
            self.ctrlOutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=afficherCocher)
            self.olv.ctrlOutils = self.ctrlOutils
        self.ctrlOlv.SetMinSize(minSize)
        self.ctrlOlv.db = self.db
        self.Sizer()

    def SetFooter(self,reinit=False):
        if reinit:
            del self.ctrlFooter
        self.ctrlFooter = Footer.Footer(self)
        self.ctrlFooter.listview = self.ctrlOlv
        self.ctrlFooter.dictColFooter = self.dictColFooter
        self.ctrlOlv.avecFooter = True
        self.ctrlOlv.ctrlFooter = self.ctrlFooter

    def Sizer(self):
        #composition de l'écran selon les composants
        sizerbase = wx.BoxSizer(wx.HORIZONTAL)
        sizercorps = wx.BoxSizer(wx.VERTICAL)
        sizercorps.Add(self.olv, 10, wx.TOP|wx.LEFT|wx.EXPAND, 3)
        if self.avecFooter:
            sizercorps.Add(self.ctrlFooter, 0,wx.ALL|wx.EXPAND, 5)
        if self.avecRecherche:
            sizercorps.Add(self.ctrlOutils, 0,wx.ALL|wx.EXPAND, 5)
        sizerbase.Add(sizercorps, 10, wx.EXPAND, 10)
        # ajout des boutons d'actions
        if self.lstBtnActions:
            self.lstBtnCtrl = xboutons.GetAddManyBtns(self,self.lstBtnActions)
            sizeractions = wx.BoxSizer(wx.VERTICAL)
            sizeractions.AddMany(self.lstBtnCtrl)
            sizerbase.Add(sizeractions, 0, wx.TOP, 10)
        self.SetSizer(sizerbase)

    def EstAdmin(self):
        dicUser = {'utilisateur':'User inconnu!','profil':'inconnu'}
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

    def OnDblClick(self,event):
        self.Parent.OnDblClick(event)

    def OnAjouter(self, event):
        if hasattr(self.parent,'OnModifier'):
            self.parent.OnDupliquer(event)
        else:
            if not self.EstAdmin(): return
            # l'ajout d'une ligne nécessite d'appeler un écran avec les champs en lignes
            olv = self.ctrlOlv
            ligne = olv.GetSelectedObject()
            ixLigne = 0
            if ligne:
                ixLigne = olv.modelObjects.index(ligne)
            else: ixLigne = len(olv.lstDonnees)
            self.dicOlv['mode'] = 'ajout'
            dlgSaisie = DLG_saisie(self.lanceur,self.dicOlv, kwValideSaisie=self.dicOlv)
            ret = dlgSaisie.ShowModal()
            if ret == wx.OK:
                #récupération des valeurs saisies puis ajout dans les données avant reinit olv
                ddDonnees = dlgSaisie.pnl.GetValues()
                nomsCol, donnees = xformat.DictToList(ddDonnees)
                self.parent.GereDonnees(mode='ajout',nomsCol=nomsCol, donnees=donnees, ixLigne=ixLigne,dicOlv=self.dicOlv)
                self.ctrlOutils.barreRecherche.SetValue('')
                olv.Filtrer('')
            olv.Select(ixLigne)

    def OnModifier(self, event):
        if hasattr(self.parent,'OnModifier'):
            self.parent.OnDupliquer(event)
        else:
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
            self.dicOlv['mode'] = 'modif'
            dlgSaisie = DLG_saisie(self.lanceur,self.dicOlv,kwValideSaisie=self.dicOlv)
            dlgSaisie.pnl.SetValues(dDonnees,)
            ret = dlgSaisie.ShowModal()
            if ret == wx.OK:
                #récupération des valeurs saisies puis ajout dans les données avant reinit olv
                ddDonnees = dlgSaisie.pnl.GetValues()
                nomsCol, donnees = xformat.DictToList(ddDonnees)
                self.parent.GereDonnees(mode='modif',nomsCol=nomsCol, donnees=donnees, ixLigne=ixLigne,dicOlv=self.dicOlv)
                olv.Filtrer()
            olv.Select(ixLigne)

    def OnDupliquer(self, event):
        if hasattr(self.parent,'OnDupliquer'):
            self.parent.OnDupliquer(event)
        else:
            # non testé
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
            self.dicOlv['mode'] = 'modif'
            dlgSaisie = DLG_saisie(self.lanceur,self.dicOlv,kwValideSaisie=self.dicOlv)
            dlgSaisie.pnl.SetValues(dDonnees,)
            ret = dlgSaisie.ShowModal()
            if ret == wx.OK:
                #récupération des valeurs saisies puis ajout dans les données avant reinit olv
                ddDonnees = dlgSaisie.pnl.GetValues()
                nomsCol, donnees = xformat.DictToList(ddDonnees)
                self.parent.GereDonnees(mode='modif',nomsCol=nomsCol, donnees=donnees, ixLigne=ixLigne,dicOlv=self.dicOlv)
                olv.Filtrer()
            olv.Select(ixLigne)

    def OnSupprimer(self, event):
        if hasattr(self.parent,'OnSupprimer'):
            self.parent.OnDupliquer(event)
        else:
            if not self.EstAdmin(): return
            olv = self.ctrlOlv
            if olv.GetSelectedItemCount() == 0:
                wx.MessageBox("Pas de sélection faite, pas de suppression possible !",
                          'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
                return
            ligne = olv.GetSelectedObject()
            ixLigne = olv.modelObjects.index(ligne)
            olv.modelObjects.remove(ligne)
            self.dicOlv['mode'] = 'suppr'
            self.parent.GereDonnees(mode='suppr', ixLigne=ixLigne,dicOlv=self.dicOlv)
            olv.RepopulateList()

class PNL_pied(wx.Panel):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied,*args, **kwds):
        self.lanceur = parent
        self.lstInfos = dicPied.pop('lstInfos',None)
        self.lstBtns =  dicPied.pop('lstBtns',None)
        autoSizer =     dicPied.pop('autoSizer', True)
        if self.lstBtns == None:
            #force la présence d'un pied d'écran par défaut
            self.lstBtns = GetBtnsPied(self)
        wx.Panel.__init__(self, parent,*args)
        self.parent = parent
        if autoSizer:
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
            sizerbtns = wx.BoxSizer(wx.HORIZONTAL)
            sizerbtns.AddMany(xboutons.GetAddManyBtns(self,self.itemsBtns))
            sizerpied.Add(sizerbtns, 0, 0, 0)
        sizerpied.AddGrowableCol(nbinfos)
        self.SetSizer(sizerpied)
        self.Layout()

    def CreateItemsInfos(self,lstInfos):
        # images ou texte sont retenus
        self.infosImage = None
        self.infosTexte = None
        lstItems = []
        if not lstInfos: lstInfos = []
        for item in lstInfos:
            if isinstance(item,wx.Bitmap):
                self.infosImage = wx.StaticBitmap(self, wx.ID_ANY, item)
                lstItems.append((self.infosImage,0,wx.ALIGN_LEFT|wx.TOP,10))
            elif isinstance(item,str):
                self.infosTexte = wx.StaticText(self,wx.ID_ANY,item)
                lstItems.append((self.infosTexte,10,wx.ALIGN_LEFT|wx.ALL|wx.EXPAND,5))
        return lstItems

    def SetItemsInfos(self,text=None,image=None,):
        # après create  permet de modifier l'info du pied pour dernière image et dernier texte
        if image:
            self.infosImage.SetBitmap(image)
        if text:
            self.infosTexte.SetLabelText(text)

# ------------- Ecran Dialog, Lancement des composantes -------------------------------------
class DLG_tableau(xusp.DLG_vide):
    # minimum fonctionnel du dialog l'essentiel est dans les trois pnl
    def __init__(self,parent,dicParams={},dicOlv={},dicPied={}, **kwds):
        if not 'title' in kwds.keys():
            listArbo=os.path.abspath(__file__).split("\\")
            kwds['title'] = listArbo[-1] + "/" + self.__class__.__name__
        self.db =       kwds.pop('db',None) #purge d'éventuels arguments db à ne pas envoyer à super()
        autoSizer =     kwds.pop('autoSizer', True)
        size =          kwds.get('size',None)
        if not 'style' in kwds.keys():
            kwds['style'] = wx.DEFAULT_FRAME_STYLE

        # si size pas dans kwds, on pique celle de l'olv qui serait contrainte
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
        if dicOlv != {}:
            self.dicOlv = xformat.CopyDic(dicOlv)
            self.pnlOlv = PNL_corps(self, dicOlv,  **kwds )
            self.ctrlOlv = self.pnlOlv.ctrlOlv
        else:
            autoSizer = False
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

    def GereDonnees(self, mode=None, nomsCol=[], donnees=[], ixLigne=0):
        lstDonnees = self.ctrlOlv.lstDonnees
        # Appelé en retour de saisie, à vocation a être complété ou substitué par des accès base de données
        if mode == 'ajout':
            self.ctrlOlv.lstDonnees = lstDonnees[:ixLigne] + [donnees,] + lstDonnees[ixLigne:]
        elif mode == 'modif':
            if ixLigne < len(lstDonnees):
                lstDonnees[ixLigne] = donnees
            else: lstDonnees.append(donnees)
        elif mode == 'suppr':
            del lstDonnees[ixLigne]
        self.ctrlOlv.MAJ(ixLigne)

    def OnDblClick(self,event):
        if 'lstNomsBtns' in self.dicOlv.keys():
            self.pnlOlv.OnModifier(event)
        else:
            end = wx.OK
            if not len(self.pnlOlv.olv.GetSelectedObjects()):
                end = wx.ID_CANCEL
            self.OnFermer(end=end)

    def OnFermer(self, *arg, **kwd):
        end = kwd.pop('end',wx.OK)
        if self.IsModal():
            self.EndModal(end)
        else:
            self.Close()

    def OnEsc(self,*arg, **kwd):
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

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    os.chdir("..")
    """
    dicBandeau = {'titre':"MON TITRE", 'texte':"mon introduction", 'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}
    dicOlv['dicBandeau'] = dicBandeau
    #exempleframe = DLG_tableau(None,dicOlv=dicOlv,lstBtns= None)
    exempleframe = DLG_xxtableau(None,dicOlv=dicOlv,lstBtns= None)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    print("retour: ",ret)
    if ret == wx.OK :
        print(exempleframe.GetSelection().donnees)
    else: print(None)
    app.MainLoop()

    """
    liste_Colonnes = [
        ColumnDefn("null", 'centre', 0, 'IX', valueSetter=''),
        ColumnDefn("clé", 'centre', 60, 'cle', valueSetter=True,
                   isSpaceFilling=False ),
        ColumnDefn("mot d'ici", 'left', 200, 'mot', valueSetter='A saisir', isEditable=True),
        ColumnDefn("nbre", 'right', -1, 'nombre', isSpaceFilling=True, valueSetter=0.0,
                   stringConverter=xformat.FmtDecimal),
        ColumnDefn("prix", 'left', 80, 'prix', valueSetter=0.0, isSpaceFilling=True,),
        ColumnDefn("date", 'center', 80, 'date', valueSetter=wx.DateTime.FromDMY(1, 0, 1900), isSpaceFilling=True,
                   stringConverter=xformat.FmtDate),
        ColumnDefn("choice", 'center', 40, 'choice', valueSetter='mon item',choices=['CHQ','VRT','ESP'], isSpaceFilling=True,
                   )
    ]
    dicOlv = {'lstColonnes': liste_Colonnes,
              'getDonnees': GetDonnees,
              'recherche': True,
              'checkColonne': True,
              'lstNomsBtns': ['creer','modifier'],
              'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
              'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
              }

    # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche

    lstInfos = [wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, ),
                wx.Bitmap('xpy/Images/16x16/Magique.png', wx.BITMAP_TYPE_PNG),
                "Autre\nInfo"]

    # l'info se compmose d'une imgae et d'un texte
    dicPied = {'lstInfos': lstInfos}

    # cadre des paramètres
    import datetime
    bandeau = {'titre': "Mon Titre",'texte': "mes explications dans leur longueur"}
    dicParams = {"matrice": {
                      ('ident',"Vos paramètres"):[
                                    {'name': 'date', 'genre': 'Date', 'label': 'Début de période', 'value': datetime.date.today(),
                                                            'help': 'Ce préfixe à votre nom permet de vous identifier'},
                                    {'name': 'utilisateur', 'genre': 'String', 'label': 'Votre identifiant', 'value': "NomSession",
                                                            'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
                                    ],
                            },
                "bandeau":bandeau
                }

    exempleframe = DLG_tableau(None,dicParams=dicParams,dicOlv=dicOlv,dicPied=dicPied)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    print(ret)
    app.MainLoop()

