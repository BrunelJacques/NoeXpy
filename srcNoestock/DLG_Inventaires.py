#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Gestion des inventaires (dérivé de mouvements)
# Auteur:          Jacques BRUNEL 2021-06
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

# concepts

"""A chaque lancement du programme, un calcul de l'inventaire est lançé, en cumulant les mouvements postérieurs
        à la dernière date d'un inventaire historisé. il met à jour le compteur dans l'article
    Si une correction est apportée elle génère une od mouvement au jour de l'inventaire et coche la ligne.
    en sortie si présence de lignes cochées, l'historisation partielle de l'inventaire est proposée"""

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import xpy.ObjectListView.xGTE as xGTE
import xpy.ObjectListView.xGTR as xGTR
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_DB                   as xdb
from srcNoestock                import DLG_MvtOneArticle
from srcNoestock                import DLG_Articles
from srcNoelite                 import DB_schema
from xpy.ObjectListView.ObjectListView import ColumnDefn
from xpy.outils                 import xformat,xboutons, xdates
#---------------------- Matrices de paramétres -------------------------------------

DIC_BANDEAU = {'titre': "Suivi et ajustement de l'inventaire",
        'texte': "La saisie dans le tableau peut modifier la table article ou créer un mouvement correctif de quantité",
        'hauteur': 20,
        'sizeImage': (60, 60),
        'nomImage':"xpy/Images/80x80/Inventaire.png",
        'bgColor': (220, 250, 220), }

DIC_INFOS = {
        'fournisseur': "Nom du fournisseur à enregistrer dans l'article",
        'magasin': "<F4> Choix d'un magasin",
        'rayon': "<F4> Choix d'un rayon",
        'qteStock': "L'unité est celle  qui sert au décompte du stock\nQuantité en stock au jour de l'inventaire",
        'pxUn': "Prix dans l'inventaire d'une unité sortie",
         }

INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

SAISONS = ['Saison normale', 'Saison haute','Hors saison']

# Choix des params  pour reprise de inventaires antérieurs------------------------------------------------

class CtrlAnterieur(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'label':"Rappeler\nl'antérieur",
               'name':'rappel',
               'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(24,24)),
               'help':"Pour reprendre une saisie antérieurement validée",
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

def GetMatriceAnterieurs(dlg):
    dicBandeau = {'titre': "Rappel d'un inventaire Archivé",
                  'texte': "Attention l'écran précédent reconstituera l'inventaire, comparez les totaux",
                  'hauteur': 15, 'nomImage': "xpy/Images/32x32/Zoom_plus.png",
                  'bgColor':(220, 250, 220),}

    # Composition de la matrice de l'OLV anterieurs, retourne un dictionnaire

    lstChamps = ['IDdate','SUM(qteStock)','SUM(qteStock * prixMoyen)','MAX(dateSaisie)', 'COUNT(IDarticle)']

    lstNomsColonnes = ['date','qtés stocks','montants','calculé Le','nbLignes']

    lstTypes = [ 'date', 'int','float','date', 'int']
    lstCodesColonnes = [xformat.NoAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = [100,100,100,150,100]
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return {
        'table': 'stInventaires',
        'lstColonnes': lstColonnes,
        'lstChamps': lstChamps,
        'groupby': 'IDdate',
        'listeNomsColonnes': lstNomsColonnes,
        'listeCodesColonnes': lstCodesColonnes,
        'getDonnees': nust.SqlTable,
        'dicBandeau': dicBandeau,
        'sortColumnIndex': 1,
        'sensTri': False,
        'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
        'size': (650, 400)}

# Description des paramètres de la gestion des inventaires

MATRICE_PARAMS = {
("param1", "Période"): [
    {'name': 'saison', 'genre': 'Choice', 'label': "Couleur saison",
                    'help': "Le choix de la saison détermine la couleur des lignes selon les minimums prévus par article",
                    'value':0, 'values': SAISONS,
                    'ctrlAction': 'OnSaison',
                    'size':(260,30),
                    'ctrlMaxSize': (370, 40),
                    'txtSize': 105},

    {'name': 'date', 'genre': 'anyctrl', 'label': "Date d'inventaire",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez la date de l'inventaire, "),
                    'ctrl': xdates.CTRL_SaisieDateAnnuel,
                    'value':xformat.DatetimeToStr(datetime.date.today()),
                    'ctrlAction': 'OnDate',
                    'size':(280,30),
                    'ctrlMaxSize': (370, 40),
                    'txtSize': 100,},
],

("param2", "Quantités"): [
    {'name': 'qteZero', 'genre': 'Check', 'label': 'Avec quantités à zéro',
                    'help': "La coche fait apparaître les quantité en stock à zéro",
                    'value':True,
                    'ctrlAction':'OnQte',
                    'size':(250,30),
                    'txtSize': 150,},
    {'name': 'qteMini', 'genre': 'Check', 'label': 'Qtés supérieures au mini',
                    'help': "La coche fait apparaître les quantité supérieures au minim de saison",
                    'value':True,
                    'ctrlAction':'OnQte',
                    'size':(250,30),
                    'txtSize': 150,},
],

("param3", ""): [],

("param4", "Historique"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 20,
                        'ctrlMaxSize':(150,50),
                     'ctrl': CtrlAnterieur,
                     'ctrlAction': 'OnBtnAnterieur',
                     },
    ],
}

def GetDicPnlParams(dlg):
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'dicBandeau':DIC_BANDEAU,
                'lblBox':True,
                'boxesSizes': [(390, 90), (200, 90), None, (160, 90)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"entrees",
            }

def GetBoutons(dlg):
    return  [
        {'name': 'btnOneArticle', 'label': "Mouvements \narticle",
         'help': "Permet de visualiser les mouvements de l'article sélectionné",
         'size': (150, 35), 'onBtn': dlg.OnOneArticle},

        {'name': 'btnArchiver', 'label': "Archiver cet \ninventaire",
            'help': "Confirme et historise les quantités en stock vérifiées ce jour.\nVérifier la cohérence préalablement",
            'size': (150, 35),'onBtn':dlg.OnArchiver},
        {'name': 'btnImp', 'label': "Imprimer\nl'inventaire",
            'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
            'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
    ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    lstCol = [
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter=" ",isSpaceFilling=True,
                       isEditable=False),
            ColumnDefn("Fournisseur", 'left', 110, 'fournisseur', valueSetter=" ",isSpaceFilling=False,
                       isEditable=False),
            ColumnDefn("Magasin", 'left', 90, 'magasin', valueSetter=" ",isSpaceFilling=False,
                       isEditable=False),
            ColumnDefn("Rayon", 'left', 90, 'rayon', valueSetter=" ",isSpaceFilling=False,
                       isEditable=False),
            ColumnDefn("Qté stock", 'right', 80, 'qteStock',  valueSetter=0.0,isSpaceFilling=False,
                                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("Prix Unit Moy", 'right', 85, 'pxUn',  valueSetter=0.0,isSpaceFilling=False,
                                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt TTC", 'right', 100, 'mttTTC',  valueSetter=0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("QteMini", 'right', 80, 'qteMini',  valueSetter=0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Nbre Rations", 'right', 80, 'rations',  valueSetter=0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Last Achat", 'right', 80, 'lastBuy', isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDate,),
            ColumnDefn("Prix", 'left', 50, 'prixActuel', valueSetter= 0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal),
            ColumnDefn("Pb Prix", 'left', 65, 'deltaValo', valueSetter= 0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal),
            ]
    return lstCol

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['qteMvts','artRations','anomalie']

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
        'checkColonne': False,
        'recherche': True,
        'autoAddRow': False,
        'toutCocher':True,
        'toutDecocher':True,
        'couper': False,
        'coller': False,
        'copier':False,
        'supprimer':False,
        'inserer':False,
        'msgIfEmpty': "Aucun article présent (avec les options ci dessus)",
        'dictColFooter': {"magasin": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                        "qteStock": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                        "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                        "rations": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                          },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'minSize': (700, 450),
        'size': (1150, 800),
        'autoSizer': False
        }

    #----------------------- Parties de l'écrans -----------------------------------------

def GetAnterieur(dlg,db=None):
    # retourne un dict de params après lancement d'un tableau de choix de l'existants pour reprise
    dParams = {}
    dicOlv = GetMatriceAnterieurs(dlg)
    dlg = xGTR.DLG_tableau(dlg, dicOlv=dicOlv, db=db)
    ret = dlg.ShowModal()
    if ret == wx.OK and dlg.GetSelection():
        donnees = dlg.GetSelection().donnees
        for ix in range(len(donnees)):
            dParams[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
    dlg.Destroy()
    return dParams

def AnomalieLigne(track):
    # gestion des incohérences bloquant la clôture et affichées en rouge
    anomalie = None
    if not hasattr(track,'deltaQte'):
        track.deltaQte = 0.0
    if track.deltaQte > 0:
        anomalie = True
    if track.deltaValo and track.deltaValo > 10:
        anomalie = True
    if track.qteStock < 0:
        anomalie = True
    track.anomalie = anomalie
    
def CalculeLigne(dlg,track):
    try: qte = float(track.qteStock)
    except: qte = 0.0
    try: pu = float(track.pxUn)
    except: pu = 0.0
    track.mttTTC = round(qte * pu,2)
    track.rations = qte * track.artRations
    deltaQte =  qte - track.qteMvts
    track.deltaQte = deltaQte
    AnomalieLigne(track)    

def ValideLigne(dlg,track):

    CalculeLigne(dlg,track)

    # validation de la ligne de inventaire
    track.valide = True
    track.messageRefus = "Saisie incorrecte\n\n"

    # qte négative
    try:
        track.qteStock = float(track.qteStock)
    except:
        track.qteStock = 0.0
    if track.qteStock < 0.0:
        track.messageRefus += "La quantité ne peut être négative\n"

    # pxUn null
    try:
        track.pxUn = float(track.pxUn)
    except:
        track.pxUn = None
    if not track.pxUn or track.pxUn == 0.0:
        track.messageRefus += "Le pxUnitaire est à zéro\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incorrecte\n\n":
        track.valide = False
    else: track.messageRefus = ""
    return

def RowFormatter(listItem, track):
    if track.anomalie:
        # anomalie rouge / fushia
        listItem.SetTextColour(wx.RED)
        listItem.SetBackgroundColour(wx.Colour(255, 180, 200))
    elif track.rations > 1000:
        # plus de 1000 rations: écrit en BLEU
        listItem.SetTextColour(wx.BLUE)
    elif track.qteMini > 0 and track.qteStock < track.qteMini:
        # niveau de stock  inférieur au minimum saison: fond jaune
        listItem.SetBackgroundColour(wx.Colour(255, 245, 160))
    elif track.qteStock == 0:
        # stock à zero: fond vert
        listItem.SetBackgroundColour(wx.Colour(220, 237, 200))

class PNL_corps(xGTE.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xGTE.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.db = parent.db
        self.lanceur = parent

    def ValideParams(self):
        return

    def OnCtrlV(self,track):
        # avant de coller une track, raz de certains champs et recalcul
        track.IDinventaire = None
        self.ValideLigne(None,track)
        self.SauveLigne(track)

    def OnDelete(self,track):
        nust.DelInventaire(self.parent.db,self.ctrlOlv,track)

    def OnEditStarted(self,code,track=None,editor=None):
        # affichage de l'aide
        if code in DIC_INFOS:
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))

    def OnEditFinishing(self,code=None,value=None,editor=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)

        # Traitement des spécificités selon les zones
        if code == 'qteStock' or code == 'pxUn':
            # force la tentative d'enregistrement même en l'absece de saisie
            track.noSaisie = False

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False
        return value

    def CalculeLigne(self,code,track):
        # Relais de l'appel par par GetDonnnees
        CalculeLigne(self.parent,track)

    def ValideLigne(self,code,track):
        # Relais de l'appel par cellEditor à chaque colonne
        ValideLigne(self.parent,track)

    def SauveLigne(self,track):
        db = self.db
        track.qteMvts += track.deltaQte

        # génération de l'od corrective dans un mouvement
        if not hasattr(track,'IDmouvement'):
            track.IDmouvement = None
            track.qteMvtsOld = 0.0
        lstDonnees = [
            ('IDarticle', track.IDarticle),
            ('prixUnit', track.pxUn),
            ('ordi', self.parent.ordi),
            ('dateSaisie', self.parent.today),
            ('modifiable', 1),]
        if track.IDmouvement :
            qteMvts = track.deltaQte + track.qteMvtsOld
            lstDonnees += [('qte', qteMvts),]
            ret = db.ReqMAJ("stMouvements", lstDonnees,
                            "IDmouvement", track.IDmouvement,
                            mess="DLG_Inventaires.SauveLigne Modif: %d"%track.IDmouvement)
        else:
            qteMvts = track.deltaQte
            ret = 'abort'
            if qteMvts != 0.0:
                od = 'od_in'
                if qteMvts < 0:
                    od = 'od_out'
                lstDonnees += [('origine', od),
                               ('qte', qteMvts),
                               ('date', self.parent.date),
                               ('IDanalytique', '00'),
                               ]
                ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="DLG_Inventaires.SauveLigne Insert")
        if ret == 'ok':
            track.IDmouvement = db.newID
            track.qteMvtsOld = qteMvts

        # MAJ de l'article
        lstDonnees = [('qteStock',track.qteMvts),
                      ('prixMoyen',track.pxUn),
                      ]
        mess = "MAJ article '%s'"%track.IDarticle
        db.ReqMAJ('stArticles',lstDonnees,'IDarticle',track.IDarticle,mess=mess,IDestChaine=True)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDarticle':
            # Choix article
            IDarticle = DLG_Articles.GetOneIDarticle(self.db,self.ctrlOlv.GetObjectAt(row).IDarticle,f4=True)
            #self.ctrlOlv.GetObjectAt(row).IDarticle = IDarticle
            if IDarticle:
                ret = self.OnEditFinishing('IDarticle',IDarticle)

class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,date=None,**kwd):
        kwds = GetDlgOptions(self)
        self.skip = False
        self.infoLue = False
        self.dicParams = GetDicPnlParams(self)
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.checkColonne = self.dicOlv.get('checkColonne',False)
        self.dicOlv['lstCodes'] = xformat.GetCodesColonnes(GetOlvColonnes(self))
        self.dicOlv['db'] = xdb.DB()
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        self.lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION,wx.ART_OTHER,(16, 16)),
                          txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": self.lstInfos}


        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = {}
        kwds['dicPied'] = dicPied
        kwds['db'] = xdb.DB()

        super().__init__(None, **kwds)

        self.Name = "DLG_Inventaires.DLG"
        self.dictUser = xuid.GetDictUtilisateur()
        if self.dictUser:
            nom = (self.dictUser['prenom'][:5].capitalize()
                   + self.dictUser['nom'][:4].upper())
            self.ordi = "%s/%s"%(nom,self.dictUser['userdomain'])
        else:
            self.ordi = xuid.GetNomOrdi()
        self.ordi = self.ordi[:16]
        self.today = datetime.date.today()
        self.date = date
        self.lstSaisons = SAISONS
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()
        # appel des données
        self.oldParams = None
        (self.qteZero, self.qteMini) = (True, True)
        self.OnSaison(None)

    def Init(self):
        self.db = xdb.DB()
        self.db.cursor = self.db.connexion.cursor(buffered=False)
        if not self.date:
            self.date = xformat.DateSqlToDatetime(nust.GetDateLastMvt(self.db))
        self.pnlParams.SetOneValue('date',self.date, codeBox='param1')
        # définition de l'OLV
        self.ctrlOlv = None
        # récup des modesReglements nécessaires pour passer du texte à un ID d'un mode ayant un mot en commun
        for colonne in self.dicOlv['lstColonnes']:
            if 'mode' in colonne.valueGetter:
                choicesMode = colonne.choices
            if 'libelle' in colonne.valueGetter:
                self.libelleDefaut = colonne.valueSetter

        self.pnlOlv = PNL_corps(self, self.dicOlv)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE, self.OnFermer)
        self.InitOlv()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.rowFormatter = RowFormatter
        self.ctrlOlv.InitObjectListView()

    def OnDate(self,event):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.DateFrToDatetime(xformat.FmtDate(saisie))
        if self.date != saisie:
            self.date = saisie
            self.infoLue = False
            self.GetDonnees()
        if event: event.Skip()

    def OnSaison(self,event):
        self.choixSaison = self.pnlParams.GetOneValue('saison', codeBox='param1')
        ctrlQteMini = self.pnlParams.GetPnlCtrl('qteMini','param2')
        self.saisonIx = SAISONS.index(self.choixSaison)
        if self.saisonIx == 2:
            ctrlQteMini.Enable(False)
            ctrlQteMini.SetValue(True)
        else:
            ctrlQteMini.Enable(True)
        self.GetDonnees()
        if event: event.Skip()

    def OnQte(self,event):
        self.qteZero = self.pnlParams.GetOneValue('qteZero', codeBox='param2')
        self.qteMini = self.pnlParams.GetOneValue('qteMini', codeBox='param2')
        self.GetDonnees()
        if event: event.Skip()

    def OnBtnAnterieur(self,event):
        # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # choix d'un lot de lignes définies par des params
        dParams = GetAnterieur(self,db=self.db)
        if not 'date' in dParams: return
        self.pnlParams.SetOneValue('date',dParams['date'],'param1')
        self.OnDate(None)
        if event: event.Skip()

    def GetDonnees(self,dParams=None):
        messInfos = ""
        # test si les paramètres ont changé
        if not dParams:
            dParams = self.pnlParams.GetValues(fmtDD=False)
        idem = True
        if self.oldParams == None :
            idem = False
        else:
            for key in ('origine','date','analytique','fournisseur'):
                if not key in self.oldParams: idem = False
                elif not key in dParams: idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        if idem : return

        attente = wx.BusyInfo("Recherche des données...", None)
        # appel des données de l'Olv principal à éditer
        ixQte = self.dicOlv['lstCodes'].index('qteStock')
        ixMini = self.dicOlv['lstCodes'].index('qteMini')

        def filtreQte(lDonnees):
            if not self.qteZero and lDonnees[ixQte] == 0.0:
                return False
            if (not self.qteMini) and lDonnees[ixMini]:
                if lDonnees[ixQte] >= lDonnees[ixMini]:
                    return False
            return True

        # Appel des données vers SQL
        isConnected = hasattr(self.db.connexion,'connection_id')
        if isConnected and self.db.connexion.connection_id != None:
            # préalable pour éviter une accès db après le db.close() de sortie
            lstDonnees = [x for x in nust.CalculeInventaire(self,dParams) if filtreQte(x)]
        else:
            return
        del attente

        messInfos = ""
        if nust.MouvementsPosterieurs(self):
            messInfos += "Présence de mouvements postérieurs, le stock dans l'article en tient compte\n"

        self.lastInvent = nust.GetDateLastInventaire(self.db)
        if  self.date <= self.lastInvent:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE  # gestion du retour du choix dépot
            messInfos += "Présence d'un inventaire archivé au %s, modifs impossibles\n"%self.lastInvent
        else:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK  # gestion du retour du choix dépot
        if messInfos != "" and not self.infoLue:
            wx.MessageBox(messInfos,'Non bloquant',style=wx.ICON_INFORMATION)
            messInfos = ""
            self.infoLue = True

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()
        nbStNeg = 0
        # les écritures reprises sont censées être valides
        for track in self.ctrlOlv.modelObjects[:-1]:
            track.IDmouvement = None
            if track.qteStock < 0: nbStNeg += 1
        if nbStNeg > 1:
            messInfos += "%d articles ont des stocks négatifs, veuillez saisir des entrées.\n"%nbStNeg
        elif nbStNeg == 1:
            messInfos += "un article a des stocks négatifs, veuillez saisir des entrées par Mouvements articles.\n"
        self.oldParams = None
        if len(messInfos) > 0:
            styleInfos = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER,(16, 16))
        else:
            messInfos = self.lstInfos[1]
            styleInfos = self.lstInfos[0]
        self.pnlPied.SetItemsInfos(messInfos, styleInfos)

    def GetTitreImpression(self):
        date = xformat.DateSqlToFr(self.date)
        mini = ', sans Qtés au dessus du minimum'
        if self.qteMini: mini = ''
        zer = 'sans'
        if self.qteZero: zer = 'avec'
        return "Inventaire STOCKS du %s, %s Qtés à zéro%s."%(date, zer, mini)

    def OkCloture(self):
        nbAnomalies = 0
        for track in self.ctrlOlv:
            if track.anomalie:
                nbAnomalies +=1
        ret = True
        if nbAnomalies >0:
            mess = "Archiver un inventaire incohérent n'est pas possible !\n\n"
            mess += "%d lignes avec anomalies ont un fond rouge.\n"%nbAnomalies
            mess += "Stock fin négatif, Pb de prix > 10€, Pb qtés en stock...\n\n"
            mess += "Consultez 'Mouvements article' et corrigez."
            wx.MessageBox(mess,'Préalable nécessaire',style=wx.OK|wx.ICON_STOP)
            ret = False
        return ret

    def OnOneArticle(self,event):
        selection = self.ctrlOlv.GetSelectedObject()
        if not selection:
            wx.MessageBox("Veuillez sélectionner un article...","pas de sélection",
                          style= wx.ICON_INFORMATION)
            return
        id = self.ctrlOlv.innerList.index(selection)
        dlg = DLG_MvtOneArticle.DLG(article=selection.IDarticle)
        dlg.ShowModal()
        dlg.Destroy()
        self.oldParams = None
        self.db.Close()
        self.db = xdb.DB()
        self.db.cursor = self.db.connexion.cursor(buffered=False)
        self.GetDonnees()
        self.ctrlOlv.MAJ(id)

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

    def OnArchiver(self,event):
        if self.lastInvent == self.date:
            saisie = nust.GetDateSaisieLastInventaire(self.db,self.lastInvent)
            mess = "Cet inventaire a déjà été archivé le %s!"%str(saisie)
            wx.MessageBox(mess,'Impossible',style=wx.ICON_STOP)
            return
        self.ctrlOlv.SortItems(self.compare_items)
        self.ctrlOlv.MAJ()
        if not self.dictUser or self.dictUser['profil'][:5] != 'admin':
            mess = "Accès non autorisé\n\n"
            mess += "Authentifiez-vous comme admin dans le menu d'entrée\n"
            mess += "ou exportez vers Excel par un clic Droit dans le tableau"
            wx.MessageBox(mess,style=wx.ICON_STOP|wx.OK)
            return
        self.pnlParams.SetOneValue('qteZero',False,'param2')
        self.pnlParams.SetOneValue('qteMini',True,'param2')
        self.OnQte(None)
        ret = self.OkCloture()
        if ret:
            mess = "Ok pour archiver l'inventaire!\n\n"
            mess += "Après vous ne pourrez plus modifier les mouvements antérieurs\n"
            mess += "Pensez à faire un export Excel par un clic Gauche ou une édition."
            ret = wx.MessageBox(mess,'confirmez',style=wx.ICON_INFORMATION|wx.YES_NO)
            if ret == wx.YES:
                nust.InsertInventaire(self)

    def OnFermer(self, event):
        #wx.MessageBox("Traitement de sortie")
        if event:
            event.Skip()
        self.db.Close()
        if self.IsModal():
            self.EndModal(wx.ID_CANCEL)
        else:
            self.Close()

    def compare_items(self, item1, item2):
        color1 = self.list_ctrl.GetItemBackgroundColour(item1)
        color2 = self.list_ctrl.GetItemBackgroundColour(item2)
        palette1 = (color1.Red() + color1.Green() + color1.Blue())
        palette2 = (color2.Red() + color2.Green() + color2.Blue())
        return palette1 - palette2

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG()
    dlg.ShowModal()
    app.MainLoop()
