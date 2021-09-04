# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# -------------------------------------------------------------------------------------
# Services : Services d'accès à Noethys par le web
# -------------------------------------------------------------------------------------


# exemple de fichier .json 'paramètres de connexion' à placer sur '/etc'
AUTHENTIFICATION_JSON = {
    "host": "x.x.x.x",
    "port": "3306",
    "userdb": "user_mysql",
    "passwd": "xxxxx",
}

from pathlib import Path
import json
import xpy.xUTILS_DB as xdb

class Authentification(object):
    # services de connexion
    def __init__(self, **kwds):
        # établissement du connecteur
        self.mute = kwds.get('mute',True) # mute désactive les print pour suivi des tests
        self.dicAuth = {}
        self.dicUser = None
        self.isConnect = False
        self.isLogin = False

        p = Path('/etc/authentification.json')
        with p.open() as json_auth:
            self.dicAuth = json.load(json_auth)
        if not self.mute:
            print("Init Authentification !")
            print('serveur: %s,'%self.dicAuth['serveur'],'   user:%s'%self.dicAuth['userDB'])
        self.db = xdb.DB(config=self.dicAuth, mute=True)
        if self.db.echec:
            print(self.db.erreur)
        else:
            self.isConnect = True
            self.lstUsers = self.SqlLstUsers()

    def Login(self,idMail,pw):
        self.isLogin = self.GetUser(idMail,pw)
        return

    def GetUser(self,idMail,mdp):
        self.ChercheDicUser(mdp)
        if self.dicUser != None:
            self.isLogin = True
        return self.dicUser

    def ChercheDicUser(self, mdp):
        # Recherche de l'utilisateur pour alimenter dicUser
        for dictUtilisateur in self.lstUsers :
            if mdp == dictUtilisateur["mdp"] :
                dictUtilisateur['utilisateur'] =  dictUtilisateur['prenom'] + " " + dictUtilisateur['nom']
                self.dicUser = {}
                self.dicUser['utilisateur'] =  dictUtilisateur['utilisateur']
                self.dicUser['nom'] = dictUtilisateur['nom']
                self.dicUser['prenom'] = dictUtilisateur['prenom']
                self.dicUser['IDutilisateur'] =  dictUtilisateur['IDutilisateur']
                self.dicUser['droits'] = dictUtilisateur['droits']
                self.dicUser['profil'] = dictUtilisateur['profil']

    def SqlLstUsers(self):
        # Récupère la liste des utilisateurs et de leurs droits
        """ suppose l'accès à une base de donnée qui contient les tables génériques 'utilisateurs' et 'droits'"""
        if self.db.echec:
            return False
        # Droits
        req = """SELECT IDdroit, IDutilisateur, IDmodele, categorie, action, etat
        FROM droits;"""
        self.db.ExecuterReq(req)
        lstDonnees = self.db.ResultatReq()
        dictDroitsUtilisateurs = {}
        dictDroitsModeles = {}
        for IDdroit, IDutilisateur, IDmodele, categorie, action, etat in lstDonnees:
            key = (categorie, action)
            if IDutilisateur != None:
                if not IDutilisateur in dictDroitsUtilisateurs:
                    dictDroitsUtilisateurs[IDutilisateur] = {}
                dictDroitsUtilisateurs[IDutilisateur][key] = etat
            if IDmodele != None:
                if not IDmodele in dictDroitsModeles:
                    dictDroitsModeles[IDmodele] = {}
                dictDroitsModeles[IDmodele][key] = etat
    
        # Utilisateurs
        req = """SELECT IDutilisateur, sexe, nom, prenom, mdp, profil, actif
        FROM utilisateurs
        WHERE actif=1;"""
        self.db.ExecuterReq(req)
        lstDonnees = self.db.ResultatReq()
        listeUtilisateurs = []
    
        for IDutilisateur, sexe, nom, prenom, mdp, profil, actif in lstDonnees:
            droits = None
            if profil.startswith("administrateur"):
                droits = None
            if profil.startswith("modele"):
                IDmodele = int(profil.split(":")[1])
                if IDmodele in dictDroitsModeles:
                    droits = dictDroitsModeles[IDmodele]
            if profil.startswith("perso"):
                if IDutilisateur in dictDroitsUtilisateurs:
                    droits = dictDroitsUtilisateurs[IDutilisateur]
    
            dictTemp = {"IDutilisateur": IDutilisateur, "nom": nom, "prenom": prenom, "sexe": sexe, "mdp": mdp,
                        "profil": profil, "actif": actif, "droits": droits}
            listeUtilisateurs.append(dictTemp)
    
        self.db.Close()
        return listeUtilisateurs

if __name__ == '__main__':
    connect = Authentification(mute = False)
    print(connect.GetUser("toto@gmail.com",'qsdeza'))
