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
import xpy.xUTILS_DB   as xdb
import xpy.outils.xformat as xfmt
from xpy.outils import xbandeau
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, CTRL_Outils
from xpy.outils.xconst import *

# ------------------------------------------------------------------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, donnees,codesColonnes, nomsColonnes, setterValues):
        self.donnees = donnees
        if not(len(donnees) == len(codesColonnes)== len(nomsColonnes) == len(setterValues)):
            wx.MessageBox("Problème de nombre d'occurences!\n%d donnees, %d codes, %d colonnes et %d valeurs défaut"
                          %(len(donnees), len(codesColonnes), len(nomsColonnes), len(setterValues)))
        for ix in range(min(len(donnees),len(setterValues))):
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
    listeDonnees : est alimenté par la fonction getDonnees

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
        self.filtre = ""
        self.dicOlv = kwds.copy()
        style = kwds.pop("style", wx.LC_SINGLE_SEL)
        self.listeColonnes = kwds.pop("listeColonnes", [])
        self.msgIfEmpty = kwds.pop("msgIfEmpty", "Tableau vide")
        self.colonneTri = kwds.pop("colonneTri", None)
        self.sensTri = kwds.pop("sensTri", True)
        self.menuPersonnel = kwds.pop("menuPersonnel", None)
        self.getDonnees = kwds.pop("getDonnees", None)
        self.lstCodesColonnes = self.formerCodeColonnes()
        self.lstNomsColonnes = self.formerNomsColonnes()
        self.lstSetterValues = self.formerSetterValues()

        # Choix des options du 'tronc commun' du menu contextuel
        self.exportExcel = kwds.pop("exportExcel", True)
        self.exportTexte = kwds.pop("exportTexte", True)
        self.apercuAvantImpression = kwds.pop("apercuAvantImpression", True)
        self.imprimer = kwds.pop("imprimer", True)

        # Choix du mode d'impression
        self.titreImpression = kwds.pop("titreImpression", "Tableau récapitulatif")
        self.orientationImpression = kwds.pop("orientationImpression", True)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1

        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args,style=style,**kwds)
        self.InitObjectListView()
        self.MAJ()

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

    def formerTracks(self,**kwd):
        kwd['dicOlv'] = self.dicOlv
        self.listeDonnees = self.getDonnees(**kwd)

        tracks = list()
        if self.listeDonnees is None:
            return tracks
        for ligneDonnees in self.listeDonnees:
            tracks.append(TrackGeneral(donnees=ligneDonnees,codesColonnes=self.lstCodesColonnes,
                                            nomsColonnes=self.lstNomsColonnes,setterValues=self.lstSetterValues))
        return tracks

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        # On définit les colonnes0
        self.SetColumns(self.listeColonnes)
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT))
        # Si la colonne à trier n'est pas précisée on trie selon la première par défaut
        if self.ColumnCount > 1:
            if self.colonneTri == None:
                self.SortBy(1, self.sensTri)
            else:
                self.SortBy(self.colonneTri, self.sensTri)

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

# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(wx.Panel):
    #panel olv avec habillage optionnel pour des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        self.parent = parent
        dicBandeau = dicOlv.pop('dicBandeau',None)
        autoSizer = dicOlv.pop('autoSizer',True)
        self.lstBtns = kwds.pop('lstBtns',None)
        if self.lstBtns == None:
            self.lstBtns = dicOlv.pop('lstBtns', None)
        self.lstActions = kwds.pop('lstActions',None)
        self.dicOnClick = kwds.pop('dicOnClick',None)
        if self.lstBtns == None :
            #force la présence d'un pied d'écran par défaut
            self.lstBtns =  [
                ('BtnPrec', wx.ID_CANCEL, wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (32, 32)),
                "Abandon, Cliquez ici pour retourner à l'écran précédent"),
               ('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/32x32/Valider.png", wx.BITMAP_TYPE_ANY),
                "Cliquez ici pour Choisir l'item sélectionné"),
            ]

        wx.Panel.__init__(self, parent, *args,  **kwds)
        #ci dessous l'ensemble des autres paramètres possibles pour OLV
        if dicBandeau:
            self.bandeau = xbandeau.Bandeau(self,**dicBandeau)
        else:self.bandeau = None

        if 'recherche' in dicOlv:
            self.avecRecherche = dicOlv['recherche']
        else : self.avecRecherche = True

        #récup des seules clés possibles pour dicOLV
        lstParamsOlv = ['id',
                        'style',
                        'listeColonnes',
                        'listeChamps',
                        'colonneTri',
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
                        ]
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur

        self.ctrlOlv = ListView(self,**dicOlvOut)
        if self.avecRecherche:
            afficherCocher = False
            if self.ctrlOlv.checkStateColumn: afficherCocher = True
            self.ctrloutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=afficherCocher)
            self.ctrloutils.Bind(wx.EVT_CHAR,self.OnRechercheChar)
            self.pnlPied = (10,10)
        else:
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
        if self.lstActions:
            sizeractions = wx.StaticBoxSizer(wx.VERTICAL, self, label='Gestion')
            self.itemsActions = self.GetItemsBtn(self.lstActions)
            sizeractions.AddMany(self.itemsActions)
            sizercentre.Add(sizeractions,0,wx.ALL|wx.EXPAND,3)
        sizerbase.Add(sizercentre, 10, wx.EXPAND, 0)

        sizerbase.Add(wx.StaticLine(self), 0, wx.TOP| wx.EXPAND, 3)

        sizerpied = wx.FlexGridSizer(rows=1, cols=10, vgap=0, hgap=0)
        if self.avecRecherche:
            sizerpied.Add(self.ctrloutils, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, 3)

        sizerpied.Add(self.pnlPied, 0, wx.EXPAND|wx.ALIGN_LEFT, 0)

        if self.lstBtns:
            self.itemsBtns = self.GetItemsBtn(self.lstBtns)
            sizerpied.AddMany(self.itemsBtns)
        sizerpied.AddGrowableCol(0)
        sizerbase.Add(sizerpied,0,wx.EXPAND,5)
        self.SetSizerAndFit(sizerbase)
        if self.avecRecherche:
            self.ctrloutils.SetFocus()

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
            self.ctrlOlv.Filtrer(self.ctrloutils.GetValue())
            self.ctrlOlv.SetFocus()
            return
        evt.Skip()

class DLG_tableau(wx.Dialog):
    # minimum fonctionnel dans dialog tout est dans pnl
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        # inutile si SetSizerAndFit qui ajuste
        size = dicOlv.pop("size", (600,300))
        self.db = kwds.pop("db",xdb.DB())
        pnlTableau = dicOlv.pop("pnlTableau",PNL_tableau )
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

# -- pour tests -----------------------------------------------------------------------------------------------------

def GetDonnees(db=None,**kwds):
    filtre = kwds.pop('filtre',"")
    donnees = [[18, "Bonjour", -1230.05939, -1230.05939, None, None],
                     [19, "Bonsoir", 57.5, 208.99, wx.DateTime.FromDMY(2, 11, 2020), datetime.date.today()],
                     [1, "Jonbour", 0, 209, wx.DateTime.FromDMY(6, 11, 2018), datetime.date(2018,12,6)],
                     [29, "Salut", 57.082, 209, wx.DateTime.FromDMY(28, 1, 2020), datetime.date(2020,2,28)],
                     [None, "Salutation", 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), datetime.date(1997,8,1)],
                     [2, "Python", 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), datetime.date(1997,2,7)],
                     [3, "Java", 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), '2019-08-25'],
                     [98, "langage C", 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                     ]
    donneesFiltrees = [x for x in donnees if filtre.upper() in x[1].upper() ]
    return donneesFiltrees

liste_Colonnes = [
    ColumnDefn("clé", 'left', 10, "cle",valueSetter=1,isSpaceFilling = True,),
    ColumnDefn("mot d'ici", 'left', 200, "mot",valueSetter=''),
    ColumnDefn("nbre", 'right', -1, "nombre",isSpaceFilling = True, valueSetter=0.0, stringConverter=xfmt.FmtDecimal),
    ColumnDefn("prix", 'left', 80, "prix",valueSetter=0.0,isSpaceFilling = True, stringConverter=xfmt.FmtMontant),
    ColumnDefn("date", 'center', 80, "date",valueSetter=wx.DateTime.FromDMY(1,0,1900),isSpaceFilling = True,
               stringConverter=xfmt.FmtDate),
    ColumnDefn("date SQL", 'center', 80, "datesql", valueSetter=datetime.date.today(),isSpaceFilling = True,
               stringConverter=xfmt.FmtDate)
]

# params d'actions: ce sont des boutons placés à droite et non en bas
lstActions = [('Action1',wx.ID_COPY,'Choix un',"Cliquez pour l'action 1"),
              ('Action2',wx.ID_CUT,'Choix deux',"Cliquez pour l'action 2")]
# params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
dicOnClick = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                'Action2': 'self.parent.Close()',}
dicOlv = {'listeColonnes':liste_Colonnes,
                'getDonnees':GetDonnees,
                'recherche':True,
                'msgIfEmpty':"Aucune donnée ne correspond à votre recherche",
                'dictColFooter':{"nombre" : {"mode" : "total",  "alignement" : wx.ALIGN_RIGHT},
                                 "mot" : {"mode" : "nombre",  "alignement" : wx.ALIGN_CENTER},
                                 "prix": {"mode": "total", "alignement": wx.ALIGN_RIGHT},}
        }

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dicBandeau = {'titre':"MON TITRE", 'texte':"mon introduction", 'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}
    dicOlv['dicBandeau'] = dicBandeau
    exempleframe = DLG_tableau(None,dicOlv=dicOlv,lstActions=lstActions,lstBtns= None,dicOnClick=dicOnClick)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    if exempleframe.GetSelection():
        print(exempleframe.GetSelection().donnees)
    else: print(None)
    app.MainLoop()
