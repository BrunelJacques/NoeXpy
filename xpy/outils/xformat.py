# Il faudra optimiser les fonctions de ce fichier mais plus tard
SYMBOLE = "€"

import wx
import datetime
import unicodedata

# fonctions pour OLV
def AppelLignesMatrice(categ=None, possibles={}):
    # retourne les lignes de la  matrice de l'argument categ ou la première catégorie si not categ
    code = None
    label = ''
    lignes = {}
    if possibles:
        for code, labelCategorie in possibles:
            if isinstance(code, str):
                if categ:
                    if categ == code:
                        label = labelCategorie
                        lignes = possibles[(code, labelCategorie)]
                else:
                    label = labelCategorie
                    lignes = possibles[(code, labelCategorie)]
                    break
    return code, label, lignes

def OlvToMatrice(key,olv):
    ld = []
    for col in olv.lstColonnes:
        genre = col.valueSetter.__class__.__name__
        info = "Saisir une valeur dans le format %s"%genre
        param = {'name': col.valueGetter,
                 'label': col.title,
                 'value': col.valueSetter,
                 'genre': genre,
                 'help': info}
        if hasattr(col.valueSetter,'choices'):
            param['genre'] = 'combo'
            param['choices'] = col.choices
        ld.append(param)
    matrice = {key: ld}
    return matrice

def TrackToDdonnees(track,olv):
    # retourne les dict de donnees d'une track
    dDonnees = {}
    for col in olv.lstColonnes:
        dDonnees[col.valueGetter] = eval('track.%s'%col.valueGetter)
    return dDonnees

def CompareModels(original,actuel):
    # retourne les données modifiées dans le modelobject original % actuel
    lstNews, lstCancels, lstModifs = [], [], []
    # l'id doit être en première position des données
    lstIdActuels = [x.donnees[0] for x in actuel]
    lstIdOriginaux = [x.donnees[0] for x in original]
    # retrouver l'original dans l'actuel
    for track in original:
        if track.donnees[0] in lstIdActuels:
            ix = lstIdActuels.index(track.donnees[0])
            if track.donnees == actuel[ix].donnees:
                continue
            if not actuel[ix].valide:
                continue
            else:
                lstModifs.append(actuel[ix].donnees)
        else: lstCancels.append(track.donnees)
    #repérer les nouveaux
    for track in actuel:
        if track.donnees[0] in lstIdOriginaux:
            continue
        elif not track.vierge: lstNews.append(track.donnees)
    return lstNews,lstCancels,lstModifs

def ComposeWhereFiltre(filtre,lstChamps,lstColonnes=None, lien='WHERE'):
        if lstColonnes:
            lstNames = [x.valueGetter for x in lstColonnes]
            lstChamps = [lstChamps[x] for x in range(len(lstChamps)) if lstNames[x] in lstChamps[x]]
        whereFiltre = ''
        if filtre and len(filtre) > 0 and len(lstChamps)>0:
            texte = ''
            ordeb = """
                    ("""
            for ix in range(len(lstChamps)):
                texte += "%s %s LIKE '%%%s%%' )"%(ordeb,lstChamps[ix],filtre)
                ordeb = """
                    OR ("""
            whereFiltre = """
                %s ( %s )"""%(lien,texte)
        return whereFiltre

def SupprimeAccents(texte,lower=True):
    # met en minuscule sans accents et sans caractères spéciaux
    code = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    #code = str(unicodedata.normalize('NFD', texte).encode('ascii', 'ignore'))
    if lower: code = code.lower()
    code = ''.join(car for car in code if car not in " %)(.[]',;/\n")
    return code

# Automatismes de gestion des ColumnDef

def GetLstChamps(table=None,cutend=None):
    if cutend == 0 or cutend == None: cutend = None
    else: cutend = -cutend
    return [x for x,y,z in table[:cutend] ]

def GetLstNomsColonnes(table=None,cutend=None):
    if cutend == 0 or cutend == None: cutend = None
    else: cutend = -cutend
    return [x for x, y, z in table[:cutend]]

def ValeursDefaut(lstNomsColonnes,lstTypes,wxDates=False):
    # Détermine des valeurs par défaut selon le type des variables, précision pour les dates wx ou datetime
    # la valeur par défaut détermine le cellEditor
    lstValDef = [0,]
    for ix in range(1,len(lstNomsColonnes)):
        tip = lstTypes[ix].lower()
        if tip[:3] == 'int': lstValDef.append(0)
        elif tip[:10] == 'tinyint(1)': lstValDef.append(False)
        elif tip[:5] == 'float': lstValDef.append(0.0)
        elif tip[:4] == 'bool': lstValDef.append(False)
        elif tip[:4] == 'date':
            if wxDates:
                lstValDef.append(wx.DateTime.Today())
            else: lstValDef.append(datetime.date.today())
        else: lstValDef.append('')
    return lstValDef

def LargeursDefaut(lstNomsColonnes,lstTypes,IDcache=True):
    # Evaluation de la largeur nécessaire des colonnes selon le type de donnee et la longueur du champ
    lstLargDef=[]
    ix =0
    if IDcache:
        lstLargDef = [0,]
        ix = 1
    for ix in range(ix, len(lstNomsColonnes)):
        nomcol = lstNomsColonnes[ix]
        lgtitle = int(len(nomcol) * 7.5)
        tip = lstTypes[ix]
        tip = tip.lower()
        if tip[:3] == 'int': lstLargDef.append( max(lgtitle,50))
        elif tip[:5] == 'float': lstLargDef.append(max(lgtitle,60))
        elif tip[:4] == 'date': lstLargDef.append(max(lgtitle,80))
        elif tip[:7] == 'varchar':
            lgdef = int(tip[8:-1])*4
            lg = max(lgtitle,lgdef)
            if lg <= 24: lg=24
            if lg > 200:
                lg = -1
            lstLargDef.append(lg)
        else:
            lstLargDef.append(-1)
    return lstLargDef

def DefColonnes(lstNoms,lstCodes,lstValDef,lstLargeur):
    from xpy.outils.ObjectListView import ColumnDefn
    # Composition d'une liste de définition de colonnes d'un OLV; remarque faux ami: 'nom, code' == 'label, name'
    ix=0
    # normalise les len() des listes en ajoutant des items
    for lst in (lstCodes,lstValDef,lstLargeur):
        if lst == None : lst = []
        if len(lst)< len(lstNoms):
            lst.extend(['']*(len(lstNoms)-len(lst)))

    lstColonnes = []
    yaSpaceFil = False

    for colonne in lstNoms:
        if isinstance(lstValDef[ix],(str,wx.DateTime,datetime.date)):
            posit = 'left'
        elif isinstance(lstValDef[ix],bool):
            #posit = 'centre'
            posit = 'left'
        else: posit = 'right'
        # ajoute un converter à partir de la valeur par défaut
        if isinstance(lstValDef[ix], (float,)):
            if '%' in colonne:
                stringConverter = FmtPercent
            else:
                stringConverter = FmtDecimal
        elif isinstance(lstValDef[ix], bool):
            if lstValDef[ix] == False:
                # le false est à blanc True:'X'
                stringConverter = FmtBoolX
            else:
                # le false est 'N' le True 'O'
                stringConverter = FmtBool
        elif isinstance(lstValDef[ix], int):
            if '%' in colonne:
                stringConverter = FmtPercent
            else:
                stringConverter = FmtIntNoSpce
        elif isinstance(lstValDef[ix], (datetime.date,wx.DateTime)):
            stringConverter = FmtDate
        elif lstCodes[ix][:3] == 'tel' and isinstance(lstValDef[ix],(str)):
            # téléphone repéré par tel dans le début du code
            stringConverter = FmtTelephone
        else: stringConverter = None
        if lstLargeur[ix] in ('',None,'None',-1):
            lstLargeur[ix] = -1
            isSpaceFilling = True
            yaSpaceFil = True
        else: isSpaceFilling = False
        code = lstCodes[ix]
        lstColonnes.append(ColumnDefn(title=colonne,align=posit,width=lstLargeur[ix],valueGetter=code,
                                      valueSetter=lstValDef[ix],isSpaceFilling=isSpaceFilling,
                                      stringConverter=stringConverter))
        ix += 1
    if not yaSpaceFil:
        maxW = 0
        ixMax = None
        # si aucun space Filling, on active sur la plus large
        for col in lstColonnes:
            if col.width > maxW:
                maxW = col.width
                ixMax = lstColonnes.index(col)
        if not ixMax == None:
                lstColonnes[ixMax].isSpaceFilling = True
    return lstColonnes

def GetLstColonnes(**kwd):
    # Compose ColumnsDefn selon schéma table, sans champs cutend, format dates et masquer ou pas ID
    table = kwd.pop('table',None)
    cutend = kwd.pop('cutend',None)
    IDcache = kwd.pop('IDcache',True)
    wxDates = kwd.pop('wxDates',True)
    # si les listes sont fournies, les param précédents sont inutiles
    lstNoms = kwd.pop('lstNoms',GetLstNomsColonnes(table,cutend))
    if cutend == 0 or cutend == None: cutend = None
    else: cutend = -cutend
    lstTypes = kwd.pop('lstTypes',[y for x, y, z in table[:cutend]])
    lstCodes = kwd.pop('lstCodes',[SupprimeAccents(x,lower=False) for x in lstNoms])
    lstValDef = kwd.pop('lstValDef',ValeursDefaut(lstNoms, lstTypes,wxDates=wxDates))
    lstLargeur = kwd.pop('lstLargeur',LargeursDefaut(lstNoms, lstTypes,IDcache=IDcache))
    return DefColonnes(lstNoms, lstCodes, lstValDef, lstLargeur)

# Conversion wx.Datetime % datetime.date

def DatetimeToWxdate(date):
    assert isinstance(date, (datetime.datetime, datetime.date))
    tt = date.timetuple()
    dmy = (tt[2], tt[1] - 1, tt[0])
    return wx.DateTime.FromDMY(*dmy)

def WxdateToDatetime(date):
    assert isinstance(date, wx.DateTime)
    if date.IsValid():
        ymd = map(int, date.FormatISODate().split('-'))
        return datetime.date(*ymd)
    else:
        return None

# Conversion des dates SQL aaaa-mm-jj

def DateSqlToWxdate(dateiso):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj(ou déjà en datetime) en wx.datetime
    if dateiso == None : return None
    # si ce n'est pas une date iso
    if '/' in dateiso:
        dateiso = DateFrToSql(dateiso)

    if isinstance(dateiso,datetime.date):
        return wx.DateTime.FromDMY(dateiso.day,dateiso.month-1,dateiso.year)

    if isinstance(dateiso,str) and len(dateiso) >= 10:
        return wx.DateTime.FromDMY(int(dateiso[8:10]),int(dateiso[5:7])-1,int(dateiso[:4]))

def DateSqlToDatetime(dateiso):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj (ou déjà en datetime) en datetime
    if dateiso == None : return None

    elif isinstance(dateiso,datetime.date):
        return dateiso

    elif isinstance(dateiso,str) and len(dateiso) >= 10:
        return datetime.date(int(dateiso[:4]),int(dateiso[5:7]),int(dateiso[8:10]))

def DateToDatetime(date):
    # FmtDate normalise en FR puis retourne en datetime
    return DateFrToDatetime(FmtDate(date))

def DateSqlToFr(date):
    # Conversion de date récupérée de requête SQL  en jj/mm/aaaa
    date = DateSqlToIso(date)
    if len(date) < 10: return ""
    return '%s/%s/%s'%(date[8:10],date[5:7],date[:4])

def DateSqlToIso(date):
    # Conversion de date récupérée de requête SQL en aaaa-mm-jj
    if date == None : return ""
    if not isinstance(date, str) : date = str(date)
    date = date.strip()
    if date == "" : return ""
    if len(date) == 8:
        an,mois,jour = date[:4],date[4:6],date[6:8]
        return '%s-%s-%s'%(an,mois,jour)
    lsplit = date.split('-')
    if len(lsplit) == 3 :
        an,mois,jour = lsplit[0],lsplit[1],lsplit[2]
    lsplit = date.split('/')
    if len(lsplit) == 3 :
        jour,mois,an = lsplit[0],lsplit[1],lsplit[2]
    if len(an) == 2:
        mil = 20
        if int(an)>50: mil = 19
        an = mil + an
    return '%s-%s-%s'%(an,mois,jour)

def DateFrToSql(datefr):
    if not datefr: return ''
    # Conversion de date string française reçue en formats divers
    if not isinstance(datefr, str) : datefr = str(datefr)
    datefr = datefr.strip()
    # normalisation des formats divers
    datefr = FmtDate(datefr)
    if len(datefr)!= 10:
        raise Exception("Date non gérable par DateFrToSql: '%s'"%str(datefr))
    datesql = datefr[6:10]+'-'+datefr[3:5]+'-'+datefr[:2]
    # transposition
    return datesql

def DateFrToWxdate(datefr):
    # Conversion d'une date chaîne jj?mm?aaaa en wx.datetime
    if not isinstance(datefr, str) : datefr = str(datefr)
    datefr = datefr.strip()
    if len(datefr) != 10: return None
    datefr = datefr.strip()
    try:
        dmy = (int(datefr[:2]), int(datefr[3:5]) - 1, int(datefr[6:10]))
        dateout = wx.DateTime.FromDMY(*dmy)
    except: dateout = None
    return dateout

def DateFrToDatetime(datefr):
    # Conversion de date française jj/mm/aaaa (ou déjà en datetime) en datetime
    if datefr == None :
        return None
    elif isinstance(datefr,datetime.date):
        return datefr
    elif isinstance(datefr,str) and len(datefr) >= 10:
        return datetime.date(int(datefr[6:10]),int(datefr[3:5]),int(datefr[:2]))

def WxDateToStr(dte,iso=False):
    # Conversion wx.datetime en chaîne
    if isinstance(dte, wx.DateTime):
        if iso: return dte.Format('%Y-%m-%d')
        else: return dte.Format('%d/%m/%Y')
    else: return str(dte)

def DatetimeToStr(dte,iso=False):
    # Conversion d'une date datetime ou wx.datetime en chaîne
    if isinstance(dte, wx.DateTime):
        if iso: return dte.Format('%Y-%m-%d')
        else: return dte.Format('%d/%m/%Y')
    elif isinstance(dte, datetime.date):
        dd = ("00" + str(dte.day))[-2:]
        mm = ("00" + str(dte.month))[-2:]
        yyyy = ("0000" + str(dte.year))[-4:]
        if iso: return "%s-%s-%s"%(yyyy,mm,dd)
        else: return "%s/%s/%s"%(dd,mm,yyyy)
    else: return str(dte)

# Formatages pour OLV -------------------------------------------------------------------------------------

def SetBgColour(self,montant):
    if montant > 0.0:
        self.SetBackgroundColour(wx.Colour(200, 240, 255))  # Bleu
    elif montant < 0.0:
        self.SetBackgroundColour(wx.Colour(255, 170, 200))  # Rose
    else:
        self.SetBackgroundColour(wx.Colour(200, 255, 180))  # Vert

def FmtDecimal(montant):
    if isinstance(montant,str): montant = montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtInt(montant):
    if isinstance(montant,str):
        montant = montant.replace(',','.')
    try:
        x=float(montant)
    except: return ""
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:,.0f} '.format(int(float(montant)))
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtIntNoSpce(montant):
    if isinstance(montant,str):
        montant = montant.replace(',','.')
    try:
        x=float(montant)
    except: return ""
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:.0f} '.format(int(float(montant)))
    return strMtt

def FmtPercent(montant):
    if isinstance(montant,str): montant = montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:}% '.format(int(float(montant)))
    return strMtt

def FmtDate(date):
    strdate = ''
    if date == None or date in (wx.DateTime.FromDMY(1,0,1900),'',datetime.date(1900,1,1),"1899-12-30"):
        return ''
    if isinstance(date,str):
        date = date.strip()
        tplansi = date.split('-')
        tpldate = date.split('/')
        if date == '00:00:00': strdate = ''
        elif len(tplansi)==3:
            strdate = ('20'+tplansi[0])[-4:]+'-'+('00'+tplansi[1])[-2:]+'-'+('00'+tplansi[2])[-2:]
        elif len(tpldate) == 3:
            if len(date)>8:
                strdate = (tpldate[2])[:4] + '-' + ('00' + tpldate[1])[-2:] + '-' + ('00' + tpldate[0])[-2:]
            else:
                strdate = ('20' + tpldate[2])[:4] + '-' + ('00' + tpldate[1])[-2:] + '-' + ('00' + tpldate[0])[-2:]
        elif len(date) == 6:
            strdate = ('20'+date[4:] + '-' + date[2:4] + '-' + date[:2])
        elif len(date) == 8:
            strdate = (date[4:] + '-' + date[2:4] + '-' + date[:2])
    else:
        strdate = DatetimeToStr(date,iso=True)
    if not strdate or strdate == '':
        mess = "Date non reconnue: %s\n<esc> pour abandonner"%str(date)
        wx.MessageBox(mess,"Resaisir une date correcte")
        return ''
    return DateSqlToFr(strdate)

def FmtTelephone(texte):
    # formatage du numéro de téléphone
    if texte == None: return ''
    if not isinstance(texte,str):
        texte = str(texte)
    if texte[:2] == '00':
        texte = '+'+texte[2:]

    # on accepte deux tirets pour les numéros étrangers, sinon c'est abusif
    nbtir = texte.count('-')
    if nbtir >2: texte= texte.replace('-',' ')

    texte = texte.replace('.',' ')
    nbspc = texte.count(' ')
    # cas d'une saisie déjà formatée, on la laisse
    if nbspc > 2 : return texte

    # si moins de trois espaces on les enlève pour refaire
    texte = texte.replace(' ','')
    texte += 'xxx' # force la dernière occurence
    if len(texte) == 10+3 and texte[0] != '+':
        # cas français simple
        ntel = ' '.join([i + j for i, j in zip(texte[::2], texte[1::2])])
    else:
        # autres cas découpés par 3
        ntel = ' '.join([i + j + k for i, j, k in zip(texte[::3], texte[1::3],texte[2::3])])
    ntel = ntel.replace('( ','(')
    ntel = ntel.replace(' )',')')
    ntel = ntel.replace('x','') # retire le forçage
    return ntel.strip()

def FmtBool(value):
    if value == False:
        return 'N'
    if value == True:
        return 'O'
    return ''

def FmtBoolX(value):
    if value == True:
        return 'X'
    return ''

def FmtMontant(montant,prec=2,lg=None):
    out = ''
    if isinstance(montant,str):
        montant = montant.replace(',','.')
        try: montant = float(montant)
        except: pass
    if not isinstance(montant,(int,float)): montant = 0.0
    if float(montant) != 0.0:
        out = "{: ,.{prec}f} {:} ".format(montant,SYMBOLE,prec=prec).replace(',', ' ')
    if lg:
        out = (' '*lg + out)[-lg:]
    return out

def FmtSolde(montant):
    if isinstance(montant,str):montant = montant.replace(',','.')
    if montant == None or montant == '':
        return ""
    strMtt = '{:+,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')+ SYMBOLE
    return strMtt

# Diverses fonctions-------------------------------------------------------------------------------------------

def Nz(param):
    # fonction Null devient zero, et extrait les chiffres d'une chaîne pour faire un nombre
    if isinstance(param,str):
        tmp = ''
        for x in param:
            if (ord(x) > 42 and ord(x) < 58):
                tmp +=x
        tmp = tmp.replace(',','.')
        lstval = tmp.split('.')
        if len(lstval)>=2: tmp = lstval[0] + '.' + lstval[1]
        param = tmp
    if isinstance(param,int):
        valeur = param
    else:
        try:
            valeur = float(param)
        except: valeur = 0.0
    return valeur

def ListToDict(lstCles,lstValeurs):
    dict = {}
    if isinstance(lstCles,list):
        for cle in lstCles:
            idx = lstCles.index(cle)
            dict[cle] = None
            if isinstance(lstValeurs, (list,tuple)) and len(lstValeurs) >= idx:
                dict[cle] = lstValeurs[idx]
    return dict

def DictToList(dic):
    # sépare les clés et les valeurs d'un dictionnaire
    lstCles = []
    lstValeurs = []
    if isinstance(dic,dict):
        for cle,valeur in dic.items():
            # cas des dictionnaires dans dictionnaires, le premier niveau est ignoré
            if isinstance(valeur,dict):
                sscles, ssval = DictToList(valeur)
                lstCles += sscles
                lstValeurs += ssval
            else:
                lstCles.append(cle)
                lstValeurs.append(valeur)
    return lstCles,lstValeurs

def PrefixeNbre(param):
    if not isinstance(param,str):
        return ''
    # extrait le préfixe chaîne d'un nombre
    radicalNbre = str(Nz(param))
    ix = len(param)
    if radicalNbre != '0.0':
        ix = param.find(radicalNbre[0])
    return param[:ix]

def LettreSuivante(lettre=''):
        # incrémentation d'un lettrage
        if not isinstance(lettre, str): lettre = 'A'
        if lettre == '': lettre = 'A'
        lastcar = lettre[-1]
        precars = lettre[:-1]
        if ord(lastcar) in (90, 122):
            if len(precars) == 0:
                precars = chr(ord(lastcar) - 25)
            else:
                precars = LettreSuivante(precars)
            new = precars + chr(ord(lastcar) - 25)
        else:
            new = precars + chr(ord(lastcar) + 1)
        return new

def IncrementeRef(ref):
    # incrémente une référence compteur constituée d'un préfixe avec un quasi-nombre ou pas
    pref = PrefixeNbre(ref)
    if len(ref) > len(pref):
        nbre = int(Nz(ref))+1
        lgnbre = len(str(nbre))
        nbrstr = '0'*lgnbre + str(nbre)
        refout = pref + nbrstr[-lgnbre:]
    else:
        # référence type lettrage
        refout = LettreSuivante(ref)
    return refout

def BorneMois(dte,fin=True, typeOut=datetime.date):

    if not typeOut in (datetime.date,datetime.time,wx.DateTime,str):
        typeOut = None

    # traitement de sortien si typeOut a été précisé
    def formatOut(wxdte):
        if typeOut == datetime.date:
            return WxdateToDatetime(wxdte)
        if typeOut == str:
            return WxDateToStr(wxdte,iso=True)
        return wxdte

    # traitement apres normalisation en wxDate
    def action(wxdte):
        # action  calcul début ou fin de mois sur les wx.DateTime
        if isinstance(wxdte,wx.DateTime):
            if fin:
                dteout = wx.DateTime.FromDMY(1,wxdte.GetMonth(),wxdte.GetYear())
                dteout += wx.DateSpan(days=-1,months=1)
            else:
                # dte début de mois
                dteout = wx.DateTime.FromDMY(1,wxdte.GetMonth(),wxdte.GetYear())
            return dteout
        return None

    # analyse de l'entrée
    if isinstance(dte,(datetime.date,datetime.datetime)):
        if not typeOut:
            formatOut = WxdateToDatetime
        return formatOut(action(DatetimeToWxdate(dte)))

    elif isinstance(dte,wx.DateTime):
        if not typeOut or typeOut == wx.DateTime:
            return action(dte)
        return formatOut(action(dte))

    elif isinstance(dte,str):
        dte = dte.strip()
        wxdte = DateSqlToWxdate(FmtDate(dte))
        if typeOut != str:
            return formatOut(action(wxdte))
        #  sans précision sur le retour : fait dans le format str initial
        if "-" in dte:
            return WxDateToStr(action(wxdte),iso=True)
        elif "/" in dte:
                dtefr = WxDateToStr(action(wxdte), iso=False)
                if len(dte)> 8:
                    return dtefr
                else: return dtefr[:6]+dtefr[8:]
        else:
            dtefr = WxDateToStr(action(wxdte), iso=False)
            dtefr = dtefr.replace('/','')
            if len(dte) == 6:
                return dtefr[:4]+dtefr[6:]
            elif len(dte) == 8:
                return dtefr
            else:
                msg = "Date entrée non convertible : %s"%dte
                raise Exception(msg)

    # transformation en sortie

    return dte

def FinDeMois(date,typeOut=datetime.date):
    # Retourne le dernier jour du mois dans le format reçu
    return BorneMois(date,fin=True,typeOut=typeOut)

def DebutDeMois(date,typeOut=datetime.date):
    # Retourne le dernier jour du mois dans le format reçu
    return BorneMois(date,fin=False,typeOut=typeOut)

def ProrataCommercial(entree,sortie,debutex,finex):
    # Prorata d'une présence sur exercice sur la base d'une année commerciale pour un bien entré et sorti
    # normalisation des dates iso en datetime
    [entree,sortie,debut,fin] = [DateToDatetime(x) for x in [entree,sortie,debutex,finex]]
    if not debut or not fin:
        mess = "Date d'exercices impossibles: du '%s' au '%s'!"%(str(debutex),str(finex))
        raise Exception(mess)
    # détermination de la période d'amortissement
    if not entree: entree = debut
    if not sortie: sortie = fin
    if entree > fin: debutAm = fin
    elif entree > debut : debutAm = entree
    else: debutAm = debut
    if sortie < debut: finAm = debut
    elif sortie < fin : finAm = sortie
    else: finAm = fin

    def delta360(deb,fin):
        #nombre de jours d'écart en base 360jours / an
        def jour30(dte):
            # arrondi fin de mois en mode 30 jours
            if dte.day > 30:
                return 30
            # le lendemain est-il un changement de mois? pour fin février bissextile ou pas
            fdm = (dte + datetime.timedelta(days=1)).month - dte.month
            if fdm >0:
                return 30
            return dte.day
        return 1 + jour30(fin) - jour30(deb) + ((fin.month - deb.month) + ((fin.year - deb.year) * 12)) * 30
    taux = round(delta360(debutAm,finAm) / 360,6)
    return taux

if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
    """
    print(FmtDecimal(1230.05189),FmtDecimal(-1230.05189),FmtDecimal(0))
    print(FmtSolde(8520.547),FmtSolde(-8520.547),FmtSolde(0))
    print(FmtMontant(8520.547),FmtMontant(-8520.547),FmtMontant(0))
    print(FmtDate('01022019'))
    print(SupprimeAccents("ÊLève!"))
    """
    ret = FmtTelephone('0494149367')

    print(ret +'|')




