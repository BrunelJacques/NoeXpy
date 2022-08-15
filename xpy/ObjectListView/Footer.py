#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
from wx import Control

class Footer(Control):
    def __init__(self, 
            parent, 
            id=-1, 
            pos=wx.DefaultPosition, 
            size=wx.DefaultSize, 
            style=wx.NO_BORDER, 
            name="footer",
        ):
        self.hauteur = 24
        self.afficherColonneDroite = True
        
        self.listview = None
        self.dictColFooter = {}
        self.dictTotaux = {}
        self.listeImpression = []
        Control.__init__(self, parent, id=id, pos=pos, size=size, style=style, name=name)
        self.SetInitialSize(size)
                    
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
        self.Bind(wx.EVT_SIZE, self.MAJ_affichage)
    
    def MAJ_affichage(self, event=None):
        self.Refresh() 
    
    def MAJ_totaux(self):
        # Normalisation casse des noms de colonne
        dictColFooter = {}
        for nomColonne, dictColonne in self.dictColFooter.items():
            dictColFooter[nomColonne]=dictColonne
        self.dictColFooter = dictColFooter
        objects = self.listview.GetCheckedObjects()
        if len(objects) == 0:
            objects = self.listview.innerList
        self.dictTotaux = {}
        for track in objects:
            for nomColonne, dictColonne in self.dictColFooter.items() :
                if dictColonne["mode"] == "maximum":
                    if hasattr(track, nomColonne):
                        maximum = getattr(track, nomColonne)
                        if not nomColonne in self.dictTotaux:
                            self.dictTotaux[nomColonne] = 0
                        if maximum != None :
                            if isinstance(maximum,str):
                                maximum = float(maximum.replace(',','.'))
                            self.dictTotaux[nomColonne] = max(maximum,self.dictTotaux[nomColonne])
                if dictColonne["mode"] == "total":
                    if hasattr(track, nomColonne):
                        total = getattr(track, nomColonne)
                        if not nomColonne in self.dictTotaux:
                            self.dictTotaux[nomColonne] = 0
                        if total != None :
                            if isinstance(total,str):
                                try:
                                    total = float(total.replace(',','.'))
                                except: total = 0.0
                            self.dictTotaux[nomColonne] += total
                if dictColonne["mode"] == "nombre" :
                    if hasattr(track, nomColonne):
                        valeur = getattr(track, nomColonne)
                        if not nomColonne in self.dictTotaux:
                            self.dictTotaux[nomColonne] = 0
                        if valeur != None and len(str(valeur)) > 0:
                            self.dictTotaux[nomColonne] += 1

    def DrawColonne(self, dc, x, largeur, label="", alignement=None, couleur=None, font=None):
        """ Dessine une colonne """
        render = wx.RendererNative.Get()
        options = wx.HeaderButtonParams()
        if not isinstance(label,str):
            label = str(label)
        options.m_labelText = label
        if alignement : options.m_labelAlignment = alignement
        if couleur : options.m_labelColour = couleur
        if font : options.m_labelFont = font
        render.DrawHeaderButton(self, dc, (x, 1, largeur, self.hauteur), params=options)
        
    def Paint(self, dc):
        """Draws the ticker text at the current offset using the provided DC"""
        defaultFont = self.GetFont()
        dc.SetFont(defaultFont)
        
        x = 0 - self.listview.GetScrollPos(wx.HORIZONTAL) 
        self.listeImpression = []
        dernierTexte = ""
        self.MAJ_totaux()
        for (indexColonne, col) in enumerate(self.listview.columns):
            texte = ""
            font = wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            couleur = wx.Colour(140, 140, 140)
            largeur = col.width
            #largeur = self.listview.GetColumnWidth(indexColonne)
            converter = col.stringConverter
            nom = col.valueGetter
            alignement = wx.ALIGN_CENTER
            if col.align == "left" : alignement = wx.ALIGN_LEFT
            if col.align == "centre" : alignement = wx.ALIGN_CENTER
            if col.align == "right" : alignement = wx.ALIGN_RIGHT

            # Recherche infos personnalisées à afficher dans la colonne
            mode = None
            if nom in self.dictColFooter :
                infoColonne = self.dictColFooter[nom]

                mode = infoColonne["mode"]

                # Valeur : MAXIMUM
                if mode == "maximum" :
                    if nom in self.dictTotaux :
                        texte = self.dictTotaux[nom]
                    else :
                        texte = 0
                    if converter != None :
                        texte = converter(texte)
                    if type(texte) in (int, float) :
                        texte = str(texte)

                # Valeur : TOTAL
                if mode == "total" :
                    if nom in self.dictTotaux :
                        texte = self.dictTotaux[nom]
                    else :
                        # Total format classique (numérique)
                        texte = 0
                        # Autres formats de total
                        if "format" in infoColonne :
                            if infoColonne["format"] in ("temps", "duree") :
                                texte = datetime.timedelta(0)
                    if converter != None :
                        texte = converter(texte)
                    if type(texte) in (int, float) :
                        texte = str(texte)
                
                # Valeur : NOMBRE
                if mode == "nombre" :
                    singulier = u"ligne cochée"
                    pluriel = u"lignes cochées"
                    if "singulier" in infoColonne:  singulier = infoColonne["singulier"]
                    if "pluriel" in infoColonne:    pluriel   = infoColonne["pluriel"]
                    objects = self.listview.GetCheckedObjects()
                    nombre = len(objects)
                    if len(objects) == 0:
                        if not "singulier" in infoColonne:  singulier = u"ligne non nulle"
                        if not "pluriel" in infoColonne:    pluriel   = u"lignes non nulles"
                        if nom in self.dictTotaux:
                            nombre = self.dictTotaux[nom]
                        else:
                            nombre = 0
                    if nombre > 1 :
                        texte = "%d %s" % (nombre, pluriel)
                    else :
                        texte = "%d %s" % (nombre, singulier)
                        
                # Valeur : TEXTE
                if mode == "texte" :
                    texte = infoColonne["texte"]

                # Paramètres personnalisés
                if "alignement" in infoColonne : alignement = infoColonne["alignement"]
                if "font" in infoColonne : font = infoColonne["font"]
                if "couleur" in infoColonne : couleur = infoColonne["couleur"]
            
            # Pour éviter les bords si les cases sont vides
            ajustement = 0
            if mode != "total" and dernierTexte == "" :
                ajustement = 5
                
            self.DrawColonne(dc, x-ajustement, largeur+ajustement, texte, alignement, couleur, font)
            x += largeur
            
            # Mémorisation pour impression
            self.listeImpression.append({"texte" : texte, "alignement" : alignement})
            
            if mode == "total" :
                dernierTexte = texte
            else :
                dernierTexte = ""
        
        # Dernière colonne de remplissage
        if self.afficherColonneDroite :
            self.DrawColonne(dc, x, self.GetSize()[0]-x)

    def GetDonneesImpression(self, typeInfo="texte"):
        """ Renvoie infos pour impression """
        """ typeInfo = "texte" ou "alignement" """
        lstDonnees = []
        for info in self.listeImpression :
            lstDonnees.append(info[typeInfo])
        return lstDonnees[1:]
    
    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        self.Paint(dc)
        
    def OnErase(self, evt):
        """Noop because of double buffering"""
        pass

    def AcceptsFocus(self):
        """Non-interactive, so don't accept focus"""
        return False
        
    def DoGetBestSize(self):
        """Width we don't care about, height is either -1, or the character
        height of our text with a little extra padding
        """
        return (100, self.hauteur-1)

    def ShouldInheritColours(self): 
        """Don't get colours from our parent..."""
        return False


if __name__ == '__main__':
    """ DEMO FRAME"""
    app = wx.App()
    f = wx.Frame(None)
    p = wx.Panel(f)
    t = Footer(p)
    s = wx.BoxSizer(wx.VERTICAL)
    s.Add(t, flag=wx.GROW, proportion=1)
    p.SetSizer(s)
    f.Show()
    app.MainLoop()
    
    
