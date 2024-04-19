#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Permet un choix dans une liste et retourne l'indice
#------------------------------------------------------------------------

import wx, copy
import decimal
from xpy.ObjectListView.ObjectListView import FastObjectListView, ColumnDefn, CTRL_Outils
#import xpy.ObjectListView.Filter as Filter
import xpy.outils.xbandeau      as xbd
from xpy.outils import xformat

class Track(object):
    def __init__(self, donnees,champs):
        self.donnees = donnees
        for ix in range(len(champs)):
            champ= champs[ix]
            if champ != '0':
                commande = "self.%s = donnees[ix]"%(champ)
                exec(commande)

class CTRL_Solde(wx.Panel):
    def __init__(self, parent, toolTip=None, size=(100, 30)):
        wx.Panel.__init__(self, parent, id=-1, name='ctrl_solde',
                          style=wx.BORDER_SUNKEN,
                          size=size)
        # Solde du compte
        self.ctrl_solde = wx.TextCtrl(self, -1,style=wx.TE_READONLY|wx.TE_RIGHT)
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)
        self.bgCouleurs = [wx.Colour(220, 237, 200), # vert positif
                           wx.Colour(255, 205, 210), # Rouge négatif
                           "#e0e0e0",                # gris null
                           ]
        self.SetBackgroundColour(self.bgCouleurs[2])  # gris
        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_solde, 0,
                            wx.ALIGN_RIGHT|wx.EXPAND, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        if toolTip:
            self.ctrl_solde.SetToolTip(toolTip)
    def SetDefaultStyle(self,couleur):
        self.ctrl_solde.SetDefaultStyle(couleur)

    def SetValue(self, montant):
        """ MAJ intégrale du controle avec MAJ des donnees """
        if not montant or montant == '':
            label = ''
        elif montant > 0.0:
            label = "+ %.2f " % montant
            self.ctrl_solde.SetBackgroundColour(self.bgCouleurs[0])
        elif montant == 0.0:
            label = "0.00 "
            self.ctrl_solde.SetBackgroundColour(self.bgCouleurs[2])  # gris
        else:
            label = "- %.2f " % (-montant,)
            self.ctrl_solde.SetBackgroundColour(self.bgCouleurs[1])  # Rouge
        self.ctrl_solde.SetValue(label)
        self.Layout()
        self.Refresh()

    def GetValue(self):
        value = xformat.NoLettre(self.ctrl_solde.GetValue())
        if value == "": value = 0.0
        return decimal.Decimal(value)

class DialogLettrage(wx.Dialog):
    # Non encore utilisé en python3 cf xGestion_TableauVentilation déjà implémenté
    #Gestion d'un lettrage à partir de deux dictionnaires, mots clés des champs : montant en dernière position
    # La première colonne sera l'ID suivi du sens (origine fichier) et lettre. La suite sera les champs
    def __init__(self, parent,dicList1={},lstChamps1=[],dicList2={},lstChamps2=[],lstLettres=[],columnSort=3,
                 LargeurCode=80,LargeurLib=100,minSize=(350, 350),titre=u"Lettrage des montants",
                 intro=u"Cochez les lignes associées puis cliquez sur lettrage...", altOK = False):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.SetTitle("xchoixListe.DialogLettrage")
        self.parent = parent
        self.lstLettresOriginal = copy.deepcopy(lstLettres)
        self.lstLettres = lstLettres
        self.dicList1 = dicList1
        self.dicList2 = dicList2
        self.lstChamps1 = lstChamps1
        self.lstChamps2 = lstChamps2
        self.columnSort = columnSort
        self.altOK = altOK
        self.choix = None
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.nbValeurs = len(lstChamps2)
        if len(lstChamps1) > len(lstChamps2): self.nbValeurs = len(lstChamps1)
        self.nbColonnes = self.nbValeurs + 4
        self.lstLibels = [u"DC",u"ID",u"Let",]+([u"",]*(self.nbValeurs-1))+[u"Débits",u"Crédits",]

        #composition des libelles colonnes et des codes
        i=3
        for item in lstChamps1:
            if item.lower() == u"montant": continue
            self.lstLibels[i] = item
            i +=1
        i=3
        for item in lstChamps2:
            if item.lower() == u"montant": continue
            if self.lstLibels[i] != item:
                self.lstLibels[i] += u"/%s"%item
            i +=1
        # le code est le dernier mot du libellé de la colonne, sans accent et en minuscule
        self.lstCodes = [xformat.NoAccents(x.split(u"/")[-1].strip()).lower() for x in self.lstLibels]
        # vérif unicité code
        lstano = [x for x in self.lstCodes if self.lstCodes.count(x)>1]
        if len(lstano)>0:
            wx.MessageBox(u"Les noms des champs doivent être uniques dans un même liste liste!\n voir le doublon: '%s'"%lstano[0], u"Impossible")
            return
        # constitution de la liste de données et calcul au passage de la largeur nécessaire pour les colonnes
        self.lstDonnees = []
        self.lstWidth = [30]*self.nbColonnes # préalimentation d'une largeur par défaut
        self.lstWidth[1]=60 # lardeur de la colonne ID
        multiwidth = 6 # multiplicateur du nombre de caratère maxi dans la colonne pour déterminer la largeur
        for libel in self.lstLibels:
            if self.lstWidth[self.lstLibels.index(libel)] < multiwidth*len(libel)+10:
                self.lstWidth[self.lstLibels.index(libel)] = multiwidth*len(libel)+10
        for sens in (+1,-1):
            # les montants seront alignés dans les deux colonnes le plus à droite
            if sens == +1:
                ixMtt = self.nbColonnes-2
                dic = dicList1
                champs = lstChamps1
            else:
                ixMtt = self.nbColonnes-1
                dic = dicList2
                champs = lstChamps2
            if not "montant" in str(champs).lower():
                wx.MessageBox(u"Les listes de données n'ont pas chacune un champ 'montant'!",u"Impossible")
                return
            nbval = len(champs)
            # balayage des deux dictionnaires de données et de leur liste de champs
            for key,item in dic.items():
                donnee=[sens,key,""] + ([""]*(self.nbValeurs-1)) + [0.0,0.0]
                ixVal = 3
                valMtt = None
                for i in range(nbval):
                    if u"montant" in champs[i].lower():
                        valMtt = item[i]
                        continue
                    donnee[ixVal] = item[i]
                    if isinstance(item[i],(str)):
                        lg = len(item[i])
                    else: lg = len(str(item[i]))
                    if self.lstWidth[ixVal] < lg*multiwidth + 10: self.lstWidth[ixVal] = lg*multiwidth + 10
                    ixVal += 1
                # ajout du montant à droite
                donnee[ixMtt] = valMtt
                self.lstDonnees.append(donnee)

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro, hauteur=15,
                                                 nomImage="xpy/Images/32x32/matth.png")
        # conteneur des données
        self.listview = FastObjectListView(self, id=-1, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.listview.SetMinSize((10, 10))
        self.barre_recherche = CTRL_Outils(self, listview=self.listview, afficherCocher=True)

        # Boutons
        self.bouton_lettrer = wx.Button(self, id = wx.ID_APPLY,label="Lettrer")
        self.bouton_lettrer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Action.png"))
        self.bouton_delettrer = wx.Button(self, label=u"DeLettrer", )
        self.bouton_delettrer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Depannage.png"))
        self.bouton_fermer = wx.Button(self, label=u"Annuler",)
        self.bouton_fermer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Annuler.png"))
        self.bouton_ok = wx.Button(self, label=u"Valider", )
        self.bouton_ok.SetBitmap(wx.Bitmap("xpy/Images/32x32/Valider.png"))
        self.__set_properties()
        self.MAJ()
        self.__do_layout()

    def __set_properties(self):
        # TipString, Bind et constitution des colonnes de l'OLV
        self.SetMinSize(self.minSize)
        self.bouton_lettrer.SetToolTip(u"Cliquez ici après avoir coché des lignes à associer")
        self.bouton_delettrer.SetToolTip(u"Cliquez ici après avoir sélectionné une ligne de la lettre à supprimer")
        self.bouton_ok.SetToolTip(u"Cliquez ici pour valider et enregistrer les modifications")
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour abandonner les modifications")
        self.listview.SetToolTip(u"Double Cliquez pour cocher")
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.Bind(wx.EVT_BUTTON, self.OnClicLettrer, self.bouton_lettrer)
        self.Bind(wx.EVT_BUTTON, self.OnClicDelettrer, self.bouton_delettrer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDblClic)

        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        # Construction des colonnes de l'OLV
        lstColumns = [ ColumnDefn("coche", "left", 0, 0),]
        for ix in range(self.nbColonnes-2):
            if ix in (1,2):
                justif = 'right'
            else: justif = 'left'
            code = self.lstCodes[ix]
            lstColumns.append(ColumnDefn(self.lstLibels[ix], justif, width=self.lstWidth[ix], valueGetter=code,
                                         maximumWidth=self.lstWidth[ix],isEditable=False,isSpaceFilling=True,))
        lstColumns.append(ColumnDefn(self.lstLibels[-2],'right',maximumWidth=80,valueGetter="debits",stringConverter=xformat.FmtMontant,
                                     isEditable=False,isSpaceFilling=True))
        lstColumns.append(ColumnDefn(self.lstLibels[-1],'right',maximumWidth=80,valueGetter="credits",stringConverter=xformat.FmtMontant,
                                     isEditable=False,isSpaceFilling=True))
        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(0)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)
        gridsizer_base.Add(self.barre_recherche, 1, wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_lettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_delettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def MAJ(self):
        lettre = "a"
        # réinit lettrage à partir de lstLettres
        self.dicEquiLet = {}
        self.dicLettres = {}
        for ID1,ID2 in self.lstLettres:
            let3 = None
            try:
                let1 = self.dicLettres[(+1,ID1)]
            except: let1=None
            try:
                let2 = self.dicLettres[(-1,ID2)]
            except: let2=None
            if let1 and let2:
                #lignes déjà lettrées
                if let1 != let2:
                    # fusionne let1 dans let2
                    for sens in (+1,-1):
                        for key,item in self.dicLettres.items():
                            if key == (sens,ID1) or key == (sens,ID2):
                                if item == let2 : item = let1
            # on étend la lettre déjà présente
            elif let1: self.dicLettres[(-1,ID2)] = let1
            elif let2: self.dicLettres[(+1,ID1)] = let2
            # pose la lettre dans les deux lignes car non encore lettrées
            else:
                self.dicLettres[(+1,ID1)] = lettre
                self.dicLettres[(-1,ID2)] = lettre
                let3 = lettre
                lettre = self.LettreSuivante(lettre)
            for let9 in (let1,let2,let3):
                if let9 and (not let9 in self.dicEquiLet):
                    self.dicEquiLet[let9] = 0.0

        # calcul de l'équilibre
        for donnee in self.lstDonnees:
            if (donnee[0],donnee[1]) in self.dicLettres:
                let = self.dicLettres[(donnee[0],donnee[1])]
                for ix in (0,-1,-2):
                    if not donnee[ix]: donnee[ix]=0
                self.dicEquiLet[let] += donnee[0]*(donnee[-1]+donnee[-2])
        # application de la lettre dans les données et vérif de l'équilibre pour la mettre en majuscules
        for donnee in self.lstDonnees:
            key = (donnee[0],donnee[1])
            if key in self.dicLettres:
                let = self.dicLettres[key]
                if abs(self.dicEquiLet[let]) < 0.5:
                    let = let.upper()
                donnee[2] = let
            else: donnee[2] = ""
        # constitution des données track pour l'OLV
        self.tracks = [Track(don,self.lstCodes) for don in self.lstDonnees]
        self.listview.SetObjects(self.tracks)
        #self.listview.Refresh()
        self.listview.CocheListeRien()
        #self.__do_layout()

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state:
            state = False
        else:
            state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(), state)
        self.listview.Refresh()

    def ClearLetters(self,choix):
        # récup des ID à lettrer, puis suppression des items
        lstID1 = []
        lstID2 = []
        for ligne in choix:
            if ligne.dc == +1: lstID1.append(ligne.id)
            else: lstID2.append(ligne.id)
            ligne.let = ''
        # constitution de la liste des suppressions dans lstLettres
        lstSupprimer = []
        for ID1,ID2 in self.lstLettres:
            if ID1 in lstID1 or ID2 in lstID2:
                lstSupprimer.append((ID1,ID2))
        # suppression des ancienes lettres
        for item in lstSupprimer:
            self.lstLettres.remove(item)
        return lstID1,lstID2

    def LettreSuivante(self,lettre=''):
        # Fonction déplacée
        return xformat.LettreSuivante(lettre)

    def OnClicLettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if self.listview.GetSelectedObjects()[0] not in choix:
            # attention la sélection n'est pas cochée
            wx.MessageBox(u"La ligne sélectionnée n'est pas cochée!\n\nrisque de quiproquo sur le travail demandé")
            event.Skip()
            return
        # on ne relettre pas les lettres majuscules qui sont équilibrées
        lettrer = [x for x in choix if x.let.lower() == x.let]
        if len(lettrer) == 0:
            wx.MessageBox(u"Pas de lettre modifiable !\n\nIl faut cocher des lettres en minuscule ou sans lettre pour pouvoir lettrer")
            event.Skip()
            return
        lstID1,lstID2 = self.ClearLetters(choix)
        # ajout de nouveaux lettrages produit cartésien des lignes cochées
        if lstID1 == [] : lstID1=[None]
        if lstID2 == [] : lstID2=[None]
        for ID1 in lstID1:
            for ID2 in lstID2:
                self.lstLettres.append((ID1,ID2))
        event.Skip()
        self.MAJ()

    def OnClicDelettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if self.listview.GetSelectedObjects()[0] not in choix:
            # attention la sélection n'est pas cochée
            wx.MessageBox(u"La ligne sélectionnée n'est pas cochée!\n\nrisque de quiproquo sur le travail demandé")
            event.Skip()
            return
        delettrer = [x for x in choix if (x.let.lower() == x.let) and (x.let != '')]
        if len(delettrer) == 0:
            wx.MessageBox(u"Pas de lettre modifiable !\n\nIl faut cocher des lettres en minuscule pour pouvoir delettrer")
        lstID1,listID2 = self.ClearLetters(choix)
        event.Skip()
        self.MAJ()

    def OnClicFermer(self, event):
        self.choix = []
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.EndModal(wx.OK)

    def GetLettresSuppr(self):
        return [x for x in self.lstLettresOriginal if not x in self.lstLettres]

    def GetLettresNews(self):
        return [(x,y) for (x,y) in self.lstLettres if not (x,y) in self.lstLettresOriginal]

class DialogCoches(wx.Dialog):
    def __init__(self, parent, listeOriginale=[("Choix1","Texte1"),("Choix2","Texte2"),],columnSort=1,
                 LargeurCode=80,LargeurLib=100,minSize=(350, 350),titre=u"Faites un choix !",
                 intro=u"Double Clic sur la ou les réponses souhaitées...", altOK = False):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.SetTitle("xchoixListe.DialogCoches")
        self.columnSort = columnSort
        self.altOK = altOK
        self.choix= None
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        self.nbColonnes=0
        for item in listeOriginale :
            if isinstance(item,(list,tuple)):
                self.nbColonnes = len(item)
            else:
                self.nbColonnes = 1
                item = (str(item),)
            self.liste.append(item)

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=15, nomImage="xpy/Images/32x32/Python.png")
        # conteneur des données
        self.listview = FastObjectListView(self)
        # Boutons
        self.bouton_ok = wx.Button(self, label=u"Valider" )
        self.bouton_ok.SetBitmap(wx.Bitmap("xpy/Images/32x32/Valider.png"))
        self.bouton_annuler = wx.Button(self, label=u"Annuler")
        self.bouton_annuler.SetBitmap(wx.Bitmap("xpy/Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_annuler)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_annuler.SetToolTip(u"Cliquez ici pour fermer")
        self.listview.SetToolTip(u"Double Cliquez pour choisir")
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        if self.nbColonnes >1:
            filCode = False
        else: filCode = True
        lstColumns = [
            ColumnDefn("Code", "left", 0, 0),
            ColumnDefn("Code", "left", self.wCode, 0,isSpaceFilling=filCode),]
        if self.nbColonnes >1:
            texte = "Libelle (non modifiables)"
            for ix in range(1,self.nbColonnes):
                lstColumns.append(ColumnDefn(texte, "left", self.wLib, ix, isSpaceFilling=True))
                texte = "-"

        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(0)
        self.listview.SetObjects(self.liste)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_annuler, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnClicFermer(self, event):
        self.choix = []
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.choix = self.listview.GetCheckedObjects()
        if len(self.choix) == 0:
            dlg = wx.MessageDialog(self, u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler", u"Accord Impossible", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            if self.nbColonnes == 1:
                self.choix = [x[0] for x in self.choix]
            self.EndModal(wx.OK)

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state :
            state = False
        else : state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(),state)
        self.listview.Refresh()

class DialogAffiche(wx.Dialog):
    def __init__(self, *args,**kwd):
        titre =     kwd.pop('titre',"Ici mon titre")
        intro =     kwd.pop('intro',"et mes explications")
        lstDonnees = kwd.pop('lstDonnees',[("a",2),("b",10),("c","jj")])
        lstColonnes = kwd.pop('lstColonnes',None)
        if not lstColonnes:
            item = lstDonnees[0]
            if isinstance(item,str):
                lstColonnes = ['col1',]
            else:
                lstColonnes = ["col "+ str(x) for x in item]
        lstWnomsCol = [len(x)*6 for x in lstColonnes]
        self.lstWcol =   kwd.pop('lstWcol',lstWnomsCol)
        self.lstSetters = kwd.pop('lstSetters',None)
        self.withCheck  = kwd.pop('withCheck', False)
        self.columnSort = kwd.pop('columnSort',min(1,len(lstColonnes)-1))
        size = kwd.pop('size',(600,600))


        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetMinSize(size)
        mess = None
        self.donneeIsStr = False
        if isinstance(lstDonnees[0],str):
            self.donneeIsStr = True
            lstDonnees = [ (x,) for x in lstDonnees]
        if not lstDonnees or len(lstDonnees)==0 : mess = "xchoixListe.DialogAffiche reçoit 'lstDonnees' vide"
        if (not lstDonnees[0]) or (not isinstance(lstDonnees[0],(tuple,list))):
            mess = "xchoixListe.DialogAffiche reçoit 'lstDonnees' contenant un type :%s"%type(lstDonnees[0])
        if mess:
            wx.MessageBox(mess)
            self.EndModal(wx.ID_ABORT)
        if len(lstColonnes) != len(lstDonnees[0]):
            lstColonnes=[]
            for i in range(len(lstDonnees[0])):
                lstColonnes.append("col " + str(i))
        self.lstDonnees = lstDonnees
        self.SetTitle("xchoixListe.DialogAffiche")
        self.choix= None
        self.lstColonnes = lstColonnes
        self.nbColonnes = len(lstColonnes)

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=18, nomImage="xpy/Images/32x32/Python.png")

        # Boutons
        bmpabort = wx.Bitmap("xpy/Images/32x32/Annuler.png")
        self.bouton_annuler = wx.Button(self, id=wx.ID_CANCEL,label=(u"Abandon"))
        self.bouton_annuler.SetBitmap(bmpabort)
        bmpok = wx.Bitmap("xpy/Images/32x32/Valider.png")
        self.bouton_fermer = wx.Button(self, id=-1,label=(u"Valider"))
        self.bouton_fermer.SetBitmap(bmpok)
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour valider votre choix")
        self.InitOlv()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicOk, self.bouton_fermer)

    def InitOlv(self):
        self.listview = FastObjectListView(self,style= wx.LC_REPORT)
        self.listview.SetToolTip(u"Double Cliquez pour choisir")
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClicOk)

        lstColumns = []
        self.lstCodes = [xformat.NoAccents(x) for x in  self.lstColonnes]
        for ix  in range(self.nbColonnes):
            width = self.lstWcol[ix]
            label = self.lstColonnes[ix]
            code = self.lstCodes[ix]
            lstColumns.append(ColumnDefn(label, "left", width, code,  isSpaceFilling=True))

        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        if self.withCheck:
            self.listview.CreateCheckStateColumn()

        self.tracks = [Track(don,self.lstCodes) for don in self.lstDonnees]

        self.listview.SetObjects(self.tracks)
        self.listview.Refresh()

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        sizerolv = wx.BoxSizer(wx.VERTICAL)
        sizerolv.Add(self.listview, 10, wx.EXPAND, 10)
        gridsizer_base.Add(sizerolv, 10, wx.EXPAND, 10)
        gridsizer_base.Add(wx.StaticLine(self), 0, wx.TOP| wx.EXPAND, 3)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_annuler, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND,5)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def GetDonnees(self,**kwd):
        return self.lstDonnees

    def OnDblClicOk(self, event):
        selection = self.listview.GetSelectedObject()
        if selection == None and len(self.listview.innerList)>1:
            dlg = wx.MessageDialog(self, (u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"), (u"Accord Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.choix = self.GetChoix()
            event.Skip()
            self.EndModal(wx.OK)

    def GetChoix(self):
        selection = self.listview.GetSelectedObject()
        donnees = None
        if selection :
            donnees = selection.donnees
        elif len(self.listview.innerList) == 1:
            donnees = self.listview.innerList[0].donnees
        if self.donneeIsStr and donnees:
            # les données entrées n'étant pas des tuples, il faut les détupiliser
            donnees = donnees[0]
        return donnees

if __name__ == u"__main__":

    app = wx.App(0)
    import os
    # remonter de deux niveaux
    os.chdir("..")
    os.chdir("..")

    dialog_1 = DialogAffiche()
    app.SetTopWindow(dialog_1)

    dialog_2 = DialogCoches(None)
    app.SetTopWindow(dialog_2)

    dialog_3 = DialogLettrage(None,{12456:[u"choïx 1",15]},[u"libellé1",u"Montant"],{6545:[u"éssai",50,25]},[u"libellé2",u"libellé1","montant"],[(12456,None),])
    app.SetTopWindow(dialog_3)

    #print(xformat.FmtMontant(-124566.45765,prec=3))
    print(dialog_1.ShowModal())
    print(dialog_1.choix)
    app.MainLoop()

