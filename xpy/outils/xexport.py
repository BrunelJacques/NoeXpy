#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------


import wx
import os
import datetime
import six
import decimal
import platform

from xpy.outils import xctrlbi
from xpy.outils import xdates
from xpy.outils import xselection
from xpy.outils import xbandeau
from xpy.outils.xconst import *
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn

class DataType(object):
    #Classe permetant la conversion facile vers le format souhaité (nombre de caractéres, alignement, décimales)
    def __init__(self,cat=int,lg=1,align="<",precision=2,fmt=None,**kwd):
        """
        initialise l'objet avec les paramétres souhaité
        """
        self.cat = cat
        self.length = lg
        self.align = align
        self.precision = precision
        self.fmt = fmt
        if self.cat == 'const':
            self.constante = kwd.pop('constante',None)

    def Convert(self,data):
        # convertit au format souhaité
        ret_val = ""

        # gestion des valeurs nulles selon la catégorie attendue
        if data == None:
            if self.cat in (int,float,bool,decimal.Decimal): data = self.cat(0)
            elif self.cat == str:           data = ''
            elif self.cat == wx.DateTime:   data = wx.DateTime.FromDMY(1,0,1900)
            elif self.cat == datetime.date: data = datetime.date(1900,1,1)

        # avec un format spécifique fourni
        if self.fmt: # attention la catégorie doit bien correspondre à la réalité attendue par le format
            if self.cat == wx.DateTime:
                # exemple data.Format("%d%m%y")
                ret_val = data.Format(self.fmt)
            elif self.cat == datetime.date:
                # exemple '{:%d%m%y}'.format(data)
                ret_val = self.fmt.format(data)
            else:
                # exemple "{0:{align}0{length}.{precision}f}".format(+1254.126,align=">",length=10,precision=2)
                # ou directement "{0:+010.0f}".format(+1254.126) pour '+000001254'
                ret_val = self.fmt.format(data,align=self.align,length=self.length,prec=self.precision)

        elif self.cat == int:                        #si l'on veux des entier
            if data!="":
                try:                                #on vérifie qu'il s'agit bien d'un nombre
                    data=int(data)
                except ValueError as e:
                    print("/!\ Erreur de format, impossible de convertir en int /!\\")
                    print(e)
                    data=0
                ret_val = u"{0:{align}0{length}d}".format(data,align=self.align,length=self.length)
            else:
                ret_val = u"{0:{align}0{length}s}".format(data,align=self.align,length=self.length)

        elif self.cat == str:                      #si l'on veux des chaines de caractéres
            if not isinstance(data,(str)): data = str(data)
            for a in ['\\',';',',']:
                data = data.replace(a,'')
            ret_val = u"{0: {align}0{length}s}".format(data,align=self.align,length=self.length)

        elif self.cat == 'const':                      # la valeur est une constante
            if not isinstance(data,(str)): data = str(data)
            ret_val = self.constante

        elif self.cat == float:                    #si l'on veux un nombre a virgule
            if data!="":
                try:
                    data=float(data)
                    #on vérifie qu'il s'agit bien d'un nombre
                except ValueError as e:
                    print("/!\ Erreur de format, impossible de convertir en float /!\\")
                    print(e)
                    data=0
                ret_val = u"{0: {align}0{length}.{precision}f}".format(data,align=self.align,length=self.length,precision=self.precision)
            else:
                ret_val = u"{0: {align}0{length}s}".format(data,align=self.align,length=self.length)

        if len(ret_val)>self.length:                #on tronc si la chaine est trop longue
            ret_val=ret_val[:self.length]
        return ret_val
        #fin Convert
    #fin class DataType

def GetValeursListview(listview=None, format="texte"):
    """ Récupère les valeurs affichées sous forme de liste """
    """ format = "texte" ou "original" """
    # Récupère les labels de colonnes
    listeColonnes = []
    for colonne in listview.columns:
        listeColonnes.append((colonne.title, colonne.align, colonne.width, colonne.valueGetter))

    # Récupère les valeurs
    listeValeurs = []
    listeObjects = listview.innerList  # listview.GetFilteredObjects()
    for object in listeObjects:
        valeursLigne = []
        for indexCol in range(0, listview.GetColumnCount()):
            if format == "texte":
                valeur = listview.GetStringValueAt(object, indexCol)
            else:
                valeur = listview.GetValueAt(object, indexCol)
            valeursLigne.append(valeur)
        listeValeurs.append(valeursLigne)

    return listeColonnes, listeValeurs

def GetValeursGrid(grid=None):
    """ Récupère les valeurs affichées sous forme de liste """
    # Récupère les labels de colonnes
    listeColonnes = [("titre_ligne", None, grid.GetColLabelSize(), "titre_ligne"), ]
    for numCol in range(0, grid.GetNumberCols()):
        listeColonnes.append(
            (grid.GetColLabelValue(numCol), None, grid.GetColSize(numCol), grid.GetColLabelValue(numCol)))

    # Récupère les valeurs
    listeValeurs = []
    for numLigne in range(0, grid.GetNumberRows()):
        labelLigne = grid.GetRowLabelValue(numLigne)
        valeursLigne = [labelLigne, ]
        for numCol in range(0, grid.GetNumberCols()):
            valeur = grid.GetCellValue(numLigne, numCol)
            if type(valeur) not in ("str", "unicode"):
                valeur = str(valeur)
            valeursLigne.append(valeur)
        listeValeurs.append(valeursLigne)

    return listeColonnes, listeValeurs

def ChoixDestination(nomFichier,wildcard):
    # Demande à l'utilisateur le nom de fichier et le répertoire de destination
    sp = wx.StandardPaths.Get()
    cheminDefaut = sp.GetDocumentsDir()
    dlg = wx.FileDialog(
        None, message="Veuillez sélectionner le répertoire de destination et le nom du fichier",
        defaultDir=cheminDefaut,
        defaultFile=nomFichier,
        wildcard=wildcard,
        style=wx.FD_SAVE
    )
    dlg.SetFilterIndex(0)
    if dlg.ShowModal() == wx.ID_OK:
        cheminFichier = dlg.GetPath()
        dlg.Destroy()
    else:
        dlg.Destroy()
        return

    # Le fichier de destination existe déjà :
    if os.path.isfile(cheminFichier) == True:
        dlg = wx.MessageDialog(None, "Un fichier portant ce nom existe déjà. \n\nVoulez-vous le remplacer ?",
                               "Attention !", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_NO:
            dlg.Destroy()
            return False
        else:
            dlg.Destroy()
    return cheminFichier

def Confirmation(cheminFichier):
    # Confirmation de création du fichier et demande d'ouverture directe
    txtMessage = "Le fichier a été créé avec succès. Souhaitez-vous l'ouvrir dès maintenant ?"
    dlgConfirm = wx.MessageDialog(None, txtMessage, "Confirmation", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
    reponse = dlgConfirm.ShowModal()
    dlgConfirm.Destroy()
    if reponse == wx.ID_YES:
        LanceFichierExterne(cheminFichier)
    return wx.OK

def LigneLgFixe(matrice):
    # crée une fonction appelant les datatype pour formater une ligne à données fixes
    # la matrice décrivant les params doit être structurée: {'code': 'champ1', 'typ': str, 'lg': 8, 'align': "<"},
    lstFunc = [DataType(**x).Convert for x in matrice]
    lstChamps = [x['code'] for x in matrice]

    def func(valeurs):
        texte = ''
        if len(valeurs) != len(lstFunc):
            wx.MessageBox('La matrice prévoit %d champs, la ligne a %d valeurs\n%s\n%s'%(len(lstFunc),len(valeurs),
                                                                                        str(lstChamps),
                                                                                        str(valeurs)),
                          'Echec xexport.LigneLgFixe')
        for ix in range(len(lstFunc)):
            texte += lstFunc[ix](valeurs[ix])
        return texte

    return func

# -------------------------------------------------------------------------------------------------------------------------------

def LanceFichierExterne(nomFichier) :
    """ Ouvre un fichier externe sous windows ou linux """
    if platform.system() == "Windows":
        nomFichier = nomFichier.replace("/", "\\")
        os.startfile(nomFichier)
    if platform.system() == "Linux":
        os.system("xdg-open " + nomFichier)

def ExportTexte(listview=None, grid=None, titre=u"", listeColonnes=None, listeValeurs=None, autoriseSelections=True):
    """ Export de la liste au format texte """
    if (listview != None and len(listview.innerList) == 0) or (
            grid != None and (grid.GetNumberRows() == 0 or grid.GetNumberCols() == 0)):
        dlg = wx.MessageDialog(None, "Il n'y a aucune donnée dans la liste !", "Erreur", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return wx.CANCEL

    # Récupération des valeurs
    if listview != None and listeColonnes == None and listeValeurs == None:
        listeColonnes, listeValeurs = GetValeursListview(listview, format="texte")

    if grid != None and listeColonnes == None and listeValeurs == None:
        autoriseSelections = False
        listeColonnes, listeValeurs = GetValeursGrid(grid)

    # Selection des lignes
    if autoriseSelections == True:
        dlg = xselection.Dialog(None, listeColonnes, listeValeurs, type="exportTexte")
        if dlg.ShowModal() == wx.ID_OK:
            listeSelections = dlg.GetSelections()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return wx.CANCEL

    nomFichier = "ExportTexte_%s.txt" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    wildcard = "Fichier texte (*.txt)|*.txt|" \
               "All files (*.*)|*.*"
    cheminFichier = ChoixDestination(nomFichier,wildcard)
    if not cheminFichier : return wx.CANCEL

    # Création du fichier texte
    texte = ""
    separateur = ";"
    for labelCol, alignement, largeur, code in listeColonnes:
        try:
            if "CheckState" in str(code):
                code = "Coche"
        except:
            pass
        texte += labelCol + separateur
    texte = texte[:-1] + "\n"

    for valeurs in listeValeurs:
        if autoriseSelections == False or valeurs[0] == "" or int(valeurs[0]) in listeSelections:
            for valeur in valeurs:
                if valeur == None:
                    valeur = u""
                texte += u"%s%s" % (valeur, separateur)
            texte = texte[:-1] + "\n"

    # Elimination du dernier saut à la ligne
    texte = texte[:-1]

    # Création du fichier texte
    f = open(cheminFichier, "w")
    f.write(texte)
    print(texte.encode('utf-8'))
    f.close()
    return Confirmation(cheminFichier)

def ExportLgFixe(nomfic='',matrice={},valeurs=[],entete=False):
    """ Export de la liste au format texte """
    if len(valeurs) == 0:
        wx.MessageBox("On ne peut exporter une liste de valeurs vide")
        return wx.CANCEL
    if len(matrice) != len(valeurs[0]):
        wx.MessageBox("Pb: matrice décrit %d colonnes et valeurs[0] en contient %d!"%(len(matrice),
                                                                                        len(valeurs)[0]))

    # Demande à l'utilisateur le nom de fichier et le répertoire de destination
    nomFichier = "%s"%nomfic
    wildcard = "Fichier texte (*.txt)|*.txt|" \
               "All files (*.*)|*.*"
    cheminFichier = ChoixDestination(nomFichier,wildcard)
    if not cheminFichier : return wx.CANCEL

    # Création du fichier texte
    texte = ""
    if entete:
        ligne = [x['code'] for x in matrice]
        matriceEntete = [{'code':x['code'],'cat':str,'lg':x['lg'],} for x in matrice]
        texte += LigneLgFixe(matriceEntete)(ligne)+ "\n"

    makeLigne= LigneLgFixe(matrice)
    for ligne in valeurs:
        texte += makeLigne(ligne)
        texte = texte[:-1] + "\n"

    # Elimination du dernier saut à la ligne
    texte = texte[:-1]

    # Création du fichier texte
    f = open(cheminFichier, "w")
    f.write(texte)
    f.close()
    return Confirmation(cheminFichier)

def ExportExcel(listview=None, grid=None, titre="Liste", listeColonnes=None, listeValeurs=None, autoriseSelections=True):
    # Export de la liste au format Excel
    autoriseSelections = False

    # Vérifie si données bien présentes
    if (listview != None and len(listview.innerList) == 0) or (
            grid != None and (grid.GetNumberRows() == 0 or grid.GetNumberCols() == 0)):
        dlg = wx.MessageDialog(None, "Il n'y a aucune donnée dans la liste !", "Erreur", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return wx.CANCEL

    # Récupération des valeurs
    if listview != None and listeColonnes == None and listeValeurs == None:
        listeColonnes, listeValeurs = GetValeursListview(listview, format="original")

    if grid != None and listeColonnes == None and listeValeurs == None:
        autoriseSelections = False
        listeColonnes, listeValeurs = GetValeursGrid(grid)

    # Selection des lignes
    if autoriseSelections == True:
        dlg = xselection.Dialog(None, listeColonnes, listeValeurs, type="exportExcel")
        if dlg.ShowModal() == wx.ID_OK:
            listeSelections = dlg.GetSelections()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return wx.CANCEL

    # Définit le nom et le chemin du fichier
    nomFichier = "ExportExcel_%s.xls" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    wildcard = "Fichier Excel (*.xls)|*.xls|" \
               "All files (*.*)|*.*"
    cheminFichier = ChoixDestination(nomFichier,wildcard)
    if not cheminFichier : return wx.CANCEL

    # Export
    import xlwt
    # Création d'un classeur
    wb = xlwt.Workbook()
    # Création d'une feuille
    ws1 = wb.add_sheet(titre)
    # Remplissage de la feuille

    al = xlwt.Alignment()
    al.horz = xlwt.Alignment.HORZ_LEFT
    al.vert = xlwt.Alignment.VERT_CENTER

    ar = xlwt.Alignment()
    ar.horz = xlwt.Alignment.HORZ_RIGHT
    ar.vert = xlwt.Alignment.VERT_CENTER

    styleEuros = xlwt.XFStyle()
    styleEuros.num_format_str = '"$"#,##0.00_);("$"#,##'
    styleEuros.alignment = ar

    styleDate = xlwt.XFStyle()
    styleDate.num_format_str = 'DD/MM/YYYY'
    styleDate.alignment = ar

    styleHeure = xlwt.XFStyle()
    styleHeure.num_format_str = "[hh]:mm"
    styleHeure.alignment = ar

    # Création des labels de colonnes
    x = 0
    y = 0
    for labelCol, alignement, largeur, nomChamp in listeColonnes:
        try:
            if "CheckState" in nomChamp:
                nomChamp = "Coche"
        except:
            pass
        ws1.write(x, y, labelCol)
        if largeur <=0 : largeur = 1
        ws1.col(y).width = largeur * 42
        y += 1

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Création des lignes
    def RechercheFormatFromChaine(valeur):
        """ Recherche le type de la chaîne """
        if valeur.endswith(SYMBOLE):
            # Si c'est un montant en euros
            try:
                if valeur.startswith("- "):
                    valeur = valeur.replace("- ", "-")
                if valeur.startswith("+ "):
                    valeur = valeur.replace("+ ", "")
                nbre = float(valeur[:-1])
                return (nbre, styleEuros)
            except:
                pass

        # Si c'est un nombre
        try:
            if valeur.startswith("- "):
                valeur = valeur.replace("- ", "-")
            nbre = float(valeur)
            return (nbre, None)
        except:
            pass

        # Si c'est une date
        try:
            if len(valeur) == 10:
                if valeur[2] == "/" and valeur[5] == "/":
                    return (valeur, styleDate)
        except:
            pass

        if type(valeur) == datetime.timedelta:
            return (valeur, styleHeure)

        # Si c'est une heure
        try:
            if len(valeur) > 3:
                if ":" in valeur:
                    separateur = ":"
                elif "h" in valeur:
                    separateur = "h"
                else:
                    separateur = None
                if separateur != None:
                    heures, minutes = valeur.split(separateur)
                    valeur = datetime.timedelta(minutes=int(heures) * 60 + int(minutes))
                    # valeur = datetime.time(hour=int(valeur.split(separateur)[0]), minute=int(valeur.split(separateur)[1]))
                    return (valeur, styleHeure)
        except:
            pass

        return str(valeur), None

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def RechercheFormat(valeur):
        """ Recherche le type de la donnée """
        if type(valeur) == decimal.Decimal:
            valeur = float(valeur)
            return (valeur, styleEuros)

        if type(valeur) == float:
            return (valeur, None)

        if type(valeur) == int:
            return (valeur, None)

        if type(valeur) == datetime.date:
            valeur = xdates.DateDDEnFr(valeur)
            return (valeur, styleDate)

        if type(valeur) == datetime.timedelta:
            return (valeur, styleHeure)

        try:
            if len(valeur) > 3:
                if ":" in valeur:
                    separateur = ":"
                elif "h" in valeur:
                    separateur = "h"
                else:
                    separateur = None
                if separateur != None:
                    donnees = valeur.split(separateur)
                    if len(donnees) == 2:
                        heures, minutes = donnees
                    if len(donnees) == 3:
                        heures, minutes, secondes = donnees
                    valeur = datetime.timedelta(minutes=int(heures) * 60 + int(minutes))
                    # valeur = datetime.time(hour=int(valeur.split(separateur)[0]), minute=int(valeur.split(separateur)[1]))
                    return (valeur, styleHeure)
        except:
            pass

        if type(valeur) in (str, six.text_type):
            if len(valeur) == 10:
                if valeur[2] == "/" and valeur[5] == "/": return (valeur, styleDate)
                if valeur[4] == "-" and valeur[7] == "-": return (xdates.DateEngFr(valeur), styleDate)

        return str(valeur), None

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    x = 1
    y = 0
    for valeurs in listeValeurs:
        if autoriseSelections == False or int(valeurs[0]) in listeSelections:
            for valeur in valeurs:
                if valeur == None:
                    valeur = u""

                # Recherche s'il y a un format de nombre ou de montant
                if isinstance(valeur,str):
                    valeur, format = RechercheFormatFromChaine(valeur)  # RechercheFormatFromChaine(valeur)
                else:
                    valeur, format = RechercheFormat(valeur)

                # Enregistre la valeur
                if format != None:
                    ws1.write(x, y, valeur, format)
                else:
                    ws1.write(x, y, valeur)

                y += 1
            x += 1
            y = 0

    # Finalisation du fichier xls
    try:
        wb.save(cheminFichier)
    except:
        dlg = wx.MessageDialog(None,
            "Il est impossible d'enregistrer le fichier Excel. Veuillez vérifier que ce fichier n'est pas déjà ouvert en arrière-plan.",
                               "Erreur", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return wx.CANCEL

    return Confirmation(cheminFichier)

# -------------------------------------------------------------------------------------------------------------------------------------------------------------

class DLG_Choix_action(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Choix_action",
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent

        # Bandeau
        intro = "Vous pouvez enregistrer le fichier généré dans le répertoire souhaité."
        titre = "Exporter vers Excel"
        self.ctrl_bandeau = xbandeau.Bandeau(self, titre=titre, texte=intro,hauteur=30,
                                                 nomImage=EXCEL_16X16_IMG)

        self.bouton_enregistrer = xctrlbi.CTRL(self, texte="Enregistrer sous",
                                               cheminImage= SAUVEGARDER_16X16_IMG,
                                               tailleImage=(48, 48), margesImage=(40, 20, 40, 0),
                                               positionImage=wx.TOP, margesTexte=(10, 10))
        self.bouton_enregistrer.SetToolTip(wx.ToolTip("Enregistrer le fichier Excel"))

        self.bouton_annuler = xctrlbi.CTRL(self, id=wx.ID_CANCEL, texte="Annuler",
                                           cheminImage=ANNULER_32X32_IMG)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnregistrer, self.bouton_enregistrer)

    def __set_properties(self):
        self.SetTitle("Exporter vers Excel")
        self.bouton_annuler.SetToolTip(wx.ToolTip("Annuler"))
        self.SetMinSize((370, 300))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)  # mettre cols à 1 ?
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.bouton_enregistrer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonEnregistrer(self, event):
        self.Close()


# ------------------------- POUR LES TESTS ---------------------------------------------

class Track(object):
    def __init__(self, donnees):
        self.ID = donnees["ID"]
        self.texte = donnees["texte"]
        self.entier = donnees["entier"]
        self.date = donnees["date"]
        self.montant = donnees["montant"]
        self.heure = donnees["heure"]


class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        FastObjectListView.__init__(self, *args, **kwds)

    def InitObjectListView(self):

        def FormateDate(dateDD):
            return xdates.DateComplete(dateDD)

        def FormateMontant(montant):
            if montant == None or montant == "": return ""
            return u"%.2f %s" % (montant, SYMBOLE)

        self.SetColumns([
            ColumnDefn(u"ID", "left", 50, "ID", ),
            ColumnDefn(u"Texte", "left", 100, "texte", ),
            ColumnDefn(u"Entier", "left", 100, "entier",),
            ColumnDefn(u"Date", "left", 100, "date", ),
            ColumnDefn(u"Montant", "left", 100, "montant", stringConverter=FormateMontant, ),
            ColumnDefn(u"Heure", "left", 100, "heure", ),
        ])

        self.SetObjects(self.donnees)

    def MAJ(self, ID=None):
        # Création de données exemples
        dictDonnees = {
            "ID": 1,
            "texte": u"Texte unicode",
            "entier": 22,
            "date": datetime.date.today(),
            "montant": decimal.Decimal(13.50),
            "heure": "35h30",
        }
        self.donnees = []
        for x in range(10):
            self.donnees.append(Track(dictDonnees))
        # MAJ
        self.InitObjectListView()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer_1)
        self.listview = ListView(panel, id=-1, name="OL_test",
                                 style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.listview.MAJ()
        # Test de l'export Texte
        ExportExcel(listview=self.listview)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.listview, 1, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    os.chdir("..")
    # wx.InitAllImageHandlers()
    #frame_1 = MyFrame(None, -1, "OL Test Export")
    frame_1 = DLG_Choix_action( None,)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
