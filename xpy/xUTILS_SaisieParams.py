# !/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------------------------
# Application :    Projet XPY, gestion de paramètres, différentes formes de grilles de saisie
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------------------------

import wx
import datetime
import os
import wx.propgrid as wxpg
from copy                      import deepcopy
from xpy.outils                import xformat,xboutons

OPTIONS_CTRL = ('name', 'label', 'ctrlAction', 'btnLabel', 'btnImage','btnAction', 'value', 'labels', 'values', 'enable',
                'genre', 'help','ctrlSize','txtSize', 'btnHelp','boxMaxSize','boxMinSize','boxSize','ctrl')
# les Binds de ctrl se posent dans le pannel
OPTIONS_PANEL = ('pos','style','name', 'size')

def DDstrdate2wxdate(date,iso=True):
    if not isinstance(date, str) : date = str(date)
    if len(date) < 10: return None
    if iso:
        dmy = (int(date[8:10]), int(date[5:7]) - 1, int(date[:4]))
    else:
        dmy = (int(date[:2]), int(date[3:5]) - 1, int(date[6:10]))
    dateout = wx.DateTime.FromDMY(*dmy)
    dateout.SetCountry(5)
    return dateout

def DDwxdate2strdate(date,iso=True):
    if not isinstance(date, wx.DateTime): return None
    #if date.IsValid():
    if iso:
        return date.Format('%Y-%m-%d')
    else:
        return date.Format('%d/%m/%Y')

def Transpose(matrice,dlColonnes,lddDonnees):
    # Transposition des lignes de la matrice pour présentation colonnes dans le format grille listCtrl
    def LtColonnes(dlColonnes, matrice):
        #Ajoute le format aux colonnes
        ltColonnes=[]
        for code in dlColonnes:
            for colonne in dlColonnes[code]:
                cle = None
                format = 'LEFT'
                for (cat,libel) in matrice.keys():
                    if cat == code : cle = (cat,libel)
                if cle :
                    for ligne in matrice[cle]:
                        if 'name' in ligne:
                            if colonne in ligne['name']:
                                if 'genre' in ligne:
                                    if ligne['genre'] in ['Float','Int']: format = 'RIGHT'
                                    elif ligne['genre'] in ['Check','Bool']: format = 'CENTER'
                                namecol = code + '.' + ligne['name']
                                if not 'label' in ligne:
                                    wx.MessageBox("Pb de matrice : il faut un champ 'label' dans le dictionnaire ci dessous\n%s" % ligne)
                                ltColonnes.append((namecol,ligne['label'],format))
                        else : wx.MessageBox("Pb de matrice : il faut un champ 'name' dans le dictionnaire ci dessous\n%s"%ligne)
        return ltColonnes

    def LlItems(ltColonnes,lddDonnees):
        llItems = []
        for ddDonnees in lddDonnees:
            lItems = []
            for (namecol, label, format) in ltColonnes:
                [code, champ] = namecol.split('.')
                valeur = ''
                for code, dictDonnee in ddDonnees.items():
                    if champ in dictDonnee:
                        valeur = dictDonnee[champ]
                lItems.append(valeur)
            llItems.append(lItems)
        return llItems

    # si pas de liste de colonnes pour une catégorie c'est toutes les colonnes qui sont prises
    if len(dlColonnes)==0:
        for (codm, label) in matrice:
            if not codm in dlColonnes:
                dlColonnes[codm] = []
                for ligne in matrice[(codm, label)]:
                    if ('name' in ligne):
                        if not 'pass' in ligne['name'].lower():
                            dlColonnes[codm].append(ligne['name'])
    ltColonnes = LtColonnes(dlColonnes, matrice)
    llItems = LlItems(ltColonnes, lddDonnees)
    return lddDonnees, ltColonnes, llItems

def Normalise(genre, name, label, value):
    #gestion des approximations de cohérence
    genre = genre.lower()
    if not name : name = 'noname'
    if not isinstance(name,str): name = str(name)
    if not label: label = name
    if genre in ('int','wxintproperty'):
        if not isinstance(value, int): value = 0
    elif genre in ('float','wxfloatproperty'):
        if not isinstance(value, float): value = 0.0
    elif genre in ['bool', 'check','wxboolproperty']:
        if not isinstance(value, bool): value = True
    elif genre in ['enum', 'combo','choice','wxenumproperty']:
        if not isinstance(value, int): value = 0
    elif (genre in ['multichoice']):
        if (not isinstance(value, list)): value = []
    elif genre in ['date','time','datetime']:
        if not isinstance(value,(wx.DateTime)): value = wx.DateTime.Today()
    else :
        if not isinstance(value,str) :
            if not value: value=''
            value = str(value)
    return genre,name,label,value

def ExtractList(lstin, champDeb=None, champFin=None):
    # Extraction d'une sous liste à partir du contenu des items début et fin
    lstout = []
    if champDeb in lstin:
        ix1 = lstin.index(champDeb)
    else:
        ix1 = 0
    if champFin in lstin:
        ix2 = lstin.index(champFin)
    elif champFin in ('last','dernier','tous'):
        ix2 = len(lstin)-1
    else:
        ix2 = ix1
    for ix in range(ix1, ix2 + 1):
        lstout.append(lstin[ix])
    return lstout

def ComposeMatrice(champDeb=None,champFin=None,lstChamps=[],lstTypes=[],lstHelp=[],record=(),
                   dicOptions={},lstCodes=None):
    # Retourne une matrice (dic[chapitre][champ]) et  donnees (dic[champ][valeur])
    lstNomsColonnes = ExtractList(lstChamps, champDeb=champDeb, champFin=champFin)
    options = {}
    for key, dic in dicOptions.items():
        options[xformat.SupprimeAccents(key)] = dic
    if lstCodes:
        lstCodesColonnes = lstCodes
    else:
        lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    if len(lstTypes) < len(lstChamps) and len(record) == len(lstChamps):
        lstTypes = []
        for valeur in record:
            if not valeur: valeur = ''
            if isinstance(valeur, bool): tip = 'bool'
            elif isinstance(valeur, int): tip = 'int'
            elif isinstance(valeur, float): tip = 'float'
            elif isinstance(valeur, datetime.date): tip = 'date'
            else: tip = 'str'
            if tip == 'str' and len(valeur)>200: tip = 'longstring'
            lstTypes.append(tip)

    ldmatrice = []
    def Genre(tip):
        if tip[:3] == 'int':
            genre = 'int'
        elif tip == 'tinyint(1)':
            genre = 'bool'
        elif tip[:7] == 'varchar':
            genre = 'string'
            if len(tip) == 12 and tip[8] > '2': genre = 'longstring'
            if len(tip) > 12: genre = 'longstring'
        elif 'blob' in tip:
            genre = 'blob'
        else:
            genre = tip
        return genre

    for nom, code in zip(lstNomsColonnes, lstCodesColonnes):
        ix = lstChamps.index(nom)
        dicchamp = {
            'genre': Genre(lstTypes[ix]),
            'name': code,
            'label': nom,
            'help': lstHelp[ix]
        }
        # Présence de la définition d'options ou dérogations au standart
        if code in options:
            for key,item in options[code].items():
                dicchamp[key]=item
        ldmatrice.append(dicchamp)

    # composition des données
    dicdonnees = {}
    for nom, code in zip(lstNomsColonnes, lstCodesColonnes):
        ix = lstChamps.index(nom)
        if len(record) > ix:
            dicdonnees[code] = record[ix]
    return ldmatrice, dicdonnees

def DicFiltre(dic,options):
    # ne retient qu'une liste de clés du dictionnaire
    dicout = {}
    for kw in options:
        if kw in dic:
            dicout[kw] = dic[kw]
    return dicout

#**********************************************************************************
#                   GESTION des CONTROLES: Grilles ou composition en panel
#**********************************************************************************
class AnyCtrl(wx.Panel):
    # Exemple d'un controle pour s'insérer dans une matrice 'genre':'anyctrl', 'ctrl':'MyAnyCtrl'
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        self.choice = wx.Choice(self,wx.ID_ANY,choices=[])
        self.Sizer()

    def Sizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.choice,1,wx.EXPAND, 0)
        self.SetSizer(box)

    def SetValue(self,value):
        self.choice.SetStringSelection(value)

    def GetValue(self):
        return self.choice.GetStringSelection()

    def Set(self,values):
        # définie les values possibles dans le contrôle
        self.choice.Set(values)

class CTRL_property(wxpg.PropertyGrid):
    # grille property affiche les paramètres gérés par PNL_property
    def __init__(self, parent, matrice={}, valeursDefaut={}, enable=True, style=wxpg.PG_SPLITTER_AUTO_CENTER):
        wxpg.PropertyGrid.__init__(self, parent, wx.ID_ANY, style=style)
        self.parent = parent
        self.dictValeursDefaut = valeursDefaut
        self.Bind(wxpg.EVT_PG_CHANGED, self.OnPropGridChange)
        if not enable:
            self.Enable(False)
            couleurFond = wx.LIGHT_GREY
            self.SetCaptionBackgroundColour(couleurFond)
            self.SetCellBackgroundColour(couleurFond)
            self.SetMarginColour(couleurFond)
            self.SetEmptySpaceColour(couleurFond)

        # Remplissage de la matrice
        self.InitMatrice(matrice)

        # Remplissage des valeurs
        if len(self.dictValeursDefaut) > 0:
            self.SetValues(self.dictValeursDefaut)

    def OnPropGridChange(self, event):
        event.Skip()

    def InitMatrice(self, matrice={}):
        # Compose la grille de saisie des paramètres selon le dictionnaire matrice
        for (code, chapitre) in matrice:
            # Chapitre
            if isinstance(chapitre, str):
                self.Append(wxpg.PropertyCategory(chapitre))
                for ligne in matrice[(code, chapitre)]:
                    if 'name' in ligne and 'genre' in ligne:
                        if not 'label' in ligne : ligne['name'] = None
                        if not 'value' in ligne : ligne['value'] = None
                        if not 'enable' in ligne : ligne['enable'] = True
                        codeName = code + '.' + ligne['name']
                        genre, name, label, value = Normalise(ligne['genre'],codeName,ligne['label'],ligne['value'])
                        if not 'labels' in ligne: ligne['labels'] = []
                        if 'values' in ligne and ligne['values']:
                            if ligne['labels']:
                                if len(ligne['values']) > 0 and len(ligne['labels']) == 0:
                                    ligne['labels'] = ligne['values']
                            else: ligne['labels'] = ligne['values']
                        commande = ''
                        try:
                            commande = genre
                            if genre in ['enum','combo','choice']:
                                values = list(range(0,len(ligne['labels'])))
                                choix = wxpg.PGChoices(ligne['labels'], values=[])
                                propriete = wxpg.EnumProperty(label, name,
                                                              choix,
                                                              value)
                            elif genre == 'multichoice':
                                propriete = wxpg.MultiChoiceProperty(label, name, choices=ligne['labels'], value=value)

                            elif genre in ['bool','check']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.BoolProperty(label= label, name=name, value= value)
                                propriete.PG_BOOL_USE_CHECKBOX = 1

                            elif genre in ['date','datetime','time']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.DateProperty(label= label, name=name, value= value)
                                propriete.SetFormat('%d/%m/%Y')
                                propriete.PG_BOOL_USE_CHECKBOX = 1

                            elif genre in ['blob','longstring']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.LongStringProperty(label= label, name=name, value= value)
                                propriete.PG_BOOL_USE_CHECKBOX = 1

                            elif genre in ['str','string','texte','txt']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.StringProperty(label= label, name=name, value= value)
                                propriete.PG_BOOL_USE_CHECKBOX = 1

                            elif genre == 'dir':
                                propriete = wxpg.DirProperty(name)

                            elif genre == 'dirfile':
                                propriete = wxpg.FileProperty(name)

                            else:
                                commande = "wxpg." + genre.upper()[:1] + genre.lower()[1:] + "Property(label= label, name=name, value=value)"
                                propriete = eval(commande)
                            if 'help' in ligne:
                                propriete.SetHelpString(ligne['help'])
                            self.Append(propriete)

                        except Exception as err:
                            wx.MessageBox(
                            "Echec sur Property de name: '%s' - value: '%s' (%s)\n"
                            + "Le retour d'erreur est : \n%s\n\nSur commande : %s"
                            %(name,value,type(value),err,commande),
                            'CTRL_property.InitMatrice() : Paramètre ligne indigeste !', wx.OK | wx.ICON_STOP
                            )

    def Reinitialisation(self):
        dlg = wx.MessageDialog(None, ("Souhaitez-vous vraiment réinitialiser tous les paramètres ?"),
                               ("Paramètres par défaut"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse == wx.ID_YES:
            self.SetValues(self.dictValeursDefaut)

    def SetValues(self, ddDonnees={}):
        # Alimente les valeurs dans la grille en composant le nom avec le code
        for code, valeurs in ddDonnees.items():
            for champ, valeur in valeurs.items():
                nom = code + '.' +champ
                #n = self.GetLastItem().GetName()
                propriete = self.GetPropertyByName(nom)
                if propriete:
                    genre = propriete.GetClassName()
                    label = propriete.GetName()
                    genre,nom,label,valeur = Normalise(genre,nom,label,valeur)
                    propriete.SetValue(valeur)

    def GetValues(self):
        values = self.GetPropertyValues()
        ddDonnees = {}
        for nom, valeur in values.items():
            [code, champ] = nom.split('.')
            if not code in ddDonnees : ddDonnees[code] = {}
            ddDonnees[code][champ] = valeur
        return ddDonnees

class PNL_property(wx.Panel):
    #affichage d'une grille property sans autre bouton que sortie
    def __init__(self, parent, topWin, *args, matrice={}, donnees=[], lblBox="Paramètres item_property", **kwds):
        self.parent = parent
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self, parent, *args, **kw)

        #********************** CTRL PRINCIPAL ***************************************
        self.ctrl = CTRL_property(self,matrice,donnees)
        #***********************************************************************

        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblBox)
        topbox = wx.StaticBoxSizer(cadre_staticbox)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        #topbox.MinSize = (300,400)
        self.SetSizer(topbox)

    def GetValues(self):
        return self.ctrl.GetValues()

    def SetValues(self,donnees):
        ret = self.ctrl.SetValues(donnees)
        return ret

class PNL_ctrl(wx.Panel):
    # Panel contenant un contrôle ersatz d'une ligne de propertyGrid
    """ et en option (code) un bouton d'action permettant de contrôler les saisies
        GetValue retourne la valeur choisie dans le ctrl avec action possible par bouton à droite"""
    def __init__(self, parent, *args, genre='string', name=None, label='', value= None, labels=[], values=[],
                 help=None, btnLabel=None, btnImage=None, btnHelp=None,  txtSize=100, ctrl=None, **kwds):

        if 'ctrlSize' in kwds:
            kwds['size'] = kwds['ctrlSize']
        kw = DicFiltre(kwds,OPTIONS_PANEL )
        wx.Panel.__init__(self,parent,*args, **kw)
        genre = genre.lower()
        self.value = value
        self.name = name
        self.SetOneSet = self.Set

        if btnLabel or btnImage :
            self.avecBouton = True
        else: self.avecBouton = False
        lg = max(txtSize,int(len(label)*5.5))
        if label and len(label)>0:
            self.txt = wx.StaticText(self, wx.ID_ANY, label + " :")
            self.txt.MinSize = (lg, 25)
        else: self.txt = wx.StaticText(self, wx.ID_ANY,  "")
        self.SetMaxSize((400,35))

        # seul le PropertyGrid gère le multichoices, pas le comboBox
        if genre == 'multichoice': genre = 'combo'
        lgenre,lname,llabel,lvalue = Normalise(genre, name, label, value)
        if not labels: labels = []
        if not values: values = []
        if len(values) > 0 and len(labels) == 0:
            labels = values
        self.genre = lgenre
        self.values = values
        try:
            commande = 'debut'
            # construction des contrôles selon leur genre
            if lgenre in ['enum','combo','multichoice','choice']:
                if lgenre == 'choice':
                    style = wx.TE_PROCESS_ENTER | wx.CB_READONLY
                else: style = wx.TE_PROCESS_ENTER
                self.ctrl = wx.ComboBox(self, wx.ID_ANY,style = style)
                if labels:
                    commande = 'Set in combo'
                    self.ctrl.Set(labels)
                    if isinstance(lvalue,list): lvalue=lvalue[0]
                    if isinstance(lvalue,int): lvalue=labels[lvalue]
                    self.ctrl.SetValue(lvalue)
                else: lvalue = None

            elif lgenre in ['bool', 'check']:
                self.ctrl = wx.CheckBox(self, wx.ID_ANY)
                self.UseCheckbox = 1
            elif lgenre == 'anyctrl':
                self.ctrl = ctrl(self)
            else:
                style = wx.TE_PROCESS_ENTER
                if lname:
                    if 'pass' in lgenre:
                        lgenre = 'str'
                        style = wx.TE_PASSWORD | wx.TE_PROCESS_ENTER
                self.ctrl = wx.TextCtrl(self, wx.ID_ANY, style=style)

            if lvalue:
                commande = 'Set Value'
                if lgenre in ['int','float']:
                    lvalue = str(lvalue)
                if lgenre in ['date','time','datetime']:
                    lvalue = DDwxdate2strdate(lvalue,iso=False)
                self.ctrl.SetValue(lvalue)
            if help:
                self.ctrl.SetToolTip(help)
                self.txt.SetToolTip(help)
            commande = "création Boutons"
            if not btnLabel: btnLabel = ''
            if lgenre in ('dir','dirfile'):
                self.avecBouton = True
                if lgenre == 'dirfile':
                    onBtn = self.OnDirfile
                else:
                    onBtn = self.OnDir
                self.btn = xboutons.Bouton(self,label=btnLabel, image=wx.ART_GO_DIR_UP,onBtn=onBtn)
            elif self.avecBouton:
                self.btn = xboutons.Bouton(self,label=btnLabel, image=btnImage,help=btnHelp)
            self.BoxSizer()
        except Exception as err:
            wx.MessageBox(
                "Echec sur PNL_ctrl de:\ngenre: %s\nname: %s\nvalue: %s (%s)\n\n"
                +"Le retour d'erreur est : \n%s\n\nSur commande : %s"
                % (lgenre, name, value, type(value), err, commande),
                'PNL_ctrl.__init__() : Paramètre de ligne indigeste !', wx.OK | wx.ICON_STOP
            )

    def BoxSizer(self):
        topbox = wx.BoxSizer(wx.HORIZONTAL)
        topbox.Add(self.txt,0, wx.LEFT|wx.TOP|wx.ALIGN_TOP, 5)
        topbox.Add(self.ctrl, 1, wx.ALL|wx.EXPAND , 4)
        if self.avecBouton:
            topbox.Add(self.btn, 0, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(topbox)

    def GetValue(self):
            return self.ctrl.GetValue()

    def SetValue(self,value):
        if self.genre in ('int','float'):
            if not value: value = 0
            value = str(value)
        if self.genre in ('bool','check'):
            try:
                value = int(value)
            except Exception as err:
                value = 0
        if value == None:
            value = ''
        self.ctrl.SetValue(value)

    # c'est la mise à jour des choices du controle
    def Set(self,values):
        self.ctrl.Set(values)

    def OnDir(self,event):
        """ Open a dir"""
        self.dirname = ''
        dlg = wx.DirDialog(self, "Choisissez un emplacement", self.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

    def OnDirfile(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choisissez un fichier", self.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

#*****************  GESTION des COMPOSITIONS DE CONTROLES **********************************

class PNL_listCtrl(wx.Panel):
    #affichage d'une listeCtrl avec les boutons classiques pour gérer les lignes
    def __init__(self, parent, *args, ltColonnes=[], llItems=[], **kwds):
        self.lblList = kwds.pop('lblList',"Liste des éléments")
        self.styleLstCtrl = kwds.pop('styleLstCtrl',wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.parent = parent
        self.llItems = llItems
        self.ltColonnes = ltColonnes
        self.colonnes = []
        self.lddDonnees = []

        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kw)

        #********************** Objet principal pouvant être substitué ************************
        self.ctrl = wx.ListCtrl(self, wx.ID_ANY, style=self.styleLstCtrl)
        #**********************************************************************

        # Remplissage de la matrice
        ret = self.InitMatrice(ltColonnes)
        # Remplissage des valeurs
        self.SetValues(llItems,ltColonnes)
        self.lstBtnAction = []
        self.InitLstBtnAction(self.lstBtnAction)
        self.Sizer()

    # Boutons personnalisable
    def InitLstBtnAction(self,lst):
        lst +=self.GetLstBtnAction()

    def Sizer(self):
        # Ajout éventuel d'un cadre autour de l'OLV
        if self.lblList:
            cadre_staticbox = wx.StaticBox(self, wx.ID_ANY, label=self.lblList)
            topbox = wx.StaticBoxSizer(cadre_staticbox, wx.HORIZONTAL)
        else:
            topbox = wx.BoxSizer(wx.HORIZONTAL)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        droite_flex = wx.FlexGridSizer(16,1,0,0)
        for btn in self.lstBtnAction:
            droite_flex.Add(btn, 0, wx.ALL|wx.TOP, 4)
        topbox.Add(droite_flex,0,wx.ALL|wx.TOP,1)
        topbox.MinSize = (300,400)
        self.SetSizer(topbox)

    def InitMatrice(self, ltColonnes=[]):
        # Compose la grille de saisie des paramètres selon la liste colonnes
        for (name, label, format) in ltColonnes:
            format = eval("wx.LIST_FORMAT_%s" % format.upper())
            self.ctrl.AppendColumn( label, format, width=100)
        return 'fin matrice'

    # série de boutons standards
    def GetLstBtnAction(self):
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

    def AjoutBtnRaz(self):
        return xboutons.BTN_action(self, name='raz',
                                image=wx.Bitmap("xpy/Images/16x16/Supprimer_2.png"),
                                help="Supprimer toutes les lignes",
                                onBtn=self.OnRaz)

    def SetValues(self, llItems=[], ltColonnes=[]):
        # Alimente les valeurs dans la grille
        self.ctrl.DeleteAllItems()
        for items in llItems:
            self.ctrl.Append(items)
        for i in range(len(ltColonnes)):
            self.ctrl.SetColumnWidth(i,wx.LIST_AUTOSIZE_USEHEADER)

    def GetValues(self,ixLigne=None):
        # réciproque de Set valeur  ou choix d'une seule ligne d'items-----------------------------------------------
        """ wx!!!: un item est une ligne dans la fonction Insert, mais un seul element dans les fonctions Set et Get
            la fonction Append permet de remplir la ligne, je n'ai pas trouve une fonction inverse il faut boucler
        """
        llItems=[]
        nblig = self.ctrl.GetItemCount()
        cols = self.ctrl.GetColumnCount()
        dep = 0
        fin = nblig
        if ixLigne:
            dep = max(ixLigne,0)
            fin = min(ixLigne+1, nblig)
        for row in range(nblig)[dep:fin]:
            lItems = []
            for col in range(cols):
                lItems.append(self.ctrl.GetItem(row,col).GetText())
            llItems.append(lItems)
        return llItems

    def OnAjouter(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnAjouter(event)

    def OnModifier(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        if self.ctrl.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de modification possible !" ,
                                'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        self.parent.OnModifier(event,self.ctrl.GetFirstSelected())

    def OnSupprimer(self, event):
        if self.ctrl.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de suppression possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnSupprimer(event,self.ctrl.GetFirstSelected())

    def OnDupliquer(self, event):
        if self.ctrl.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de duplication possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnDupliquer(event,self.ctrl.GetFirstSelected())

    def OnRaz(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnRaz(event,)

class BoxPanel(wx.Panel):
    # aligne les contrôles définis par la matrice dans une box verticale
    def __init__(self, parent, *args, lblBox="Box", code = '1', lignes=[], dictDonnees={}, **kwds):
        size = kwds.pop('boxSize',None)
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        if size: kw['size']=size
        wx.Panel.__init__(self,parent, *args, **kw)
        maxSize = kwds.pop('boxMaxSize',None)
        minSize = kwds.pop('boxMinSize',None)
        if maxSize: self.SetMaxSize(maxSize)
        if minSize: self.SetMinSize(minSize)
        self.kwds = kwds
        self.parent = parent
        self.code = code
        self.lstPanels=[]
        self.dictDonnees = dictDonnees
        if lblBox:
            cadre_staticbox = wx.StaticBox(self, wx.ID_ANY, label=lblBox)
            self.ssbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        else:
            self.ssbox = wx.BoxSizer(wx.VERTICAL)
        self.InitMatrice(lignes)

    def InitMatrice(self,lignes):
        for ligne in lignes:
            kwdLigne= self.kwds.copy()
            for nom,valeur in ligne.items():
                if nom in OPTIONS_CTRL + OPTIONS_PANEL:
                    kwdLigne[nom] = valeur
                else:
                    possibles = "Liste des possibles: %s"%str(OPTIONS_CTRL)
                    wx.MessageBox("BoxPanel: L'options '%s' de la ligne %s n'est pas reconnue!\n\n%s"%(nom,
                                                                                        ligne['name'],possibles))
            if 'genre' in ligne:
                panel = PNL_ctrl(self, **kwdLigne)
                if ligne['genre'].lower() in ['bool', 'check']:
                    self.UseCheckbox = 1
                if panel:
                    for cle in ('name', 'label', 'ctrlAction', 'btnLabel', 'btnAction',
                                'value', 'labels', 'values','enable'):
                        if not cle in ligne:
                            ligne[cle]=None
                    self.ssbox.Add(panel,1,wx.EXPAND, wx.ALL,0)
                    codename = self.code + '.' + ligne['name']
                    panel.ctrl.genreCtrl = ligne['genre'].lower()
                    panel.ctrl.nameCtrl = codename
                    panel.ctrl.labelCtrl = ligne['label']
                    panel.ctrl.actionCtrl = ligne['ctrlAction']
                    panel.ctrl.valueCtrl = ligne['value']
                    panel.ctrl.valOrigine = ligne['value']
                    panel.ctrl.valuesCtrl = ligne['values']
                    panel.ctrl.labelsCtrl = ligne['labels']
                    if ligne['enable'] == False:
                        panel.ctrl.Enable(False)
                        panel.txt.Enable(False)
                    if panel.avecBouton and ligne['genre'].lower()[:3] != 'dir' :
                        panel.btn.nameBtn = codename
                        panel.btn.labelBtn = ligne['btnLabel']
                        panel.btn.actionBtn = ligne['btnAction']
                        panel.btn.Bind(wx.EVT_BUTTON,self.parent.OnBtnAction)
                    if panel.ctrl.actionCtrl:
                        panel.ctrl.Bind(wx.EVT_TEXT_ENTER, self.parent.OnCtrlAction)
                        panel.ctrl.Bind(wx.EVT_KILL_FOCUS, self.parent.OnCtrlAction)
                        if panel.ctrl.genreCtrl in ['enum','combo','multichoice','choice']:
                            panel.ctrl.Bind(wx.EVT_COMBOBOX,self.parent.OnCtrlAction)
                            panel.ctrl.Bind(wx.EVT_CHECKBOX, self.parent.OnCtrlAction)

                    self.lstPanels.append(panel)
        self.SetSizer(self.ssbox)

    # Get de tous les ctrl, mis dans un dictionnaire de données
    def GetValues(self):
        for panel in self.lstPanels:
            [code, champ] = panel.ctrl.nameCtrl.split('.')
            self.dictDonnees[champ] = panel.GetValue()
        return self.dictDonnees

    # Set pour tous les ctrl nommés dans le dictionnaire de données
    def SetValues(self,dictDonnees):
        for panel in self.lstPanels:
            if panel.ctrl.nameCtrl in dictDonnees:
                panel.SetValue(dictDonnees[panel.ctrl.nameCtrl])
            else:
                (box, champ) = panel.ctrl.nameCtrl.split('.')
                if champ in dictDonnees:
                    panel.SetValue(dictDonnees[champ])
        return

    # Get du ctrl nommé
    def GetOneValue(self,name = ''):
        lrad = name.split('.')
        if len(lrad) == 2:
            [code,champ] = lrad
            name = champ
        value = None
        self.dictDonnees = self.GetValues()
        if name in self.dictDonnees:
            value = self.dictDonnees[name]
        else: value = 'ko'
        return value

    # Set du ctrl nommé
    def SetOneValue(self,name = '', value=None):
        ok = False
        for panel in self.lstPanels:
            [code,champ] = panel.ctrl.nameCtrl.split('.')
            if champ == name or panel.ctrl.nameCtrl == name:
                panel.SetValue(value)
                ok = True
                break
        if  not ok:
            wx.MessageBox("Impossible de trouver le ctrl '%s'"%name,
                          "Echec: %s/%s.SetOneValue"%(self.GrandParent.Name,self.Parent))
        return

    # SetChoices du ctrl nommé
    def SetOneSet(self,name = '', values=None):
        if values:
            for panel in self.lstPanels:
                [code, champ] = panel.ctrl.nameCtrl.split('.')
                if champ == name or panel.ctrl.nameCtrl == name:
                    if panel.ctrl.genreCtrl.lower() in ['enum', 'combo','multichoice','choice']:
                        panel.Set(values)
        return

    def GetPnlCtrl(self,name = ''):
        pnlctrl = None
        for panel in self.lstPanels:
            [code,champ] = panel.ctrl.nameCtrl
            if champ == name or panel.ctrl.nameCtrl == name:
                pnlctrl
        return pnlctrl

class TopBoxPanel(wx.Panel):
    #gestion de pluieurs BoxPanel juxtaposées horizontalement
    def __init__(self, parent, *args, matrice={}, donnees={}, dlChamps=None,**kwds):
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self,parent,*args, **kw)

        lblTopBox = kwds.pop('lblTopBox',None)

        self.parent = parent
        self.matrice = matrice.copy()

        # cas ou on limite les champs à éditer la matrice est réduite
        if dlChamps and len(dlChamps) > 0:
            for (code,label) in matrice:
                lChamps = []
                if code in dlChamps : lChamps = dlChamps[code]
                self.matrice[(code,label)] = [x for x in matrice[(code,label)] if  x['name'] in lChamps]
        self.ddDonnees = donnees

        # Cadres suplémentaire possible si un label est donné à TopBox
        if lblTopBox:
            cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblTopBox)
            self.topbox = wx.StaticBoxSizer(cadre_staticbox,wx.HORIZONTAL)
        else:
            self.topbox = wx.BoxSizer(wx.HORIZONTAL)


        kwdBox = {}
        for nom, valeur in kwds.items():
            if nom in OPTIONS_CTRL + OPTIONS_PANEL:
                kwdBox[nom] = valeur
            else:
                possibles = "Liste des possibles: %s" % str(OPTIONS_CTRL + OPTIONS_PANEL)
                wx.MessageBox("TopBox: L'option '%s' pour la topbox n'est pas reconnue!\n\n%s" % (nom, possibles))

        self.lstBoxes = []
        for code, label in self.matrice:
            if isinstance(code,str):
                if not code in self.ddDonnees:
                     self.ddDonnees[code] = {}
                box = BoxPanel(self, wx.ID_ANY, lblBox=label,
                               code = code,
                               lignes=self.matrice[(code,label)],
                               dictDonnees=self.ddDonnees[code],
                               **kwdBox)
                self.lstBoxes.append(box)
                self.topbox.Add(box, 1, wx.EXPAND|wx.ALL,3)

        self.SetSizer(self.topbox)

    def OnCtrlAction(self,event):
        self.parent.OnChildCtrlAction(event)

    def OnBtnAction(self,event):
        self.parent.OnChildBtnAction(event)

    def GetLstValeurs(self,):
        # récupère une liste à partir du ddDonnees
        lstChamps, lstDonnees = [], []
        ddDonnees = self.GetValues()
        for code, label in self.matrice.keys():
            for dicCtrl in self.matrice[(code,label)]:
                lstChamps.append(dicCtrl['name'])
                lstDonnees.append(ddDonnees[code][dicCtrl['name']])
        return lstChamps,lstDonnees

    def GetValues(self):
        ddDonnees = {}
        for box in self.lstBoxes:
            dic = box.GetValues()
            ddDonnees[box.code] = deepcopy(dic)
        return ddDonnees

    def GetValeur(self,name=None,codeBox=None):
        valeur = None
        if codeBox :
            box = self.GetBox(codeBox)
            valeur = box.GetOneValue(name)
        else:
            for box in self.lstBoxes:
                ret = box.GetOneValue(name)
                if ret != 'ko':
                    valeur = ret
        return valeur

    def SetLstValeurs(self,lstChamps,lstDonnees):
        # compose un dict pour SetValues
        ddDonnees = {}
        champs = [x.lower() for x in lstChamps]
        for code, label in self.matrice.keys():
            ddDonnees[code]={}
            for dicCtrl in self.matrice[(code,label)]:
                if dicCtrl['name'].lower() in champs:
                    valeur = lstDonnees[champs.index(dicCtrl['name'].lower())]
                    name = dicCtrl['name']
                    ddDonnees[code][name]=valeur
        self.SetValues(ddDonnees)

    def SetValues(self, ddDonnees):
        for box in self.lstBoxes:
            if box.code in ddDonnees:
                dic = ddDonnees[box.code]
                box.SetValues(dic)
        return

    def SetOneValue(self,name=None,valeur=None,codeBox=None):
        if codeBox :
            box = self.GetBox(codeBox)
            box.SetOneValue(name,valeur)
        else:
            for box in self.lstBoxes:
                ret = box.GetOneValue(name)
                if ret != 'ko':
                    box.SetOneValue(name,valeur)
        return valeur

    def GetBox(self,codeBox):
        # utile pour lui adresser les méthodes ex: box.SetOneValue()
        for box in self.lstBoxes:
            if box.code == codeBox:
                return box

    def GetPnlCtrl(self,name,codebox=None):
        panel = None
        lrad = name.split('.')
        if codebox:
            box = self.GetBox(codebox)
            name = lrad[-1]
        elif len(lrad) == 2:
            [code,name] = lrad
            box = self.GetBox(code)
        else:
            for box in self.lstBoxes:
                for pnlctrl in box.lstPanels:
                    if pnlctrl.name == lrad[-1]:
                        panel = pnlctrl
                        break
        if not panel:
            for pnlctrl in box.lstPanels:
                if pnlctrl.name == name:
                    panel = pnlctrl
        return panel

class DLG_listCtrl(wx.Dialog):
    #Dialog contenant le PNL_listCtrl qui intégre la gestion ajout,
    """
    modif par PorpertyGrid ou PanelsCtrl (cf propriété  gestionProperty )...
    dldMatrice contient les lignes de descriptif des champs gérés :
            dict{(code,label): groupe} de liste[champ1, ] de dict{attrib:valeur,}
    dlColonnes contient les listes des champs affichés dans les colonnes de la grille de type ListCtrl:
            dict{code:groupe,}  de liste[champ1, ]
    lddDonnees est une liste de dictionnaires dont les clés sont les champs et les valeurs celle des items de la ligne.

    Par Transpose() ces infos sont restituées dans ltColonnes liste de tuples descritif ordonné des colonnes
            et llItems liste des lignes, listes d'items (autant que de colonnes)
    """
    def __init__(self,parent, *args, dldMatrice={}, dlColonnes={}, lddDonnees=[], dlChamps=None, **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        name =  kwds.pop('name',self.__class__.__name__)
        title = kwds.pop('title',listArbo[-1] + "/" + name)
        style = kwds.pop('style',wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pos =   kwds.pop('pos',(200,50))
        #wx.Dialog.__init__(self,parent, wx.ID_ANY, *args, title=title, pos=pos, style=style, name= name)
        super().__init__(parent, wx.ID_ANY, *args,title=title, pos=pos, style=style, name= name)

        #pour une gestion simplifiée sans mot de passe caché ni checkbox, ni action : gestionProperty True
        self.gestionProperty =  kwds.pop('gestionProperty',False)
        colorBack =             kwds.pop('colorBack',wx.WHITE)
        self.lblList =          kwds.pop('lblList',"Liste des éléments")
        self.dlChamps = dlChamps
        self.SetBackgroundColour(colorBack)
        self.parent = parent
        self.dlColonnes=dlColonnes
        self.dldMatrice = dldMatrice
        self.lddDonnees = lddDonnees
        self.args = args
        self.kwds = kwds
        self.marge = 10
        # bouton bas d'écran
        self.btn = xboutons.BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnEsc = xboutons.BTN_esc(self)
        self.MinSize = (400, 300)
        self.dlgGest = None

    # définition (par défaut) de l'écran de gestion d'une ligne
    def InitDlgGestion(self):
        # permet d'intervenir avant le lancement du sizer global pour personnaliser l'écran de gestion
        self.dlgGest = DLG_vide(self,)
        if self.gestionProperty:
            self.dlgGest.pnl = PNL_property(self.dlgGest, self, matrice=self.dldMatrice, **self.kwds)
        else:
            self.dlgGest.pnl = TopBoxPanel(self.dlgGest, matrice=self.dldMatrice, dlChamps=self.dlChamps, **self.kwds)

    # Sizer optionnel de l'écran de gestion par défaut
    def SizerDlgGestion(self):
        # ne sera lancé par Init qu'avec un self.dlgGest créé par défaut
        self.dlgGest.Sizer(self.dlgGest.pnl)

    def Init(self):
        if not self.dlgGest:
            self.InitDlgGestion()
            self.SizerDlgGestion()
        if self.dldMatrice != {}:
            # transposition avant appel du listCtrl
            self.lddDonnees, self.ltColonnes, self.llItems\
                = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            #********************** Chaînage *******************************
            kwdList = {'lblList': self.lblList}
            kwdList['ltColonnes'] = self.ltColonnes
            kwdList['llItems'] = self.llItems
            self.pnl = self.GetPnl_listCtrl(kwdList)
            #***************************************************************
        self.Sizer()

    def GetPnl_listCtrl(self,kwdList):
        return  PNL_listCtrl(self, *self.args, **kwdList)

    def Sizer(self):
        topbox = wx.BoxSizer(wx.VERTICAL)
        topbox.Add(self.pnl, 1, wx.ALL, self.marge)
        btnbox = wx.BoxSizer(wx.HORIZONTAL)
        btnbox.Add(self.btnEsc, 0, wx.RIGHT,7)
        btnbox.Add(self.btn, 0, wx.RIGHT,7)
        topbox.Add(btnbox,0,wx.RIGHT|wx.ALIGN_RIGHT,20)
        topbox.SetSizeHints(self)
        self.SetSizer(topbox)

    def SetOneItems(self,ddDonnees):
        #Ajoute une ligne d'items dans le lddDonnees
        self.lddDonnees.append(self.Calcul(ddDonnees))
        self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
        self.pnl.SetValues(self.llItems, self.ltColonnes)

    def Calcul(self,ddDonnees):
        # Possibilité de gérer un calcul combinant les lignes après saisie et avant affichage de la liste
        return ddDonnees

    def EnableID(self,enable=True):
        ctrlID = self.dlgGest.pnl.GetPnlCtrl('ID')
        if ctrlID:
            ctrlID.Enable(enable)

    def OnAjouter(self,event):
        self.EnableID(enable=True)
        # l'ajout d'une ligne nécessite d'appeler un écran avec les champs en lignes
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            #récupération des valeurs saisies
            ddDonnees = self.Calcul(self.dlgGest.pnl.GetValues())
            self.SetOneItems(ddDonnees)

    def OnModifier(self,event, items):
        # documentation dans dupliquer
        ddDonnees = self.lddDonnees[items]
        self.dlgGest.pnl.SetValues(ddDonnees)
        self.EnableID(enable=False)
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            ddDonnees = self.Calcul(self.dlgGest.pnl.GetValues())
            self.lddDonnees[items] = ddDonnees
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValues(self.llItems, self.ltColonnes)
        self.pnl.ctrl.Select(items)
        #self.dlgGest.Destroy()

    def OnSupprimer(self,event,items):
        # retire la ligne d'items de la liste de données
        del self.lddDonnees[items]
        # supprime la ligne affichée dans le ctrl
        self.pnl.ctrl.DeleteItem(items)
        # poursuite pour les sélections multiples
        items = self.pnl.ctrl.GetFirstSelected()
        while items != -1:
            del self.lddDonnees[items]
            self.pnl.ctrl.DeleteItem(items)
            items = self.pnl.ctrl.GetFirstSelected()
        self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice,
                                         self.dlColonnes, self.lddDonnees)
        self.pnl.SetValues(self.llItems, self.ltColonnes)

    def OnRaz(self,event):
        # documentation dans dupliquer
        self.pnl.ctrl.DeleteAllItems()
        self.lddDonnees = []
        self.OnFermer(None)

    def OnDupliquer(self,event, items):
        # récupération des données de la ligne que l'on place dans l'écran de saisie
        ddDonnees = self.lddDonnees[items].copy()
        self.dlgGest.pnl.SetValues(ddDonnees)
        self.EnableID(enable=True)
        # affichage de l'écran de saisie
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            #stockage des données
            ddDonnees = self.Calcul(self.dlgGest.pnl.GetValues())
            donnees = ddDonnees.copy()
            self.lddDonnees.append(donnees)
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValues(self.llItems, self.ltColonnes)

    def OnFermer(self, event):
        return self.Close()

    def OnEsc(self, event):
            self.Destroy()

class DLG_vide(wx.Dialog):
    # pour la gestion d'une ligne extraite d'un tableau listctrl ou toute situation pour gérer la matrice après init
    def __init__(self,parent, *args, **kwds):

        listArbo=os.path.abspath(__file__).split("\\")
        name =      kwds.pop('name',self.__class__.__name__)
        title =     kwds.pop('title',listArbo[-1] + "/" + name)
        style =     kwds.pop('style',wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pos =       kwds.pop('pos',(200,100))
        size =      kwds.pop('size',(600, 450))
        minSize =   kwds.pop('minSize',(300, 250))
        marge =     kwds.pop('marge',10)
        couleur =   kwds.pop('couleur',wx.WHITE)

        super().__init__(None, wx.ID_ANY, *args, title=title, style=style, pos=pos, **kwds)
        self.marge = marge
        self.parent = parent
        self.SetMinSize(minSize)
        self.SetSize(size)
        self.SetBackgroundColour(couleur)

        # composants possibles de l'écran
        self.bandeau = None
        self.pnlParams = None
        self.pnl = None
        self.pnlPied = None
        self.btn = None

        #****************Exemple de Chaînage à faire passer au sizer*****************
        # définir self.bandeau ou self.pnlParam pour le haut
        # self.btn  ou self.pnlPied pour le bas
        # envoyer au Sizer
        #       pnl = PNL_property(self, parent, *args, matrice = matrice, **kwds )
        #       pnl = TopBoxPanel(self, matrice=dictMatrice, donnees=dictDonnees)
        #****************************************************************************

    def Sizer(self,pnl=None):
        # Le panel contient l'essentiel de l'écran, il est transmis par le parent qui appelle Sizer
        if pnl:
            self.pnl = pnl

        sizer = wx.BoxSizer(wx.VERTICAL)
        # bouton à minima par défaut
        if not self.btn and not self.pnlPied:
            self.btn = xboutons.BTN_fermer(self,label="Valider")

        # haut d'écran
        if self.bandeau:
            sizer.Add(self.bandeau, 0, wx.EXPAND | wx.ALL, self.marge)
        if self.pnlParams:
            sizer.Add(self.pnlParams, 0, wx.EXPAND | wx.ALL, self.marge)

        # corps de l'écran
        if self.pnl:
            sizer.Add(self.pnl, 1, wx.EXPAND | wx.ALL, self.marge)

        # bas d'écran
        if self.btn:
            sizer.Add(self.btn, 0,  wx.ALL|wx.ALIGN_RIGHT,self.marge)
        if self.pnlPied:
            sizer.Add(self.pnlPied, 0,  wx.ALL|wx.ALIGN_RIGHT,self.marge)

        #sizer.SetSizeHints(self)
        self.SetSizer(sizer)

    def OnFermer(self, event):
        # si présence d'un Final et pas de sortie par fermeture de la fenêtre
        if event and not event.EventObject.ClassName == 'wxDialog' and hasattr(self,'Final'):
            self.Final()

        if self.IsModal():
            self.EndModal(wx.OK)
        else:
            self.Close()

    def OnEsc(self, event):
        if self.IsModal():
            self.EndModal(wx.CANCEL)
        else:
            self.Close()

    def GetPnlCtrl(self,name,codebox=None):
        return self.pnl.GetPnlCtrl(name,codebox)

    # ------------------- Lancement des actions sur Bind -----------------------

    def OnChildBtnAction(self, event):
        # relais des actions sur les boutons du bas d'écran
        if self.parent != self and hasattr(self.parent, 'OnChildBtnAction'):
            self.parent.OnChildBtnAction(event)
        else:
            action = 'self.%s(event)' % event.EventObject.actionBtn
            eval(action)

    def OnChildCtrlAction(self, event):
        # relais des actions sur boutons ou contrôles priorité si le parent gère ce relais
        if self.parent and hasattr(self.parent, 'OnChildCtrlAction'):
            self.parent.OnChildCtrlAction(event)
        else:
            action = 'self.%s(event)' % event.EventObject.actionCtrl
            eval(action)

#************************   Pour Test ou modèle  *********************************

class xFrame(wx.Frame):
    # reçoit les controles à gérer sous la forme d'un ensemble de paramètres
    def __init__(self, *args, matrice={}, donnees={}, btnaction=None, lblTopBox="Paramètres xf", **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        self.parent = None
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Frame.__init__(self,*args, title=titre, **kwds)
        self.topPnl = TopBoxPanel(self,wx.ID_ANY, matrice=matrice, donnees=donnees, dlChamps=None, lblTopBox=lblTopBox)
        self.btn0 = wx.Button(self, wx.ID_ANY, "Action Frame")
        self.btn0.Bind(wx.EVT_BUTTON,self.OnBoutonAction)
        self.marge = 10
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.topPnl, 0, wx.LEFT|wx.EXPAND,self.marge)
        sizer_1.Add(self.btn0, 0, wx.RIGHT,self.marge)
        self.SetSizer(sizer_1)
        self.CentreOnScreen()

    def OnCtrlAction(self,event):
        wx.MessageBox('Bonjour Enter sur le ctrl : %s'%event.EventObject.Name)
        print(event.EventObject.genreCtrl, event.EventObject.nameCtrl, event.EventObject.labelCtrl,)
        print('Action prévue : ',event.EventObject.actionCtrl)

    def OnChildBtnAction(self,event):
        wx.MessageBox('Vous avez cliqué sur le bouton',event.EventObject.Name)
        print( event.EventObject.nameBtn, event.EventObject.labelBtn,)
        print('vous avez donc souhaité : ',event.EventObject.actionBtn)

    def OnBoutonAction(self, event):
        #Bouton Test
        wx.MessageBox("Bonjour l'action OnBoutonAction de l'appli")

class FramePanels(wx.Frame):
    def __init__(self, *args, **kwds):
        # cette frame moins paramétrée ne passe pas par des panels multilignes
        # elle appelle un à un les panels des controles
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Frame.__init__(self,*args, title=titre, **kwds)
        self.Size = (600,400)
        def ComposeDonnees():
            self.combo1 = PNL_ctrl(self,wx.ID_ANY,
                                genre="combo",
                                label="Le nom du choix PEUT être long ",
                                labels=["ceci est parfois plus long, plus long qu'un autre", 'cela', 'ou un autre', 'la vie est faite de choix'],
                                help="Je vais vous expliquer",
                                btnLabel=" ! ",
                                btnHelp="Là vous pouvez lancer une action par clic")

            self.combo2 = PNL_ctrl(self,wx.ID_ANY,genre="combo",label="Le nom2",values=['ceci', 'cela', 'ou un autre', 'la vie LOong fleuve tranquile'],help="Je vais vous expliquer",btnLabel="...", btnHelp="Là vous pouvez lancer une action de gestion des choix possibles")
            self.combo3 = PNL_ctrl(self,wx.ID_ANY,genre="combo",label="Le nom3 plus long",values=['ceci sans bouton', 'cela', 'ou un autre', 'la vie EST COURTE'], btnHelp="Là vous pouvez lancer une action telle que la gestion des choix possibles")
            self.ctrl1 = PNL_ctrl(self,wx.ID_ANY,genre="string",label="Un ctrl à saisir",value='monchoix', help="Je vais vous expliquer",)
            self.ctrl2 = PNL_ctrl(self,wx.ID_ANY,genre="string",label="Avec bouton de ctrl",value='monchoix étendu', help="Je vais vous expliquer", btnLabel="Ctrl", btnHelp="Là vous pouvez lancer une action de validation")
        ComposeDonnees()
        self.combo1.btn.Bind(wx.EVT_BUTTON,self.OnBoutonActionCombo1)
        self.combo2.btn.Bind(wx.EVT_BUTTON,self.OnBoutonActionCombo2)
        self.ctrl2.btn.Bind(wx.EVT_BUTTON,self.OnBoutonActionTexte2)

        self.marge = 10
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add((10,10), 0, wx.LEFT|wx.ALIGN_TOP,self.marge)
        sizer_1.Add(self.combo1, 1, wx.LEFT,self.marge)
        sizer_1.Add(self.combo2, 1, wx.LEFT,self.marge)
        sizer_1.Add(self.ctrl1, 1, wx.LEFT,self.marge)
        sizer_1.Add(self.combo3, 1, wx.LEFT,self.marge)
        sizer_1.Add(self.ctrl2, 1, wx.LEFT,self.marge)
        self.SetBackgroundColour(wx.WHITE)
        self.SetSizer(sizer_1)
        self.Layout()
        self.CentreOnScreen()

    def OnBoutonActionCombo1(self, event):
        #Bouton Test
        wx.MessageBox("Bonjour l'action OnBoutonActionCombo1 de l'appli")
        self.combo1.btn.SetLabel("Clic")

    def OnBoutonActionCombo2(self, event):
        #Bouton Test
        wx.MessageBox("Bonjour l'action OnBoutonActionCombo2 de l'appli")
        self.combo2.ctrl.Set(["Crack","boum","hue"])
        self.combo2.ctrl.SetSelection (0)

    def OnBoutonActionTexte2(self, event):
        #Bouton Test
        wx.MessageBox("Bonjour l'action OnBoutonActionCombo2 de l'appli\nHouston nous avons un problème!",style=wx.OK)
        self.ctrl2.ctrl.SetValue("corrigez")

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dictDonnees = {"bd_reseau": {'serveur': 'serveur2',
                                 'bdReseau':False,
                                 'config': DDstrdate2wxdate('2020-02-28',iso=True),
                                 'localisation': "ailleurs",
                                 'choix': 12,
                                 'multi':[12, 13],
                                'nombre': 456.45,
                                 },
                   "ident":      {'domaine': 'mon domaine',
                                  'usateur': 'nouveau',},
                  }
    dictMatrice = {
        ("ident", "Votre session"):
            [
                {'genre': 'String', 'name': 'domaine', 'label': 'Votre organisation', 'value': "NomDuPC",
                                 'help': 'Ce préfixe à votre nom permet de vous identifier','enable':False},
                {'genre': 'String', 'name': 'usateur', 'label': 'Utilisateur', 'value': "moi",
                                 'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
            ],
        ("choix_config", "Choisissez votre configuration"):
            [
                {'genre': 'Date', 'name': 'config', 'label': 'DateConfiguration','value':DDstrdate2wxdate('27/02/2019',iso=False),
                      'help': "Le bouton de droite vous permet de créer une nouvelle configuration"},
                {'genre': 'Combo', 'name': 'multi', 'label': 'Configurations','labels':['aa','bb','cc'], 'value':'1',
                         'help': "Le bouton de droite vous permet de créer une nouvelle configuration",
                         'btnLabel': "...", 'btnHelp': "Cliquez pour gérer les configurations",
                        'btnAction': 'OnCtrlAction'},
            ],
        ("bd_reseau", "Base de donnée réseau"):
            [
                {'genre': 'Dirfile', 'name': 'localisation', 'label': 'myHome.',
                        'value': 'home',
                        'help': "Il faudra connaître les identifiants d'accès à cette base"},
                {'genre': 'String', 'name': 'serveur', 'label': 'Nom du serveur', 'value': 'monServeur',
                        'help': "Il s'agit du serveur de réseau porteur de la base de données"},
                {'genre': 'Float', 'name': 'nombre', 'label': 'Nombre', 'value': 40.12,
                 'help': "test de nombre"},
            ]
        }
    dictColonnes = {'bd_reseau': ['serveur', 'choix', 'localisation', 'nombre'],
                     'ident': ['usateur']}
    dictDonneesSimple = {'filtre': {'serveur': 'my server',
                              'localisation': "ailleurs",
                              'nombre': 456.45,
                              }, }
    dictMatriceSimple = {
        ('filtre', "Base de donnée réseau"):
            [
                {'name': 'localisation', 'label': 'Fichier',
                 'value': True, 'genre': 'Dirfile',
                 'help': "Il faudra connaître les identifiants d'accès à cette base"},
                {'name': 'serveur', 'label': 'Nom du serveur',
                 'genre': 'String', 'value': 'monServeur',
                 'help': "Il s'agit du serveur de réseau porteur de la base de données"},
                {'name': 'nombre', 'label': 'float',
                 'genre': 'Float', 'value': 40.12,
                 'help': "test de nombre"},
            ]
    }
    dictColonnesSimple = {}

    # Lancement des tests
    """
    dlg_4 = DLG_listCtrl(None,dldMatrice=dictMatrice,
                                dlColonnes=dictColonnes,
                                lddDonnees=[dictDonnees])
    dlg_4.Init()
    app.SetTopWindow(dlg_4)
    dlg_4.Show()
    """

    dlg_3 = DLG_vide(None)
    #pnl = PNL_property(dlg_3,dlg_3,matrice=dictMatrice,donnees=dictDonnees)
    pnl = TopBoxPanel(dlg_3,matrice=dictMatrice,donnees=dictDonnees)
    dlg_3.Sizer(pnl)
    app.SetTopWindow(dlg_3)
    dlg_3.Show()

    """
    frame_2 = FramePanels(None, )
    frame_2.Position = (500,300)
    frame_2.Show()

    frame_1 = xFrame(None, matrice=dictMatrice, donnees=dictDonnees)
    app.SetTopWindow(frame_1)
    frame_1.Position = (50,50)
    frame_1.Show()
    """

    app.MainLoop()
