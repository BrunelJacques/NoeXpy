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
import xpy.xUTILS_Shelve as xucfg

DICT_CONNEXIONS = {}

def NoPunctuation(txt = ''):
    import re
    punctuation = u"'!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'"
    regex = re.compile('[%s]' % re.escape(punctuation))
    return regex.sub(' ', txt)

def Supprime_accent(texte):
    liste = [ (u"é", u"e"), (u"è", u"e"), (u"ê", u"e"), (u"ë", u"e"), (u"à", u"a"), (u"û", u"u"), (u"ô", u"o"), (u"ç", u"c"), (u"î", u"i"), (u"ï", u"i"),]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateDDEnDateEng(datedd):
    if not isinstance(datedd, datetime.date):
        return '1900-01-01'
    aaaa = str(datedd.year)
    mm = ('00'+str(datedd.month))[-2:]
    jj = ('00'+str(datedd.day))[-2:]
    return aaaa+'-'+mm+'-'+jj

class DB():
    # accès à la base de donnees principale
    def __init__(self, IDconnexion = None, config=None, typeConfig='db_prim', nomFichier=None, mute=False):
        # config peut être soit un nom de config soit un dictionaire
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
            # appel des params de connexion stockés dans UserProfile
            cfg = xucfg.ParamUser()
            grpUSER= cfg.GetDict(groupe='USER',close=False)
            grpAPPLI = cfg.GetDict(groupe='APPLI',close=False)
            self.dictAppli = grpAPPLI
            if 'TYPE_CONFIG' in grpAPPLI:
                typeConfig= grpAPPLI['TYPE_CONFIG']

            nomAppli = grpAPPLI.pop('NOM_APPLICATION',None)
            # appel des params de connexion stockés dans Data
            cfg = xucfg.ParamFile()
            grpCONFIGS= cfg.GetDict(groupe='CONFIGS')
            self.grpConfigs = grpCONFIGS
            # recherche du nom de configuration par défaut, cad la dernière des choix
            if 'choixConfigs' in grpCONFIGS:
                if nomAppli and nomAppli in grpCONFIGS['choixConfigs'].keys():
                    if 'lastConfig' in grpCONFIGS['choixConfigs'][nomAppli].keys():
                        nomConfig = grpCONFIGS['choixConfigs'][nomAppli]['lastConfig']
            else: nomConfig=None
            try:
                # priorité la config passée en kwds puis recherche de la dernière config dans 'USER'
                if config:
                    # Présence de kwds 'config', peut être le nom de la config ou un dictionaire de configuration
                    if isinstance(config, str):
                        nomConfig = config
                    elif isinstance(config,dict):
                        nomConfig = None
                        self.cfgParams = copy.deepcopy(config)
                if nomConfig:
                    if 'lstConfigs' in grpCONFIGS:
                        lstNomsConfigs = [x[typeConfig]['ID'] for x in grpCONFIGS['lstConfigs']]
                        if not (nomConfig in lstNomsConfigs):
                            mess = "xDB: Le nom de config '%s' n'est pas dans la liste des accès base de donnée"%(nomConfig)
                            self.erreur = mess
                            if not mute:
                                wx.MessageBox(mess)
                            return mess
                        ix = lstNomsConfigs.index(nomConfig)
                        # on récupére les paramétres dans toutes les configs par le pointeur ix dans les clés
                        self.cfgParams = grpCONFIGS['lstConfigs'][ix][typeConfig]
                # on ajoute les choix pris dans grpUSER,  pour mot passe, aux paramètres de la config retenue
                if self.cfgParams:
                    for cle, valeur in grpUSER.items():
                        self.cfgParams[cle] = valeur
                    if self.cfgParams['serveur'][-1:] in ('/','\\'):
                        self.nomBase = self.cfgParams['serveur']+self.cfgParams['nameDB']
                    else:
                        self.nomBase = self.cfgParams['serveur']+'\\'+self.cfgParams['nameDB']
            except Exception as err:
                mess = "xDB: La récup des identifiants de connexion a échoué : \nErreur detectee :%s" % err
                if not mute:
                    wx.MessageBox(mess)
                self.erreur = err
                return mess
            if not self.cfgParams : return
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
            raise NameError("Pas de réponse du serveur %s à la commande PING\n\n%s"%(serveur,mess))
            ret = 'ko'
        else: ret = 'ok'
        return ret

    def AfficheTestOuverture(self):
        style = wx.ICON_STOP
        if self.echec == 0: style = wx.ICON_INFORMATION
        accroche = ['Ouverture réussie',"Echec d'ouverture"][self.echec]
        retour = ['avec succès', ' SANS SUCCES !\n'][self.echec]
        mess = "%s\n\nL'accès à la base '%s' s'est réalisé %s" % (accroche,self.nomBase, retour)
        if self.erreur:
            mess += '\nErreur: %s'%self.erreur
        wx.MessageBox(mess, style=style)

    def CreateBaseMySql(self, config):
        """ Version RESEAU avec MYSQL """
        try:
            # Récupération des paramètres de connexion
            host = config['serveur']
            port = config['port']
            nomBase = config['nameDB']
            user = config['userDB']
            passwd = config['mpUserDB']

            # usage de  "mysql.connector":
            self.connexion = mysql.connector.connect(**self.dictConnector)

            self.cursor = self.connexion.cursor()
            # Création
            self.cursor.execute(
                "CREATE DATABASE IF NOT EXISTS %s CHARSET utf8 COLLATE utf8_unicode_ci;" % nomBase)

            # Utilisation
            if nomBase not in ("", None):
                self.cursor.execute("USE %s;" % nomBase)

        except Exception as err:
            print( "La connexion avec la base de donnees MYSQL a echouee. Erreur :")
            print(err, )
            self.erreur = err
            self.echec = 1
            # AfficheConnexionOuvertes()
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
            nomFichier = config['nameDB']
            etape = 'Ping %s'%(host)
            ret = self.Ping(host)
            if not ret == 'ok':
                self.echec = 1
                self.connexion = None
                return
            etape = 'Création du connecteur %s - %s - %s - %s'%(host,userdb,passwd, port)
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
            DSN = ('PROVIDER = Microsoft.Jet.OLEDB.4.0;DATA SOURCE = ' + self.nomBase + ';')
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
                self.cursor.execute(req)
                self.retourReq = 'ok'
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess +'\n\n'
            else: self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq +=  ("ExecuterReq:\n%s\n\nErreur detectee:\n%s"% (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def Executermany(self, req="", listeDonnees=[], commit=True):
        """ Executemany pour local ou réseau """
        """ Exemple de req : "INSERT INTO table (IDtable, nom) VALUES (?, ?)" """
        """ Exemple de listeDonnees : [(1, 2), (3, 4), (5, 6)] """
        # Adaptation réseau/local
        if self.isNetwork == True :
            # Version MySQL
            req = req.replace("?", "%s")
        else:
            # Version Sqlite
            req = req.replace("%s", "?")
        # Executemany
        self.cursor.executemany(req, listeDonnees)
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
            lsttemp=[]
            lstChamps=[]
            lstlstDonnees = []
            for (champ,donnee) in lstDonnees:
                lstChamps.append(champ)
                lsttemp.append(donnee)
            lstlstDonnees.append(lsttemp)
        if len(lstChamps)* len(lstlstDonnees) == 0:
            if affichError:
                wx.MessageBox('%s\n\nChamps ou données absents'%mess)
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

    def ReqMAJ(self, nomTable='',couples=None,nomChampID=None,ID=None,condition=None,lstDonnees=[],lstChamps=[],
               mess=None, affichError=True, IDestChaine = False):
        """ Permet de mettre à jour des couples présentées en dic ou liste de tuples"""
        # si couple est None, on en crée à partir de lstChamps et lstDonnees
        if couples :
            update = self.DonneesMAJ(couples)
        elif (len(lstChamps) > 0) and (len(lstChamps) == len(lstDonnees)):
            update = self.ListesMAJ(lstChamps,lstDonnees)
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
            listeChamps = self.GetListeChamps2(nomTable)

            index = 0
            varChamps = ""
            varNomsChamps = ""
            for nomTmp, typeTmp in listeChamps :
                if nomTmp == nomChamp :
                    listeChamps.pop(index)
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
        if not self.IsChampExists(nomTable,nomChamp):
            if dicTables:
                for champ,typeChamp,comment in dicTables[nomTable]:
                    if nomChamp.lower().strip() != champ.strip(): continue
                    comment = comment.replace("'","''")
                    req = "ALTER TABLE %s ADD %s %s COMMENT '%s';" % (nomTable, champ, typeChamp, comment)
            if req:
                ret = self.ExecuterReq(req)
                self.Commit()
                print(req , "----- ", ret)
            else: print("ECHEC Ajout table.champ: %s.%s"%(nomTable,nomChamp))

    def IsChampExists(self, nomTable="",nomChamp=""):
        """ Vérifie si le champ d'une table existe dans la base """
        champExists = False
        req = """SELECT *
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '%s'
                AND COLUMN_NAME = '%s'"""%(nomTable,nomChamp)
        ret = self.ExecuterReq(req)
        if ret == 'ok':
            recordset = self.ResultatReq()
            if len(recordset) >0:
                champExists = True
        return champExists

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

    def CreationUneTable(self, dicTables={},nomTable=None):
        #dicTables = DB_schema.DB_TABLES
        retour = None
        if nomTable == None : return "Absence de nom de table!!!"
        req = "CREATE TABLE IF NOT EXISTS %s (" % nomTable
        for nomChamp, typeChamp, comment in dicTables[nomTable]:
            comment = comment.replace("'", "''")
            # Adaptation à Sqlite
            if self.isNetwork == False and typeChamp == "LONGBLOB" : typeChamp = "BLOB"
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
            req = req + "%s %s COMMENT '%s', " % (nomChamp, typeChamp, comment)
        req = req[:-2] + ");"
        retour = self.ExecuterReq(req)
        if retour == "ok":
                self.Commit()
        return retour
        #fin CreationUneTable

    def CreationTables(self, dicTables={}, fenetreParente=None):
        for nomTable in dicTables.keys():
            if self.IsTableExists(nomTable):
                continue
            ret = self.CreationUneTable(dicTables=dicTables,nomTable=nomTable)
            mess = "Création de la table de données %s: %s" %(nomTable,ret)
            # Affichage dans la StatusBar
            if fenetreParente == None:
                print(mess)
            else:
                fenetreParente.SetStatusText(mess)

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
            if nomIndex[:2] == "PK":
                req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            else :
                req = "CREATE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            retour = self.ExecuterReq(req)
            if retour == "ok":
                    self.Commit()
        return retour

    def CreationTousIndex(self,dicIndex,fenetreParente=None):
        """ Création de tous les index """
        for nomIndex, temp in dicIndex.items() :
            if not self.IsIndexExists(nomIndex) :
                ret = self.CreationIndex(nomIndex,dicIndex)
                mess = "Création de l'index %s: %s" %(nomIndex,ret)
                # Affichage dans la StatusBar
                if fenetreParente == None:
                    print(mess)
                else:
                    fenetreParente.SetStatusText(mess)

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

    def GetListeChamps2(self, nomTable=""):
        """ Affiche la liste des champs de la table donnée """
        listeChamps = []
        if self.typeDB == 'sqlite':
            # Version Sqlite
            req = "PRAGMA table_info('%s');" % nomTable
            self.ExecuterReq(req)
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps:
                listeChamps.append((valeurs[1], valeurs[2]))
        else:
            # Version MySQL
            req = "SHOW COLUMNS FROM %s;" % nomTable
            self.ExecuterReq(req)
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps:
                listeChamps.append((valeurs[0], valeurs[1]))
        return listeChamps

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

    def MaFonctionTest(self):
        import pyodbc
        """Important: 32bit MS driver - 32bit python!"""
        """N'est pas compatible access 95"""
        cnxn = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=c:/temp/test.mdb;')
        cursor = cnxn.cursor()
        cursor.execute("select * from table1")
        for row in cursor.fetchall():
            print(row)

        csr = cnxn.cursor()
        csr.close()
        del csr
        cnxn.close()

        import mysql
        cnx = mysql.connector.connect(host='192.168.1.43', user='root', database='matthania_data',password='xxxxx')
        cursor = cnx.cursor()

        query = ("SELECT * FROM caisses")

        cursor.execute(query)

        for ligne in cursor:
          print(ligne)

        cursor.close()
        cnx.close()



        import pymysql.cursors

        # Connect to the database
        connection = pymysql.connect(host='192.168.1.43',
                                     user='root',
                                     password='xxxxx',
                                     db='matthania_data',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)

        try:
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT * FROM `caisses` "
                cursor.execute(sql,)
                for ligne in cursor:
                    print(ligne)

                result = cursor.fetchmany(size=2)
                print(result)


            with connection.cursor() as cursor:
                # Create a new record
                sql = "SELECT IDcaisse FROM caisses;"
                cursor.execute(sql, ('IDcaisse',))
                result = cursor.fetchone()
                print(result)

            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()

            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
                cursor.execute(sql, ('webmaster@python.org',))
                result = cursor.fetchone()
                print(result)

        finally:
            connection.close()

def Init_tables():
    os.chdir("..")
    db = DB()
    print("echec ouverture: ",db.echec)
    from srcNoelite.DB_schema import DB_TABLES, DB_IX, DB_PK
    db.CreationTables(dicTables=DB_TABLES)
    db.CreationTousIndex(DB_IX)
    db.CreationTousIndex(DB_PK)

if __name__ == "__main__":
    app = wx.App()
    os.chdir("..")
    db = DB()
    print("test echec ouverture: ",db.echec)
    from srcNoelite.DB_schema import DB_TABLES, DB_IX, DB_PK
    db.CreationTables(dicTables=DB_TABLES)
    db.CreationTousIndex(DB_IX)
    db.CreationTousIndex(DB_PK)
