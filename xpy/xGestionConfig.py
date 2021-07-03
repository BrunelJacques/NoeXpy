# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet XPY, gestion d'identification
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import os
import xpy.xUTILS_SaisieParams as xusp
import xpy.xUTILS_DB as xdb
from  xpy.outils import xformat,xboutons,xbandeau,xshelve



# Constantes de paramétrage des écrans de configuration et identification
MATRICE_CREATE_BASE = {
("create_base","Création d'une nouvelle base de donnée"):[
    {'name': 'nameDB', 'genre': 'texte', 'label': 'Nom de la base',
                        'help': "C\'est le nom qui sera donné à la base de données",
                        'txtSize': 140,
                        'ctrlaction':"OnNameDB",
                        'btnLabel':"...", 'btnHelp': "Cliquez pour gérer les configurations d'accès aux données",
                        'btnAction': "OnBtnConfig",
    },
    ]
}
MATRICE_IDENT = {
("ident","Votre session"):[
    {'name': 'userdomain', 'genre': 'String', 'label': 'Votre organisation', 'value': "NomDuPC",
                        'help': 'Ce préfixe à votre nom permet de vous identifier'},
    {'name': 'username', 'genre': 'String', 'label': 'Identifiant session', 'value': "NomSession",
                        'help': "Nom d'ouverture de la sesssion sur l'ordi local"},
    {'name': 'utilisateur', 'genre': 'String', 'label': "Nom présenté à l'appli.", 'value': "Nom pour l'appli",
                        'help': ''},
    ],
}
MATRICE_USER = {
("infos_user","Accès base de donnée"):[
    {'name': 'mpUserDB', 'genre': 'Mpass', 'label': 'Mot de Passe du Serveur',
                        'help': "C'est le mot de passe d'accès à la base de données," +
                                "\nce n'est pas celui demandé au lancement de l'appli ou lors de l'authentification",
                        'txtSize': 140},
    ]
}
MATRICE_CHOIX_CONFIG = {
("infos_config","Infos partagées"):[
     {'name': 'config', 'genre': 'Enum', 'label': 'Données actives',
                        'help': "Le bouton de droite vous permet de créer une nouvelle configuration",
                        'ctrlAction':'OnCtrlConfig',
                        'btnLabel':"...", 'btnHelp':"Cliquez pour gérer les configurations d'accès aux données",
                        'btnAction':"OnBtnConfig",
                        'txtSize': 85},]}
# db_reseau et db_fichier sont des types de config, pourront être présentes dans dictAPPLI['TYPE_CONFIG'] et xUTILS_DB
MATRICE_CONFIGS = {
    ('db_reseau', "Acccès à une base avec authentification"): [
    {'name': 'ID', 'genre': 'String', 'label': 'Désignation config', 'value': 'config1',
                    'help': "Désignez de manière unique cette configuration"},
    {'name': 'typeDB', 'genre': 'choice', 'label': 'Type de Base',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':['MySql','Access','SQLite'],},
    {'name': 'serveur', 'genre': 'dirfile', 'label': 'Path ou Serveur', 'value':'',
                    'help': "Choixir l'emplacement 'c:\...' pour un choix local - l'Adresse IP du serveur si réseau",},
    {'name': 'port', 'genre': 'Int', 'label': 'Port',
                    'help': "Pour réseau seulement, information disponible aurpès de l'administrateur système",},
    {'name': 'nameDB', 'genre': 'combo', 'label': 'Nom de la Base',
                     'help': "Choisir un base de donnée présente sur le serveur",
                     'ctrlAction':'OnNameDB'},
    {'name': 'userDB', 'genre': 'String', 'label': 'Utilisateur BD',
                    'help': "Si nécessaire, utilisateur ayant des droits d'accès à la base de donnée", 'value':'invite'},
    {'name': 'mpUserDB', 'genre': 'Mpass', 'label': 'Mot de passe BD',
                    'help': "C'est le mot de passe d'accès à la base de données," +
                            "\nce n'est pas celui demandé au lancement de l'appli ou lors de l'authentification"},
    ],
    ('db_fichier',"Accès à un fichier local"): [
        {'name': 'typeDB', 'genre': 'Enum', 'label': 'Type de Base',
                        'help': "Le choix est limité par la programmation", 'value': 0,
                        'values': ['Access', 'SQLite']},
        {'name': 'ID', 'genre': 'String', 'label': 'Désignation config', 'value': 'config1',
                        'help': "Désignez de manière unique cette configuration"},
        {'name': 'serveur', 'genre': 'String', 'label': "Chemin d'accès:", 'value': '',
                        'help': "Répertoire 'c:\...' si local - Adresse IP ou nom du serveur si réseau"},
        {'name': 'nameDB', 'genre': 'String', 'label': 'Nom de la Base',
                         'help': "Base de donnée présente sur le serveur"},
    ],
}

def GetLstCodesMatrice(matrice):
    # retourne une liste des premiers composant des tuples clé d'une matrice
    return [x[0] for x in matrice.keys()]

def GetCleMatrice(code,matrice):
    # retourne la clé complète d'une matrice selon son ID
    cle = None
    for cle in matrice.keys():
        if not code:
            break
        if cle[0] == code:
            break
    return cle

def GetIxLigneMatrice(name,lignes):
    ix = 0
    for dic in lignes:
        if dic['name'] == name:
            ix = lignes.index(dic)
            break
    return ix

def GetLstConfigs(configs,typeconfig=None):
    lstIDconfigs = []
    lstConfigsOK = []
    lstConfigsKO = []
    if 'lstConfigs' in configs:
        for config in configs['lstConfigs']:
            for typconf in config:
                if (not typeconfig) or (typeconfig == typconf):
                    lstIDconfigs.append(config[typconf]['ID'])
                    lstConfigsOK.append(config)
                else: lstConfigsKO.append(config)
    return lstIDconfigs,lstConfigsOK,lstConfigsKO

def GetDdConfig(configs,nomConfig=None):
    # retourne le fichier de configuration d'une connexion
    ddConfig = {}
    if 'lstConfigs' in configs:
        for dic in configs['lstConfigs']:
            for typeConfig,config in dic.items():
                if config['ID'] == nomConfig:
                    ddConfig = {typeConfig:config}
                    break
    return ddConfig

def GetBases(self,cfgParams=None):
        # connexion actuelle stockée pour vérif modifs
        oldval = None
        if not cfgParams or cfgParams['nameDB']=='':
            #récupération d'un connexion antérieure, soit d'un précédent passage, soit celle par défaut
            if not self.DB:
                self.DB = xdb.DB(mute=True)
        else:
            oldval = cfgParams['nameDB']
            self.DB = xdb.DB(config=cfgParams,mute=True)

        if self.DB.connexion:
            lstBases = [x for (x,) in self.DB.GetDataBases() if x[-4:].lower()=='data']
        else:
            lstBases = [oldval,'Recherche échouée',]
        return lstBases

# Panel de gestion des configurations
class ChoixConfig(xusp.BoxPanel):
    def __init__(self,parent,lblBox, codebox, lignes, dictDonnees):
        # le codebox n'étant pas visible, on écrase le label devant le contrôle
        lignes[0]['label'] = codebox
        xusp.BoxPanel.__init__(self, parent, lblBox=lblBox, code=codebox, lignes=lignes,
                               dictDonnees=dictDonnees,)
        self.SetMinSize((350,50))
        self.Name = codebox+"."+lignes[0]['name']

# Ecran de choix des configurations d'implantation
class DLG_choixConfig(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent, **kwds):
        style = kwds.pop('style',wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        size = kwds.pop('size',(400,430))
        self.typeConfig = kwds.pop('typeConfig',None)
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, parent, -1,title = titre, style=style,size = size)
        self.parent = parent

        # Récup du code de la description des champs pour une configuration
        lstcode = GetLstCodesMatrice(MATRICE_CONFIGS)
        if not self.typeConfig:
            self.typeConfig = lstcode[0]
        if self.parent and 'TYPE_CONFIG' in self.parent.dictAppli:
            self.typeConfig = self.parent.dictAppli['TYPE_CONFIG']
            if not (self.typeConfig in lstcode):
                wx.MessageBox("L'option '%s' n'est pas dans MATRICECONFIGS " % (self.typeConfig))

        ddDonnees = {}
        valeurs = {}
        ident = None
        # Bouton sortie de pied d'écran
        self.btnTest = xboutons.BTN_tester(self)
        self.btn = xboutons.BTN_fermer(self)

        #  IDENT :  appel de l'identification IDENT partie grisée -----------------------------------------------------
        try:
            utilisateur = self.parent.dictUser['utilisateur']
        except : utilisateur = None

        for (code,label), lignes in MATRICE_IDENT.items():
            for ligne in  lignes:
                if ligne['name'].lower() in ('username', 'user'):
                    valeurs[ligne['name']] = os.environ['USERNAME']
                    ident = code
                if ligne['name'].lower() in ('userdomain','domaine', 'workgroup'):
                    try:
                        valeurs[ligne['name']] = os.environ['USERDOMAIN']
                    except:
                        import platform
                        valeurs[ligne['name']] = platform.node()
                if ligne['name'].lower() in ('utilisateur',):
                    valeurs[ligne['name']] = utilisateur
                    ident = code

        self.ctrlID = xusp.CTRL_property(self, matrice=MATRICE_IDENT, enable=False)
        if ident:
            ddDonnees[ident] = valeurs
            self.ctrlID.SetValues(ddDonnees=ddDonnees)

        # recherche dans profilUser ----------------------------------------------------------------------------------
        cfg = xshelve.ParamUser()
        # lecture des valeurs préalablement utilisées
        choixUser= cfg.GetDict(dictDemande=None, groupe='USER', close=True)
        dictAppli= cfg.GetDict(dictDemande=None, groupe='APPLI')
        if dictAppli == {}:
            dictAppli = self.parent.dictAppli
        self.nomAppli = dictAppli['NOM_APPLICATION']

        # CONFIGS : appel du modèle des configurations ----------------------------------------------------------------
        codeBox,labelBox,lignes = xformat.AppelLignesMatrice(None, MATRICE_CHOIX_CONFIG)
        # Composition des choix de configurations selon l'implantation
        self.lstChoixConfigs = []
        if self.parent and 'CHOIX_CONFIGS' in self.parent.dictAppli:
            lstchoix = self.parent.dictAppli['CHOIX_CONFIGS']
            for codeBox,labelBox in lstchoix:
                self.lstChoixConfigs.append(ChoixConfig(self, labelBox, codeBox, lignes, {}))
        else:
            # le nom de la configuration c'est le premier champ décrit dans la matrice
            self.lstChoixConfigs.append(ChoixConfig(self, labelBox, codeBox, lignes, {}))

        # choix de la configuration prise dans paramFile
        cfgF = xshelve.ParamFile()
        grpConfigs = cfgF.GetDict(dictDemande=None, groupe='CONFIGS')
        # filtrage des des configs selon type retenu
        self.lstIDconfigsOK, self.lstConfigsOK, self.lstConfigsKO = GetLstConfigs(grpConfigs,self.typeConfig)
        ddchoixConfigs = grpConfigs.pop('choixConfigs',{})
        # les choix de config sont stockés par application car Data peut être commun à plusieurs
        if not (self.nomAppli in ddchoixConfigs):
            ddchoixConfigs[self.nomAppli]= {}
        choixConfigs = ddchoixConfigs[self.nomAppli]
        # alimente la liste des choix possibles
        for ctrlConfig in self.lstChoixConfigs:
            ctrlConfig.SetOneSet(ctrlConfig.Name,self.lstIDconfigsOK)
            if ctrlConfig.Name in choixConfigs:
                ctrlConfig.SetOneValue(ctrlConfig.Name,choixConfigs[ctrlConfig.Name])
        # last config sera affichée en 'Fermer' si pas modifiée
        if 'lastConfig' in choixConfigs:
            self.lastConfig = choixConfigs['lastConfig']
        else: self.lastConfig = ''

        # SEPARATEUR : simple texte
        self.titre =wx.StaticText(self, -1, "Eléments de connexion")

        self.Sizer()


    def Sizer(self):
        # Déroulé de la composition
        cadre_staticbox = wx.StaticBox(self, -1, label='identification')
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        topbox.Add(self.ctrlID, 0,wx.ALL | wx.EXPAND, 5)
        topbox.Add((20,20), 1, wx.ALIGN_TOP, 0)
        topbox.Add(self.titre, 0, wx.LEFT, 60)
        for ctrlConfig in self.lstChoixConfigs:
            topbox.Add((20,20), 1, wx.ALIGN_TOP, 0)
            topbox.Add(ctrlConfig, 1, wx.ALIGN_TOP , 0)
        topbox.Add((20,20), 1, wx.ALIGN_TOP, 0)
        topbox.Add((40,40), 1, wx.EXPAND, 0)
        piedbox = wx.BoxSizer(wx.HORIZONTAL)
        piedbox.Add(self.btnTest, 0, 0, 0)
        piedbox.Add(self.btn, 0, wx.RIGHT, 11)
        topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)
        self.SetSizer(topbox)

    def OnTester(self,event,mute=False):
        # appelé par le bouton tester tente toutes les connexions de l'appli.
        self.OnCtrlConfig(None)
        for ctrlConfig in self.lstChoixConfigs:
            nomConfig = ctrlConfig.dictDonnees['config']
            config = xdb.GetOneConfig(self,nomConfig)
            DB = xdb.DB(config=config,mute=True)
            self.echec = DB.echec
            if not mute:
                DB.AfficheTestOuverture(info=" pour %s"%nomConfig)


    def OnCtrlAction(self, event):
        # relais des actions sur les ctrls
        action = 'self.%s(event)' % event.EventObject.actionCtrl
        try:
            eval(action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s" % (action, err))

    def OnCtrlConfig(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        self.SauveParamUser()
        self.SauveConfig()

    def OnBtnAction(self, event):
        # relais des actions sur les boutons associés aux ctrls
        #ctrl = event.EventObject.GrandParent
        action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(action)
        except Exception as err:
            mess = "Commande: '%s' \n\nErreur: \n%s" % (action, err)
            mess += "\n Le Oui permet de récupérer l'erreur"
            ret = wx.MessageBox(
                mess,
            "Echec sur lancement de l'action bouton",style=wx.YES_NO)
            if ret == wx.YES:
                raise(err)

    def OnBtnConfig(self,event):
        ctrl = event.EventObject.Parent
        # sur clic du bouton pour élargir le choix de la combo
        sc = DLG_listeConfigs(self,select=ctrl.GetValue(),typeConfig=self.typeConfig)
        if sc.ok :
            ret = sc.ShowModal()
            if ret == wx.OK:
                self.lstIDconfigsOK = sc.GetDonnees()
                for conf in self.lstChoixConfigs:
                    for pnl in conf.lstPanels:
                        if pnl.ctrl.name == ctrl.name:
                            pnl.ctrl.Set(self.lstIDconfigsOK)
                value = sc.GetChoix(idxColonne=0)
                if len(value) > 0:
                    ctrl.SetValue(value)
                # choix de configs user stockées
                self.SauveConfig()
        else: wx.MessageBox('DLG_listeConfigs : lancement impossible, cf MATRICE_CONFIGS et  TYPE_CONFIG')


    def SauveParamUser(self):
        # sauve ID dans le registre de la session
        cfg = xshelve.ParamUser()
        dic = {}
        for ctrlConfig in self.lstChoixConfigs:
            dic.update(ctrlConfig.GetValues())
        #dic.update(self.ctrlConnect.GetValues())
        cfg.SetDict(dic, groupe='USER',close=False)
        dic = self.ctrlID.GetValues()
        cfg.SetDict(dic['ident'], groupe='IDENT')

    def SauveConfig(self):
        # sauve les configs sur appli/data local
        dicconfigs = {}
        value = "Non défini"
        for ctrl in self.lstChoixConfigs:
            value = ctrl.GetOneValue(ctrl.Name)
            dicconfigs[ctrl.Name] =  value
        dicconfigs['lastConfig'] = value
        self.lastConfig = value
        #récupère l'ensemble des choix existants antérieurement
        cfgF = xshelve.ParamFile()
        grpConfigs = cfgF.GetDict(groupe='CONFIGS',close=False)
        dicchoix = grpConfigs.pop('choixConfigs',{})
        # actualise seulement ceux de l'application
        dicchoix[self.nomAppli] = dicconfigs
        grpConfigs['choixConfigs'] = dicchoix
        cfgF.SetDict(grpConfigs, groupe='CONFIGS')

    def OnFermer(self,event):
        # enregistre les valeurs de l'utilisateur
        self.SauveParamUser()
        self.SauveConfig()
        dic = self.ctrlID.GetValues()
        if self.IsModal():
            self.EndModal(wx.OK)
        else: self.Destroy()

# Visu-Choix d'une Liste pour gestion des configs d'accès aux bases de données
class DLG_listeConfigs(xusp.DLG_listCtrl):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent, *args, **kwds):
        typeConfig = kwds.pop('typeConfig',None)
        select = kwds.pop('select',None)
        kwds['lblList'] = "Configurations actuelles"
        super().__init__(parent, *args, **kwds)
        self.parent = parent
        self.dlColonnes = {}
        self.lddDonnees = []
        self.lstIDconfigsOK = []
        self.lstConfigsKO = []
        self.dldMatrice = {}
        self.typeConfig = typeConfig
        # composition des paramètres
        self.gestionProperty = False
        self.ok = False
        self.DB=None
        cle = GetCleMatrice(typeConfig,MATRICE_CONFIGS)
        self.dldMatrice[cle] = MATRICE_CONFIGS[cle]
        self.dlColonnes[typeConfig] = [x ['name'] for x in MATRICE_CONFIGS[cle]]
        cfgF = xshelve.ParamFile()
        grpConfigs= cfgF.GetDict(None,'CONFIGS')
        if 'lstConfigs' in grpConfigs:
            self.lstIDconfigsOK, lstConfigsOK, lstConfigsKO = GetLstConfigs(grpConfigs,typeConfig)
            self.lddDonnees = lstConfigsOK

        # paramètres pour self.pnl contenu principal de l'écran
        self.kwds['lblTopBox'] = ''
        self.Size = (400,300)

        if self.dldMatrice != {}:
            self.InitDlgGestion()
            self.dlgGest.SetSize(350,400)
            self.dlgGest.btn = self.Boutons(self.dlgGest)
            self.SizerDlgGestion()
            self.Init()
            self.ok = True
            if 'lstConfigs' in grpConfigs:
                if select in self.lstIDconfigsOK:
                    ix = self.lstIDconfigsOK.index(select)
                    self.pnl.ctrl.Select(ix)
                    self.pnl.ctrl.SetItemState(ix,wx.LIST_STATE_SELECTED,wx.LIST_STATE_SELECTED)
            self.InitDlGest()

    def InitDlGest(self):
        # pose les relais pour récupérer les actions
        self.dlgGest.OnNameDB = self.OnNameDB
        #self.dlgGest.OnBtnNameDB = self.OnBtnNameDB
        self.dlgGest.OnTypeDB = self.OnTypeDB

    def Boutons(self,dlg):
        btnOK = xboutons.BTN_fermer(dlg,label='Fermer',onBtn=dlg.OnFermer)
        btnTest = xboutons.BTN_tester(dlg,onBtn=self.OnTester)
        boxBoutons = wx.BoxSizer(wx.HORIZONTAL)
        boxBoutons.Add(btnTest, 0,  wx.RIGHT,20)
        boxBoutons.Add(btnOK, 0,  wx.RIGHT,20)
        return boxBoutons

    def OnTypeDB(self,event):
        ctrl = self.dlgGest.pnl.GetPnlCtrl('typeDB')
        valeurs = [x for x in ctrl.values]
        ctrl2 = self.dlgGest.pnl.GetPnlCtrl('nameDB')
        ctrl2.Set(valeurs)
        ctrl2.ctrl.SetValue(valeurs[0])
        val = ctrl2.ctrl.GetValue()
        event.Skip()

    def OnNameDB(self,event):
        if event.EventType == wx.EVT_COMBOBOX_DROPDOWN.typeId:
            cfgConfig = self.dlgGest.pnl.GetValues()[self.typeConfig]
            # réalimente le contenu de la combo
            lstBases = GetBases(self,cfgConfig)
            ctrl = self.dlgGest.pnl.GetPnlCtrl('nameDB')
            ctrl.Set(lstBases)
            label = cfgConfig['nameDB']
            ctrl.SetValue(label)
        else: event.Skip()

    def OnFermer(self, event):
        cfgF = xshelve.ParamFile()
        cfgF.SetDict({'lstConfigs':self.lstConfigsKO + self.lddDonnees}, 'CONFIGS')
        if self.IsModal():
            self.EndModal(wx.OK)
        else: self.Close()

    def GetChoix(self, idxColonne = 0):
        # récupère le choix fait dans le listCtrl par la recherche de son ID
        ctrl = self.pnl.ctrl
        idxLigne = ctrl.GetFirstSelected()
        # en l'absence de choix on prend la première ligne
        if idxLigne == -1:
            if ctrl.GetItemCount() > 0:
                idxLigne = 0
        if idxLigne >= 0:
            # le nom de la config est dans la colonne pointée par l'index fourni
            cell = ctrl.GetItem(idxLigne,idxColonne)
            choix = cell.GetText()
        else: choix=''
        return choix

    def GetDonnees(self):
        self.lstIDconfigsOK = [x[self.typeConfig]['ID'] for x in self.lddDonnees ]
        return self.lstIDconfigsOK

    def OnTester(self,event):
        # test à partir de l'écran de saisie d'une config
        dicParam = event.EventObject.Parent.pnl.lstBoxes[0].GetValues()
        DB = xdb.DB(config=dicParam,mute=True)
        DB.AfficheTestOuverture()
        DB.Close()

# Accès particulier à une config_base de donnée, sans passer par la liste des configs
class DLG_saisieUneConfig(xusp.DLG_vide):
    # saisie d'un nouvelle configuration d'accès aux données
    def __init__(self,parent,**kwds):
        nomConfig = kwds.pop('nomConfig',None)
        lblBox =    kwds.pop('lblBox',"Paramètres de la base de donnée")
        modeBase =  kwds.pop('modeBase','pointeur')
        kwds['size']=(350,430)
        super().__init__(parent, **kwds)
        self.modeBase = modeBase
        self.DB = None

        # récup info de l'utilisateur de la session
        cfg = xshelve.ParamUser()
        dicUser = cfg.GetDict(dictDemande=None, groupe='USER')
        mess = "Accès aux ParamUser"
        try:
            # vérif des droits
            if modeBase == 'creation':
                mess = "Echec de la vérification des droits de création"
                if dicUser['profil'] != 'administrateur':
                    mess += "\n\n%s de profil %s n'est pas administrateur!"%(dicUser['utilisateur'],dicUser['profil'])
                    raise(mess)
            mess = None
        except : wx.MessageBox(mess,"xGestionConfig.DLG_saisieUneConfig")
        if mess:
            self.Destroy()

        # choix de la configuration prise dans paramFile
        cfgF = xshelve.ParamFile()
        grpConfigs = cfgF.GetDict(dictDemande=None, groupe='CONFIGS')

        # les choix de config sont stockés par application car Data peut être commun à plusieurs
        if parent and hasattr(parent,'dictAppli'):
            dictAppli = self.parent.dictAppli
        else:
            cfg = xshelve.ParamUser()
            dictAppli= cfg.GetDict(dictDemande=None, groupe='APPLI')
        nomAppli = dictAppli['NOM_APPLICATION']

        # récup des données à afficher après construction

        choixConfigs = grpConfigs['choixConfigs'][nomAppli]
        if 'lastConfig' in choixConfigs:
            lastConfig = choixConfigs['lastConfig']
        else: lastConfig = None
        ddConfig = GetDdConfig(grpConfigs,lastConfig)

        # récup de la matrice ayant servi à la gestion des données
        typeConfig = kwds.pop('typeConfig',None)
        if not typeConfig:
            lstcode = GetLstCodesMatrice(MATRICE_CONFIGS)
            typeConfig = lstcode[0]
        key = (typeConfig,lblBox)
        matrice = {key: MATRICE_CONFIGS[GetCleMatrice(typeConfig,MATRICE_CONFIGS)]}
        self.typeConfig = typeConfig

        # ajustement de la matrice selon les modeBase
        ix = GetIxLigneMatrice('nameDB', matrice[key])
        if self.modeBase == 'pointeur':
            matrice[key][ix] = {'name': 'nameDB', 'genre': 'combo', 'label': 'Nom de la Base',
                    'help': "Le nom de la base est le fichier en local, ou son nom sur le serveur",
                    'ctrlAction': 'OnNameDB',}

        elif self.modeBase == 'creation':
            matrice[key][ix] = {'name': 'nameDB', 'genre': 'texte', 'label': 'Nom de la Base',
                    'help': "Choisir un base de donnée non présente sur le serveur ou fichier non existant",
                    'ctrlAction': 'OnNameDB',}

        # place la valeur du champ ID
        if nomConfig:
            ix = GetIxLigneMatrice('ID',matrice[key])
            matrice[key][ix]['value'] = nomConfig

        # construction de l'écran de saisie
        self.pnl = xusp.TopBoxPanel(self, matrice=matrice, lblTopBox=None)
        self.pnl.SetValues(ddConfig)

        # grise le champ ID
        ctrlID = self.pnl.GetPnlCtrl('ID')
        #ctrlID.Enable(False)
        if self.modeBase == 'creation' :
            titre = "Création d'une nouvelle base de données"
            texte = "Définissez les pointeurs d'accès et le nom de la base à y créer\n"
            texte += "le mot de passe présenté sera celui  des 'Accès aux bases de données'"
        else:
            titre = "Définition de la base de données"
            texte = "Définissez les pointeurs d'accès et le nom de la base souhaitée\n"
            texte += "l'éventuel mot de passe présenté sera celui des 'Accès aux bases de données'"

        # personnalisation des éléments de l'écran
        self.bandeau = xbandeau.Bandeau(self,titre=titre,texte=texte,
                                        nomImage='xpy/images/32x32/Configuration.png')
        self.btn = self.Boutons(self)

        # layout
        self.Sizer(self.pnl)

    def Boutons(self,dlg):
        btnOK = xboutons.BTN_fermer(dlg,label='',onBtn=dlg.OnFermer,size=(35,35),
                                    image='xpy/images/32x32/Valider.png',
                                    help='Cliquez pour fermer la fenêtre')
        btnTest = xboutons.BTN_tester(dlg,label='Tester\nla base',onBtn=self.OnTester,
                                      help="Cette option vous permet de vérifier l'accés à la base sus nommée")
        boxBoutons = wx.BoxSizer(wx.HORIZONTAL)
        if self.modeBase == 'creation':
            btnCreate = xboutons.Bouton(dlg,onBtn=self.OnCreate,label='Création\nde la base',
                                        image='xpy/images/32x32/Action.png',
                                        help="Cliquez pour lancer la création de la base de donnée sus nommée")
            boxBoutons.Add(btnCreate, 0,  wx.RIGHT,5)
        boxBoutons.Add(btnTest, 0,  wx.RIGHT,5)
        boxBoutons.Add(btnOK, 0,  wx.RIGHT,5)
        return boxBoutons

    def GetValues(self):
        return self.pnl.GetValues()

    def GetConfig(self):
        return self.pnl.GetValues()['db_reseau']

    def OnNameDB(self,event):
        cfgConfig = self.pnl.GetValues()[self.typeConfig]
        if self.modeBase == 'creation':
            if event.EventType == wx.EVT_KILL_FOCUS.typeId:
                #Vérification de l'unicité
                label = cfgConfig['nameDB']
                lstBases = GetBases(self,cfgConfig)
                if label in lstBases:
                    wx.MessageBox("En mode création, il faut choisir un nom nouveau!",caption="Base de donnée déjà présente")
        elif self.modeBase == 'pointeur':
            if event.EventType == wx.EVT_COMBOBOX_DROPDOWN.typeId:
                # réalimente le contenu de la combo
                lstBases = GetBases(self,cfgConfig)
                ctrl = self.pnl.GetPnlCtrl('nameDB')
                ctrl.Set(lstBases)
                label = cfgConfig['nameDB']
                ctrl.SetValue(label)
            else:
                event.Skip()
        event.Skip()

    def OnTester(self,event):
        dicParam = event.EventObject.Parent.pnl.lstBoxes[0].GetValues()
        DB = xdb.DB(config=dicParam,mute=True)
        DB.AfficheTestOuverture()
        DB.Close()

    def OnCreate(self,event):
        cfgParams = event.EventObject.Parent.pnl.lstBoxes[0].GetValues()
        DB = xdb.DB(config=cfgParams,mute=True)
        DB.CreateBaseMySql(ifExist=False)
        DB.Close()

# Box d'un jeu de paramètres d'un module, stocké localement
class PNL_paramsLocaux(xusp.TopBoxPanel):
    def __init__(self, parent, *args, **kwds):
        kwdsTopBox = {}
        for key in xusp.OPTIONS_TOPBOX:
            if key in kwds.keys(): kwdsTopBox[key] = kwds[key]
        super().__init__(parent, *args, **kwdsTopBox)
        self.pathData = kwds.pop('pathdata',"")
        self.nomFichier = kwds.pop('nomfichier',"params")
        self.nomGroupe = kwds.pop('nomgroupe',"paramLocal")
        self.parent = parent

    # Init doit être lancé après l'initialisation du super() qui alimente les champs par défaut
    def Init(self):
        # choix de la configuration prise dans paramUser
        self.paramsFile = xshelve.ParamFile(nomFichier=self.nomFichier, path=self.pathData)
        self.dicParams = self.paramsFile.GetDict(dictDemande=None, groupe=self.nomGroupe, close=False)
        if self.dicParams:
            # pose dans la grille la valeur de les dernières valeurs utilisées
            self.SetValues(self.dicParams)

    def SauveParams(self,close=False):
        # peut être lancé avec close forcé du shelve
        dicValeurs = self.GetValues()
        self.paramsFile.SetDict(dictEnvoi=dicValeurs,groupe=self.nomGroupe,close=close )

#************************   Pour Test ou modèle  *********************************

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    frame_1 = wx.Frame(None)
    app.SetTopWindow(frame_1)
    frame_1.dictAppli ={
            'NOM_APPLICATION'       : "Noelite",
            'REP_DATA'              : "srcNoelite/Data",
            'TYPE_CONFIG'           : 'db_reseau',
            'CHOIX_CONFIGS': [('Donnees', "Base de travail, peut être la centrale  en mode connecté"),]
            }
    #frame_1.dlg = DLG_choixConfig(frame_1)
    #frame_1.dlg = DLG_listeConfigs(frame_1)
    frame_1.dlg = DLG_saisieUneConfig(frame_1, modeBase='creation')
    #frame_1.dlg = DLG_saisieUneConfig(frame_1, modeBase='pointeur')
    frame_1.dlg.ShowModal()
    app.MainLoop()

