#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel
#  MATTHANIA - Projet XPY -Lancement de choix de filtres
#  2020/11/26

import wx
import os
import datetime
import xpy.xUTILS_SaisieParams as xusp
import wx.propgrid as wxpg
from xpy.outils.ObjectListView import Filter

#**************************  Gestion des filtres à ajouter************************************************************

# Filtres OLV conditions possibles
CHOIX_FILTRES = {float:[
                            ('EGAL','égal à '),
                            ('DIFFERENT','différent de '),
                            ('INF','inférieur à '),
                            ('INFEGAL','inférieur ou égal à '),
                            ('SUP','supérieur à '),
                            ('SUPEGAL','supérieur ou égal à ')],
                 int:[
                            ('EGAL','égal à '),
                            ('DIFFERENT','différent de '),
                            ('INF','inférieur à '),
                            ('INFEGAL','inférieur ou égal à '),
                            ('SUP','supérieur à '),
                            ('SUPEGAL','supérieur ou égal à ')],
                 bool:[
                            ('EGAL','égal à '),
                            ('DIFFERENT','différent de '),],
                 wx.DateTime: [
                            ('EGAL', 'égal à '),
                            ('DIFFERENT', 'différent de '),
                            ('INF', 'avant '),
                            ('INFEGAL', 'avant ou égal à '),
                            ('SUP', 'après '),
                            ('SUPEGAL', 'après ou égal à ')],
                 datetime.date: [
                            ('EGAL', 'égal à '),
                            ('DIFFERENT', 'différent de '),
                            ('INF', 'avant '),
                            ('INFEGAL', 'avant ou égal à '),
                            ('SUP', 'après '),
                            ('SUPEGAL', 'après ou égal à ')],
                 datetime.datetime: [
                            ('EGAL', 'égal à '),
                            ('DIFFERENT', 'différent de '),
                            ('INF', 'avant '),
                            ('INFEGAL', 'avant ou égal à '),
                            ('SUP', 'après '),
                            ('SUPEGAL', 'après ou égal à ')],
                 str:[
                            ('CONTIENT','contient '),
                            ('CONTIENTPAS','ne contient pas '),
                            ('COMMENCE','commence par '),
                            ('DIFFERENT','différent de '),
                            ('EGAL','égal à '),
                            ('PASVIDE',"pas à blanc "),
                            ('VIDE','est à blanc '),
                            ('DANS','dans la liste '),
                            ('INFEGAL', 'inférieur ou égal à '),
                            ('SUPEGAL', 'supérieur ou égal à ')],
}

MATRICE_saisie = {  'nomchapitre': "Choix du filtre",
                    'lignes':   [
                            {'name': 'colonne', 'label': 'Colonne à filtrer :',
                                                'genre': 'Enum', 'value': 1,
                                                'help': 'Choisir par le triangle noir',
                                                'values': [], },
                            {'name': 'action', 'label': 'Type de filtre :',
                                                'genre': 'Enum', 'values': []},
                            {'name': 'valeur', 'label': 'Valeur :',
                                                'genre': 'String', 'value': '',
                                                'help': 'Choisir la valeur'}
                                ]
                  }

MATRICE = {
    ("filtre", "Composition du Filtre"):
        [
            {'name': 'colonne','genre': 'Combo',  'label': 'Colonne à filtrer','value':'',
                     'help': "Le bouton de droite vous permet de créer une nouvelle configuration",},
            {'name': 'action', 'genre': 'Combo', 'label': 'Type de filtre à appliquer','value':'',
             'help': "Le bouton de droite vous permet de créer une nouvelle configuration", },
            {'name': 'valeur', 'genre': 'texte', 'label': 'Valeur','value':'',
             'help': "Le bouton de droite vous permet de créer une nouvelle configuration", },
        ]
        }


class CTRL_property(wxpg.PropertyGrid):
    # grille property affiche les paramètres
    def __init__(self, parent, matrice={}, valeursDefaut={}, enable=True, style=wxpg.PG_SPLITTER_AUTO_CENTER):
        wxpg.PropertyGrid.__init__(self, parent, wx.ID_ANY, style=style)
        self.parent = parent
        self.MinSize = (300,100)
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

    def OnPropGridChange(self, event):
        event.Skip()
        self.parent.OnChoix(False)

    def InitMatrice(self, matrice):
        # Compose la grille de saisie des paramètres selon le dictionnaire matrice
        self.matrice=matrice
        self.dicProperties = {}
        chapitre = self.matrice['nomchapitre']
        if isinstance(chapitre, str):
            self.Append(wxpg.PropertyCategory(chapitre))
        for ligne in self.matrice['lignes']:
            if 'name' in ligne and 'genre' in ligne:
                if not 'label' in ligne : ligne['name'] = None
                if not 'value' in ligne : ligne['value'] = None
                genre, name, label, value = (ligne['genre'],ligne['name'],ligne['label'],ligne['value'])
                genre = genre.lower()
                if not 'values' in ligne: ligne['values'] = []
                """
                if 'values' in ligne and ligne['values']:
                    if ligne['values']:
                        if len(ligne['values']) > 0 and len(ligne['values']) == 0:
                            ligne['values'] = ligne['values']
                    else: ligne['values'] = ligne['values']
                """
                commande = ''
                try:
                    commande = genre
                    if genre in ['enum','combo']:
                        values = list(range(0,len(ligne['values'])))
                        if not isinstance(value,int): value = 0
                        choix = wxpg.PGChoices(ligne['values'], values=values)
                        propriete = wxpg.EnumProperty(label=label,name=name,choices=choix, value = value)

                    elif genre == 'multichoice':
                        propriete = wxpg.MultiChoiceProperty(label, name, choices=ligne['values'], value=value)

                    elif genre in ['bool','check']:
                        wxpg.PG_BOOL_USE_CHECKBOX = 1
                        propriete = wxpg.BoolProperty(label= label, name=name, value= value)
                        propriete.PG_BOOL_USE_CHECKBOX = 1

                    elif genre in ['date','datetime','time']:
                        wxpg.PG_BOOL_USE_CHECKBOX = 1
                        propriete = wxpg.DateProperty(label= label, name=name, value= value)
                        propriete.SetFormat('%d/%m/%Y')
                        propriete.PG_BOOL_USE_CHECKBOX = 1

                    else:
                        commande = "wxpg."  + genre.upper()[:1] + genre.lower()[1:] \
                                            + "Property(label= label, name=name, value=value)"
                        propriete = eval(commande)
                    if 'help' in ligne:
                        propriete.SetHelpString(ligne['help'])
                    self.Append(propriete)
                    self.dicProperties[propriete] = name
                    self.dicProperties[name] = propriete
                except Exception as err:
                    wx.MessageBox(
                    "Echec sur Property de name - value: %s - %s (%s)\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                    %(name,value,type(value),err,commande),
                    'CTRL_property.InitMatrice() : Paramètre ligne indigeste !', wx.OK | wx.ICON_STOP
                    )

    def GetValeurs(self):
        values = self.GetPropertyValues()
        ddDonnees = {}
        for nom, valeur in values.items():
            if self.dicProperties[nom].ClassName == 'wxEnumProperty':
                label = self.dicProperties[nom].GetDisplayedString()
            else:
                label = self.dicProperties[nom].GetValue()
            ddDonnees[nom] = label
        return ddDonnees

class DLG_saisiefiltre(wx.Dialog):
    def __init__(self,parent, *args, **kwds):
        self.parent = parent
        self.listview = kwds.pop('listview',None)
        self.etape=0
        idxDefault = 1
        titre = kwds.pop('titre',"Pas d'argument kwd 'listview' pas de choix de colonnes")
        if self.listview:
            self.lstNomsColonnes = self.listview.lstNomsColonnes
            self.lstCodesColonnes = self.listview.lstCodesColonnes
            self.lstSetterValues = self.listview.lstSetterValues
            titre = "Saisie d'un filtre élaboré"

        wx.Dialog.__init__(self, parent, *args, title=titre, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           **kwds)
        self.marge = 10
        self.btnOK = wx.Button(self, id=wx.ID_ANY, label="OK")
        self.btnAbort = wx.Button(self, id=wx.ID_ANY, label="Abandon")
        self.Bind(wx.EVT_BUTTON, self.OnChoix, self.btnOK)
        self.Bind(wx.EVT_BUTTON, self.OnBtnAbort, self.btnAbort)
        if self.listview:
            dictMatrice = MATRICE_saisie
            dictMatrice['lignes'][0]['values']=self.lstNomsColonnes
            choixactions = self.GetChoixActions(idxDefault)
            values = []
            for (code, label) in choixactions:
                values.append(label)
            dictMatrice['lignes'][1]['values'] = values

            self.ctrl = CTRL_property(self, matrice=dictMatrice)
            self.Sizer()
            self.ctrl.SelectProperty('colonne',True)

    def Sizer(self):
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.ctrl, 1, wx.EXPAND | wx.ALL, self.marge)
        gridpied = wx.FlexGridSizer(1, 2, 0, 0)
        gridpied.Add(self.btnAbort)
        gridpied.Add(self.btnOK)
        sizerbase.Add(gridpied, 0, wx.ALL|wx.ALIGN_RIGHT , self.marge)
        sizerbase.SetSizeHints(self)
        self.SetSizer(sizerbase)
        self.Layout()

    def OnChoix(self,evt):
        values = self.ctrl.GetValeurs()
        nomColonne = values['colonne']
        ix = self.lstNomsColonnes.index(nomColonne)
        self.colonne = ix
        self.codeColonne = self.lstCodesColonnes[ix]
        self.action = values['action']
        self.valeur = values['valeur']

        self.etape = ['colonne','action','valeur'].index(self.ctrl.dicProperties[self.ctrl.GetSelection()])+1
        if self.etape == 1:
            # nouveau choix de colonne, les actions sont différentes
            self.SetActions()
            self.ctrl.SelectProperty('action',focus=True)
        elif self.etape == 2:
            pass
        elif self.etape == 3:
            if self.valeur and evt:
                self.EndModal(wx.ID_OK)
            else: wx.MessageBox("Pas de valeur saisie\n\nvous pouvez cliquer sur 'Abandon'","Saisie d'un filtre")

        else:
            wx.MessageBox('Quelle étape ?', str(values))

    def OnBtnAbort(self,evt):
        self.EndModal(wx.ID_CANCEL)

    def GetChoixActions(self,ixColonne):
        self.tip = type(self.lstSetterValues[ixColonne])
        if not self.tip in CHOIX_FILTRES.keys():
            nomColonne = self.lstNomsColonnes[ixColonne]
            wx.MessageBox("SetterValue de la colonne '%s' non connu de CHOIX_FILTRES"%(nomColonne),
                          "outils.olv.Filter.py")
            self.tip = str
        choixactions = CHOIX_FILTRES[self.tip]
        return choixactions

    def SetActions(self):
        idx = self.colonne
        choixactions = self.GetChoixActions(idx)
        #recomposition des choix d'action
        labels = []
        for (code,label) in choixactions:
            labels.append(label)
        values = list(range(0, len(labels)))
        choix = wxpg.PGChoices(labels, values=values)
        self.ctrl.dicProperties['action'].SetChoices(choix)
        self.Layout()

    def GetDonnees(self):
        codechoix = 'None'
        for (code,label) in CHOIX_FILTRES[self.tip]:
            if label == self.action:
                codechoix = code
                break

        filtre =  {'typeDonnee': self.tip,
                   'criteres': self.valeur,
                   'choix': codechoix,
                   'code': self. codeColonne,
                   'titre': self.codeColonne}
        return filtre


class DLG_LstFiltres(xusp.DLG_listCtrl):
    def __init__(self, parent,listview =None):
        self.listview = listview
        xusp.DLG_listCtrl.__init__( self,None,
                                    dldMatrice=MATRICE,
                                    lddDonnees=[],
                                    lblList="Liste des filtres",
                                    gestionProperty=False,
                                    size=(800, 200),
                                    ctrlSize=(130,30),
                                    txtSize=140,
                                    boxMaxSize=(900,120))
        self.Init()

# pour test -------------------------------------------------
class objet(object):
    def __init__(self):
        self.lstNomsColonnes = ['nbre', 'nom','date']
        self.lstCodesColonnes = ['nbre', 'nom','date']
        self.lstSetterValues = [0, 'bonjour', datetime.date.today()]

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    os.chdir("..")
    os.chdir("..")
    obj = objet()
# Lancement des tests
    dlg = DLG_LstFiltres(None)
    #dlg = DLG_saisiefiltre(None,listview = obj)
    dlg.ShowModal()