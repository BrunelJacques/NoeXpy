#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Matthania Janvier 2020
# Auteur:          Jacques BRUNEL 
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import xpy.xUTILS_DB as xdb
import xpy.outils.xchoixListe as xcl
import re
import datetime

def NoPunctuation(txt = u''):
    if not txt: return u''
    if txt.strip()== u'': return u''
    punctuation = "!\"#$%&()*+,./:;<=>?@[\\]^_`{|}~"
    regex = re.compile('[%s]' % re.escape(punctuation))
    regex = regex.sub(' ', txt)
    return regex.replace('  ',' ')

def Normalisation(lstAdresse):
    # formate majuscules sans ponctuations, tronque la longueur (pour modifier l'ordre des champs, cf TransposeAdresse)
    if len(lstAdresse) == 6 : lstAdresse.append("")
    if len(lstAdresse) != 7 :
        mess = "Adresse au nombre de ligne non conforme\n\n%s"
        for ligne in lstAdresse: mess += "%s\n"%ligne
        wx.MessageBox(mess)
    for i in range(2,6):
        lstAdresse[i] = NoPunctuation(lstAdresse[i]).upper()
    for i in range(6):
        lstAdresse[i] = lstAdresse[i].strip().replace(":"," ")
        lgmax = 38 + 1
        lstAdresse[i] = lstAdresse[i][:lgmax].strip()
    return lstAdresse

def CompacteAdresse(lstAdresse):
    # retourne sous forme d'unicode, sans ligne vide, l'adresse reçue en liste
    stradresse = ""
    if not lstAdresse: return "à saisir..."
    i = 0
    for ligne in lstAdresse:
        if i == 4:  sep = " "
        else:       sep = "\n"
        if len(ligne.strip())>0:
            stradresse += ligne + sep
        i += 1
    if len(stradresse) == 0 :return "à saisir..."
    return stradresse[:-1]

def VerifieVille(codepost="",ville="",pays=""):
    # vérifie la présence des éléments dans les possibles retourne ok ou message
    if len(pays)>0 : return "ok"
    # Seulement les adresses en france    if not ville or len(ville.strip()) == 0: return "Ville à blanc."
    if "'"in ville:
        lst = ville.split("'")
        ville = "_".join(lst)
    conditioncp = ""
    filtre = codepost.upper()
    tronque = 0
    # filtrage des zéro non significatifs pour le premier accès
    if len(filtre) > 0:
        while filtre[0] == "0" and len(filtre) > 1:
            tronque += 1
            filtre = filtre[1:]
        if filtre == '0':
            filtre = ""
            tronque += 1
        conditioncp  = "AND cp LIKE '%s%%'"%(filtre)
    for chaine in (ville, conditioncp):
        chaine = chaine.replace("'","''")
    condition = "WHERE nom LIKE '%s' %s "%(ville, conditioncp)
    DB = xdb.DB(nomFichier="srcNoelite/Data/Geographie.dat")
    req = """  SELECT IDville, nom, cp     
                FROM villes 
                %s;"""% condition
    DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.VerifieVille")
    ret = DB.ResultatReq()
    DB.Close()
    if len(ret)== 1:
            if len(pays.strip())==0: return "ok"

    # la ville n'est pas en france avec le code postal
    # Importation des corrections de villes et codes postaux
    DB = xdb.DB()
    ville = ville.replace("'","?")
    condition = "WHERE nom LIKE '%s'" %(ville)
    if len(codepost)>1:
        condition +=" AND cp = '%s'"% codepost

    req = """SELECT IDcorrection, mode, IDville, nom, cp, pays
    FROM corrections_villes %s; """%condition
    DB.ExecuterReq(req, mess="aUTILS_Adresses_saisie.VerifieVille2")
    ret = DB.ResultatReq()
    DB.Close()
    if len(ret)==1: return "ok"
    return "Ville non trouvée avec ce code postal"

def GetVilles(champFiltre="ville",filtre=""):
    # Importation de la base par défaut avec un filtre sur le code postal ou sur le nom de la ville
    if not filtre: filtre = ""
    tronque = 0
    filtre = filtre.upper().replace("'","?")
    filtrecp = filtre
    # filtrage des zéro non significatifs pour le premier accès
    if champFiltre == "cp" and len(filtre) > 0:
        while filtre[0] == "0" and len(filtre) > 1:
            tronque += 1
            filtre = filtre[1:]
        if filtre == '0':
            filtre = ""
            tronque += 1
        condition  = "WHERE %s LIKE '%s%%'"%(champFiltre,filtre)
    else:
        # filtre sur ville
        condition  = "WHERE %s LIKE '%s%%'"%("nom",filtre)

    if len(filtre)==0:
        condition = "WHERE 1 = 0 "
        filtrecp = "zzzzz"

    # Importation des villes par défaut
    DB = xdb.DB(nomFichier="srcNoelite/Data/Geographie.dat")
    req = """   SELECT IDville, nom, cp, NULL 
                FROM villes %s"""%condition
    DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetVilles")
    ret = DB.ResultatReq()
    listeVillesTmp = []
    DB.Close()
    if champFiltre == "cp":
        filtre = "00000"[:tronque] + filtrecp
    for id,nom,cp,pays in ret:
        if len(cp) < 5:
            # Correction du fichier qui ne renvoit pas le zéro devant le code postal
            cp = ("00000" + cp)[-5:]
        if (champFiltre == "cp" and cp[:len(filtre)] == filtre) or (champFiltre == "ville" and nom[:len(filtre)] == filtre):
            listeVillesTmp.append((id,nom,cp,pays))


    # Importation des corrections de villes et codes postaux
    DB = xdb.DB()
    req = """SELECT IDcorrection, mode, IDville, nom, cp, pays
    FROM corrections_villes; """ 
    DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetVilles")
    listeCorrections = DB.ResultatReq()
    DB.Close()
    
    # Ajout des corrections
    dictModifSuppr = {}
    for IDcorrection, mode, IDville, nom, cp, pays in listeCorrections :
        if not pays: pays = ""
        if not nom: nom = ""
        if not cp: cp = ""
        if champFiltre == "cp":
            champ = cp
            filtre = filtrecp
        else: champ = nom

        if condition == "" or champ[:len(filtre)] == filtre:
            if mode == "ajout" :
                listeVillesTmp.append((None, nom, cp, pays))
            else :
                # modification suppression
                dictModifSuppr[IDville] = {"mode":mode, "nom":nom, "cp":cp, "pays":pays}

    listeVilles = []
    for IDville, nom, cp, pays in listeVillesTmp:
        if not pays: pays = ""

        # Traitement des modifs et suppressions
        valide = True
        if IDville in dictModifSuppr :
            if dictModifSuppr[IDville]["mode"] == "modif" :
                nom = dictModifSuppr[IDville]["nom"]
                cp = dictModifSuppr[IDville]["cp"]
                pays = dictModifSuppr[IDville]["pays"]
            if dictModifSuppr[IDville]["mode"] == "suppr" :
                valide = False
        
        # Mémorisation
        if valide == True :
            if pays == "" and len(cp) < 5:
                cp = (cp + "00000")[:5]
            listeVilles.append(( "%s"%cp, nom,"%s"%pays))
    if len(listeVilles) == 0:
        listeVilles.append(("","",""))
    return listeVilles

def GetDepartements():
    # Importation de la base par défaut
    DB = xdb.DB(nomFichier="srcNoelite/Data/Geographie.dat")
    req = """   SELECT num_dep, num_region, departement 
                FROM departements"""
    DB.ExecuterReq(req)
    listeDepartements = DB.ResultatReq()
    DB.Close()
    dictDepartements = {}
    for num_dep, num_region, departement in listeDepartements:
        dictDepartements[num_dep] = (departement, num_region)

    return dictDepartements

def GetRegions():
    # Importation de la base
    DB = xdb.DB(nomFichier="srcNoelite/Data/Geographie.dat")
    req = """   SELECT num_region, region 
                FROM regions"""
    DB.ExecuterReq(req)
    listeRegions = DB.ResultatReq()
    DB.Close()

    dictRegions = {}
    for num_region, region in listeRegions:
        dictRegions[num_region] = region

    return dictRegions

def GetOnePays(filtre=""):
    filtre = filtre.upper().replace("'","?")
    if filtre == "FRANCE":
        wx.MessageBox("La France n'est pas un pays étranger, il faut laisser le champ à blanc!")
        return ""
    if filtre in ("ANGLETERRE","ECOSSE","PAYS DE GALLE"):
        return "ROYAUME UNI"
    if len(filtre)>0:
        condition = "WHERE secteurs.nom LIKE '%s%%'"%filtre
    else: condition = ""
    db = xdb.DB()
    def Requete(condition):
        db = xdb.DB()
        req = """SELECT secteurs.nom
        FROM secteurs
        %s ;"""%condition
        db.ExecuterReq(req,mess="UTILS_Adresses_saisie.GetOnePays")
        return db.ResultatReq()

    lstDonnees = Requete(condition)
    if len(lstDonnees) == 1:
        pays =  lstDonnees[0][0]
    else:
        pays = ""
        if len(lstDonnees) == 0:
            # le pays saisi n'existe pas on propose tout
            lstDonnees = Requete("")
        # Choisir dans la liste
        dlg = xcl.DialogAffiche(lstDonnees=lstDonnees, titre="Précisez le pays",
                                      intro="Si le pays n'existe pas passer par la gestion des pays postaux")
        ret = dlg.ShowModal()
        if ret == wx.OK:
            pays = dlg.GetChoix()[0]
        dlg.Destroy()
    db.Close()
    return pays

    listeListeView = []
    for item in lstDonnees :
        valide = True
        if listeID != None :
            if item[0] not in listeID :
                valide = False
        if valide == True :
            track = Track(item)
            listeListeView.append(track)
            if self.selectionID == item[0] :
                self.selectionTrack = track

def GetDBCorrespondant(IDfamille):
    # Importation de la base par défaut
    DB = xdb.DB()
    IDindividu = None
    designIndiv = None
    lstChamps = ['zero','IDindividu','titulaire','prenom','nom','rue','cp','ville']
    req = """SELECT 0,rattachements.IDindividu,rattachements.titulaire, individus.prenom, individus.nom, 
                    individus.rue_resid, individus.cp_resid, individus.ville_resid
            FROM rattachements 
            INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
            WHERE (((rattachements.IDfamille) = %d));
            """%IDfamille
    DB.ExecuterReq(req)
    lstMembres = DB.ResultatReq()
    if len(lstMembres) == 0:
        wx.MessageBox("Famille '%d' sans aucun membre!"%IDfamille,style=wx.ICON_ERROR)
        return wx.ID_ABORT
    DB.Close()
    lstColonnes =   ["0","ind","tit","prenom","nom","rue","cp","ville"]
    lstWcol =       [0,    80,  30,     120,   120,   180, 60,     180]
    dlg = xcl.DialogAffiche(titre=u"Choisissez un membre ayant une adresse", intro=u"Sinon allez gérer les individus",
                            lstDonnees=lstMembres, lstColonnes=lstColonnes,lstWcol=lstWcol)
    ret = dlg.ShowModal()
    if ret == wx.OK and dlg.GetChoix():
        ix = lstMembres.index(dlg.GetChoix())
        IDindividu = lstMembres[ix][lstChamps.index('IDindividu')]
        prenom = lstMembres[ix][lstChamps.index('prenom')]
        nom = lstMembres[ix][lstChamps.index('nom')]
        designIndiv = "%d - %s %s" % (IDindividu, prenom, nom)
    dlg.Destroy()
    ix = lstChamps.index('ville')
    lstVilles = [x[ix] for x in lstMembres if (x[ix]!= None) and (len(x[ix])>0)]
    if len(lstVilles) == 0:
        # gestion d'absence d'une adresse dans la famille. ID_APPLI est un flag en retour
        return (wx.ID_APPLY,IDindividu,designIndiv)
    return IDindividu

def ChampsToLstAdresse(rue,cp,ville):
    if not rue: rue = ""
    if not cp: cp = ""
    if not ville: ville = ""
    lstRue = [''] * 4 + rue.split("\n")
    lstRue = lstRue[-4:]
    lstVille = ville.split("\n") + [""] * 2
    lstAdresse = lstRue + [cp] + lstVille[:2]
    #lstAdresse = TransposeAdresse(lstAdresse)
    #lstAdresse = Normalisation(lstAdresse)
    return lstAdresse

def LstAdresseToChamps(lstAdresse):
    # éclatement pour alimenter les anciens champs
    rue = ""
    # rue contient 4 lignes même si vides
    for i in range(4):
        ajout = "%s\n"%(lstAdresse[i]).strip()
        rue += ajout
    rue = rue[:-1]
    cp = lstAdresse[4].strip()
    ville = lstAdresse[5].strip()
    # ville avec pays sur 2eme ligne
    if len(lstAdresse[6])>0:
        ville += "\n%s"%lstAdresse[6]
    else: ville += "\n"
    return rue,cp,ville

def GetDBadresse(IDindividu=None,retNom=False):
    # lit dans la base une adresse et retourne une liste de 7 lignes dont certaines à blanc
    adresse = ['']*7
    nom = None
    prenom = None
    if IDindividu and IDindividu >0:
        # Importation de l'adresse de l'individu
        DB = xdb.DB()
        req = """SELECT individus.adresse_auto, individus.rue_resid, individus.cp_resid, individus.ville_resid, 
                        secteurs.nom, individus.adresse_normee,individus.nom,individus.prenom
                FROM individus 
                LEFT JOIN secteurs ON individus.IDsecteur = secteurs.IDsecteur
                WHERE individus.IDindividu = %d
                ;"""%IDindividu
        ret = DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetDBadresse")
        if ret == "ok":
            recordset = DB.ResultatReq()
            # un seul record possible au plus
            for auto,rue,cp,ville,secteur,normee,nom,prenom in recordset:
                # rue et ville peuvent contenir plusieurs lignes à séparer
                if auto and auto >0 and auto != IDindividu:
                    # appel de l'adresse indirecte sur un autre individu
                    adresse,IDindividu, (nom,prenom) = GetDBadresse(auto,retNom=True)
                else:
                    # adresse découpée et complétée.
                    adresse = ChampsToLstAdresse(rue,cp,ville)
        DB.Close()
    if retNom:
        return adresse,IDindividu,(nom,prenom)
    else:
        return adresse,IDindividu

def GetDBfamille(IDfamille=None):
    # lit dans la base les données de la table famille
    dicCorrespondant = {'IDindividu':None,'designation':None,'IDfamille':IDfamille,'designIndiv':""}

    if IDfamille and IDfamille >0:
        # Importation de l'adresse de l'individu
        DB = xdb.DB()
        req = """SELECT familles.adresse_individu, familles.adresse_intitule, individus.prenom, individus.nom
                FROM familles 
                LEFT JOIN individus ON familles.adresse_individu = individus.IDindividu
                WHERE (familles.IDfamille = %d)
                ;"""%IDfamille
        ret = DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetDBfamille")
        if ret == "ok":
            recordset = DB.ResultatReq()
            # un seul record possible au plus
            for IDindividu, designation, prenom, nom in recordset:
                designIndiv = "%d - %s %s" % (IDindividu, prenom, nom)
                dicCorrespondant['IDindividu'] = IDindividu
                dicCorrespondant['designIndiv'] = designIndiv
                dicCorrespondant['designation'] = designation
        DB.Close()
    return dicCorrespondant

def GetDBoldAdresse(IDindividu=None):
    # lit dans la base l'ancienne adresse et retourne une liste de 7 lignes dont certaines à blanc sans modifs
    reponse = None
    adresse = []*7
    if IDindividu and IDindividu >0:
        # Importation de l'adresse de l'individu
        DB = xdb.DB()
        req = """SELECT rue_resid, cp_resid, ville_resid 
                FROM exadresses
                WHERE IDindividu = %d
                ;"""%IDindividu
        ret = DB.ExecuterReq(req,mess="UTILS_Adresses_saisie.GetDBoldAdresse")
        if ret == "ok":
            recordset = DB.ResultatReq()
            # un seul record possible au plus
            for rue,cp,ville in recordset:
                # rue et ville contiennent plusieurs lignes à séparer
                reponse = ChampsToLstAdresse(rue,cp,ville)
                break
        DB.Close()
    return reponse

def SetDBadresse(DB,IDindividu=None,adresse = "\n\n\n\n\n\n\n"):
    # Stocke dans la base de donnée l'adresse avec 4 lignes obligatoires pour rue, 2 pour ville et cp à part.
    if not DB: DB=xdb.DB()
    def ajustetype(adresse):
        #-------- validation
        if isinstance(adresse,(str)):
            # adresse en un texte de 6 ou 7 lignes dont la 5eme regroupe CP+ville
            lstAdresse = adresse.split("\n")
            if len(lstAdresse) == 5: lstAdresse.append("")
            if len(lstAdresse)==6:
                lstcpvil = lstAdresse[4].split(" ")
                cp = lstcpvil[0]
                ville = lstAdresse[4][len(cp):].strip()
                lstAdresse.append("")
                lstAdresse[6] = lstAdresse[5]
                lstAdresse[5] = ville
                lstAdresse[4] = cp
        elif isinstance(adresse,(list,tuple)):
            lstAdresse = adresse
        else:
            mess = "Adresse d'un type non géré!\n\nvariable de type '%s'"%type(adresse)
            wx.MessageBox(mess)
            return mess
        if len(lstAdresse) != 7:
            mess = "Adresse n'ayant pas sept lignes!\n\n%s"%str(adresse)
            wx.MessageBox(mess)
            return mess
        return lstAdresse
    lstAdresse = ajustetype(adresse)
    if not IDindividu or int(IDindividu)==0: return "pas d'IDindividu fourni!"
    # enlever les ponctuations, et mettre en majuscules les éléments significatifs
    lstAdresse = Normalisation(lstAdresse)

    rue_resid,cp_resid,ville_resid = LstAdresseToChamps(lstAdresse)
    lstDonnees = [  ("rue_resid",rue_resid),
                    ("cp_resid", cp_resid),
                    ("ville_resid", ville_resid),
                    ("adresse_normee", 1),
                    ("adresse_auto", None)]
    # envoi dans la base de donnée
    ret = DB.ReqMAJ("individus",lstDonnees,"IDindividu",IDindividu,mess="Insert Adresse Individu")
    return ret

def SetDBcorrespondant(dicCorrespondant):
    # Stocke dans la base de donnée l'adresse avec 4 lignes obligatoires pour rue, 2 pour ville et cp à part.
    lstDonnees = [  ("adresse_intitule",dicCorrespondant['designation']),
                    ("adresse_individu", dicCorrespondant['IDindividu'])]
    # envoi dans la base de donnée
    DB=xdb.DB()
    ret = DB.ReqMAJ("familles",lstDonnees,"IDfamille",dicCorrespondant['IDfamille'],mess="Insert familles Correspondant")
    return ret

def SetDBoldAdresse(DB,IDindividu=None,adresse = "\n\n\n\n\n\n\n"):
    if not DB: DB = xdb.DB()
    # Stocke dans la base de donnée l'adresse avec 4 lignes obligatoires pour rue, 2 pour ville et cp à part.
    rue_resid,cp_resid,ville_resid = LstAdresseToChamps(adresse)
    # envoi dans la base de donnée
    lstDonnees = [  ("rue_resid",rue_resid),
                    ("cp_resid", cp_resid),
                    ("ville_resid", ville_resid),
                    ("adresse_normee", 1),
                    ("date_modification", xdb.DateDDEnDateEng(datetime.date.today()))]
    ret = DB.ReqMAJ("exadresses",lstDonnees,"IDindividu",IDindividu,mess="Insert exAdresse")
    return ret

def Validation(adresse):
    # controle de cohérence de l'adresse, retourne 'ok' ou message des anomalies
    mess = ""
    if len(adresse[2].strip())==0 : mess += "\nUne adresse doit comporter à minima une rue."
    if len(adresse[4].strip())!=5 and len(adresse[6].strip())==0 :
            mess += "\nLe code postal à 5 caractères en France. Ou à blanc pour parti. "
    if len(adresse[5].strip())==0 :
        mess += "\nUne adresse doit comporter à minima une ville."
    else:
        ret = VerifieVille(adresse[4],adresse[5],adresse[6])
        if ret != "ok": mess += "\n%s"%ret
    # adresse sans code postal = acceptée
    if len(adresse[4].strip())==0:
        mess = "L'absence de code postal signifie que le client est parti\n"
        mess += "Mettez le code postal devant la ville (pour les éventuelles factures)"
        wx.MessageBox(mess)
        mess = ""
    if mess != "":
        return "ANOMALIES:\n" + mess
    return wx.OK

def TransposeAdresse(adresse=[]):
    # eclate l'adresse fournie en segments contenant un mot clé identifié, puis recompose selon l'ordre normé
    if len(adresse) != 7 or (not isinstance(adresse,(list,tuple))):
        wx.MessageBox("L'adresse reçue n'est pas une liste de six lignes\n\n%s"%str(adresse))
        return adresse
    adresse = [x.strip() for x in adresse]

    # les quatre lstMots correspondent aux quatre premières lignes de la norme, suivies de cp+ville et pays
    motsBatiment = ["batiment","bâtiment"," bat "," bât ","-bât","-bat"," hall"," entrée", "immeuble"]
    motsResidence= ["maison de quartier ","résidence","residence"," res.","rés."," res "," rés "," allée "," cour ",
                    "le clos ","les clos "]
    lstMotsBatRes= motsBatiment + motsResidence
    lstMotsAppart=["appt","appartement","appart ","app ","étage","etage"," etg ","escalier"," esc "," apt ",
                    " log ","logement"," porte ","service","serv ","rdc","rez "]
    lstMotsRue=["passage","ruelle "," rue "," place "," montée ","square","chemin","avenue","impasse",
                "boulevard", " bvd ","traverse"," allée "," cour "," route "," chem "," av "," rte "," cours "]
    lstMotsLieux=[" bp "," bp-","bp:","quartier ","lieu dit "," lieudit ","lieu-dit"," zi "]
    tplMotsTip = ((lstMotsAppart, "app"), (lstMotsBatRes, "bat"), (lstMotsRue, "rue"), (lstMotsLieux, "lie"))

    # détection des mots clés dans les lignes, retourne trois listes synoptiques ayant une ligne pour chaque mot trouvé
    def chercheMots(ligne):
        # retourne la liste des mot clé dans la chaîne en param
        lstTypes,lstTypesRes,lstMotsTrouves = [],[],[]
        for lstMots, tip in tplMotsTip:
            for mot in lstMots:
                # mot présent dans la chaine ou au début ou à la fin, '-' ajouté pour contrer le strip sur l'espace
                if mot in ligne \
                        or (mot + "-").strip()[:-1] == ligne[:len((mot + "-").strip()) - 1]\
                        or ("-" + mot).strip()[1:] == ligne[-len(("-" + mot).strip()) + 1:]:

                    # teste si le mot n'est pas déjà confus par inclusion dans un mot plus long
                    sortie = False
                    for motold in lstMotsTrouves:
                        if mot in motold and mot != motold: sortie = True
                        if motold in mot and mot != motold:
                            ixligold = lstMotsTrouves.index(motold)
                            lstMotsTrouves[ixligold] = mot
                            lstTypes = [] # on suppose qu'il n'y a pas d'autre mot concerné, pb s'il fallait nuancer!
                            lstTypesRes = []
                        if isinstance(motold,tuple):
                            for item in motold:
                                if mot in item  and mot != item: sortie = True
                    if sortie: continue

                    if tip not in lstTypes:
                        if len(lstTypes)>0:
                            #conflit de type: le mot était dans deux listes, stockage provisoire d'un tuple
                            if isinstance(lstTypes[0],tuple):
                                lstTypes[0] +=  (tip,)
                            else:
                                lstTypes[0] = (lstTypes[0],tip)
                        else:
                            lstTypes.append(tip)
                        if mot in motsResidence:
                            if len(lstTypesRes) == 0:
                                lstTypesRes.append("res")
                    if mot not in lstMotsTrouves:
                        lstMotsTrouves.append(mot)
        return lstTypes,lstTypesRes,lstMotsTrouves

    def chercheLstMots(adr=[],nblig=0):
        if nblig == 0:
            nblig = len(adr)
        lstTypes,lstTypesRes,lstMotsTrouves = [],[],[]
        for x in range(nblig):
            lstMotsTrouves.append([])
            lstTypes.append([])
            lstTypesRes.append([])
        for ix in range(nblig):
            ligne = adr[ix].lower()
            lstTypes[ix], lstTypesRes[ix], lstMotsTrouves[ix] =  chercheMots(ligne)
        for tips in lstTypes:
            # traitement des conflits de type: les ambiguités sont dans un tuple
            if len(tips)>0 and isinstance(tips[0],tuple):
                # annulation des tips présents dans le tuple visé et dans une autre ligne non tuple
                lstUniques = []
                for tip in tips[0]:
                    unique = True
                    for alttips in lstTypes:
                        if len(alttips)>0 and alttips[0] == tip : unique = False
                    if unique: lstUniques.append(tip[:3])
                ix = lstTypes.index(tips)

                priorites = ["lie", "app", "bat", "rue"]
                def prioritaire(tips, ordre):
                    # défini le tip prioritaire qu'il faut retenir
                    tipok = ''
                    tipokprior = 0
                    for tip in tips:
                        if ordre.index(tip) > tipokprior :
                            tipok = tip
                            tipokprior = ordre.index(tip)
                    return tipok

                if len(lstUniques) == 1 :
                    # il ne reste qu'une possibilité on la retient
                    lstTypes[ix] = lstUniques
                elif len(lstUniques) == 0:
                    # tous les tip sont aussi dans les autres lignes
                    ordre = [x for x in reversed(priorites)]
                    tipok = prioritaire(tips[0], ordre )
                    lstTypes[ix] = [tipok,]
                else:
                    # aucun tip n'était présent dans les autres lignes
                    tipok = prioritaire(lstUniques, priorites)
                    lstTypes[ix] = [tipok,]
        return lstTypes,lstTypesRes,lstMotsTrouves

    lstTypes,lstTypesRes,lstMotsTrouves = chercheLstMots(adresse,4)

    # fonction découpe d'une chaine selon la liste de mots qu'elle contient
    def coupeAvantMot(chaineBrute,mots, corrNoRue=0):
        # retourne deux morceaux de la chaine  séparés par le premier mot trouvé après le début
        """ on peut accoler au mot une correction pour no de rue ou de résidence qui le précède"""
        chaine = chaineBrute.lower().strip()
        lstFragments = []
        posMot = 9999
        motD = None
        motN = None
        motN1 = None
        for mot in mots :
            motpur = (mot + "-").strip()[:-1]
            yamotpur = (motpur == chaine[:len(motpur)])
            if (mot in chaine) or yamotpur :
                # le mot est dans la chaîne ou au début tronqué de son espace
                if yamotpur:
                    motfocus = motpur
                else: motfocus = mot
                # un batiment emporte le no de résidence qui le suit
                if motD in lstMotsBatRes and mot in motsResidence: corrNoRue = 0
                newpos = chaine.index(motfocus)-corrNoRue
                if newpos < posMot and newpos > 0:
                    posMot = chaine.index(motfocus)
                    motN1 = motN
                    motN = mot
                else:
                    if newpos == 0:
                        motD = mot
                        motN1 = motN
                    else: motN1 = mot
        # la coupure doit englober le numéro précédent un mot clé de type rue ou appart
        correctif = 0
        if motN in lstMotsAppart + motsBatiment:
            # recherche le début du no de batiment ou d'appartement placé devant en ième
            lstItems = chaine[:posMot].split(" ")
            posChiffre = None
            ix = -1
            # recule en sautant les espaces qui ont fait des items vides
            while len(lstItems[ix]) == 0 and ix >= -len(lstItems):
                ix -= 1
            noBat = NoPunctuation(lstItems[ix]).strip()
            tolerance = 6
            finsmot = (" er","1er","ier","eme","ème","éme")
            if len(noBat)>0 and len(noBat)<= 3 and noBat[-1].lower()== u"e" :
                finsmot += (("  "+noBat)[-3:],)
                tolerance = 2
            if ("   "+noBat.lower())[-3:] in finsmot :
                tolerance += len(noBat)
                # nobat est soit une abréviation précédée d'un chiffre soit la fin du mot complet
                if ord(noBat[0]) in range(48,58):
                    posChiffre = True
                elif len(noBat) > 8:  posChiffre = True
                elif ix-1 >= -len(lstItems):
                    # nobat est court et ne contenant pas le numéro il est peut être devant
                    ix -=1
                    noBat = lstItems[ix]
                    for let in noBat:
                        # teste présence chiffre
                        if ord(let) in range(48, 58):
                            posChiffre = True
                            tolerance += 1
                else: posChiffre = False
            # intègre le no devant le batiment
            if posChiffre and (posMot - chaine.index(noBat) < tolerance) :
                correctif = posMot - chaine.index(noBat)
                posMot = chaine.index(noBat)
        if motN in lstMotsRue or (motN in motsResidence and not motD):
            # recherche le début du no de rue par découpe en lst
            lstItems = NoPunctuation(chaine[:posMot]).split(" ")
            posChiffre = None
            ix = -1
            # recule en sautant les espaces qui ont fait des items vides
            while len(lstItems[ix])==0 and ix >= -len(lstItems): ix -= 1
            noRue = NoPunctuation(lstItems[ix]).strip()
            # une lettre isolée peut suivre le no de rue
            if len(noRue) == 1 and not ord(noRue[0]) in range(48,58):ix -= 1
            tolerance = 6
            if noRue.lower() in ("bis","ter","quater","grand","grande","ancien","ancienne","vieux"):
                tolerance += len(noRue)
                ix -= 1
                posChiffre = True
            if ix >= -len(lstItems):
                noRue = lstItems[ix]
                for let in noRue:
                    # teste présence chiffre
                    if ord(let) in range(48, 58):
                        posChiffre = True
                        tolerance += 1
            # intègre le no de rue devant la rue
            if posChiffre and (posMot - chaine.index(noRue) < tolerance) :
                correctif = posMot - chaine.index(noRue)
                posMot = chaine.index(noRue)

        if posMot == 0 and not motN1:
            a = chaineBrute.strip()
            b = ""
        elif posMot == 0 and motN1:
            lstTestCoupe = coupeAvantMot(chaineBrute,[motN1,],0)
            posMot = len(lstTestCoupe[0])
            a = chaineBrute[:posMot].strip()
            b = chaineBrute[posMot:]
        else:
            a = chaineBrute[:posMot].strip()
            b = chaineBrute[posMot:]
        lstFragments.append(a)
        while len(lstFragments[-1])>0:
            lstFragments += coupeAvantMot(b,mots,correctif)
        return lstFragments

    # éclatement de l'adresse dans une nouvelle liste
    eclate = []
    # éclatement des lignes qui comportent plusieurs mots clé
    for ixligne in range(4):
        if len(lstTypes)>1:
            # si plusieurs types de mots ont été détectés on crée au tant de ligne commençant par un mot identifié
            eclate += coupeAvantMot(adresse[ixligne],lstMotsTrouves[ixligne])
    # rajoute les lignes non éclatées
    for ixligne in range(4):
        if len(lstTypes)<=1:
            eclate.append(adresse[ixligne])

    # purge les lignes vides, après éclatement
    eclate = [x for x in eclate if len(x)>0]
    lstTypes,lstTypesRes,lstMotsTrouves = chercheLstMots(eclate)

    # verifie les espaces séparateurs derrière les mots clés
    for mots in lstMotsTrouves:
        ixligne = lstMotsTrouves.index(mots)
        for mot in mots:
            mot = mot.strip()
            posAfter = eclate[ixligne].lower().index(mot) + len(mot)
            if len(eclate[ixligne]) < posAfter + 1: continue # fin de ligne
            if eclate[ixligne][posAfter] == " ": continue # espace déjà présent
            # insertion d'un espace derrière le mot
            eclate[ixligne] = eclate[ixligne][:posAfter] + " " + eclate[ixligne][posAfter:]

    # élargi la recherche de résidence, si aucune encore identifiée
    nbrues = lstTypes.count("rue")
    lsttmp = [x for x in lstTypesRes if x != []]
    if len(lsttmp) == 0 and nbrues > 0:
        # pas de mot de résidence dans les autres segments
        ixtmp = None
        lgtmp = 0
        for ixtip in range(len(lstTypes)):
            if lstTypes[ixtip] == []:
                # présence d'une occurence non identifiée
                if len(NoPunctuation(eclate[ixtip])) <= 1: continue # non retenue car trop courte
                if ixtmp and len(eclate[ixtip]) > lgtmp:
                    # non retenue si plus courte que la précédente
                    continue
                # pris comme  résidence (risque de manque de pertinence, mais permettra de récupérer un numéro éventuel
                ixtmp = ixtip
                lgtmp = len(eclate[ixtip])
        if ixtmp:
            lstTypes[ixtmp].append("bat")
            lstTypesRes[ixtmp].append("res")

    # rassemble les lignes de même type, début de composition de newadresse
    tosuppr = []
    newadresse = ["","","",""]
    for ixadr in range(len(newadresse)):
        lstMots, tip = tplMotsTip[ixadr]
        ligne = ""
        # pour chaque segment de eclate
        for ixecl in range(len(lstTypes)):
            # pour chaque type possible sur ce segment
            for item in lstTypes[ixecl]:
                if item == tip:
                    # ce type correspond à la liste de mots clés en cours
                    if not eclate[ixecl] in ligne:
                        # le segment n'est pas déjà posé sur la ligne
                        if lstTypesRes[ixecl] == ["res"]:
                            ligne += (" "+eclate[ixecl])
                        else: ligne = (eclate[ixecl]+" "+ligne)
                        ligne = ligne.strip()
                        tosuppr.append(eclate[ixecl])
        newadresse[ixadr] = ligne

    # ce qui a été pris est enlevé de l'origine, pour isoler ce qui reste
    for ligne in tosuppr:
        eclate.remove(ligne)

    # complète avec les lignes non identifiées (pas encore dans newadresse)

    # inscrit le segment dans adress, avec les priorités de position dans lstix, ajoutsi permet d'ajouter si lg < n car
    def poseligne(adress,segment,lstix=[],ajoutsi=0,coupeok=True):
        if len(segment) > 38:
            lstmots = segment.split(" ")
            if len(lstmots)>1:
                lgpart1 = int(len(lstmots)/2)
                part1 = ""
                for i in range(lgpart1): part1 += lstmots[i]+" "
                reste = poseligne(adress,part1,lstix,ajoutsi,coupeok)
                if len(reste)>0:
                    segment = reste.strip() + " " + segment[len(part1):]
                else:
                    segment = segment[len(part1):]
        # le segment de ligne tente d'être posé dans adress[ix], retourne l'excédent ou chaine vide
        reste = segment
        for ix in lstix:
            if len(reste) > 0:
                lgligne = len(adress[ix].strip())
                if lgligne <= ajoutsi:
                    if lgligne > 0:
                        adress[ix] = adress[ix].strip() + " "
                        lgligne += 1
                    restenew = segment[(38 + 1 - lgligne):]
                    if coupeok or len(restenew) == 0:
                        # ajout du reste dans la ligne
                        adress[ix] += segment.strip()[:38 + 1 - lgligne ]
                        reste = segment[(38 + 1 - lgligne):]
                        if len(reste) > 0:
                            # une coupure a eu lieu on ajoute sur la ligne suivante si elle est vide
                            if ix <3 and len(adress[ix+1]) == 0 :
                                reste = poseligne(adress,reste,[ix+1,],0, coupeok=False)
                            elif ix >0 and len(adress[ix - 1]) == 0:
                                # sinon on remonte sur celle de dessus
                                adress[ix-1] = adress[ix]
                                adress[ix] = ''
                                reste = poseligne(adress,reste, [ix,], 0, coupeok=False)
                            else: #abandon de l'ajout du reste
                                reste = ''
        return reste.strip()
        #fin de poseligne

    restefinal = False
    # déroule lignes restantes non identifiées pour les placer où on peut
    lsteclate = []
    for ligne in eclate:
        lsteclate.append((-len(ligne),ligne))
    # ordre de longeurs de lignes décroissantes pour trouver toujours le même ordre si recalcul ensuite
    for ix,ligne in sorted(lsteclate):
        ligne = ligne.strip()
        if len(NoPunctuation(ligne)) <= 1: continue
        # priorité à un nom de rue trop court ou absent
        if len(newadresse[2])<=5:
            ligne = poseligne(newadresse,ligne,[2,],ajoutsi=6,coupeok=False)
            if len(ligne)==0:continue
        # priorité aux lignes les plus courtes pour les concatener
        n = 1
        # la ligne non tronquée était présente dans l'orginal, on tente la même position
        if ligne in adresse:
            n = adresse.index(ligne)
        for ajoutsi in (0, 10, 20):
            # cherche une ligne vide sans couper, puis avec découpe possible
            for coupeok in (False, True):
                ligne = poseligne(newadresse, ligne, [n, 1, 3, 0], ajoutsi=ajoutsi, coupeok=coupeok)

                if len(ligne) == 0: break
            if len(ligne) == 0: break
        if len(ligne) == 0: continue
        else: restefinal = True
    if restefinal :
        mess = "Cette adresse n'a pas été récupérée complètement\n\n"
        for ligne in adresse: mess += "%s\n"%ligne
        wx.MessageBox(mess)
    # ajout final des trois dernières lignes de l'original qui n'ont pas été modifiées
    newadresse += adresse[-3:]
    # la normalisation consiste à enlever les ponctuation et mettre e majuscule selon les lignes
    return Normalisation(newadresse)

def DesignationFamille(IDfamille):
    # composition automatique d'une désignation famille
    DB = xdb.DB()
    # Récupération des individus de la famille
    req = """
            SELECT rattachements.IDindividu, rattachements.titulaire, rattachements.IDcategorie, individus.nom, individus.prenom
            FROM rattachements 
                INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
            WHERE rattachements.IDfamille = %d AND rattachements.IDcategorie IN (1,2);
            """%IDfamille
    DB.ExecuterReq(req,MsgBox="aUTILS_SaisieAdresse.DesignationFamille")
    ltplIndividus = DB.ResultatReq()

    titulaires = []
    representants = []
    nomsEnfants = []
    for IDindividu, titulaire, categorie, nom, prenom in ltplIndividus:
        if titulaire == 1:
            titulaires.append((nom,prenom))
        if categorie == 1:
            representants.append((nom,prenom))
        elif not nom in nomsEnfants:
                nomsEnfants.append(nom)

    def ajoutNom(nomA,prenomA,nomB,prenomB):
        if len(nomA) == 0:
            nomA = nomB
            prenomA= prenomB
        elif nomA == nomB:
            if len(prenomA) >0:
                prenomA += u" et "+prenomB
            else: prenomA = prenomB
        else:
            # deux noms différents
            lstradA = nomA.split(u" ")
            lstradB = nomB.split(u" ")
            for mot in lstradB:
                if mot in lstradA: lstradA.remove(mot)
            for mot in lstradA:
                if mot in lstradB: lstradB.remove(mot)
            nomAB = u" ".join(lstradA+lstradB)
            if nomAB == nomA + u" " + nomB:
                # il n'y avait pas de radical commun
                nomA = nomA + u" " + prenomA
                prenomA = u"et " + nomB + u" "+prenomB
            else:
                nomA = nomAB
                prenomA = prenomA + u" et " +prenomB
        return nomA, prenomA

    nomF = ""
    prenomF = ""
    if len(titulaires)>1:
        for nom,prenom in titulaires:
            nomF,prenomF = ajoutNom(nomF,prenomF,nom,prenom)
    elif len(representants) > 1:
        for nom, prenom in representants:
            nomF, prenomF = ajoutNom(nomF, prenomF, nom, prenom)
    elif len(nomsEnfants)>0:
        if len(titulaires)>0:
            nomTit = titulaires[0][0]
            nomF = u"Famille %s"%nomTit
        else : nomF = u"Famille"
        for nom in nomsEnfants:
            if not nom in nomF:
                nomF += u" %s"%nom
    elif len(titulaires)>0: nomF,prenomF = titulaires[0]
    designation = (nomF + " " + prenomF)[:55]
    return designation


# -----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(0)
    #InitialiseFamilles()

    lstAdresse = [  u"1, rue du Belvedere de la Ronce ",
                    u"bâtiment 5 3 ème étage",
                    u"",
                    u"",
                    u"83160 plan d'Aups",
                    u"",u""]
    ret = TransposeAdresse(lstAdresse)

    for ix in range(7):
        print((lstAdresse[ix]+u" "*50)[:50],u"\t",ret[ix])
    app.MainLoop()
