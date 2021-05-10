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
from xpy.outils import xboutons

#**************************  Gestion des filtres à ajouter************************************************************

# Filtres OLV conditions possibles

MATRICE = {
    ("filtre", "Composition du Filtre"):
        [
            {'name': 'nomCol','genre': 'Combo',  'label': "Colonne à filtrer",'value':'',
                            'ctrlAction':'parent.OnChoixCol',
                            'help': "Choisissez la colonne sur laquelle portera le filtre",},
            {'name': 'txtChoix', 'genre': 'Combo', 'label': "Action à appliquer",'value':'',
                            'ctrlAction': 'parent.OnChoixAction,',
                            'help': "Choisissez le type de filtre à appliquer dans la colonne", },
            {'name': 'critere', 'genre': 'texte', 'label': "Valeur filtrée",'value':'',
                            'ctrlAction': 'parent.OnChoixValeur',
                            'help': "Valeur proposée à l'action pour le filtre", },
            {'name': 'code', 'label': "code de la Colonne stocké", 'value': '',},
            {'name': 'choix', 'label': "code du choix stocké", 'value': '',},
            {'name': 'designation', 'label': "Texte complet du filtre", 'value': '',},
        ]
        }
CHAMPS = {'filtre':['nomCol','txtChoix','critere',]}
COLONNES = {'filtre':['designation']}

#====================================================================================

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

        # recherche les liste définissants les colonnes
        if not hasattr(listview,'lstNomsColonnes'):
            lstNoms, lstCodes = [],[]
            for col in listview.columns:
                lstNoms.append(col.title)
                lstCodes.append(col.valueGetter)
            listview.lstNomsColonnes = lstNoms
            listview.lstCodesColonnes = lstCodes
        self.lstNomsColonnes = listview.lstNomsColonnes
        self.lstCodesColonnes = listview.lstCodesColonnes

        # recherche la liste des valeurs par défaut pour déterminer le type de la colonne
        if not hasattr(listview,'lstSetterValues'):
            lstSet = []
            for col in listview.columns:
                lstSet.append(col.valueSetter)
            listview.lstSetterValues = lstSet
        for value in listview.lstSetterValues:
            if value == None:
                ix = listview.lstSetterValues.index(value)
                value = listview.CalcNonNullValue(ix)
                listview.lstSetterValues[ix] = value
        self.lstSetterValues = listview.lstSetterValues

        self.listview = listview

        self.codeBox =[x for (x,y) in MATRICE.keys()][0]
        super().__init__(parent,
                                    dldMatrice=MATRICE,
                                    dlColonnes=COLONNES,
                                    lddDonnees=[],
                                    dlChamps=CHAMPS,
                                    lblList="Liste des filtres",
                                    gestionProperty=False,
                                    boxSize=(350,450),
                                    ctrlSize=(280,30),
                                    txtSize=110)

        # alimentation des valeurs premiere combo
        choixColonnes = [x for x in self.lstNomsColonnes if x != 'null' and len(x)>1]
        self.btn.Destroy()
        self.btn = xboutons.BTN_fermer(self,label="Filtrer")
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)

        self.Init()
        # alimentation des valeurs possibles premiere combo
        pnlColonne = self.dlgGest.GetPnlCtrl('nomCol')
        pnlColonne.Set(choixColonnes)
        pnlColonne.SetValue(choixColonnes[0])
        pnlColonne.SetFocus()
        self.lstChoix = []
        self.lstTxtChoix = []
        self.SetFiltres(ldFiltres)

    # substitue un pnl spécifique en construisant
    def GetPnl_listCtrl(self,kwdList):
        return  PNL_listeFiltres(self, *self.args, **kwdList)

    # Actions sur les ctrls affichés en gestion de ligne-----------------------------
    def OnChoixCol(self,evt):
        # Choix d'une colonne
        nomCol = evt.EventObject.GetValue()
        ixcol = self.lstNomsColonnes.index(nomCol)
        self.SetChoixActions(ixcol)
        evt.Skip()

    def OnChoixAction(self,evt):
        # choix d'une action
        #pnlValeur.SetFocus()
        evt.Skip()

    def OnChoixValeur(self,evt):
        #self.btn.SetFocus()
        evt.Skip()

    def VerifSetterValues(self):
        for ix in range(len(self.lstSetterValues)):
            self.GetChoixActions(ix)

    def SetChoixActions(self,ixcolonne):
        pnlAction = self.dlgGest.GetPnlCtrl('txtChoix')
        oldval = pnlAction.GetValue()
        # alimentation des valeurs possibles selon premiere combo
        self.GetChoixActions(ixcolonne)
        pnlAction.Set(self.lstTxtChoix)
        if oldval in self.lstTxtChoix:
            pnlAction.SetValue(oldval)
        else:
            pnlAction.SetValue(self.lstTxtChoix[0])
            pnlCritere = self.dlgGest.GetPnlCtrl('critere')
            pnlCritere.SetValue('')
            pnlCritere.Refresh()
            pnlAction.Refresh()

    def GetChoixActions(self,ixColonne):
        # retrourne la liste des choix d'actions possibles: selon le type de valeur...
        if self.lstSetterValues[ixColonne] == None:
            self.lstSetterValues[ixColonne] = ''
        typeValeur = type(self.lstSetterValues[ixColonne])
        # ...pour chercher le type d'actions à proposer
        if not typeValeur in Filter.CHOIX_FILTRES.keys():
            nomColonne = self.lstNomsColonnes[ixColonne]
            wx.MessageBox("Le type de variable '%s', setterValue de '%s' absent dans Filter.CHOIX_FILTRES"%(typeValeur,
                                                                                                            nomColonne),
                          "outils.olv.Filter.py")
            typeValeur = str
        self.lstChoix = Filter.CHOIX_FILTRES[typeValeur]
        self.lstTxtChoix = [ Filter.DIC_TXTFILTRES[x] for x in self.lstChoix]
        return

    def Calcul(self,ddDonnees,*args,**kwd):
        # complète les données saisies par la grille avant d'afficher laliste
        if not ddDonnees: return ddDonnees
        for code in ddDonnees:
            dx = ddDonnees[code]
            dx['designation'] = '  '.join(["'%s'" % dx['nomCol'], dx['txtChoix'], "'%s'" % dx['critere']])
            ixcol = self.lstNomsColonnes.index(dx['nomCol'])
            dx['code'] = self.lstCodesColonnes[ixcol]
            dx['choix'] = self.lstChoix[self.lstTxtChoix.index(dx['txtChoix'])]
        return ddDonnees

    # Actions sur le listCtrl ---------------------------------------------------------
    def SetFiltres(self,ldFiltres):
        # transpose les textes et insère la code de la box comme niveau supplémentaire
        for dx in ldFiltres:
            ixcol = self.lstCodesColonnes.index(dx['code'])
            dx['nomCol'] = self.lstNomsColonnes[ixcol]
            self.SetChoixActions(ixcol)
            dx['txtChoix'] = self.lstTxtChoix[self.lstChoix.index(dx['choix'])]
            ddDonnees = {self.codeBox: dx}
            self.SetOneItems(ddDonnees)

    def GetFiltres(self):
        ldFiltres = []
        for dDonnees in self.lddDonnees:
            dx = dDonnees[self.codeBox]
            ixcol = self.lstCodesColonnes.index(dx['code'])
            typeDonnee = type(self.lstSetterValues[ixcol])
            ldFiltres.append({  "code": dx['code'],
                                "choix": dx['choix'],
                                "critere": dx['critere'],
                                "typeDonnee": typeDonnee,
                                "titre": dx['nomCol']})
        return ldFiltres

    def OnFermer(self, event):
        self.EndModal(wx.ID_OK)


# pour test ***************************************************************************
class objet(object):
    def __init__(self):
        self.lstNomsColonnes = ['Nbre', 'Nom_Complet','Date']
        self.lstCodesColonnes = ['nbre', 'nom','date']
        self.lstSetterValues = [0.0, 'bonjour', datetime.date.today()]

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    os.chdir("..")
    os.chdir("..")
    obj = objet()
    # Lancement des tests
    dlg = DLG_listeFiltres(None,listview = obj,
                           ldFiltres=[{'code':'date','choix':'DTEGAL','critere':'10/12/2019','typeDonnee':wx.DateTime},])
    #dlg = DLG_saisiefiltre(None,listview = obj)
    dlg.ShowModal()