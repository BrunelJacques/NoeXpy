#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, ventilation des Reglements
# Usage:           trace les actions dans la table historique
# Auteur:           Ivan LUCAS, traduit python3 Jacques BRUNEL
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import wx
import xpy.xUTILS_DB       as xdb

def VerificationDroits(dictUtilisateur=None, categorie="", action="", IDactivite=""):
    """ Vérifie si un utilisateur peut accéder à une action """
    if ((dictUtilisateur == None) or ("droits" in dictUtilisateur)) == False :
        return True
    
    dictDroits = dictUtilisateur["droits"]
    key = (categorie, action)
        
    if (dictDroits != None) and (key in dictDroits) :
        etat = dictDroits[key]
        # Autorisation
        if etat.startswith("autorisation") :
            return True
        # Interdiction
        if etat.startswith("interdiction") :
            return False
        # Restriction
        if etat.startswith("restriction") :
            code = etat.replace("restriction_", "")
            mode, listeID = code.split(":")
            listeID = [int(x) for x in listeID.split(";")]
                        
            if mode == "groupes" :
                if len(listeID) == 1 : condition = "IDtype_groupe_activite=%d" % listeID[0]
                if len(listeID) >1 : condition = "IDtype_groupe_activite IN %s" % str(tuple(listeID))
                DB = xdb.DB()
                req = """SELECT IDgroupe_activite, activites 
                FROM groupes_activites
                WHERE %s;""" % condition
                DB.ExecuterReq(req)
                lstDonnees = DB.ResultatReq()
                listeActivites = []
                for IDgroupe_activite, IDactivite_temp in lstDonnees :
                    listeActivites.append(IDactivite_temp)
                DB.Close()
                
            if mode == "activites" :
                listeActivites = listeID
            
            if IDactivite in listeActivites :
                return True
            else :                
                return False

    return True
    
def VerificationDroitsUtilisateurActuel(categorie="", action="", IDactivite="", afficheMessage=True):
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
        dictUtilisateur = topWindow.dictUser
    except :
        dictUtilisateur = None
    if not dictUtilisateur:
        try :
            import xpy.outils.xshelve as xucfg
            cfg = xucfg.ParamUser()
            dictUtilisateur = cfg.GetDict(groupe='USER')
        except:
            pass
    if dictUtilisateur:
        # Si la frame 'General' est chargée, on y récupère le dict de config
        resultat = VerificationDroits(dictUtilisateur, categorie, action, IDactivite)
        if resultat == False and afficheMessage == True :
            wx.MessageBox("'%s'\n\nVotre profil utilisateur  ne permet pas d'accéder à la fonctionnalité demandée!\n'%s' - '%s'"
                          %(dictUtilisateur['nom'],categorie,action),style=wx.ICON_AUTH_NEEDED)
        return resultat
    return True

def GetIDutilisateur(afficheMessage=True):
    try :
        topWindow = wx.GetApp().GetTopWindow()
        dictUtilisateur = topWindow.dictUser
    except :
        dictUtilisateur = None
    if not dictUtilisateur:
        try :
            import xpy.outils.xshelve as xucfg
            cfg = xucfg.ParamUser()
            dictUtilisateur = cfg.GetDict(groupe='USER')
        except:
            pass
    if 'IDutilisateur' in dictUtilisateur.keys():
        # Si la frame 'General' est chargée, on y récupère le dict de config
        return dictUtilisateur['IDutilisateur']
    else:
        if afficheMessage == True :
            wx.MessageBox("Vous n'êtes pas identifiés\n\nrepassez par l'entrée",style=wx.ICON_AUTH_NEEDED)
    return None

def GetDictUtilisateur(afficheMessage=True):
    try :
        topWindow = wx.GetApp().GetTopWindow()
        dictUtilisateur = topWindow.dictUser
    except :
        dictUtilisateur = None
    if not dictUtilisateur:
        try :
            import xpy.outils.xshelve as xucfg
            cfg = xucfg.ParamUser()
            dictUtilisateur = cfg.GetDict(groupe='USER')
        except:
            pass
    if dictUtilisateur:
        # Si la frame 'General' est chargée, on y récupère le dict de config
        return dictUtilisateur
    else:
        if afficheMessage == True :
            wx.MessageBox("Vous n'êtes pas identifiés\n\nrepassez par l'entrée",style=wx.ICON_AUTH_NEEDED)
    return None

class CTRL_Bouton_image(wx.Button):
    # La classe xGestion_TableauEditor.Button reprend le concept de manière plus large
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    print(VerificationDroits({'IDutilisateur': 2, 'nom': 'LORIOL', 'prenom': 'Isabelle', 'sexe': 'F', 'mdp': 'lor', 'profil': 'administrateur', 'actif': 1, 'droits': None},
                             "parametrage_modes_reglements", "supprimer"))
    print(VerificationDroitsUtilisateurActuel("parametrage_modes_reglements", "supprimer"))
    print(GetIDutilisateur(),GetDictUtilisateur()['nom'])