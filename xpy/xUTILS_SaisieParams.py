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
from xpy.outils                import xformat

OPTIONS_CTRL = ('name', 'label', 'ctrlAction', 'btnLabel', 'btnAction', 'value', 'labels', 'values', 'enable',
                'genre', 'help','size','txtSize', 'btnHelp')
# les Binds de ctrl se posent dans le pannel
OPTIONS_PANEL = ('pos','style','name')

def SetEnableID(matrice,enable=False):
    trouve = False
    if isinstance(matrice,dict):
        if 'name' in matrice.keys() and matrice['name'] == 'ID':
            matrice['enable']=enable
            trouve = True
        if not trouve:
            for key,item in matrice.items():
                trouve = SetEnableID(item,enable)
                if trouve: break
    elif isinstance(matrice,list):
        for item in matrice:
            trouve = SetEnableID(item,enable)
            if trouve: break
    return trouve

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
                for (cat,libel) in matrice.keys():
                    if cat == code : cle = (cat,libel)
                if cle :
                    for ligne in matrice[cle]:
                        if 'name' in ligne:
                            if colonne in ligne['name']:
                                if 'genre' in ligne:
                                    if ligne['genre'] in ['Float','Int']: format = 'RIGHT'
                                    elif ligne['genre'] in ['Check','Bool']: format = 'CENTER'
                                    else: format = 'LEFT'
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
    elif genre in ['enum', 'combo','wxenumproperty']:
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

class BTN_reinitialisation(wx.BitmapButton):
    # à parfaire
    def __init__(self, parent, ctrl_parametres=None):
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, wx.Bitmap("xpy/Images/16x16/Actualiser.png", wx.BITMAP_TYPE_ANY))
        self.ctrl_parametres = ctrl_parametres
        self.SetToolTip(("Cliquez ici pour réinitialiser tous les paramètres"))
        self.Bind(wx.EVT_BUTTON, self.OnBouton)
    def OnBouton(self, event):
        self.ctrl_parametres.Reinitialisation()

class BTN_action(wx.BitmapButton):
    def __init__(self, parent, image=None, help='', action=None):
        if not image: image=wx.Bitmap("xpy/Images/16x16/Loupe.png")
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, bitmap=image, )
        self.SetToolTip(help)
        self.Bind(wx.EVT_BUTTON, action)

class BTN_fermer(wx.BitmapButton):
    def __init__(self, parent):
        wx.BitmapButton.__init__(self, parent, wx.OK, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY))
        self.SetToolTip(("Cliquez ici pour enregistrer et fermer la fenêtre"))

class BTN_esc(wx.BitmapButton):
    def __init__(self, parent, image=None, action=None):
        if not image: image=wx.Bitmap("xpy/Images/100x30/Bouton_annuler.png",wx.BITMAP_TYPE_ANY)
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, bitmap=image, )
        self.SetToolTip(("Cliquez ici pour abandonner et fermer la fenêtre"))
        self.Bind(wx.EVT_BUTTON, action)

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
            self.SetValeurs(self.dictValeursDefaut)

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
                            if genre in ['enum','combo']:
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
                            "Echec sur Property de name: '%s' - value: '%s' (%s)\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                            %(name,value,type(value),err,commande),
                            'CTRL_property.InitMatrice() : Paramètre ligne indigeste !', wx.OK | wx.ICON_STOP
                            )

    def Reinitialisation(self):
        dlg = wx.MessageDialog(None, ("Souhaitez-vous vraiment réinitialiser tous les paramètres ?"),
                               ("Paramètres par défaut"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse == wx.ID_YES:
            self.SetValeurs(self.dictValeursDefaut)

    def SetValeurs(self, ddDonnees={}):
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

    def GetValeurs(self):
        values = self.GetPropertyValues()
        ddDonnees = {}
        for nom, valeur in values.items():
            [code, champ] = nom.split('.')
            if not code in ddDonnees : ddDonnees[code] = {}
            ddDonnees[code][champ] = valeur
        return ddDonnees

class PNL_property(wx.Panel):
    #affichage d'une grille property sans autre bouton que sortie
    def __init__(self, parent, topWin, *args, matrice={}, donnees=[], lblbox="Paramètres item_property", **kwds):
        self.parent = parent
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self, parent, *args, **kw)

        #********************** CTRL PRINCIPAL ***************************************
        self.ctrl = CTRL_property(self,matrice,donnees)
        #***********************************************************************

        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
        topbox = wx.StaticBoxSizer(cadre_staticbox)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        #topbox.MinSize = (300,400)
        self.SetSizerAndFit(topbox)

    def GetValeurs(self):
        return self.ctrl.GetValeurs()

    def SetValeurs(self,donnees):
        ret = self.ctrl.SetValeurs(donnees)
        return ret

class PNL_ctrl(wx.Panel):
    # Panel contenant un contrôle ersatz d'une ligne de propertyGrid
    """ et en option (code) un bouton d'action permettant de contrôler les saisies
        GetValue retourne la valeur choisie dans le ctrl avec action possible par bouton à droite"""
    def __init__(self, parent, *args, genre='string', name=None, label='', value= None, labels=[], values=[],
                 help=None, btnLabel=None, btnHelp=None, size=None, txtSize=100, **kwds):
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self,parent,*args, **kw)
        self.value = value
        self.name = name
        if btnLabel :
            self.avecBouton = True
        else: self.avecBouton = False
        if not size:
            size = (2000, 30)
        self.MaxSize = size
        lg = max(txtSize,len(label)*6)
        if label and len(label)>0:
            self.txt = wx.StaticText(self, wx.ID_ANY, label + " :")
            self.txt.MinSize = (lg, 25)
        else: self.txt = wx.StaticText(self, wx.ID_ANY,  "")

        # seul le PropertyGrid gère le multichoices, pas le comboBox
        if genre == 'multichoice': genre = 'combo'
        lgenre,lname,llabel,lvalue = Normalise(genre, name, label, value)
        if not labels: labels = []
        if not values: values = []
        if len(values) > 0 and len(labels) == 0:
            labels = values
        self.genre = lgenre

        try:
            commande = 'debut'
            # construction des contrôles selon leur genre
            if lgenre in ['enum','combo','multichoice']:
                self.ctrl = wx.ComboBox(self, wx.ID_ANY)
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
            if lgenre in ('dir','dirfile'):
                self.avecBouton = True
                if not btnLabel: btnLabel = '...'
                self.btn = wx.Button(self, wx.ID_ANY, btnLabel, size=(30, 20))
                if lgenre == 'dirfile':
                    self.btn.Bind(wx.EVT_BUTTON, self.OnDirfile)
                else:
                    self.btn.Bind(wx.EVT_BUTTON, self.OnDir)
            elif self.avecBouton:
                self.btn = wx.Button(self, wx.ID_ANY, btnLabel, size=(30, 20))
                if btnHelp:
                    self.btn.SetToolTip(btnHelp)
            self.BoxSizer()

        except Exception as err:
            wx.MessageBox(
                "Echec sur PNL_ctrl de:\ngenre: %s\nname: %s\nvalue: %s (%s)\n\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                % (lgenre, name, value, type(value), err, commande),
                'PNL_ctrl.__init__() : Paramètre de ligne indigeste !', wx.OK | wx.ICON_STOP
            )

    def BoxSizer(self):
        topbox = wx.BoxSizer(wx.HORIZONTAL)
        topbox.Add(self.txt,0, wx.LEFT|wx.TOP|wx.EXPAND|wx.ALIGN_TOP, 5)
        topbox.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 4)
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
        if self.genre in ('combo','multichoice','enum'):
            self.ctrl.SetValue(value)
        else: self.ctrl.SetValue(value)

    # c'est la mise à jour des choices du controle
    def SetValues(self,values):
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
    def __init__(self, parent, *args, ltColonnes=[], llItems=[], lblbox="Paramètres listCtrl", **kwds):
        self.parent = parent
        self.llItems = llItems
        self.ltColonnes = ltColonnes
        self.colonnes = []
        self.lddDonnees = []
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kw)

        #********************** Objet principal *******************************
        self.ctrl = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        #**********************************************************************

        # Remplissage de la matrice
        ret = self.InitMatrice(ltColonnes)
        # Remplissage des valeurs
        self.SetValeurs(llItems,ltColonnes)

        self.bouton_ajouter = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Ajouter.png"),
                                         help="Créer une nouvelle ligne",action=self.OnAjouter )
        self.bouton_modifier = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Modifier.png"),
                                          help="Modifier la ligne selectionnée",action=self.OnModifier )
        self.bouton_supprimer = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Supprimer.png"),
                                           help="Supprimer la ligne selectionée",action=self.OnSupprimer )
        self.bouton_dupliquer = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Dupliquer.png"),
                                           help="Dupliquer la ligne selectionée",action=self.OnDupliquer )
        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
        topbox = wx.StaticBoxSizer(cadre_staticbox,wx.HORIZONTAL)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        droite_flex = wx.FlexGridSizer(4,1,0,0)
        droite_flex.Add(self.bouton_ajouter, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_modifier, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_supprimer, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_dupliquer, 0, wx.ALL|wx.TOP, 4)
        topbox.Add(droite_flex,0,wx.ALL|wx.TOP,1)
        topbox.MinSize = (300,400)
        self.SetSizerAndFit(topbox)

    def InitMatrice(self, ltColonnes=[]):
        # Compose la grille de saisie des paramètres selon la liste colonnes
        for (name, label, format) in ltColonnes:
            format = eval("wx.LIST_FORMAT_%s" % format.upper())
            self.ctrl.AppendColumn( label, format, width=100)
        return 'fin matrice'

    def SetValeurs(self, llItems=[], ltColonnes=[]):
        # Alimente les valeurs dans la grille
        self.ctrl.DeleteAllItems()
        for items in llItems:
            self.ctrl.Append(items)
        for i in range(len(ltColonnes)):
            self.ctrl.SetColumnWidth(i,wx.LIST_AUTOSIZE_USEHEADER)

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

class BoxPanel(wx.Panel):
    # aligne les contrôles définis par la matrice dans une box verticale
    def __init__(self, parent, *args, lblbox="Box", code = '1', lignes=[], dictDonnees={}, **kwds):
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self,parent, *args, **kw)
        self.parent = parent
        self.code = code
        self.lstPanels=[]
        self.dictDonnees = dictDonnees
        if lblbox:
            cadre_staticbox = wx.StaticBox(self, wx.ID_ANY, label=lblbox)
            self.ssbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        else:
            self.ssbox = wx.BoxSizer(wx.VERTICAL)
        self.InitMatrice(lignes)

    def InitMatrice(self,lignes):
        for ligne in lignes:
            kwds={}
            for nom,valeur in ligne.items():
                if nom in OPTIONS_CTRL + OPTIONS_PANEL:
                    kwds[nom] = valeur
                else:
                    possibles = "Liste des possibles: %s"%str(OPTIONS_CTRL)
                    wx.MessageBox("L'options '%s' de la ligne %s n'est pas reconnue!\n\n%s"%(nom,
                                                                                        ligne['name'],possibles))
            if 'genre' in ligne:
                panel = PNL_ctrl(self, **kwds)
                if ligne['genre'].lower() in ['bool', 'check']:
                    self.UseCheckbox = 1
                if panel:
                    for cle in ('name', 'label', 'ctrlAction', 'btnLabel', 'btnAction',
                                'value', 'labels', 'values','enable'):
                        if not cle in ligne:
                            ligne[cle]=None
                    self.ssbox.Add(panel,1,wx.ALL|wx.EXPAND,0)
                    codename = self.code + '.' + ligne['name']
                    panel.ctrl.genreCtrl = ligne['genre']
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
                        if panel.ctrl.genreCtrl in ['enum','combo','multichoice']:
                            panel.ctrl.Bind(wx.EVT_COMBOBOX, self.parent.OnCtrlAction)
                            panel.ctrl.Bind(wx.EVT_CHECKBOX, self.parent.OnCtrlAction)
                        else:
                            panel.ctrl.Bind(wx.EVT_KILL_FOCUS,self.parent.OnCtrlAction)
                    self.lstPanels.append(panel)
        self.SetSizerAndFit(self.ssbox)

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
    def SetOneValues(self,name = '', values=None):
        if values:
            for panel in self.lstPanels:
                [code, champ] = panel.ctrl.nameCtrl.split('.')
                if champ == name or panel.ctrl.nameCtrl == name:
                    if panel.ctrl.genreCtrl.lower() in ['enum', 'combo','multichoice']:
                        panel.SetValues(values)
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
    def __init__(self, parent, *args, matrice={}, donnees={}, lblbox="Paramètres top", **kwds):
        kw = DicFiltre(kwds,OPTIONS_PANEL)
        wx.Panel.__init__(self,parent,*args, **kw)
        self.parent = parent
        self.matrice = matrice
        if lblbox:
            cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
            self.topbox = wx.StaticBoxSizer(cadre_staticbox,wx.HORIZONTAL)
        else:
            self.topbox = wx.BoxSizer(wx.HORIZONTAL)
        self.ddDonnees = donnees
        self.lstBoxes = []
        for code, label in matrice:
            if isinstance(code,str):
                if not code in self.ddDonnees:
                     self.ddDonnees[code] = {}
                box = BoxPanel(self, wx.ID_ANY, lblbox=label, code = code, lignes=matrice[(code,label)], dictDonnees=self.ddDonnees[code])
                self.lstBoxes.append(box)
                self.topbox.Add(box, 1, wx.EXPAND|wx.ALL,3)
        self.SetSizerAndFit(self.topbox)

    def OnCtrlAction(self,event):
        self.parent.OnChildCtrlAction(event)

    def OnBtnAction(self,event):
        self.parent.OnChildBtnAction(event)

    def GetLstValeurs(self,):
        # récupère une liste à partir du ddDonnees
        lstChamps, lstDonnees = [], []
        ddDonnees = self.GetValeurs()
        for code, label in self.matrice.keys():
            for dicCtrl in self.matrice[(code,label)]:
                lstChamps.append(dicCtrl['name'])
                lstDonnees.append(ddDonnees[code][dicCtrl['name']])
        return lstChamps,lstDonnees

    def GetValeurs(self):
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
        # compose un dict pour SetValeurs
        ddDonnees = {}
        champs = [x.lower() for x in lstChamps]
        for code, label in self.matrice.keys():
            ddDonnees[code]={}
            for dicCtrl in self.matrice[(code,label)]:
                if dicCtrl['name'].lower() in champs:
                    valeur = lstDonnees[champs.index(dicCtrl['name'].lower())]
                    name = dicCtrl['name']
                    ddDonnees[code][name]=valeur
        self.SetValeurs(ddDonnees)

    def SetValeurs(self, ddDonnees):
        for box in self.lstBoxes:
            if box.code in ddDonnees:
                dic = ddDonnees[box.code]
                box.SetValues(dic)
        return

    def SetValeur(self,name=None,valeur=None,codeBox=None):
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

    def GetPanel(self,name,codebox=None):
        panel = None
        lrad = name.split('.')
        if codebox:
            box = self.GetBox(codebox)
            name = lrad[-1]
        elif lrad == 2:
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
    def __init__(self,parent, *args, dldMatrice={}, dlColonnes={}, lddDonnees=[], **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        super().__init__(parent, wx.ID_ANY, *args, title=titre,  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER , **kwds)

        #pour une gestion simplifiée sans mot de passe caché ni checkbox ni gestion d'action de contrôle : gestionProperty True
        self.gestionProperty = True
        self.SetBackgroundColour(wx.WHITE)
        self.parent = parent
        self.dlColonnes=dlColonnes
        self.dldMatrice = dldMatrice
        self.lddDonnees = lddDonnees
        self.args = args
        self.kwds = kwds
        self.marge = 10
        # bouton bas d'écran
        self.btn = BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnEsc = BTN_esc(self,action=self.OnBtnEsc)
        self.MinSize = (400, 300)
        self.dlgGest = None

    def InitDlgGestion(self):
        # permet d'intervenir avant le lancement de Init
        self.dlgGest = DLG_vide(self,)
        if self.gestionProperty:
            self.dlgGest.pnl = PNL_property(self.dlgGest, self, matrice=self.dldMatrice, lblbox='Ajout d\'une ligne')
        else:
            self.dlgGest.pnl = TopBoxPanel(self.dlgGest, matrice=self.dldMatrice, lblbox='Ajout d\'une ligne')

    def SizerDlgGestion(self):
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
            self.kwds['ltColonnes'] = self.ltColonnes
            self.kwds['llItems'] = self.llItems
            self.pnl = PNL_listCtrl(self, *self.args, **self.kwds )
            #***************************************************************
        self.Sizer()

    def Sizer(self):
        topbox = wx.BoxSizer(wx.VERTICAL)
        topbox.Add(self.pnl, 1,wx.EXPAND | wx.ALL, self.marge)
        btnbox = wx.BoxSizer(wx.HORIZONTAL)
        btnbox.Add(self.btnEsc, 0, wx.RIGHT,7)
        btnbox.Add(self.btn, 0, wx.RIGHT,7)
        topbox.Add(btnbox,0,wx.RIGHT|wx.ALIGN_RIGHT,20)
        topbox.SetSizeHints(self)
        self.SetSizer(topbox)

    def OnAjouter(self,event):
        SetEnableID(self.dldMatrice,enable=True)
        # l'ajout d'une ligne nécessite d'appeler un écran avec les champs en lignes
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            #récupération des valeurs saisies
            ddDonnees = self.dlgGest.pnl.GetValeurs()
            donnees={}
            for (x,y) in ddDonnees.items():
                donnees[x] = y
            #donnees = deepcopy(ddDonnees)
            self.lddDonnees.append(donnees)
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValeurs(self.llItems, self.ltColonnes)
        #self.dlgGest.Destroy()

    def OnModifier(self,event, items):
        # documentation dans dupliquer
        ddDonnees = self.lddDonnees[items]
        SetEnableID(self.dldMatrice)
        self.dlgGest.pnl.SetValeurs(ddDonnees)
        #self.dlgGest.Sizer(self.dlgGest.pnl)
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            ddDonnees = self.dlgGest.pnl.GetValeurs()
            #self.lddDonnees[items] = deepcopy(ddDonnees)
            self.lddDonnees[items] = ddDonnees
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValeurs(self.llItems, self.ltColonnes)
        self.pnl.ctrl.Select(items)
        #self.dlgGest.Destroy()

    def OnSupprimer(self,event,items):
        # documentation dans dupliquer
        del self.lddDonnees[items]
        self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice,
                                         self.dlColonnes, self.lddDonnees)
        self.pnl.SetValeurs(self.llItems, self.ltColonnes)

    def OnDupliquer(self,event, items):
        ddDonnees = self.lddDonnees[items].copy()
        ret = SetEnableID(self.dldMatrice,enable=True)
        self.dlgGest.pnl.SetValeurs(ddDonnees)
        #self.dlgGest.Sizer(self.dlgGest.pnl)
        ret = self.dlgGest.ShowModal()
        if ret == wx.OK:
            ddDonnees = self.dlgGest.pnl.GetValeurs()
            donnees = ddDonnees.copy()
            self.lddDonnees.append(donnees)
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValeurs(self.llItems, self.ltColonnes)
        #self.dlgGest.Destroy()

    def OnFermer(self, event):
        return self.Close()

    def OnBtnEsc(self, event):
            self.Destroy()

class DLG_vide(wx.Dialog):
    # pour la gestion d'une ligne extraite d'un tableau listctrl ou toute situation pour gérer la matrice après init
    def __init__(self,parent, *args, **kwds):
        self.parent = parent
        name = kwds.pop('name',None)
        if not name:
            listArbo=os.path.abspath(__file__).split("\\")
            name = listArbo[-1:][0]
        super().__init__(None, wx.ID_ANY, *args, title=name,  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER , **kwds)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        self.btn = None

        #****************Exemple de Chaînage à faire passer au sizer*****************
        #self.pnl = PNL_property(self, parent, *args, matrice = matrice, **kwds )
        #****************************************************************************

    def Bouton(self,parent, btnLabel = 'OK'):
        # bouton 'ok' par défaut
        btn = wx.Button(self, wx.ID_ANY, btnLabel)
        btn.Bind(wx.EVT_BUTTON, parent.OnFermer)
        return btn

    def Sizer(self,panel):
        # Le panel contient l'essentiel de l'écran, bouton peut être aussi un sizer de boutons en bas
        self.pnl = panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.pnl, 1, wx.EXPAND | wx.ALL, self.marge)
        if not self.btn:
            self.btn = self.Bouton(self)
        sizer.Add(self.btn, 0,  wx.RIGHT|wx.ALIGN_RIGHT,20)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)

    def OnFermer(self, event):
        # si présence d'un Final et pas de sortie par fermeture de la fenêtre
        if event and not event.EventObject.ClassName == 'wxDialog' and hasattr(self,'Final'):
            self.Final()

        if self.IsModal():
            self.EndModal(wx.OK)
        else:
            self.Close()

    # ------------------- Lancement des actions sur Bind -----------------------

    def OnChildBtnAction(self, event):
        # relais des actions sur les boutons du bas d'écran
        if self.parent != self and hasattr(self.parent, 'OnChildBtnAction'):
            self.parent.OnChildBtnAction(event)
        else:
            action = 'self.%s(event)' % event.EventObject.actionBtn
            try:
                eval(action)
            except Exception as err:
                wx.MessageBox(
                    "Commande: '%s' \n\nErreur: \n%s" % (action, err),
                "Echec sur lancement de l'action bouton")

    def OnChildCtrlAction(self, event):
        # relais des actions sur boutons ou contrôles priorité si le parent gère ce relais
        if self.parent and hasattr(self.parent, 'OnChildCtrlAction'):
            self.parent.OnChildCtrlAction(event)
        else:
            action = 'self.%s(event)' % event.EventObject.actionCtrl
            try:
                eval(action)
            except Exception as err:
                wx.MessageBox(
                    "Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s" % (action, err))

class DLG_monoLigne(wx.Dialog):
    # variante DLG_vide, avec relais possible d'évènements Boutons ou Controles gérés dans matrice
    def __init__(self, parent, *args, dldMatrice={}, ddDonnees={}, **kwds):
        self.gestionProperty = kwds.pop('gestionProperty',False)
        lblbox = kwds.pop('lblbox','Gestion d\'une ligne')
        self.marge = kwds.pop('marge',10)
        self.minSize = kwds.pop('minSize',(800, 500))
        self.couleur = kwds.pop('couleur',wx.WHITE)
        listArbo = os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        super().__init__(None, wx.ID_ANY, *args, title=titre, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                         **kwds)
        self.pos = kwds.pop('pos',(50, 50))
        self.parent = parent
        self.SetBackgroundColour(self.couleur)
        self.parent = parent
        self.dldMatrice = dldMatrice
        self.ddDonnees = ddDonnees
        self.args = args
        self.kwds = kwds
        # bouton bas d'écran
        self.btn = BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnEsc = BTN_esc(self, action=self.OnBtnEsc)
        if self.gestionProperty:
            self.pnl = PNL_property(self, self, matrice=self.dldMatrice, lblbox=lblbox)
        else:
            self.pnl = TopBoxPanel(self, matrice=self.dldMatrice, lblbox=lblbox)
        self.pnl.MinSize = self.minSize
        self.Sizer()
        self.pnl.SetValeurs(self.ddDonnees)

    def Sizer(self):
        topbox = wx.BoxSizer(wx.VERTICAL)
        topbox.Add(self.pnl, 1, wx.EXPAND | wx.ALL, self.marge)
        btnbox = wx.BoxSizer(wx.HORIZONTAL)
        btnbox.Add(self.btnEsc, 0, wx.RIGHT, 40)
        btnbox.Add(self.btn, 0, wx.RIGHT, 40)
        topbox.Add(btnbox, 0, 0)
        topbox.SetSizeHints(self)
        self.SetSizer(topbox)

    def OnFermer(self, event):
        if self.parent != None:
            self.EndModal(wx.ID_OK)
        else:
            return self.Close()

    def OnBtnEsc(self, event):
        if self.parent != None:
            self.EndModal(0)
        else:
            self.Destroy()

    def OnChildBtnAction(self, event):
            if self.parent != None:
                self.parent.OnChildBtnAction(event)
            else:
                wx.MessageBox("Bonjour BtnAction de DLG_monoligne")

    def OnChildCtrlAction(self, event):
            if self.parent != None:
                self.parent.OnChildCtrlAction(event)
            else:
                wx.MessageBox("Bonjour CtrlAction de DLG_monoligne")

#************************   Pour Test ou modèle  *********************************

class xFrame(wx.Frame):
    # reçoit les controles à gérer sous la forme d'un ensemble de paramètres
    def __init__(self, *args, matrice={}, donnees={}, btnaction=None, lblbox="Paramètres xf", **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        self.parent = None
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Frame.__init__(self,*args, title=titre, **kwds)
        self.topPnl = TopBoxPanel(self,wx.ID_ANY, matrice=matrice, donnees=donnees, lblbox=lblbox)
        self.btn0 = wx.Button(self, wx.ID_ANY, "Action Frame")
        self.btn0.Bind(wx.EVT_BUTTON,self.OnBoutonAction)
        self.marge = 10
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.topPnl, 0, wx.LEFT|wx.EXPAND,self.marge)
        sizer_1.Add(self.btn0, 0, wx.RIGHT,self.marge)
        self.SetSizerAndFit(sizer_1)
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
    dictDonnees = {"bd_reseau": {'serveur': 'my server',
                                 'bdReseau':False,
                                 'utilisateur' : 'moi-meme',
                                 'config': DDstrdate2wxdate('2020-02-28',iso=True),
                                 'localisation': "ailleurs",
                                 'choix': 12,'multi':[12, 13],
                                'nombre': 456.45,
                                 },
                   "ident": {'domaine': 'mon domaine'}}
    dictMatrice = {
        ("ident", "Votre session"):
            [
                {'genre': 'String', 'name': 'domaine', 'label': 'Votre organisation', 'value': "NomDuPC",
                                 'help': 'Ce préfixe à votre nom permet de vous identifier','enable':False},
                {'genre': 'String', 'name': 'utilisateur', 'label': 'Votre identifiant', 'value': "NomSession",
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
                {'genre': 'Dirfile', 'name': 'localisation', 'label': 'Fichier',
                        'value': True,
                        'help': "Il faudra connaître les identifiants d'accès à cette base"},
                {'genre': 'String', 'name': 'serveur', 'label': 'Nom du serveur', 'value': 'monServeur',
                        'help': "Il s'agit du serveur de réseau porteur de la base de données"},
                {'genre': 'Float', 'name': 'nombre', 'label': 'float', 'value': 40.12,
                 'help': "test de nombre"},
            ]
        }

# Lancement des tests
    frame_4 = DLG_listCtrl(None,dldMatrice=dictMatrice, dlColonnes={'bd_reseau':['serveur','choix','localisation','nombre'],'ident':['utilisateur']},
                lddDonnees=[dictDonnees,{"bd_reseau":{'serveur': 'serveur3'}}])
    frame_4.Init()
    app.SetTopWindow(frame_4)
    frame_4.Show()
    """

    frame_3 = DLG_vide(None,)
    pnl = PNL_property(frame_3,frame_3,matrice=dictMatrice,donnees=dictDonnees)
    frame_3.Sizer(pnl)
    app.SetTopWindow(frame_3)
    frame_3.Show()
    """
    """
    frame_2 = FramePanels(None, )
    frame_2.Position = (500,300)
    frame_2.Show()

    frame_1 = xFrame(None, matrice=dictMatrice, donnees=dictDonnees)
    app.SetTopWindow(frame_1)
    frame_1.Position = (50,50)
    frame_1.Show()
    frame_5 = DLG_monoLigne(None,dldMatrice=dictMatrice,
                ddDonnees=dictDonnees,gestionProperty=False,minSize=(400,300))
    app.SetTopWindow(frame_5)
    frame_5.Position = (200,20)
    frame_5.Show()
    """
    app.MainLoop()
