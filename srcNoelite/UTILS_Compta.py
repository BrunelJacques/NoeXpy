# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet Noelite, outils pour compta
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import datetime
import xpy.outils.xshelve    as xshelve
import xpy.xGestionConfig   as xgc
import xpy.xUTILS_DB       as xdb
import xpy.ObjectListView.xGTR as xGTR
from xpy.outils             import xexport,xformat

# Paramétrage des accès aux bases de données, les 'select' de _COMPTAS doivent respecter 'lstChamps' de  _COMPTES
MATRICE_COMPTAS = {
    # noegest pointe une table 'cptComptes' directement importée de quadra compta dans la base noethys,
    # en attendant de se greffer sur une autre 'compta_comptes_comptables' est l'officiel noethys pour les seuls comptes généraux
    'noegest': {
        'fournisseurs': {'select': 'IDcompte,cle,libelle',
                         'from': 'cptaComptes',
                         'where': "Type = 'F'",
                         'filtre': "AND (IDcompte like \"%xxx%\" OR cle like \"%xxx%\" OR libelle like \"%xxx%\")"},
        'clients': {'select': 'IDcompte,cle,libelle',
                    'from': 'cptaComptes',
                    'where': "Type = 'C'",
                    'filtre': "AND (IDcompte like \"%xxx%\" OR cle like \"%xxx%\" OR libelle like \"%xxx%\")"},
        'generaux': {'select': 'IDcompte,cle,libelle',
                     'from': 'cptaComptes',
                     'where': "Type = 'G'",
                     'filtre': "AND (IDcompte like \"%xxx%\" OR cle like \"%xxx%\" OR libelle like \"%xxx%\")"},
        'cpt3car': {'select': 'LEFT (IDcompte,3), MIN(cle),MIN(libelle)',
                    'from': 'cptaComptes',
                    'where': "Type = 'G'",
                    'filtre': "AND (IDcompte like \"%xxx%\" OR cle like \"%xxx%\" OR libelle like \"%xxx%\")",
                    'group by': "LEFT(IDcompte,3)"},
        'journaux': {'select': 'IDjournal,libelle,contrepartie,type',
                     'from': ' cptaJournaux',
                     'where': "type = 'TR'",
                     'filtre': "AND (IDjournal like \"%xxx%\" OR libelle like \"%xxx%\")"},
        'journOD': {'select': 'IDjournal,libelle,contrepartie,type',
                    'from': ' cptaJournaux',
                    'where': "type = 'OD'",
                    'filtre': "AND (code like \"%xxx%\" OR libelle like \"%xxx%\")"},
    },
    'quadra': {
                'fournisseurs':{'select':'Numero,CleDeux,Intitule',
                                'from'  :'Comptes',
                                'where' :"Type = 'F'",
                                'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                'clients':  {'select': 'Numero,CleDeux,Intitule',
                                'from'  : 'Comptes',
                                'where' : "Type = 'C'",
                                'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                'generaux': {'select': 'Numero,CleDeux,Intitule',
                                'from'  :'Comptes',
                                'where' : "Type = 'G'",
                                'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                'cpt3car': {'select': 'LEFT (Numero,3), MIN(CleDeux),MIN(Intitule)',
                                'from'  :'Comptes',
                                'where' : "Type = 'G'",
                                'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")",
                                'group by':"LEFT(Numero,3)"},
                'journaux': {'select': 'Code,Libelle,CompteContrepartie,TypeJournal',
                                'from':' Journaux',
                                'where': "TypeJournal = 'T'",
                                'filtre':"AND (Code like \"%xxx%\" OR Libelle like \"%xxx%\")"},
                'journOD': {'select': 'Code,Libelle,CompteContrepartie,TypeJournal',
                             'from': ' Journaux',
                             'where': "TypeJournal = 'O'",
                             'filtre': "AND (Code like \"%xxx%\" OR Libelle like \"%xxx%\")"},
                },
        }

MATRICE_COMPTES = {
    'lstChamps': ['ID','cle','libelle'],
    'lstNomsColonnes': ["numero","cle","libelle"],
    'lstTypes': ['VARCHAR(10)','VARCHAR(30)','VARCHAR(130)'],
    'lstValDefColonnes':['','',''],
    'lstLargeurColonnes':[90,100,-1]
    }

MATRICE_JOURNAUX = {
    'lstChamps': ['ID','libelle','contrepartie','type'],
    'lstNomsColonnes': ["code","libelle",'contrepartie','type'],
    'lstTypes': ['INTEGER','VARCHAR(130)','VARCHAR(60)','VARCHAR(10)'],
    'lstValDefColonnes':[1,'','','',''],
    'lstLargeurColonnes':[90,-1,100,60]
    }

#FORMATS_EXPORT
"""les formats d'exports sont décrits plus bas, en dessous de la définition des fonctions d'exports,
    car ils les appellent ces fonctions qui doivent donc êtres déclarées avant dans le module"""

# Transposition des valeurs Export pour compta standard, gérer chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncExp(dicParams,donnees,champsIn,champsOut):
    """ 'in' est l'OLV enrichi des champs obligatoires, 'out' est le fichier de sortie
        obligatoires dans champsIN : date,compte,piece,libelle,montant,
                        facultatifs: contrepartie (qui aura priorité sur la valeur dans dicParams)
        dans dicParams sont facultatifs: journal, contrepartie, typepiece
    """
    lstOut = []
    #formatOut = dicParams['fichiers']['formatexp']
    typepiece = "B"  # cas par défaut B comme carte Bancaire
    journal = 'OD'
    contrepartie = '58999'
    if 'typepiece' in dicParams['p_export']:
        typepiece = dicParams['p_export']['typepiece']
    if 'journal' in dicParams['p_compta']:
        journal = dicParams['p_compta']['journal']
    if 'contrepartie' in dicParams['p_export']:
        contrepartie = dicParams['p_export']['contrepartie']

    # déroulé des lignes puis des champs out
    for ligne in donnees:
        ligneOut = []
        montant = ligne[champsIn.index('montant')]
        if isinstance(montant, str):
            montant = float(montant.replace(",", "."))
        elif isinstance(montant,(int,float)):
            montant = float(montant)
        else: montant = 0.0
        for champ in champsOut:
            if champ in champsIn:
                valeur = ligne[champsIn.index(champ)]
            else: valeur = ''
            # composition des champs sortie
            if champ    == 'journal':   valeur = journal
            elif champ  == 'compte':
                if not valeur or valeur == '' : valeur = '471'
            elif champ  == 'date':
                if isinstance(valeur,str):
                    valeur = xformat.DateToDatetime(valeur)
            elif champ  == 'typepiece':
                valeur = typepiece
            elif champ  == 'contrepartie':
                if 'contrepartie' in champsIn:
                    valeur = ligne[champsIn.index('contrepartie')]
                else:
                    valeur = contrepartie
            elif champ  == 'devise': valeur = 'EUR'
            elif champ  == 'sens':
                if montant >=0: valeur = 'C'
                else: valeur = 'D'
            elif champ  == 'valeur': valeur = abs(montant)
            elif champ == 'valeur00':valeur = abs(montant * 100)
            elif champ  == 'debit':
                if montant < 0.0: valeur = -montant
                else: valeur = 0.0
            elif champ  == 'credit':
                if montant >= 0.0: valeur = montant
                else: valeur = 0.0
            ligneOut.append(valeur)
        lstOut.append(ligneOut)
        # ajout de la contrepartie banque
        ligneBanque = [x for x in ligneOut]
        ligneBanque[champsOut.index('contrepartie')] = ligneOut[champsOut.index('compte')]
        if 'contrepartie' in champsIn:
            ligneBanque[champsOut.index('compte')] = ligne[champsIn.index('contrepartie')]
        else:
            ligneBanque[champsOut.index('compte')] = dicParams['p_export']['contrepartie']
        if 'debit' in champsOut:
            ligneBanque[champsOut.index('debit')]    = ligneOut[champsOut.index('credit')]
            ligneBanque[champsOut.index('credit')]    = ligneOut[champsOut.index('debit')]
        elif 'sens' in champsOut:
            ix = champsOut.index('sens')
            if ligneOut[ix] == 'D': ligneBanque[ix] = 'C'
            elif ligneOut[ix] == 'C': ligneBanque[ix] = 'D'
        lstOut.append(ligneBanque)
    return lstOut

def ExportExcel(formatExp, lstValeurs):
    matrice = FORMATS_EXPORT[formatExp]['matrice']
    champsOut   = [x['code'] for x in matrice]
    widths      = [x['lg'] for x in matrice]
    lstColonnes = [[x, None, widths[champsOut.index(x)], x] for x in champsOut]
    # envois dans un fichier excel
    return xexport.ExportExcel(lstColonnes=lstColonnes,
                        listeValeurs=lstValeurs,
                        titre=formatExp)

def ExportQuadra(formatExp, lstValeurs):
    matrice = FORMATS_EXPORT[formatExp]['matrice']
    # envois dans un fichier texte
    return xexport.ExportLgFixe(nomfic=formatExp+".txt",matrice=matrice,valeurs=lstValeurs)

FORMATS_EXPORT = {
            "Excel façon Quadra":{
                            'fonction':ComposeFuncExp,
                            'matrice':[
                                {'code':'journal',   'lg': 40,},
                                {'code':'date',      'lg': 80,},
                                {'code':'compte',    'lg': 60,},
                                {'code':'typepiece', 'lg': 25,},
                                {'code':'libelle',   'lg': 240,},
                                {'code':'debit',     'lg': 60,},
                                {'code':'credit',    'lg': 60,},
                                {'code':'noPiece',   'lg': 60,},
                                {'code':'contrepartie','lg': 60,},
                                {'code':'qte',      'lg': 60,},
                                {'code':'lettrage', 'lg': 40,},
                                {'code':'echeance', 'lg': 80,},
                            ],
                            'genere':ExportExcel,
                            },
            "ASCII pour Quadra": {
                            'fonction':ComposeFuncExp,
                            'matrice':[
                              {'code': 'typ',     'cat': 'const', 'lg': 1, 'constante': "M"},
                              {'code': 'compte',  'cat': str, 'lg': 8, 'align': "<"},
                              {'code': 'journal',      'cat': str, 'lg': 2, 'align': "<"},
                              {'code': 'fol',     'cat': int, 'lg': 3, 'fmt':"{0:03.0f}"},
                              {'code': 'date',    'cat': datetime.date, 'lg':6,'fmt': "{:%d%m%y}" },
                              {'code': 'typepiece',     'cat': str, 'lg': 1},
                              {'code': 'fil',    'cat': str, 'lg': 20, 'align': ">"},
                              {'code': 'sens',   'cat': str, 'lg': 1, 'align': "<"},
                              {'code': 'valeur00','cat': float, 'lg': 13,'fmt':"{0:+013.0f}"},
                              {'code': 'contrepartie','cat': str, 'lg': 8, 'align': "<"},
                              {'code': 'echeance','cat': datetime.date, 'lg':6,'fmt': "{%d%m%y}" },
                              {'code': 'lettrage','cat': str, 'lg': 2, 'align': "<"},
                              {'code': 'fil',    'cat': str, 'lg': 3, 'align': ">"},
                              {'code': 'fil',    'cat': str, 'lg': 15, 'align': ">"},
                              {'code': 'qte',    'cat': float, 'lg': 10,'fmt':"{0:10.2f}"},
                              {'code': 'fil',    'cat': str, 'lg': 8, 'align': ">"},
                              {'code': 'devise', 'cat': str, 'lg': 3, 'align': "<"},
                              {'code': 'journal','cat': str, 'lg': 3, 'align': "<"},
                              {'code': 'fil',    'cat': str, 'lg': 3, 'align': "<"},
                              {'code': 'libelle','cat': str, 'lg': 30, 'align': "<"},
                              {'code': 'fil',    'cat': str, 'lg': 2, 'align': "<"},
                              {'code': 'noPiece','cat': str, 'lg': 10, 'align': "<"},
                              {'code': 'fil',    'cat': str, 'lg': 73, 'align': "<"},
                            ],
                            'genere':ExportQuadra},
            "Excel façon Noegest":{
                            'fonction':ComposeFuncExp,
                            'matrice':[
                                {'code':'journal',   'lg': 40,},
                                {'code':'date',      'lg': 80,},
                                {'code':'compte',    'lg': 60,},
                                {'code':'typepiece', 'lg': 25,},
                                {'code':'libelle',   'lg': 240,},
                                {'code':'debit',     'lg': 60,},
                                {'code':'credit',    'lg': 60,},
                                {'code':'noPiece',    'lg': 60,},
                                {'code':'contrepartie','lg': 60,},
                                {'code':'qte',        'lg': 60,},
                                {'code':'lettrage',   'lg': 40,},
                                {'code':'echeance',   'lg': 80,},
                            ],
                            'genere':ExportExcel},
            }

def GetLstComptas():
    lstCpta = [x.capitalize() for x in MATRICE_COMPTAS.keys()]
    return lstCpta

def GetIDcomptaDefaut():
    # recherche le nom de la compta pointée par la gestion des bases et proposée par défaut
    paramFile = xshelve.ParamFile(nomFichier="Config")
    IDcompta = None
    dicConfig = paramFile.GetDict(None, 'CONFIGS')
    if 'choixConfigs' in dicConfig:
        if 'Noelite' in dicConfig['choixConfig']:
            if 'compta.config' in dicConfig['choixConfig']['compta.config']:
                IDcompta = dicConfig['choixConfig']['compta.config']['compta.config']
    return IDcompta

class Export(object):
    # Génération d'un fichier d'export
    def __init__(self,parent,compta):
        self.parent = parent
        try:
            self.nomCompta = compta.nomCompta
        except: self.nomCompta = "ecritures_compta"

    def Exporte(self,dicParams={},donnees=[],champsIn=[]):
        # génération du fichier
        if not 'p_export' in dicParams.keys():
            dicParams['p_export'] = dicParams['compta']
            dicParams['p_compta'] = dicParams['compta']

        formatExp = dicParams['p_export']['formatexp']
        champsOut = [x['code'] for x in FORMATS_EXPORT[formatExp]['matrice']]

        # transposition des lignes par l'appel de la fonction 'ComposeFuncExp'
        lstValeurs = FORMATS_EXPORT[formatExp]['fonction'](dicParams,
                                                            donnees,
                                                            champsIn,
                                                            champsOut)
        # appel de la fonction génération fichier
        ret = FORMATS_EXPORT[formatExp]['genere'](formatExp,lstValeurs)

        # mise à jour du dernier numero de pièce affiché avant d'être sauvegardé
        if 'noPiece' in champsOut and 'lastPiece' in dicParams['p_export']:
            ixp = champsOut.index('noPiece')
            lastPiece = lstValeurs[-1][ixp]
            box = self.parent.pnlParams.GetBox('p_export')
            box.SetOneValue('compta.lastpiece',lastPiece)
        return ret

# ouvre la base de donnée compta et interagit
class Compta(object):
    def __init__(self,parent,nomCompta=None,exercice=None):
        ok = True
        if not nomCompta or len(nomCompta) == 0:
            ok = False
        self.table = None
        self.db = None
        self.nomCompta = nomCompta
        if exercice and len(exercice) == 4:
            self.exercice = exercice
        else: 
            self.exercice = None
        if nomCompta in MATRICE_COMPTAS:
            self.dicTables = MATRICE_COMPTAS[nomCompta]
        else:
            if nomCompta:
                wx.MessageBox("Les formats de la compta %s , ne sont pas  paramétrés dans le programme"%nomCompta)
            ok = False
            
        if ok:
            cfgCompta = self.GetConfig(nomCompta)        
            self.db = self.DB(cfgCompta)
        else: self.db = None

    def GetConfig(self,nomCompta):
        # recherche des configuration d'accès aux base de données clé 'db_reseau'
        paramFile = xshelve.ParamFile(nomFichier="Config")

        self.IDconfigCpta = None
        dicConfig = paramFile.GetDict(None, 'CONFIGS')
        IDconfig = None
        cfgCompta = None
        if 'choixConfigs' in dicConfig:
            if 'Noelite' in dicConfig['choixConfigs']:
                if 'Compta.config' in dicConfig['choixConfigs']['Noelite']:
                    IDconfig = dicConfig['choixConfigs']['Noelite']['Compta.config']
        if not IDconfig:
            mess = "Aucune base de compta n'est définie par la gestion du menu_fichier!"
            wx.MessageBox(mess,style=wx.ID_ABORT)
            return
        # transposition entre les noms de configs et les possibilités de la matrice
        if nomCompta == 'quadra' and 'quad' in IDconfig.lower():
            # quadratus était par défaut
            cfgCompta = xgc.GetDdConfig(dicConfig,IDconfig)['db_reseau']
        elif nomCompta == 'noegest' and not 'quad' in IDconfig.lower():
            # on prend la compta par défaut
            cfgCompta = xgc.GetDdConfig(dicConfig,IDconfig)['db_reseau']
        else:
            # on tente une recherche directe dans la liste de configs présentes
            lstConfigs = xgc.GetLstConfigs(dicConfig)
            lstConfigsOK = lstConfigs[1]
            lstNoms = [x['db_reseau']['ID'] for x in lstConfigsOK]
            if nomCompta in lstNoms:
                ix = lstNoms.index(nomCompta)
                IDconfig = lstConfigsOK[ix]['db_reseau']['ID']
                cfgCompta = xgc.GetDdConfig(dicConfig,IDconfig)['db_reseau']
        if not cfgCompta:
            wx.MessageBox("Impossible de trouver la configuration correspondant à %s"%nomCompta)
        return cfgCompta

    # connecteur à la base compta
    def DB(self,cfgCompta):
        if self.db and self.db.echec:
            self.db = None

        if cfgCompta:
            # test de l'accès
            db = xdb.DB(config=cfgCompta)
            db.Close()

        if self.exercice:
            if 'quadra' in cfgCompta['serveur'].lower():
                annee = self.exercice
                cfgCompta['serveur'] = cfgCompta['serveur'].replace("\\DC\\","\\DA%s\\"%annee)
        if cfgCompta:
            return xdb.DB(config=cfgCompta,mute=True)

    def ComposeReq(self,table,where='',filtre=''):
        # Création d'une requête avec variables personnalisant les params par défaut
        req = ''
        dicTable = self.dicTables[table]
        for segment in ('select','from'):
            if segment in dicTable.keys():
                req += segment.upper() + " %s"%dicTable[segment] +"\n"

        # clause WHERE
        if len(where) == 0:
            # dérogation possible au paramètre par défaut pour where dans filtre
            where = dicTable['where']
        if len(where) > 0:
            req += "WHERE %s"%where

        # filtre: complement de clause where pour filtrer par variable
        txtfiltre = ''
        # pour personnaliser txtfiltre, enrichir where et laisser filtre à blanc
        if len(filtre) > 0:
            # le filtre reçu n'est qu'un mot injecté dans le param txtfiltre
            if 'filtre' in dicTable.keys():
                txtfiltre = dicTable['filtre']
            txtfiltre = txtfiltre.replace("xxx","%s"%filtre)
            # ajout du filtre dans la requête
            req += "%s\n"%txtfiltre

        if 'group by' in dicTable.keys():
            req += "GROUP BY %s" % dicTable['group by'] + "\n"
        return req

    # Appel d'une liste extraite de la base de donnée pour table préalablement renseignée
    def GetDonnees(self,**kwds):
        table = kwds.pop('table','')
        where = kwds.pop('where','')
        filtre = kwds.pop('filtre','')

        if table == '': table = self.table
        if not table or table == '':
            wx.MessageBox("UTILS_Compta: Manque l'info de la table à interroger...")
            return []
        # Appel des données, le select et group by sera par défaut non personnalisable
        donnees = []
        req = self.ComposeReq(table,where,filtre)
        ret = self.db.ExecuterReq(req,mess="UTILS_Compta.GetDonnees %s"%table)
        if ret == "ok":
            donnees = self.db.ResultatReq()
        return donnees

    # Appel d'une balance de la base de donnée compta
    def GetBalance(self,champs='Numero,Intitule,Debit,Credit',debut=None,fin=None):
        wherePeriode = ""
        if debut and fin and False:
            wherePeriode = " AND ((Ecritures.PeriodeEcriture) Between '%s' And '%s')" % (debut, fin)
        whereBilan = ""
        whereBilan = " AND (Comptes.Numero  >= '6')"
        donnees = []
        req = """
            SELECT %s
            FROM Comptes
            WHERE ((Comptes.Type ="G") %s %s)
            ;"""%(champs,wherePeriode,whereBilan)
        ret = self.db.ExecuterReq(req,mess="UTILS_Compta.GetBalance")
        if ret == "ok":
            donnees = self.db.ResultatReq()
        # ajout du solde et filtrage des comptes à zéro
        donnees = [[x[0],x[0][3:5],x[1],x[2],x[3],x[2]-x[3]] for x in donnees if (x[2]-x[3]) != 0.0]
        return donnees

    # Constitue la liste des journaux si la compta est en ligne
    def GetJournaux(self,table='journaux'):
        if not self.db: return []
        return self.GetDonnees(table=table)

    # Composition du dic de tous les paramètres à fournir pour l'OLV
    def GetDicOlv(self,table):
        nature = None
        matrice = None
        if table in ('fournisseurs','clients','generaux','cpt3car'):
            nature = 'compte'
            matrice = MATRICE_COMPTES
        elif table in ('journaux','journOD'):
            nature = 'journal'
            matrice = MATRICE_JOURNAUX
        else: raise Exception("la table '%s' n'est pas trouvée dans UTILS_Compta"%table)
        dicBandeau = {'titre':"Choix d'un %s"%nature,
                      'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                      'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}
        # Composition de la matrice de l'OLV familles, retourne un dictionnaire    
        lstChamps =         matrice['lstChamps']
        lstNomsColonnes =   matrice['lstNomsColonnes']
        lstCodesColonnes =  [xformat.NoAccents(x) for x in lstNomsColonnes]
        lstValDefColonnes =   matrice['lstValDefColonnes']
        lstLargeurColonnes = matrice['lstLargeurColonnes']
        lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return   {
                    'lstColonnes': lstColonnes,
                    'lstChamps':lstChamps,
                    'listeNomsColonnes':lstNomsColonnes,
                    'listeCodesColonnes':lstCodesColonnes,
                    'getDonnees': self.GetDonnees,
                    'dicBandeau': dicBandeau,
                    'sortColumnIndex': 2,
                    'size' : (800,600),
                    'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                    }

    # Lance un DLG pour le choix d'un enregistrement dans une liste
    def ChoisirItem(self,table='generaux',filtre=''):
        self.table = table
        dicOlv = self.GetDicOlv(table)
        dlg = xGTR.DLG_tableau(None, dicOlv=dicOlv)
        if len(filtre)>0:
            dlg.ctrlOlv.Parent.barreRecherche.SetValue(filtre)
            dlg.ctrlOlv.Filtrer(filtre)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            item = dlg.GetSelection().donnees
        else:
            item = None
        dlg.Destroy()
        return item

    def FiltreSurCle(self, text, lstItems):
        # on recherche un text entier dans des parties d'items, pour discriminer
        lstRetour = []
        for item in lstItems:
            for champvalue in item:
                # un de ces champs sera la clé, les autres peuvent matcher aussi
                txttest = text
                if not " " in champvalue:
                    # une clé d'appel n'a pas d'espace
                    txttest = xformat.Supprespaces(text,camelCase=False)
                # recherche du champ dans le text
                if champvalue.upper() in txttest:
                    if not item in lstRetour:
                        lstRetour.append(item)
                    break
        return lstRetour

    # Recherche automatique d'un mot alpha dans une table, retour d'un seul item
    def GetOneByMots(self,table='clients',text=None):
        self.table = table
        self.filtreTest = ""
        # formatage du text
        text = xformat.NoPunctuation(text)
        text = xformat.NoChiffres(text)
        text = text.upper()
        lstMots = text.split(' ')
        lstTplMots = [(len(x),x) for x in lstMots if len(x) >= 3]
        lstTplMots.sort(reverse=True)
        lstMots = [y for (x,y) in lstTplMots]

        # fonction recherche un seul item contenant un mot limité à nb de caractères puis décroisant
        def testMatch(mot,lg=10,mini=3):
            lstItems = []
            match = False
            lgrad = 0
            # recherche des items contenant le début du mot en diminuant sa longueur
            for lgrad in range(lg,mini-1,-1):
                lstItems = self.GetDonnees(table=table,filtre=mot[:lgrad])
                if len(lstItems) == 0 : continue
                else:
                    nb = len(lstItems)
                    # discriminer par clé ou libellé dans le texte
                    lstItems = self.FiltreSurCle(text, lstItems)

                    if len(lstItems) == 0: continue
                    if len(lstItems) == 1:
                        match = True
                        break

            # validation par vérif présence du mot[:7] dans un des champs
            if match:
                match = False
                for champ in lstItems[0]:
                    # test la presence du mot dans un champ
                    if len(mot) >= 7 and mot[:7] in champ:
                        # le mot long et entier est présent
                        match = True
                        break
                    elif len(mot) == lgrad and mot + " " in champ:
                        # mot plus court présent en entier dans le champ
                        match = True
                        break
                    elif " " + mot == " "+champ[-len(mot):]:
                        # le mot entier termine le champ
                        match = True
                        break
                    elif mot == champ:
                        # le mot occupe tout le champ
                        match = True
                        break
            if not match:
                lstItems = []
            return match, lstItems,lgrad

        # appel par mot de longeur décroissante
        item = None
        for mot in lstMots:
            match, lstItems, lgtest2 = testMatch(mot,lg=min(10,len(mot)))
            if len(lstItems)>0 and lgtest2 + 1 > len(mot):
                motTest = mot[:(lgtest2 +1)]
                self.filtreTest = motTest
            if match:
                item = lstItems[0]
                break
        return item

    # Recherche automatique d'un item dans une table
    def GetOneAuto(self,table='clients',filtre='',lib=None):
        self.table = table
        # la recherche peut se faire sur un filtre qui est un libellé complet
        if lib:
            # on testera la clé d'appel dans le lib d'origine compacté
            filtre = lib
            lib = lib.replace(' ','')
        # formatage du filtre
        filtre = filtre.replace(',','')
        lstMots = filtre.split(' ')

        # fonction recherche un seul item contenant un mot sur différents champs
        def testMatch(mot,lg=10,mini=3):
            lstTemp = []
            match = False
            lgrad = 0
            for lgtest in range(lg,mini-1,-1):
                lstTemp = self.GetDonnees(filtre=mot[:lgtest],table=table)
                # élimine les cas où la cle d'appel du compte n'est pas présente dans le libelle complet
                if lib:
                    lstTemp = [x for x in lstTemp if x[1] and len(x[1]) > 2 and x[1] in lib]
                if len(lstTemp) == 0 : continue
                elif len(lstTemp) == 1 :
                    match = True
                    lgrad = lgtest
                    break
                elif len(lstTemp) == 2:
                    # teste l'identité des libellés pos(2) pour comptes en double
                    if lstTemp[0][2] == lstTemp[1][2]:
                        lstTemp = lstTemp[1:2]
                        match = True
                        lgrad = lgtest
                        break
                else:
                    break
            return match, lstTemp,lgrad

        # appel avec 10 caractères du filtre puis réduit jusqu'a trouver au moins un item (cible clé d'apppel)
        lgMotUn = len(lstMots[0])
        match,lstItems,lgtest = testMatch(filtre.replace(' ',''),lg=10,mini=min(4,lgMotUn))
        if not match:
            lgtest = lgMotUn
        motTest = filtre.replace(' ','')[:lgtest+1]
        # deuxième tentative avec chaque mot du filtre de + de 3 car (cible libellé)
        if not match:
            lstIx = []
            # calcul des longeurs pour traitement par lg décroissante item 'xx0yy' xx = lg yy=ix
            for ix in range(len(lstMots)):
                if len(lstMots[ix]) <= 3: continue
                lstIx.append(1000*len(lstMots[ix])+ix)
            # appel par mot de longeur décroissante
            for pointeur in sorted(lstIx,reverse=True):
                ix = pointeur%1000
                lgMot = len(lstMots[ix])
                match, lstItems, lgtest2 = testMatch(lstMots[ix],lg=min(10,len(lstMots[ix])),mini=max(3,lgMot))
                if len(lstItems)>0 and lgtest2 + 1 > len(motTest):
                    motTest = lstMots[ix][:lgtest2 + 1]
                if match: break
        # proposition de filtre pour recherche manuelle (le radical le plus long donnant plusieurs items)
        self.filtreTest = motTest
        item = None
        if match: item = lstItems[0]
        return item

# --------------- TESTS ----------------------------------------------------------
if __name__ == u"__main__":
    import os
    os.chdir("..")
    app = wx.App(0)
    cpt = Compta(None,compta='quadra')
    #print(cpt.GetOneAuto('fournisseurs','sncf internet paris'),cpt.filtreTest)
    cpt.ChoisirItem('clients','brunel')
    app.MainLoop()
