#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------------
# Application :    Noelite, Affichage d'une balance comptable (inachevé)
# Usage : Grille d'affichage des lignes d'une balance
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------------------------------

import wx
import datetime
import xpy.ObjectListView.xGTR as xGTR
import xpy.xUTILS_Identification as nuutil
import srcNoelite.UTILS_Compta          as nucompta
from xpy.ObjectListView.ObjectListView import ColumnDefn
from xpy.outils                 import xformat,xboutons,xdates

#************************************** Paramètres PREMIER ECRAN ******************************************

MODULE = 'DLG_Balance'
TITRE = "BALANCE COMPTABLE non fini!!!!"
INTRO = "La balance appelée provient de la base de donnée comptablilité, pointée par Noelite"

# Info par défaut
INFO_OLV = "Le Double clic sur une ligne permet de sortir"


class CtrlSynchro(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'label':"Actualiser",
               'name':'synchro',
               'image':wx.ArtProvider.GetBitmap(wx.ART_UNDO,size=(24,24)),
               'help':"Pour appeler la balance",
               'size' : (130,40)}
        self.btn = xboutons.BTN_action(self,**kwd)
        self.Sizer()

    def Sizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.btn,1,wx.EXPAND, 0)
        self.SetSizer(box)

    def SetValue(self,value):
        return

    def GetValue(self):
        return None

    def Set(self,values):
        # valeurs multiples
        return


# Description des paramètres à définir en haut d'écran pour PNL_params
MATRICE_PARAMS = {
("param1", "Paramètres période"): [
    {'name': 'periode', 'genre': 'anyctrl', 'label': "",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez début et fin de la période, "),
                    'ctrl': xdates.CTRL_Periode,
                    'size':(200,40),},
    ],
("param2", "Comptes"): [
    {'name': 'bilan', 'genre': 'Check', 'label': 'Avec comptes de bilan',
                    'help': "Pour avoir les comptes des classes 1 à 5, sinon c'est seulement 6 et 7",
                    'value':False,
                    'size':(250,30),
                    'txtSize': 170,
     },
    {'name': 'exercice', 'genre': 'Combo', 'label': 'Exercice archivé',
                    'help': "L'année-mois de clôture permet de situer l'archive",
                    'value':'','values':['2019'],
                    'size':(150,30),
                    'txtSize': 100,}
],

("param4", "Boutons actions"): [
    {'name': 'synchro', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 20,
                        'ctrlMaxSize':(250,50),
                     'ctrl': CtrlSynchro,
                     'ctrlAction': 'OnBtnSynchro',
                     },
    ],
}

# paramètre les options de l'OLV
def GetDicOlv(dlg):
    return {
    'lstColonnes': [
                ColumnDefn("Compte", 'centre', 90, 'IDcompte'),
                ColumnDefn("Section", 'left', 60, 'section',valueSetter=''),
                ColumnDefn("Libellé du compte", 'left', 150, 'label', isSpaceFilling=True),
                ColumnDefn("Débits", 'right', 90, 'debit', valueSetter=0,stringConverter=xformat.FmtDecimal),
                ColumnDefn("Crédits", 'right', 90, 'credit', valueSetter=0,stringConverter=xformat.FmtDecimal),
                ColumnDefn("Solde", 'right', 90, 'solde', valueSetter=0,stringConverter=xformat.FmtDecimal),
                ],
    'dictColFooter': {'label': {"mode": "nombre", "alignement": wx.ALIGN_CENTER,'pluriel':"lignes"},
                      'debit': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'credit': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'solde': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      },
    'getDonnees': dlg.GetDonnees,
    'lstChamps': ['Numero','Intitule','Debit','Credit'],
    'minSize': (600,200),
    'sortColumnIndex':0,
    'sortAscending':True,
    'checkColonne': False,
    'recherche': True,
    'editMode': False,
    'msgIfEmpty':"Aucune écriture trouvée !",
    }

def GetDicPnlParams():
    dicBandeau = {'titre': TITRE, 'texte': INTRO, 'hauteur': 20,
                  'nomImage': "xpy/Images/48x48/Matth.png",
                  'sizeImage': (40, 40)}
    return {
                'bandeau':dicBandeau,
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':None,
                'boxesSizes': [],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"compta",
            }


def SqlBalance(dlg,dicParams):
    compta = nucompta.Compta(dlg.ctrlOlv,exercice=dicParams['exercice'])
    annee = dicParams['exercice']
    if len(annee) == 4:
        n1 = str(int(annee)-1)
        debut = annee +"-10-01"
        fin = n1 + "09-30"
    else:
        debut = "2019-10-01"
        fin = "2020-09-30"
    return compta.GetBalance(debut=debut,fin=fin)

#*********************** Parties de l'écran d'affichage de la liste *******************

class DLG_balance(xGTR.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,parent):
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        self.dicParams = GetDicPnlParams()
        super().__init__(self,dicParams=self.dicParams,dicOlv=GetDicOlv(self))

    def OnBtnSynchro(self,event):
        self.ctrlOlv.dicOptions = self.pnlParams.GetValues(False)
        self.ctrlOlv.MAJ()
        event.Skip

    def GetDonnees(self,*args,**kwds):
        if hasattr(self,'ctrlOlv'):
            return SqlBalance(self,self.dicParams)
        else: return []


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App()
    os.chdir("..")
    frame_1 = wx.Frame()
    app.SetTopWindow(frame_1)
    frame_1.dlg = DLG_balance(frame_1)
    frame_1.dlg.ShowModal()
    app.MainLoop()
