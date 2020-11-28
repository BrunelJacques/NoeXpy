#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel
#  MATTHANIA - Projet XPY -Lancement de choix de filtres
#  2020/11/26

import wx
import os
import datetime
import xpy.xUTILS_SaisieParams as xusp
from xpy.outils.ObjectListView import Filter

#**************************  Gestion des filtres à ajouter************************************************************

# Filtres OLV conditions possibles

MATRICE = {
    ("filtre", "Composition du Filtre"):
        [
            {'name': 'colonne','genre': 'Combo',  'label': "Colonne à filtrer",'value':'',
                            'ctrlAction':'parent.OnChoixCol',
                            'txtSize':145,
                            'help': "Choisissez la colonne sur laquelle portera le filtre",},
            {'name': 'choix', 'genre': 'Combo', 'label': "Choix d'action de filtre à appliquer",'value':'',
                            'ctrlAction': 'parent.OnChoixAction,',
                             'txtSize': 145,
                            'help': "Choisissez le type de filtre à appliquer dans la colonne", },
            {'name': 'valeur', 'genre': 'texte', 'label': "Valeur",'value':'',
                            'ctrlAction': 'parent.OnChoixValeur',
                            'txtSize':145,
                            'help': "Valeur proposée à l'action pour le filtre", },
        ]
        }

#------------------------------------------------------------------------------------

class PNL_listeFiltres(xusp.PNL_listCtrl):
    def __init__(self, parent, *args, **kwds):
        kwds['lblList']=''
        kwds['styleLstCtrl'] = wx.LC_REPORT
        xusp.PNL_listCtrl.__init__(self, parent, **kwds)

    # Boutons personnalisable
    def InitLstBtnAction(self,lst):
        lst += self.GetLstBtnAction()
        lst.append(self.AjoutBtnRaz())

class DLG_listeFiltres(xusp.DLG_listCtrl):
    def __init__(self, parent,listview =None,ldFiltres=[]):
        self.listview = listview
        if not hasattr(self.listview,'lstNomsColonnes'):
            lstNoms, lstCodes, lstSet = [],[],[]
            for col in self.listview.columns:
                lstNoms.append(col.title)
                lstCodes.append(col.valueGetter)
                lstSet.append(col.valueSetter)
            self.listview.lstNomsColonnes = lstNoms
            self.listview.lstCodesColonnes = lstCodes
            self.listview.lstSetterValues = lstSet
        self.lstNomsColonnes = self.listview.lstNomsColonnes
        self.lstCodesColonnes = self.listview.lstCodesColonnes
        self.lstSetterValues = self.listview.lstSetterValues
        matrice = MATRICE

        super().__init__(parent,
                                    dldMatrice=matrice,
                                    lddDonnees=[],
                                    lblList="Liste des filtres",
                                    gestionProperty=False,
                                    size=(800, 200),
                                    ctrlSize=(130,30),
                                    txtSize=140,
                                    boxMaxSize=(900,120))

        # alimentation des valeurs premiere combo
        choixColonnes = [x for x in self.lstNomsColonnes if len(x)>2]

        self.Init()
        # alimentation des valeurs possibles premiere combo
        pnlColonne = self.dlgGest.GetPnlCtrl('colonne')
        pnlColonne.SetValues(choixColonnes)
        pnlColonne.SetValue(choixColonnes[0])
        pnlColonne.SetFocus()
        self.SetFiltres(ldFiltres)

    # substitue un pnl spécifique en construisant
    def GetPnl_listCtrl(self,kwdList):
        return  PNL_listeFiltres(self, *self.args, **kwdList)

    # Actions sur les ctrls affichés en gestion de ligne
    def OnChoixCol(self,evt):
        # Choix d'une colonne
        nomCol = evt.EventObject.GetValue()
        ixcol = self.lstNomsColonnes.index(nomCol)
        self.SetChoixActions(ixcol)
        evt.Skip()

    def OnChoixAction(self,evt):
        # choix d'une action
        #pnlValeur = self.dlgGest.GetPnlCtrl('valeur')
        #pnlValeur.SetFocus()
        evt.Skip()

    def OnChoixValeur(self,evt):
        #self.btn.SetFocus()
        evt.Skip()

    def VerifSetterValues(self):
        for ix in range(len(self.lstSetterValues)):
            test = self.GetChoixActions(ix)

    def GetChoixActions(self,ixColonne):
        # récupère le type des valeurs de la colonne par défaut
        if not self.lstSetterValues[ixColonne]:
            self.lstSetterValues[ixColonne] = ''
        self.tip = type(self.lstSetterValues[ixColonne])
        # pour chercher le type d'actions à proposer
        if not self.tip in Filter.CHOIX_FILTRES.keys():
            nomColonne = self.lstNomsColonnes[ixColonne]
            wx.MessageBox("ListeFiltres: SetterValue de la colonne '%s' non connu de CHOIX_FILTRES"%(nomColonne),
                          "outils.olv.Filter.py")
            self.tip = str
        choixactions = Filter.CHOIX_FILTRES[self.tip]
        return choixactions

    def SetChoixActions(self,ixcolonne):
        pnlAction = self.dlgGest.GetPnlCtrl('choix')
        oldval = pnlAction.GetValue()
        # alimentation des valeurs possibles premiere combo
        choixActions = [y for (x,y) in self.GetChoixActions(ixcolonne)]
        pnlAction.SetValues(choixActions)
        if oldval in choixActions:
            pnlAction.SetValue(oldval)
        else: pnlAction.SetValue(choixActions[0])
        #pnlAction.ctrl.SetFocus()

    # Actions sur le listCtrl
    def SetFiltres(self,ldFiltres):

        llFiltres = []
        for x in ldFiltres:
            tip = x['typeDonnee']
            values = Filter.CHOIX_FILTRES[tip]
            choixAction = [x['choix'][1]]
            nomColonne = self.lstNomsColonnes[self.lstCodesColonnes.index(x['code'])]
            llFiltres.append([nomColonne,choixAction,x['critere'],])
        self.pnl.SetValeurs(llFiltres)

    def OnFermer(self, event):
        ldic = self.GetFiltres()
        return self.Close()

    def GetFiltres(self):
        llFiltres = self.pnl.GetValeurs()
        ldFiltres = []
        for  nomColonne, choixAction, valeur in llFiltres:
            ix = self.lstNomsColonnes.index(nomColonne)
            code = self.lstCodesColonnes[ix]
            typeDonnee = self.lstSetterValues[ix]
            choix = Filter.CHOIX_FILTRES[choixAction][typeDonnee][0]
            ldFiltres.append({"code": code, "choix": choix, "criteres": valeur,
                                 "typeDonnee": typeDonnee, "titre": nomColonne})
        return ldFiltres


# pour test -------------------------------------------------
class objet(object):
    def __init__(self):
        self.lstNomsColonnes = ['Nbre', 'Nom_Complet','Date']
        self.lstCodesColonnes = ['nbre', 'nom','date']
        self.lstSetterValues = [0, 'bonjour', datetime.date.today()]

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    os.chdir("..")
    os.chdir("..")
    obj = objet()
# Lancement des tests
    dlg = DLG_listeFiltres(None,listview = obj,
                           ldFiltres=[{'code':'nbre','choix':'EGAL','critere':'12','typeDonnee':float}])
    #dlg = DLG_saisiefiltre(None,listview = obj)
    dlg.ShowModal()