# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         Filter.py
# Author:       Phillip Piper, adaptations JB
# Created:      26 August 2008
# Copyright:    (c) 2008 Phillip Piper
# SVN-ID:       $Id$
# License:      wxWindows license
#----------------------------------------------------------------------------

"""
Filters provide a structured mechanism to display only some of the model objects
given to an ObjectListView. Only those model objects which are 'chosen' by
an installed filter will be presented to the user.

Filters are simple callable objects which accept a single parameter, which
is the list of model objects to be filtered, and returns a collection of
those objects which will be presented to the user.

This module provides some standard filters.

Filters almost always impose a performance penalty on the ObjectListView.
The penalty is normally O(n) since the filter normally examines each model
object to see if it should be included. Head() and Tail() are exceptions
to this observation.
"""

import wx
import datetime
import wx.propgrid as wxpg

# Filtres OLV conditions possibles

CHOIX_FILTRES = {
        str:    ['EGAL','DIFFERENT','CONTIENT','COMMENCE','CONTIENTPAS','VIDE','PASVIDE','DANS',
                 'INF','SUP','INFEGAL','SUPEGAL'],
        float:  ['EGAL','DIFFERENT','INF','INFEGAL','SUP','SUPEGAL','COMPRIS'],
        int:    ['EGAL','DIFFERENT','COMPRIS','INF','INFEGAL','SUP','SUPEGAL'],
        bool:   ['EGAL','DIFFERENT'],
        wx.DateTime:      ['DTEGAL','DTDIFFERENT','AVANT','AVANTEGAL','APRES','APRESEGAL'],
        datetime.date:    ['DTEGAL','DTDIFFERENT','AVANT','AVANTEGAL','APRES','APRESEGAL'],
        datetime.datetime:['DTEGAL','DTDIFFERENT','AVANT','AVANTEGAL','APRES','APRESEGAL'],
        }
# textes à afficher pour un choix de filtre
DIC_TXTFILTRES = {
                    'EGAL': 'égal à ',
                    'DIFFERENT': 'différent de ',
                    'CONTIENT': 'contient ',
                    'COMMENCE': 'commence par ',
                    'CONTIENTPAS': 'ne contient pas ',
                    'COMPRIS':  'compris entre x;y',
                    'VIDE': 'est à blanc ',
                    'PASVIDE': 'pas à blanc ',
                    'DANS': 'dans la liste a;b;... ',
                    'INF': 'inférieur à ',
                    'SUP': 'supérieur à ',
                    'INFEGAL': 'inférieur ou égal à ',
                    'SUPEGAL': 'supérieur ou égal à ',
                    'DTEGAL': 'égal à jj/mm/aaaa ',
                    'DTDIFFERENT': 'différent de jj/mm/aaaa ',
                    'AVANT': 'avant jj/mm/aaaa ',
                    'APRES': 'après jj/mm/aaaa ',
                    'AVANTEGAL': 'avant ou égal à jj/mm/aaaa ',
                    'APRESEGAL': 'après ou égal à jj/mm/aaaa ',
}

# Fonctions à lancer selon CHOIX_FILTRES
def GetFnFiltre(typeDonnee,code,choix,critere):
    filtre = None
    tpldate = critere.split('/')
    if len(tpldate) == 3:
        critere = ('20' + tpldate[2])[-4:] + '-' + ('0' + tpldate[1])[-2:] + '-' + ('0' + tpldate[0])[-2:]
    # Texte
    if typeDonnee == str:
        if choix == "EGAL":
            filtre = "track.%s != None and track.%s.lower() == '%s'.lower()" % (code, code, critere)
        elif choix == "DIFFERENT":
            filtre = "track.%s != None and track.%s.lower() != '%s'.lower()" % (code, code, critere)
        elif choix == "CONTIENT":
            filtre = "track.%s != None and '%s'.lower() in track.%s.lower()" % (code, critere, code)
        elif choix == "COMMENCE":
            lg = len(critere)
            filtre = "track.%s != None and '%s'.lower()[:%d] == track.%s.lower()[:%d]" % (code, critere, lg, code, lg)
        elif choix == "CONTIENTPAS":
            filtre = "track.%s != None and '%s'.lower() not in track.%s.lower()" % (code, critere, code)
        elif choix == "VIDE":
            filtre = "track.%s == '' or track.%s == None" % (code, code)
        elif choix == "PASVIDE":
            filtre = "track.%s != '' and track.%s != None" % (code, code)
        elif choix == "DANS":
            lst = critere.split(";")
            serie = "["
            for x in lst:
                serie += "'%s'" % x.lower().strip() + u","
            serie += "]"
            filtre = "track.%s != None and track.%s.lower() in %s" % (code, code, serie)
        elif choix == "INF":
            filtre = "track.%s.lower() < '%s'.lower()" % (code, critere)
        elif choix == "SUP":
            filtre = "track.%s.lower() > '%s'.lower()" % (code, critere)
        elif choix == "INFEGAL":
            filtre = "track.%s.lower() <= '%s'.lower()" % (code, critere)
        elif choix == "SUPEGAL":
            filtre = "track.%s.lower() >= '%s'.lower()" % (code, critere)

    # Entier, montant
    elif typeDonnee in (int, float):
        if choix == "COMPRIS":
            min = str(critere.split(";")[0])
            max = str(critere.split(";")[1])
            filtre = "track.%s >= %s and track.%s <= %s" % (code, min, code, max)
        else:
            critere = str(critere)
        if choix == "EGAL":
            filtre = "track.%s == %s" % (code, critere)
        elif choix == "DIFFERENT":
            filtre = "track.%s != %s" % (code, critere)
        elif choix == "INF":
            filtre = "track.%s < %s" % (code, critere)
        elif choix == "INFEGAL":
            filtre = "track.%s <= %s" % (code, critere)
        elif choix == "SUP":
            filtre = "track.%s > %s" % (code, critere)
        elif choix == "SUPEGAL":
            filtre = "track.%s >= %s" % (code, critere)

    # Bool
    elif typeDonnee == bool:
        critere = str(critere)
        if choix == "EGAL":
            filtre = "track.%s == %s" % (code, critere)
        elif choix == "DIFFERENT":
            filtre = "track.%s != %s" % (code, critere)

    # Date
    elif typeDonnee in  (datetime.date, wx.DateTime, datetime.datetime):
        crit = "%s%s%s" % (critere[:4], critere[5:7], critere[8:10])
        trackdat = "(str(track.%s.year)+ ('0'+str(track.%s.month))[-2:]+ ('0'+str(track.%s.day))[-2:])" \
                   % (code, code, code)
        if choix == "DTEGAL":
            filtre = " %s == '%s'" % (trackdat, crit)
        elif choix == "DTDIFFERENT":
            filtre = " %s != '%s'" % (trackdat, crit)
        elif choix == "AVANT":
            filtre = " %s < '%s'" % (trackdat, crit)
        elif choix == "AVANTEGAL":
            filtre = " %s <= '%s'" % (trackdat, crit)
        elif choix == "APRES":
            filtre = " %s > '%s'" % (trackdat, crit)
        elif choix == "APRESEGAL":
            filtre = " %s >= '%s'" % (trackdat, crit)
    elif not filtre:
        wx.MessageBox("Pb de programmation\npour le type de donnée '%s' il n'y a pas de choix '%s' connu"
                      % (typeDonnee, choix),caption='Filter.GetFiltrePython')

    def fn(track):
        try:
            result = eval(filtre)
        except: result = False
        return result
    fnfiltre = Predicate(fn)

    return fnfiltre

def Predicate(predicate):
    """
    Display only those objects that match the given predicate

    Example::
        self.olv.SetFilter(Filter.Predicate(lambda x: x.IsOverdue()))
    """
    return lambda modelObjects=[]: [x for x in modelObjects if predicate(x)]

def Head(num):
    """
    Display at most the first N of the model objects

    Example::
        self.olv.SetFilter(Filter.Head(1000))
    """
    return lambda modelObjects: modelObjects[:num]

def Tail(num):
    """
    Display at most the last N of the model objects

    Example::
        self.olv.SetFilter(Filter.Tail(1000))
    """
    return lambda modelObjects: modelObjects[-num:]

#**************************************************************************************************

class TextSearch(object):
    """
    Return only model objects that match a given string. If columns is not empty,
    only those columns will be considered when searching for the string. Otherwise,
    all columns will be searched.

    Example::
        self.olv.SetFilter(Filter.TextSearch(self.olv, text="findthis"))
        self.olv.RepopulateList()
    """

    def __init__(self, objectListView, columns=(), text=""):
        """
        Create a filter that includes on modelObject that have 'self.text' somewhere in the given columns.
        """
        self.objectListView = objectListView
        self.columns = columns
        self.text = text

    def __call__(self, modelObjects):
        """
        Return the model objects that contain our text in one of the columns to consider
        """
        if not self.text:
            return modelObjects
        
        # In non-report views, we can only search the primary column
        if self.objectListView.InReportView():
            cols = self.columns or self.objectListView.columns
        else:
            cols = [self.objectListView.columns[0]]

        textToFind = self.EnleveAccents(self.text).lower()

        def _containsText(modelObject):
            for col in cols:
                valeur = col.GetStringValue(modelObject)
                if valeur == None : valeur = ""
                textInListe = self.EnleveAccents(valeur).lower()
                # Recherche de la chaine
                if textToFind in textInListe :
                    return True
            return False

        return [x for x in modelObjects if _containsText(x)]
    
    def EnleveAccents(self, texte):
        try :
            return texte.decode("iso-8859-15")
        except : return texte

    def SetText(self, text):
        """
        Set the text that this filter will match. Set this to None or "" to disable the filter.
        """
        self.text = text

class Chain(object):
    """
    Return only model objects that match all of the given filters.

    Example::
        # Show at most 100 people whose salary is over 50,000
        salaryFilter = Filter.Predicate(lambda person: person.GetSalary() > 50000)
        self.olv.SetFilter(Filter.Chain(salaryFilter, Filter.Tail(100)))
        self.olv.RepopulateList()
    """

    def __init__(self,filterAndNotOr,*filters):
        #Create a filter that performs all the given filters. The order of the filters is important.
        self.filters = filters
        self.filterAndNotOr = filterAndNotOr

    def __call__(self, modelObjects):
        if self.filterAndNotOr:
            #Return the model objects that match all of our filters
            for filter in self.filters:
                modelObjects = filter(modelObjects)
            return modelObjects
        else:
            #Return la fusion des sous ensembles filtrés
            modelcumul = []
            for filter in self.filters:
                model = filter(modelObjects)
                for ligne in model:
                    if not ligne in modelcumul:
                        modelcumul.append(ligne)
            return modelcumul

# pour test -------------------------------------------------
class objet(object):
    def __init__(self):
        self.lstNomsColonnes = ['nbre', 'nom','date']
        self.lstCodesColonnes = ['nbre', 'nom','date']
        self.lstSetterValues = [0, 'bonjour', datetime.date.today()]

if __name__ == '__main__':
# Lancement des tests
    import os
    os.chdir("..")
    os.chdir("..")
    os.chdir("..")
    app = wx.App(0)
    """
    obj = objet()
    frame_3 = zzDLG_saisiefiltre(None,listview = obj)
    app.SetTopWindow(frame_3)
    frame_3.ShowModal()
    """
    print(GetFiltrePython(wx.DateTime,"macolonne","APRES","aujourd'hui"))
    app.MainLoop()
