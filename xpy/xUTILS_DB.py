#!/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    xPY, Gestion des bases de données
# Auteur:          Jacques Brunel, d'après Yvan LUCAS Noethys
# Copyright:       (c) 2019-04     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os
import wx
import sys
import subprocess
import mysql.connector
import win32com.client
import sqlite3
import copy
import datetime
import xpy.outils.xshelve as xucfg

DICT_CONNEXIONS = {}

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateDDEnDateEng(datedd):
    if not isinstance(datedd, datetime.date):
        return '1900-01-01'
    aaaa = str(datedd.year)
    mm = ('00'+str(datedd.month))[-2:]
    jj = ('00'+str(datedd.day))[-2:]
    return aaaa+'-'+mm+'-'+jj

def GetConfigs():
    # appel des params de connexion stockés dans UserProfile et data
    cfg = xucfg.ParamUser()
    grpUSER = cfg.GetDict(groupe='USER', close=False)
    grpAPPLI = cfg.GetDict(groupe='APPLI')
    # appel des params de connexion stockés dans Data
    cfg = xucfg.ParamFile()
    grpCONFIGS = cfg.GetDict(groupe='CONFIGS')
    return grpAPPLI,grpUSER,grpCONFIGS

def GetOneConfig(self, nomConfig='lastConfig', mute=False):
    # appel d'une configuration nommée, retourne le dict des params
    cfg = xucfg.ParamFile()
    grpCONFIGS = cfg.GetDict(groupe='CONFIGS')
    cfg = xucfg.ParamUser()
    grpAPPLI = cfg.GetDict(groupe='APPLI')
    nomAppli = ''
    if 'NOM_APPLICATION' in grpAPPLI.keys():
        nomAppli = grpAPPLI['NOM_APPLICATION']

    if nomConfig == 'lastConfig':
        # recherche du nom de configuration par défaut, cad la dernière des choix
        if 'choixConfigs' in grpCONFIGS:
            if nomAppli in grpCONFIGS['choixConfigs'].keys():
                if 'lastConfig' in grpCONFIGS['choixConfigs'][nomAppli].keys():
                    nomConfig = grpCONFIGS['choixConfigs'][nomAppli]['lastConfig']

    typeConfig = 'db_reseau'
    if 'TYPE_CONFIG' in grpAPPLI:
        typeConfig = grpAPPLI['TYPE_CONFIG']
    if 'lstConfigs' in grpCONFIGS:
        lstNomsConfigs = [x[typeConfig]['ID'] for x in grpCONFIGS['lstConfigs']]
        if not (nomConfig in lstNomsConfigs):
            mess = "xDB: Le nom de config '%s' n'est pas dans la liste des accès base de donnée" % (nomConfig)
            self.erreur = mess
            if not mute:
                wx.MessageBox(mess)
            return mess
        ix = lstNomsConfigs.index(nomConfig)
        # on récupére les paramétres de la config par le pointeur ix dans les clés
        return grpCONFIGS['lstConfigs'][ix][typeConfig]

class DB():
    # accès à la base de donnees principale
    def __init__(self, IDconnexion = None, config=None, nomFichier=None, mute=False):
        # config peut être soit un nom de config soit un dictionaire
        #print(config,nomFichier,IDconnexion)
        self.echec = 1
        self.IDconnexion = IDconnexion
        self.nomBase = 'personne!'
        self.isNetwork = False
        self.lstTables = None
        self.lstIndex = None
        self.grpConfigs = None
        self.dictAppli = None
        self.cfgParams = None
        self.erreur = None
        if nomFichier:
            self.OuvertureFichierLocal(nomFichier)
            return
        if not IDconnexion:
            self.connexion = None

            # appel des params de connexion stockés dans UserProfile et Data
            grpAPPLI, grpUSER, grpCONFIGS = GetConfigs()
            self.dictAppli = grpAPPLI
            self.grpConfigs = grpCONFIGS

            # aiguillage dans les paramètres
            try:
                # priorité la config passée en kwds puis recherche de la dernière config dans 'USER'
                if config:
                    # Présence de kwds 'config', peut être le nom de la config ou un dictionaire de configuration
                    if isinstance(config, str):
                        nomConfig = config
                    elif isinstance(config,dict):
                        nomConfig = None
                        self.cfgParams = copy.deepcopy(config)
                else: nomConfig = 'lastConfig'

                if nomConfig:
                    self.cfgParams = GetOneConfig(self,nomConfig,mute=mute)
                # on ajoute les choix pris dans grpUSER,  pour mot passe, aux paramètres de la config retenue
                if self.cfgParams:
                    for cle, valeur in grpUSER.items():
                        self.cfgParams[cle] = valeur
                        self.nomBase = self.cfgParams['nameDB']
            except Exception as err:
                mess = "xDB: La récup des identifiants de connexion a échoué : \nErreur detectee :%s" % err
                if not mute:
                    wx.MessageBox(mess)
                self.erreur = err
                return

            if not self.cfgParams :
                self.erreur = "Aucun fichier de paramètres de connexion trouvé!"
                return

            # Ouverture des bases de données selon leur type
            if 'typeDB' in self.cfgParams:
                self.typeDB = self.cfgParams['typeDB'].lower()
            else : self.typeDB = 'Non renseigné'
            if 'typeDB' in self.cfgParams.keys() and  self.cfgParams['typeDB'].lower() in ['mysql','sqlserver']:
                self.isNetwork = True
                # Ouverture de la base de données
                self.ConnexionFichierReseau(self.cfgParams, mute=mute)
            elif 'typeDB' in self.cfgParams.keys() and  self.cfgParams['typeDB'].lower() in ['access','sqlite']:
                self.isNetwork = False
                self.ConnexionFichierLocal(self.cfgParams)
            else :
                mess = "xDB: Le type de Base de Données '%s' n'est pas géré!" % self.typeDB
                self.erreur = mess
                if not mute:
                    wx.MessageBox(mess)
                return mess

            if self.connexion:
                # Mémorisation de l'ouverture de la connexion et des requêtes
                if len(DICT_CONNEXIONS) == 0:
                    self.IDconnexion = 1
                else:
                    self.IDconnexion = sorted(DICT_CONNEXIONS.keys())[-1]+1
                DICT_CONNEXIONS[self.IDconnexion] = {}
                DICT_CONNEXIONS[self.IDconnexion]['isNetwork'] = self.isNetwork
                DICT_CONNEXIONS[self.IDconnexion]['typeDB'] = self.typeDB
                DICT_CONNEXIONS[self.IDconnexion]['connexion'] = self.connexion
                DICT_CONNEXIONS[self.IDconnexion]['cfgParams'] = self.cfgParams
        else:
            if self.IDconnexion in DICT_CONNEXIONS:
                # la connexion a été conservée (absence de DB.Close)
                self.isNetwork  = DICT_CONNEXIONS[self.IDconnexion]['isNetwork']
                self.typeDB     = DICT_CONNEXIONS[self.IDconnexion]['typeDB']
                self.connexion  = DICT_CONNEXIONS[self.IDconnexion]['connexion']
                self.cfgParams  = DICT_CONNEXIONS[self.IDconnexion]['cfgParams']
                if self.connexion: self.echec = 0

    def Ping(self,serveur):
        option = '-n' if sys.platform == 'win32' else ''
        if not serveur or len(serveur) < 3 :
            raise NameError('Pas de nom de serveur fourni dans la commande PING')
        t1 = datetime.datetime.now()
        deltasec = 0
        nbre = 0
        ret = 1
        while deltasec < 3 and ret != 0 and nbre < 5:
            nbre +=1
            ret = subprocess.run(['ping', option, '1', '-w', '500', serveur,],
                                 capture_output=True).returncode
            t2 = datetime.datetime.now()
            delta = (t2 - t1)
            deltasec = delta.seconds + delta.microseconds / 10 ** 6
        mess = "%d pings en  %.3f secondes" % (nbre,deltasec)
        print(mess)
        if ret != 0:
            mess = "Time Out %d pings en %.3f secondes "%(nbre,deltasec)
            print(mess)
            print("Pas de réponse du serveur %s à la commande PING\n\n%s"%(serveur,mess))
            ret = 'ko'
        else: ret = 'ok'
        return ret

    def AfficheTestOuverture(self,info=""):
        style = wx.ICON_STOP
        if self.echec == 0: style = wx.ICON_INFORMATION
        accroche = ['Ouverture réussie ',"Echec d'ouverture "][self.echec]
        accroche += info
        retour = ['avec succès', ' SANS SUCCES !\n'][self.echec]
        mess = "%s\n\nL'accès à la base '%s' s'est réalisé %s" % (accroche,self.nomBase, retour)
        if self.erreur:
            mess += '\nErreur: %s'%self.erreur
        wx.MessageBox(mess, style=style)

    def CreateBaseMySql(self,ifExist=True):
        """ Version RESEAU avec MYSQL """

        try:
            # usage de  "mysql.connector":
            self.cursor = self.connexion.cursor()
            if ifExist: exist = 'IF NOT EXISTS'
            else: exist = ''
            # Création
            req = "CREATE DATABASE %s %s;" %(exist,self.nomBase)
            self.cursor.execute(req)

            # Utilisation
            if self.nomBase not in ("", None):
                self.cursor.execute("USE %s;" % self.nomBase)

        except Exception as err:
            mess= "La création de la base de donnees MYSQL a echoue. \nErreur: %s"%err
            wx.MessageBox(mess,'CreateBaseMySql')
            self.erreur = err
            self.echec = 1
        else:
            self.echec = 0

    def ConnexionFichierReseau(self,config,mute=False):
        self.connexion = None
        self.echec = 1
        try:
            etape = 'Décompactage de la config'
            host = config['serveur']
            port = config['port']
            userdb = config['userDB']
            passwd = config['mpUserDB']
            if len(userdb)>0 and len(config['mpUserDB'])==0:
                if not mute:
                    mess = "Pas de mot de passe saisi, veuillez configurer les accès résea"
                    wx.MessageBox(mess, caption="xUTILS_DB.ConnexionFichierReseau ")
                self.erreur = "%s\n\nEtape: %s"%("Config incompète",mess)
                self.echec = 1
                return
            nomFichier = config['nameDB']
            etape = 'Ping %s'%(host)
            ret = self.Ping(host)
            if not ret == 'ok':
                self.echec = 1
                self.connexion = None
                return
            etape = 'Création du connecteur %s:%s user: %s - %s'%(host, port,userdb,passwd)
            if self.typeDB == 'mysql':
                connexion = mysql.connector.connect(host=host, user=userdb, passwd=passwd, port=int(port))
                etape = 'Création du curseur, après connexion'
                self.cursor = connexion.cursor(buffered=True)
                self.connexion = connexion
                # Tentative d'Utilisation de la base
                etape = " Tentative d'accès à '%s'" %nomFichier
                self.cursor.execute("USE %s;" % nomFichier)
                self.echec = 0
            else:
                wx.MessageBox('xDB: Accès BD non développé pour %s' %self.typeDB)
        except Exception as err:
            mess = "La connexion MYSQL a echoué.\n\nEtape: %s,\nErreur: '%s'" %(etape,err)
            if not mute:
                wx.MessageBox(mess,caption="xUTILS_DB.ConnexionFichierReseau ")
            self.erreur = "%s\n\nEtape: %s"%(err,etape)
            self.echec = 1

    def OuvertureFichierLocal(self, nomFichier):
        """ Version LOCALE avec SQLITE """
        # Vérifie que le fichier sqlite existe bien
        if os.path.isfile(nomFichier) == False:
            wx.MessageBox("xDB: Le fichier local '%s' demande n'est pas present sur le disque dur."%nomFichier)
            self.echec = 1
            return
        # Initialisation de la connexion
        self.nomBase = nomFichier
        self.typeDB = "sqlite"
        self.ConnectSQLite()

    def ConnexionFichierLocal(self, config):
        self.connexion = None
        if config['serveur'][-1] != "\\":
            config['serveur'] += "\\"
        self.nomBase = config['serveur'] + config['nameDB']
        try:
            etape = 'Création du connecteur'
            if self.typeDB == 'access':
                self.ConnectAcessADO()
            elif self.typeDB == 'sqlite':
                self.ConnectSQLite()
            elif self.typeDB == 'mySqlLocal':
                self.ConnectMySqlLocal()
            else:
                wx.MessageBox('xDB: Accès DB non développé pour %s' %self.typeDB)
        except Exception as err:
            wx.MessageBox("xDB: La connexion base de donnée a echoué à l'étape: %s, sur l'erreur :\n\n%s" %(etape,err))
            self.erreur = "%s\n\n: %s"%(err,etape)

    def ConnectAcessOdbc(self):
        # permet un acces aux bases access sans office
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("xDB:Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            import pyodbc
            DRIVER='{Microsoft Access Driver (*.mdb, *.accdb)}'
            DBQ='c:/temp/qcompta.mdb'
            PWD = '' # passWord
            self.connexion = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRIVER,DBQ,PWD))
            cursor = self.connexion.cursor()
            allTables = cursor.tables()
            if len(allTables) == 0:
                wx.MessageBox("xDB:La base de donnees %s est présente mais vide " % self.nomBase)
                return
            # Exemple code
            """
            cursor.execute("select * from Journaux;")
            for row in cursor.fetchall():
                print(row)
            cursor.close()
            del cursor
            self.connexion.close()"""
            self.echec = 0
        except Exception as err:
            wx.MessageBox("xDB.ConnectAcessOdbc:La connexion à la base access %s a echoué : \nErreur détectée :%s" %(self.nomBase,err),
                          style=wx.ICON_WARNING)
            self.erreur = err

    def ConnectAcessADO(self):
        """Important ne tourne qu'avec: 32bit MS driver - 32bit python!
           N'est pas compatible access 95, mais lit comme access 2002"""
        # Vérifie que le fichier existe bien
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("xDB:Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            self.connexion = win32com.client.Dispatch(r'ADODB.Connection')
            #DSN = ('PROVIDER = Microsoft.Jet.OLEDB.4.0;DATA SOURCE = ' + self.nomBase + ';')
            DSN = ('PROVIDER = Microsoft.ACE.OLEDB.12.0;DATA SOURCE = ' + self.nomBase + ';')
            self.connexion.Open(DSN)
            #lecture des tables de la base de données
            cat = win32com.client.Dispatch(r'ADOX.Catalog')
            cat.ActiveConnection = self.connexion
            allTables = cat.Tables
            if len(allTables) == 0:
                wx.MessageBox("xDB:La base de donnees %s est présente mais vide " % self.nomBase)
                return
            del cat
            self.cursor = win32com.client.Dispatch(r'ADODB.Recordset')
            self.echec = 0
        except Exception as err:
            wx.MessageBox("xDB:La connexion avec la base access %s a echoué : \nErreur détectée :%s" %(self.nomBase,err),
                          style=wx.ICON_WARNING)
            self.erreur = err

    def ConnectSQLite(self):
        # Version LOCALE avec SQLITE
        #nécessite : pip install pysqlite
        # Vérifie que le fichier sqlite existe bien
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("xDB: Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            self.connexion = sqlite3.connect(self.nomBase.encode('utf-8'))
            self.cursor = self.connexion.cursor()
            self.echec = 0
        except Exception as err:
            wx.MessageBox("xDB: La connexion avec la base de donnees SQLITE a echoué : \nErreur détectée :%s" % err, style = wx.ICON_WARNING)
            self.erreur = err

    def ExecuterReq(self, req, mess=None, affichError=True):
        # Pour parer le pb des () avec MySQL
        #if self.typeDB == 'mysql' :
        #    req = req.replace("()", "(10000000, 10000001)")
        try:
            if self.typeDB == 'access':
                self.recordset = []
                # methode Access ADO
                self.cursor.Open(req, self.connexion)
                if not self.cursor.BOF:
                    self.cursor.MoveFirst()
                    while not self.cursor.EOF:
                        record = []
                        go = True
                        i=0
                        while go:
                            try:
                                record.append(self.cursor(i).value)
                                i += 1
                            except Exception:
                                go = False
                        self.recordset.append(record)
                        self.cursor.MoveNext()
                    self.retourReq = "ok"
                else:
                    self.retourReq = "Aucun enregistrement"
                self.cursor.Close()
            else:
                # autres types de connecteurs
                ret = self.cursor.execute(req)
                self.retourReq = 'ok'
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess +'\n%s\n'%err
            else: self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq +=  ("ExecuterReq:\n%s\n\nErreur detectee:\n%s"% (req, str(err)))
            if affichError:
                raise Exception(self.retourReq)
                print()
        return self.retourReq

    def Executermany(self, req="", lstDonnees=[], commit=True):
        """ Executemany pour local ou réseau """
        """ Exemple de req : "INSERT INTO table (IDtable, nom) VALUES (?, ?)" """
        """ Exemple de lstDonnees : [(1, 2), (3, 4), (5, 6)] """
        # Adaptation réseau/local
        if self.isNetwork == True :
            # Version MySQL
            req = req.replace("?", "%s")
        else:
            # Version Sqlite
            req = req.replace("%s", "?")
        # Executemany
        self.cursor.executemany(req, lstDonnees)
        if commit == True :
            self.connexion.commit()

    def ResultatReq(self):
        if self.echec == 1 : return []
        resultat = []
        try :
            if self.typeDB == 'access':
                resultat = self.recordset
            else:
                resultat = self.cursor.fetchall()
                # Pour contrer MySQL qui fournit des tuples alors que SQLITE fournit des listes
                if self.typeDB == 'mysql' and type(resultat) == tuple :
                    resultat = list(resultat)
        except :
            pass
        return resultat

    def DonneesInsert(self,donnees):
        # décompacte les données en une liste  ou liste de liste pour requêtes Insert
        donneesValeurs = '('
        def Compose(liste):
            serie = ''
            for valeur in liste:
                if isinstance(valeur,(int,float)):
                    val = "%s, " %str(valeur)
                elif isinstance(valeur, (tuple, list,dict)):
                    val = "'%s', "%str(valeur)[1:-1].replace('\'', '')
                elif valeur == None or valeur == '':
                    val = "NULL, "
                else:
                    val = "'%s', "%str(valeur).replace('\'', '')
                serie += "%s"%(val)
            return serie[:-2]
        if isinstance(donnees[0], (tuple,list)):
            for (liste) in donnees:
                serie = Compose(liste)
                donneesValeurs += "%s ), ("%(serie)
            donneesValeurs = donneesValeurs[:-4]
        else:
            donneesValeurs += "%s"%Compose(donnees)
        return donneesValeurs +')'

    def ReqInsert(self,nomTable="",lstChamps=[],lstlstDonnees=[],lstDonnees=None,commit=True, mess=None,affichError=True):
        """ Permet d'insérer les lstChamps ['ch1','ch2',..] et lstlstDonnees [[val11,val12...],[val21],[val22]...]
            self.newID peut être appelé ensuite pour récupérer le dernier'D """
        if lstDonnees:
            if len(lstDonnees[0]) != 2: raise("lstDonnees doit être une liste de tuples (champ,donnee)")
            lsttemp=[]
            lstChamps=[]
            lstlstDonnees = []
            for (champ,donnee) in lstDonnees:
                lstChamps.append(champ)
                lsttemp.append(donnee)
            lstlstDonnees.append(lsttemp)
        if len(lstChamps)* len(lstlstDonnees) == 0:
            if affichError:
                wx.MessageBox('%s\n\nChamps ou données absents'%mess,
                              'Echec ReqInsert', style= wx.ICON_STOP)
            return '%s\n\nChamps ou données absents'%mess
        valeurs = self.DonneesInsert(lstlstDonnees)
        champs = '( ' + str(lstChamps)[1:-1].replace('\'','') +' )'
        req = """INSERT INTO %s 
              %s 
              VALUES %s ;""" % (nomTable, champs, valeurs)
        self.retourReq = "ok"
        self.newID= 0
        try:
            # Enregistrement
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
            # Récupération de l'ID
            if self.typeDB == 'mysql' :
                # Version MySQL
                self.cursor.execute("SELECT LAST_INSERT_ID();")
            else:
                # Version Sqlite
                self.cursor.execute("SELECT last_insert_rowid() FROM %s" % nomTable)
            self.newID = self.cursor.fetchall()[0][0]
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess +'\n\n'
            else: self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq +=  ("ReqInsert:\n%s\n\nErreur detectee:\n%s"% (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def CoupleMAJ(self,champ, valeur):
        nonetype = type(None)
        if isinstance(valeur,(int,float)):
            val = "%s, " %str(valeur)
        elif isinstance(valeur, (nonetype)):
            val = "NULL, "
        elif isinstance(valeur, (tuple, list,dict)):
            val = str(valeur)[1:-1]
            val = val.replace("'","")
            val = "'%s', "%val
        else: val = "\"%s\", "%str(valeur)
        couple = " %s = %s"%(champ,val)
        return couple

    def DonneesMAJ(self,donnees):
        # décompacte les données en une liste de couples pour requêtes MAJ
        donneesCouples = ""
        if isinstance(donnees, (tuple,list)):
            for (champ,valeur) in donnees:
                couple = self.CoupleMAJ(champ, valeur)
                donneesCouples += "%s"%(couple)
        elif isinstance((donnees,dict)):
            for (champ, valeur) in donnees.items():
                couple = self.CoupleMAJ(champ, valeur)
                donneesCouples += "%s" % (couple)
        else: return None
        donneesCouples = donneesCouples[:-2]+' '
        return donneesCouples

    def ListesMAJ(self,lstChamps,lstDonnees):
        # assemble des données en une liste de couples pour requêtes MAJ
        donneesCouples = ''
        for ix in range(len(lstChamps)):
            couple = self.CoupleMAJ(lstChamps[ix], lstDonnees[ix])
            donneesCouples += "%s"%(couple)
        donneesCouples = donneesCouples[:-2]+' '
        return donneesCouples

    def ReqMAJ(self, nomTable='',
               lstDonnees=None,
               nomChampID=None,ID=None,condition=None,
               lstValues=[],lstChamps=[],
               mess=None, affichError=True, IDestChaine = False):
        """ Permet de mettre à jour des lstDonnees présentées en dic ou liste de tuples"""
        # si couple est None, on en crée à partir de lstChamps et lstValues
        if lstDonnees :
            update = self.DonneesMAJ(lstDonnees)
        elif (len(lstChamps) > 0) and (len(lstChamps) == len(lstValues)):
            update = self.ListesMAJ(lstChamps,lstValues)
        if nomChampID and ID:
            # un nom de champ avec un ID vient s'ajouter à la condition
            if IDestChaine == False and (isinstance(ID, int )):
                condID = " (%s=%d) "%(nomChampID, ID)
            else:
                condID = " (%s='%s') "%(nomChampID, ID)
            if condition:
                condition += " AND %s "%(condID)
            else: condition = condID
        elif (not condition) or (len(condition.strip())==0):
            # si pas de nom de champ et d'ID, la condition ne doit pas être vide sinon tout va updater
            condition = " FALSE "
        req = "UPDATE %s SET  %s WHERE %s ;" % (nomTable, update, condition)
        # Enregistrement
        try:
            self.cursor.execute(req,)
            self.Commit()
            self.retourReq = "ok"
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess + '\n\n'
            else:
                self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq += ("ReqMAJ:\n%s\n\nErreur detectee:\n%s" % (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def ReqDEL(self, nomTable,champID="",ID=None, condition="", commit=True, mess=None, affichError=True):
        """ Suppression d'un enregistrement ou d'un ensemble avec condition de type where"""
        if len(condition)==0:
            condition = champID+" = %d"%ID
        self.retourReq = "ok"
        req = "DELETE FROM %s WHERE %s ;" % (nomTable, condition)
        try:
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
                self.retourReq = "ok"
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess + '\n\n'
            else:
                self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq += ("ReqMAJ:\n%s\n\nErreur detectee:\n%s" % (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def Commit(self):
        if self.connexion:
            self.connexion.commit()

    def Close(self):
        try :
            self.connexion.close()
            del DICT_CONNEXIONS[self.IDconnexion]
        except :
            pass

    def SupprChamp(self, nomTable="", nomChamp = ""):
        """ Suppression d'une colonne dans une table """
        if self.isNetwork == False :
            lstChamps = self.GetListeChamps(nomTable)
            index = 0
            varChamps = ""
            varNomsChamps = ""
            for nomTmp, typeTmp in lstChamps :
                if nomTmp == nomChamp :
                    lstChamps.pop(index)
                    break
                else:
                    varChamps += "%s %s, " % (nomTmp, typeTmp)
                    varNomsChamps += nomTmp + ", "
                index += 1
            varChamps = varChamps[:-2]
            varNomsChamps = varNomsChamps[:-2]

            # Procédure de mise à jour de la table
            req = ""
            req += "BEGIN TRANSACTION;"
            req += "CREATE TEMPORARY TABLE %s_backup(%s);" % (nomTable, varChamps)
            req += "INSERT INTO %s_backup SELECT %s FROM %s;" % (nomTable, varNomsChamps, nomTable)
            req += "DROP TABLE %s;" % nomTable
            req += "CREATE TABLE %s(%s);" % (nomTable, varChamps)
            req += "INSERT INTO %s SELECT %s FROM %s_backup;" % (nomTable, varNomsChamps, nomTable)
            req += "DROP TABLE %s_backup;" % nomTable
            req += "COMMIT;"
            self.cursor.executescript(req)
        else:
            # Version MySQL
            req = "ALTER TABLE %s DROP %s;" % (nomTable, nomChamp)
            self.ExecuterReq(req)
            self.Commit()

    def AjoutChamp(self, nomTable = "", nomChamp = "", dicTables = None):
        req = None
        if dicTables:
            for champ,typeChamp,comment in dicTables[nomTable]:
                if nomChamp.lower().strip() != champ.lower().strip(): continue
                comment = comment.replace("'","''")
                req = "ALTER TABLE %s ADD %s %s COMMENT '%s';" % (nomTable, champ, typeChamp, comment)
        if req:
            ret = self.ExecuterReq(req)
            if ret == 'ok': self.Commit()
        else:
            ret = "ECHEC Ajout table.champ: %s.%s"%(nomTable,nomChamp)
        return ret

    def ModifNomChamp(self, nomTable="", nomChampOld="", nomChampNew=""):
        """ Pour renommer un champ - Ne fonctionne qu'avec MySQL """

        ret = "Champ %s non trouvé dans table %s"%(nomChampOld,nomTable)
        typeChamp = None
        for champ,tip in self.GetListeChamps(nomTable):
            if champ == nomChampOld:
                typeChamp = tip

        if self.isNetwork == True and typeChamp:
            req = "ALTER TABLE %s CHANGE %s %s %s;" % (nomTable, nomChampOld, nomChampNew, typeChamp)
            ret = self.ExecuterReq(req)
        if ret == 'ok': self.Commit()
        return ret

    def ModifTypeChamp(self, nomTable="", nomChamp="", typeChamp=""):
        """ Pour convertir le type d'un champ """
        ret = """ Ne fonctionne qu'avec MySQL """
        if self.isNetwork == True :
            req = "ALTER TABLE %s CHANGE %s %s %s;" % (nomTable, nomChamp, nomChamp, typeChamp)
            ret = self.ExecuterReq(req)
            if ret == 'ok': self.Commit()
            return ret

    def IsTableExists(self, nomTable=""):
        """ Vérifie si une table donnée existe dans la base """
        tableExists = False
        if not self.lstTables :
            # ne charge qu'une fois la liste des tables
            self.lstTables = self.GetListeTables()
        if nomTable.lower() in self.lstTables :
            tableExists = True
        return tableExists

    def IsIndexExists(self, nomIndex=""):
        """ Vérifie si un index existe dans la base """
        indexExists = False
        if not self.lstIndex :
            # ne charge qu'une fois la liste des tables
            self.lstIndex = self.GetListeIndex()
        if nomIndex in self.lstIndex :
            indexExists = True
        return indexExists

    def CtrlTables(self, parent, dicTables, tables):
        # création de table ou ajout|modif des champs selon description fournie
        if not tables:
            tables = dicTables.keys()
        for nomTable in tables[2:]:
            # les possibles vues sont préfixées v_ donc ignorées
            if nomTable[:2] == "v_":
                continue
            mess = None
            if not self.IsTableExists(nomTable):
                ret = self.CreationUneTable(dicTables=dicTables,nomTable=nomTable)
                mess = "Création de la table de données %s: %s" %(nomTable,ret)
            else:
                # controle des champs
                tableModel = dicTables[nomTable]
                lstChamps = self.GetListeChamps(nomTable)
                lstNomsChamps = [ x[0] for x in lstChamps]
                lstTypesChamps = [ x[1] for x in lstChamps]
                mess = "Champs: "
                for (nomChampModel, typeChampModel, info) in tableModel:
                    ret = None
                    # ajout du champ manquant
                    if not nomChampModel.lower() in lstNomsChamps:
                        ret = self.AjoutChamp(nomTable,nomChampModel,dicTables)
                    else:
                        # modif du type de champ
                        typeChamp = lstTypesChamps[lstNomsChamps.index(nomChampModel.lower())]
                        if not typeChampModel.lower()[:3] == typeChamp[:3]:
                            ret  = self.ModifTypeChamp(nomTable,nomChampModel,typeChampModel)
                        # modif de la longueur varchar
                        elif typeChamp[:3] == "var":
                            lgModel = typeChampModel.split("(")[1].split(")")[0]
                            lg = typeChamp.split("(")[1].split(")")[0]
                            if not lgModel == lg:
                                ret  = self.ModifTypeChamp(nomTable,nomChampModel,typeChampModel)
                    if ret:
                        mess += "; %s.%s: %s"%(nomTable,nomChampModel,ret)
            if mess and mess != "Champs: ":
                print(mess)
                # Affichage dans la StatusBar
                if parent and mess:
                    parent.mess += "%s %s, "%(nomTable,ret)
                    parent.SetStatusText(parent.mess[-200:])
        parent.mess += "- CtrlTables Terminé"
        parent.SetStatusText(parent.mess[-200:])

    def DropUneTable(self,nomTable=None):
        if nomTable == None : return "Absence de nom de table!!!"
        req = "DROP TABLE %s " % nomTable
        retour = self.ExecuterReq(req)
        if retour == "ok":
                self.Commit()
        print(retour)
        return retour
        #fin DropUneTable

    def CreationUneTable(self, dicTables={},nomTable=None):
        if nomTable == None : return "Absence de nom de table!!!"
        req = "CREATE TABLE IF NOT EXISTS %s (" % nomTable
        for nomChamp, typeChamp, comment in dicTables[nomTable]:
            comment = comment.replace("'", "''")
            # Adaptation à Sqlite
            if self.typeDB == 'sqlite' and typeChamp == "LONGBLOB" : typeChamp = "BLOB"
            # Adaptation à MySQL :
            if self.isNetwork == True and typeChamp == "INTEGER PRIMARY KEY AUTOINCREMENT" :
                typeChamp = "INTEGER PRIMARY KEY AUTO_INCREMENT"
            if self.isNetwork == True and typeChamp == "FLOAT" : typeChamp = "REAL"
            if self.isNetwork == True and typeChamp == "DATE" : typeChamp = "VARCHAR(10)"
            if self.isNetwork == True and typeChamp.startswith("VARCHAR") :
                nbreCaract = int(typeChamp[typeChamp.find("(")+1:typeChamp.find(")")])
                if nbreCaract > 255 :
                    typeChamp = "TEXT(%d)" % nbreCaract
                if nbreCaract > 20000 :
                    typeChamp = "MEDIUMTEXT"
            # ------------------------------
            req = req + "%s %s , " % (nomChamp, typeChamp)
            if not self.typeDB == 'sqlite':
                req = req[:-2] + "COMMENT '%s' , " %(comment,)
        req = req[:-2] + ");"
        retour = self.ExecuterReq(req)
        if retour == "ok":
                self.Commit()
        return retour
        #fin CreationUneTable

    def TestTables(self, parent,dicTables, tables):
        if not tables:
            tables = dicTables.keys()
        retour = 'ok'
        for nomTable in tables:
            if self.IsTableExists(nomTable):
                continue
            retour = 'KO'
            mess = "Manque table %s, " %(nomTable)
            print(mess)
        if self and retour == 'KO':
            mess = "Des tables manquent dans cette base de donnée\n\n"
            mess += "Identifiez-vous en tant qu'admin pour pouvoir les créer, ou changez de base"
            wx.MessageBox(mess,"Création de tables nécessaires")

    def CreationTables(self, parent,dicTables, tables):
        if not tables:
            #tables = [x for x in dicTables.keys()]
            tables = dicTables.keys()
        nb = 0
        for nomTable in tables:
            if self.IsTableExists(nomTable):
                continue
            ret = self.CreationUneTable(dicTables=dicTables,nomTable=nomTable)
            mess = "Création de la table de données %s: %s" %(nomTable,ret)
            print(mess)
            if ret == 'ok': nb +=1
            # Affichage dans la StatusBar
            if parent:
                parent.mess += "%s %s, "%(nomTable,ret)
                parent.SetStatusText(parent.mess[-200:])
        if parent:
            parent.mess += "- Creation %d tables Terminé, "%nb
            parent.SetStatusText(parent.mess[-200:])

    def CreationIndex(self,nomIndex=None,dicIndex=None):
        try:
            """ Création d'un index """
            nomTable = dicIndex[nomIndex]["table"]
            nomChamp = dicIndex[nomIndex]["champ"]
        except Exception as err:
            return "Création index: %s"%str(err)

        retour = "Absence de table: %s"%nomTable
        if self.IsTableExists(nomTable) :
            #print "Creation de l'index : %s" % nomIndex
            if nomIndex[:7] == "PRIMARY":
                if self.typeDB == 'sqlite':
                    req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
                else:
                    req = "ALTER TABLE %s ADD PRIMARY KEY (%s);" % (nomTable, nomChamp)
            elif nomIndex[:2] == "PK":
                req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            else :
                req = "CREATE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            retour = self.ExecuterReq(req)
            if retour == "ok":
                    self.Commit()
        return retour

    def CreationTousIndex(self,parent,dicIndex,tables):
        """ Création de tous les index """
        for nomIndex, dict in dicIndex.items() :
            if not 'table' in dict:
                raise Exception("Structure incorrecte: shema Index '%s' - absence cle 'table'"%nomIndex)
            if not dict['table'] in tables: continue

            if nomIndex[:7] == "PRIMARY" and self.typeDB != 'sqlite':
                nomIndex = "PRIMARY"
                # test de présence car non détecté par la liste des index
                req = """
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE   table_name = '%s'
                            AND  constraint_name = 'PRIMARY';"""%(dict['table'])
                retour = self.ExecuterReq(req)
                if retour == 'ok':
                    recordset = self.ResultatReq()
                    if len(recordset)>0:
                        # primary exists on passe
                        continue
            if not self.IsIndexExists(nomIndex) :
                ret = self.CreationIndex(nomIndex,dicIndex)
                mess = "Création de l'index %s: %s" %(nomIndex,ret)
                # Affichage dans la StatusBar
                if parent:
                    parent.mess += "%s %s, " % (nomIndex, ret)
                    parent.SetStatusText(parent.mess)
        if parent:
            if parent.mess[-17:] == "Index PK Terminés":
                parent.mess += "- Index alt Terminés"
            else:
                parent.mess += "- Index PK Terminés"
            parent.SetStatusText(parent.mess[-200:])

    def GetDataBases(self):
        self.cursor.execute("SHOW DATABASES;")
        listeBases = self.cursor.fetchall()
        return listeBases

    def GetListeTables(self,lower=True):
        # appel des tables et des vues
        if self.typeDB == 'sqlite' :
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            self.ExecuterReq(req)
            recordset = self.ResultatReq()
        else:
            # Version MySQL
            req = "SHOW FULL TABLES;"
            self.ExecuterReq(req)
            recordset = self.ResultatReq()
        lstTables = []
        for record in recordset:
            if lower:
                lstTables.append(record[0].lower())
            else: lstTables.append(record[0])
        return lstTables

    def GetListeChamps(self, nomTable=""):
        """ retrourne la liste des tuples(nom,type) des champs de la table donnée """
        lstChamps = []
        # dict de tables de liste
        if not hasattr(self,"ddTablesChamps"):
            self.dlTablesChamps = {}
        # un seul appel par table
        if not nomTable in self.dlTablesChamps.keys():
            if self.typeDB == 'sqlite':
                # Version Sqlite
                req = "PRAGMA table_info('%s');" % nomTable
                self.ExecuterReq(req)
                listeTmpChamps = self.ResultatReq()
                for valeurs in listeTmpChamps:
                    lstChamps.append((valeurs[1], valeurs[2]))
            else:
                # Version MySQL
                req = "SHOW COLUMNS FROM %s;" % nomTable
                self.ExecuterReq(req)
                listeTmpChamps = self.ResultatReq()
                for valeurs in listeTmpChamps:
                    lstChamps.append((valeurs[0].lower(), valeurs[1].lower()))
            self.dlTablesChamps[nomTable] = lstChamps
        # la table a déjà été appellée
        else: lstChamps = self.dlTablesChamps[nomTable]
        return lstChamps

    def GetListeIndex(self):
        if self.typeDB == 'sqlite':
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"
            self.ExecuterReq(req)
            listeIndex = self.ResultatReq()
        else:
            # Version MySQL
            listeIndex = []
            for nomTable in self.GetListeTables(lower=False):
                req = "SHOW INDEX IN %s;" % str(nomTable)
                self.ExecuterReq(req)
                for index in self.ResultatReq():
                    if str(index[2]) != 'PRIMARY':
                        listeIndex.append(str(index[2]))
        return listeIndex

def Init_tables(parent=None, mode='creation',tables=None,db_tables=None,db_ix=None,db_pk=None):
    # actualise ou vérifie la structure des tables : test, creation, ctrl
    if not tables:
        if mode in ('creation', 'test'):
            txt = "de toutes les tables manquantes à l'appli mère"
        else: txt = "de tous les champs des tables de l'appli mère"
        md = wx.MessageDialog(parent,
                "%s %s:\n\n'%s'"%(mode.capitalize(), txt, str(db_tables.keys())[10:-1]),
                style=wx.YES_NO)
        if md.ShowModal() != wx.ID_YES:
            return
        tables = db_tables.keys()

    db = DB()
    if db.echec: return

    if hasattr(db,'cursor'):
        del db.cursor

    db.cursor = db.connexion.cursor(buffered=False)

    if mode != "test" and parent:
        parent.mess = "Lancement créations: "
        parent.SetStatusText(parent.mess)

    if mode == "creation":
        db.CreationTables(parent,db_tables,tables)

        # réinit complet de db pour prendre en compte les nouvelles tables
        del db.cursor
        db.Close()
        db = DB()
        db.cursor = db.connexion.cursor(buffered=False)

        db.CreationTousIndex(parent,db_ix, tables)
        db.CreationTousIndex(parent,db_pk, tables)

    elif mode == "ctrl":
        db.CtrlTables(parent,db_tables,tables)

    elif mode == "test":
        db.TestTables(parent,db_tables,tables)

    db.Close() # fermeture pour prise en compte de la création

if __name__ == "__main__":
    app = wx.App()
    os.chdir("..")
    db = DB()
    db.AfficheTestOuverture()
    #db.MaFonctionTest()
    #db.DropUneTable('cpta_journaux')
    #from srcNoelite.DB_schema import DB_TABLES, DB_IX, DB_PK
    #db.CreationUneTable(DB_TABLES,'stEffectifs')
    #db.CreationTables(None,dicTables=DB_TABLES,tables=['stArticles','stEffectifs','stMouvements','stInventaires','cpta_analytiques'])
    #db.CreationTousIndex(None,DB_PK,['stEffectifs',])
