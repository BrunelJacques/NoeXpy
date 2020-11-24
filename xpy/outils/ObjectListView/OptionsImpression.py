#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------


from __future__ import absolute_import
import wx

#import UTILS_Parametres

import wx.propgrid as wxpg
import copy
import wx.html as html
import sys

from xpy.outils.xconst import *
from xpy.outils import xctrlbi

class EditeurComboBoxAvecBoutons(wxpg.PGChoiceEditor):
    """
    Les classes qui suivent (jusqu'au séparateur) sont issues de CTRL_Propertygrid
    Je les ai mises là pour rassembler tout ce qui concerne l'impression et éviter
    les multiplications de fichiers.
    """
    def __init__(self):
        wxpg.PGChoiceEditor.__init__(self)

    def CreateControls(self, propGrid, property, pos, sz):
        # Create and populate buttons-subwindow
        buttons = wxpg.PGMultiButton(propGrid, sz)

        # Add two regular buttons
        buttons.AddBitmapButton(wx.Bitmap(MECANISME_16X16_IMG, wx.BITMAP_TYPE_PNG))
        buttons.GetButton(0).SetToolTip(PARAM_IMP_TXT)

        # Create the 'primary' editor control (textctrl in this case)
        wnd = self.CallSuperMethod("CreateControls", propGrid, property, pos, buttons.GetPrimarySize())
        buttons.Finalize(propGrid, pos);
        self.buttons = buttons
        return (wnd, buttons)

    def OnEvent(self, propGrid, prop, ctrl, event):
        if event.GetEventType() == wx.wxEVT_COMMAND_BUTTON_CLICKED:
            buttons = self.buttons
            evtId = event.GetId()
            if evtId == buttons.GetButtonId(0):
                propGrid.GetPanel().OnBoutonParametres(prop)

        return self.CallSuperMethod("OnEvent", propGrid, prop, ctrl, event)


class CTRL_Propertygrid(wxpg.PropertyGrid):
    def __init__(self, parent, style=wxpg.PG_SPLITTER_AUTO_CENTER):
        wxpg.PropertyGrid.__init__(self, parent, -1, style=style)
        self.parent = parent
        # Définition des éditeurs personnalisés
        if not getattr(sys, '_PropGridEditorsRegistered', False):
            self.RegisterEditor(EditeurComboBoxAvecBoutons)
            # ensure we only do it once
            sys._PropGridEditorsRegistered = True

        self.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)

        couleurFond = "#e5ecf3"
        self.SetCaptionBackgroundColour(couleurFond)
        self.SetMarginColour(couleurFond)

        self.Bind(wxpg.EVT_PG_CHANGED, self.OnPropGridChange)

        # Remplissage du contrôle
        self.Remplissage()

        # Mémorisation des valeurs par défaut
        self.dictValeursDefaut = self.GetPropertyValues()

        # Importation des valeurs
        self.Importation()

    def OnPropGridChange(self, event):
        event.Skip()

    def Reinitialisation(self):
        dlg = wx.MessageDialog(None, REINITIALISER_PARAM_TXT,
                               "Paramètres par défaut", wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse == wx.ID_YES:
            for nom, valeur in self.dictValeursDefaut.items():
                propriete = self.GetPropertyByName(nom)
                if self.GetPropertyAttribute(propriete, "reinitialisation_interdite") != True:
                    propriete.SetValue(valeur)


class Bouton_reinitialisation(wx.BitmapButton):
    def __init__(self, parent, ctrl_parametres=None):
        wx.BitmapButton.__init__(self, parent, -1, wx.Bitmap(ACTUALISER_16X16_IMG, wx.BITMAP_TYPE_ANY))
        self.ctrl_parametres = ctrl_parametres
        self.SetToolTip(REINITIALISER_PARAM_BTN_TXT)
        self.Bind(wx.EVT_BUTTON, self.OnBouton)

    def OnBouton(self, event):
        self.ctrl_parametres.Reinitialisation()


class Bouton_sauvegarde(wx.BitmapButton):
    def __init__(self, parent, ctrl_parametres=None):
        wx.BitmapButton.__init__(self, parent, -1, wx.Bitmap(SAUVEGARDER_16X16_IMG, wx.BITMAP_TYPE_ANY))
        self.ctrl_parametres = ctrl_parametres
        self.SetToolTip(MEMORISER_PARAM_BTN_TXT)
        self.Bind(wx.EVT_BUTTON, self.OnBouton)

    def OnBouton(self, event):
        self.ctrl_parametres.Sauvegarde(forcer=True)


# ----------------------------------------------------------------------------------------------------------------------


class MyHtml(html.HtmlWindow):
    """
    Classe importée de CTRL_Bandeau pour éviter la multiplication de fichers
    Elle est utilisée dans la classe Bandeau en dessous
    """
    def __init__(self, parent, texte="", hauteur=25):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(0)
        self.SetMinSize((-1, hauteur))
        self.SetPage(u"<FONT SIZE=-1>%s</FONT>""" % texte)


class Bandeau(wx.Panel):
    """
    Classe importée de CTRL_Bandeau pour éviter la multiplication de fichers
    """
    def __init__(self, parent, titre="", texte="", hauteurHtml=25, nomImage=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.nomImage = nomImage
        if self.nomImage is not None:
            img = wx.Bitmap(self.nomImage, wx.BITMAP_TYPE_ANY)
            self.image = wx.StaticBitmap(self, -1, img)
        self.ctrl_titre = wx.StaticText(self, -1, titre)
        self.ctrl_intro = MyHtml(self, texte, hauteurHtml,)
        self.ligne = wx.StaticLine(self, -1)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.ctrl_titre.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

    def __do_layout(self):
        grid_sizer_vertical = wx.FlexGridSizer(rows=2, cols=1, vgap=4, hgap=4)
        grid_sizer_horizontal = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_texte = wx.FlexGridSizer(rows=2, cols=1, vgap=4, hgap=4)
        if self.nomImage != None :
            grid_sizer_horizontal.Add(self.image, 0, wx.ALL, 10)
        else :
            grid_sizer_horizontal.Add( (2, 2), 0, wx.ALL, 10)
        grid_sizer_texte.Add(self.ctrl_titre, 0, wx.TOP, 7)
        grid_sizer_texte.Add(self.ctrl_intro, 0, wx.RIGHT|wx.EXPAND, 5)
        grid_sizer_texte.AddGrowableRow(1)
        grid_sizer_texte.AddGrowableCol(0)
        grid_sizer_horizontal.Add(grid_sizer_texte, 1, wx.EXPAND, 0)
        grid_sizer_horizontal.AddGrowableRow(0)
        grid_sizer_horizontal.AddGrowableCol(1)
        grid_sizer_vertical.Add(grid_sizer_horizontal, 1, wx.EXPAND, 0)
        grid_sizer_vertical.Add(self.ligne, 0, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_vertical)
        grid_sizer_vertical.Fit(self)
        grid_sizer_vertical.AddGrowableRow(0)
        grid_sizer_vertical.AddGrowableCol(0)

class CTRL_Parametres(CTRL_Propertygrid):
    def __init__(self, parent):
        CTRL_Propertygrid.__init__(self, parent)

    def Remplissage(self):
        listeChampsPiedsPages = ["{DATE_JOUR}", "{TITRE_DOCUMENT}", "{NOM_ORGANISATEUR}", "{NUM_PAGE}", "{NBRE_PAGES}"]

        # --------------------------- Divers ------------------------------------------
        self.Append(wxpg.PropertyCategory("Divers"))

        # Inclure les images
        propriete = wxpg.BoolProperty(label=INCLURE_IMG_LABEL, name="inclure_images", value=True)
        propriete.SetHelpString(INCLURE_IMG_HELP)
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Entete de colonne sur chaque page
        propriete = wxpg.BoolProperty(label=AFFICHER_ENTETE_LABEL, name="entetes_toutes_pages",
                                      value=True)
        propriete.SetHelpString(AFFICHER_ENTETE_HELP)
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Qualité de l'impression
        propriete = wxpg.EnumProperty(label=CHOIX_QUALITE_LABEL,
                                      name="qualite_impression",
                                      labels=CHOIX_QUALITE_LABELS,
                                      values=CHOIX_QUALITE_VALEURS,
                                      value=wx.PRINT_QUALITY_MEDIUM)
        propriete.SetHelpString(CHOIX_QUALITE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Marges ------------------------------------------
        self.Append(wxpg.PropertyCategory("Marges"))

        # Gauche
        propriete = wxpg.IntProperty(label=MARGE_GAUCHE_LABEL, name="marge_gauche", value=5)
        propriete.SetHelpString(TAILLE_MARGE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("marge_gauche", "SpinCtrl")

        # Droite
        propriete = wxpg.IntProperty(label=MARGE_DROITE_LABEL, name="marge_droite", value=5)
        propriete.SetHelpString(TAILLE_MARGE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("marge_droite", "SpinCtrl")

        # Haut
        propriete = wxpg.IntProperty(label=MARGE_HAUT_LABEL, name="marge_haut", value=5)
        propriete.SetHelpString(TAILLE_MARGE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("marge_haut", "SpinCtrl")

        # Bas
        propriete = wxpg.IntProperty(label=MARGE_BAS_LABEL, name="marge_bas", value=5)
        propriete.SetHelpString(TAILLE_MARGE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("marge_bas", "SpinCtrl")

        # --------------------------- Quadrillage ------------------------------------------
        self.Append(wxpg.PropertyCategory("Quadrillage"))

        # Epaisseur de trait
        propriete = wxpg.FloatProperty(label=EPAISSEUR_TRAIT_LABEL, name="grille_trait_epaisseur", value=0.25)
        propriete.SetHelpString(EPAISSEUR_TRAIT_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur de trait
        propriete = wxpg.ColourProperty(label=COULEUR_TRAIT_LABEL, name="grille_trait_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TRAIT_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Titre de liste ------------------------------------------
        self.Append(wxpg.PropertyCategory("Titre"))

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="titre_taille_texte", value=16)
        propriete.SetHelpString(TAILLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("titre_taille_texte", "SpinCtrl")

        # Style
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="titre_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_BOLD)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="titre_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Alignement
        labels = ["Gauche", "Centre", "Droite"]
        propriete = wxpg.EnumProperty(label=ALIGNEMENT_TEXTE_LABEL,
                                      name="titre_alignement",
                                      labels=ALIGNEMENT_TEXTE_LABELS,
                                      values=ALIGNEMENT_TEXTE_VALUES,
                                      value=wx.ALIGN_LEFT)
        propriete.SetHelpString(ALIGNEMENT_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Intro ------------------------------------------
        self.Append(wxpg.PropertyCategory("Introduction"))

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="intro_taille_texte", value=7)
        propriete.SetHelpString(TAILLE_TEXTE_INTRO_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("intro_taille_texte", "SpinCtrl")

        # Style
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="intro_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_NORMAL)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="intro_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Alignement
        propriete = wxpg.EnumProperty(label=ALIGNEMENT_TEXTE_LABEL,
                                      name="intro_alignement",
                                      labels=ALIGNEMENT_TEXTE_LABELS,
                                      values=ALIGNEMENT_TEXTE_VALUES,
                                      value=wx.ALIGN_LEFT)
        propriete.SetHelpString(ALIGNEMENT_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Titre de colonne  ------------------------------------------
        self.Append(wxpg.PropertyCategory("Entête de colonne"))

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="titre_colonne_taille_texte", value=8)
        propriete.SetHelpString(TAILLE_TEXTE_TITRE_COL_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("titre_colonne_taille_texte", "SpinCtrl")

        #  Style
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="titre_colonne_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_NORMAL)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="titre_colonne_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Alignement
        propriete = wxpg.EnumProperty(label=ALIGNEMENT_TEXTE_LABEL,
                                      name="titre_colonne_alignement",
                                      labels=ALIGNEMENT_TEXTE_LABELS,
                                      values=ALIGNEMENT_TEXTE_VALUES,
                                      value=wx.ALIGN_CENTER)
        propriete.SetHelpString(ALIGNEMENT_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur de fond
        propriete = wxpg.ColourProperty(label=COULEUR_FOND_LABEL, name="titre_colonne_couleur_fond",
                                        value=wx.Colour(240, 240, 240))
        propriete.SetHelpString(COULEUR_FOND_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Ligne  ------------------------------------------
        self.Append(wxpg.PropertyCategory("Ligne"))

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="ligne_taille_texte", value=8)
        propriete.SetHelpString(TAILLE_TEXTE_LIGNE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("ligne_taille_texte", "SpinCtrl")

        #  Style
        labels = ["Normal", "Light", "Gras"]
        valeurs = [wx.FONTWEIGHT_NORMAL, wx.FONTWEIGHT_LIGHT, wx.FONTWEIGHT_BOLD]
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="ligne_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_NORMAL)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="ligne_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Multilignes autorisé
        propriete = wxpg.BoolProperty(label=AUTORISER_SAUT_LIGNE_LABEL, name="ligne_multilignes", value=True)
        propriete.SetHelpString(AUTORISER_SAUT_LIGNE_HELP)
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # --------------------------- Pied de page  ------------------------------------------
        self.Append(wxpg.PropertyCategory("Pied de page"))

        # Texte de gauche
        valeur = "{DATE_JOUR}"
        propriete = wxpg.StringProperty(label=PIED_TEXTE_GAUCHE_LABEL, name="pied_page_texte_gauche", value=valeur)
        propriete.SetHelpString(
            "Saisissez le texte de gauche du pied de page (Par défaut '%s'). Vous pouvez intégrer les mots-clés suivants : %s" % (
            valeur, ", ".join(listeChampsPiedsPages)))
        self.Append(propriete)

        # Texte du milieu
        valeur = "{TITRE_DOCUMENT} - {NOM_ORGANISATEUR}"
        propriete = wxpg.StringProperty(label=PIED_TEXTE_MILIEU_LABEL, name="pied_page_texte_milieu", value=valeur)
        propriete.SetHelpString(
            "Saisissez le texte du milieu du pied de page (Par défaut '%s'). Vous pouvez intégrer les mots-clés suivants : %s" % (
            valeur, ", ".join(listeChampsPiedsPages)))
        self.Append(propriete)

        # Texte de droite
        valeur = "{NUM_PAGE} / {NBRE_PAGES}"
        propriete = wxpg.StringProperty(label=PIED_TEXTE_DROITE_LABEL, name="pied_page_texte_droite", value=valeur)
        propriete.SetHelpString(
            "Saisissez le texte de droite du pied de page (Par défaut '%s'). Vous pouvez intégrer les mots-clés suivants : %s" % (
            valeur, ", ".join(listeChampsPiedsPages)))
        self.Append(propriete)

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="pied_page_taille_texte", value=8)
        propriete.SetHelpString(TAILLE_TEXTE_PIED_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("pied_page_taille_texte", "SpinCtrl")

        #  Style
        labels = ["Normal", "Light", "Gras"]
        valeurs = [wx.FONTWEIGHT_NORMAL, wx.FONTWEIGHT_LIGHT, wx.FONTWEIGHT_BOLD]
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="pied_page_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_NORMAL)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="pied_page_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Pied de colonne  ------------------------------------------
        self.Append(wxpg.PropertyCategory("Pied de colonne"))

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="pied_colonne_taille_texte", value=8)
        propriete.SetHelpString(TAILLE_TEXTE_PIED_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("pied_colonne_taille_texte", "SpinCtrl")

        #  Style
        labels = ["Normal", "Light", "Gras"]
        valeurs = [wx.FONTWEIGHT_NORMAL, wx.FONTWEIGHT_LIGHT, wx.FONTWEIGHT_BOLD]
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="pied_colonne_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_NORMAL)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="pied_colonne_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Alignement
        labels = ["Gauche", "Centre", "Droite"]
        propriete = wxpg.EnumProperty(label=ALIGNEMENT_TEXTE_LABEL,
                                      name="pied_colonne_alignement",
                                      labels=ALIGNEMENT_TEXTE_LABELS,
                                      values=ALIGNEMENT_TEXTE_VALUES,
                                      value=wx.ALIGN_CENTER)
        propriete.SetHelpString(ALIGNEMENT_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur de fond
        propriete = wxpg.ColourProperty(label=COULEUR_FOND_LABEL, name="pied_colonne_couleur_fond",
                                        value=wx.Colour(240, 240, 240))
        propriete.SetHelpString(COULEUR_FOND_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # --------------------------- Pied de liste ------------------------------------------
        self.Append(wxpg.PropertyCategory("Conclusion"))

        # Taille police
        propriete = wxpg.IntProperty(label=TAILLE_TEXTE_LABEL, name="conclusion_taille_texte", value=7)
        propriete.SetHelpString(TAILLE_TEXTE_CONCL_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("conclusion_taille_texte", "SpinCtrl")

        # Style
        propriete = wxpg.EnumProperty(label=STYLE_TEXTE_LABEL,
                                      name="conclusion_style",
                                      labels=STYLE_TEXTE_LABELS,
                                      values=STYLE_TEXTE_VALEURS,
                                      value=wx.FONTWEIGHT_BOLD)
        propriete.SetHelpString(STYLE_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur
        propriete = wxpg.ColourProperty(label=COULEUR_TEXTE_LABEL, name="conclusion_couleur", value=wx.BLACK)
        propriete.SetHelpString(COULEUR_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Alignement
        labels = ["Gauche", "Centre", "Droite"]
        propriete = wxpg.EnumProperty(label=ALIGNEMENT_TEXTE_LABEL,
                                      name="conclusion_alignement",
                                      labels=ALIGNEMENT_TEXTE_LABELS,
                                      values=ALIGNEMENT_TEXTE_VALUES,
                                      value=wx.ALIGN_LEFT)
        propriete.SetHelpString(ALIGNEMENT_TEXTE_HELP)
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

    def Validation(self):
        """ Validation des données saisies """
        for nom, valeur in list(self.GetPropertyValues().items()):
            propriete = self.GetPropertyByName(nom)
            if self.GetPropertyAttribute(propriete, "obligatoire") == True:
                if valeur == "" or valeur == None:
                    dlg = wx.MessageDialog(self, "Vous devez obligatoirement renseigner le paramètre '%s' !" % nom,
                                           "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
        return True

    def Importation(self):
        """
        Importation des valeurs dans le contrôle
        #TODO: Trouver un autre moyen de stocker les différentes valeur
            (que je ne connais même pas au passage)
        :return:
        """
        # Récupération des noms et valeurs par défaut du contrôle
        #dictValeurs = copy.deepcopy(self.GetPropertyValues())
        # Recherche les paramètres mémorisés
        #dictParametres = UTILS_Parametres.ParametresCategorie(mode="get", categorie="impression_facture",
        #                                                      dictParametres=dictValeurs)
        # Envoie les paramètres dans le contrôle
        #for nom, valeur in dictParametres.items():
        #    propriete = self.GetPropertyByName(nom)
        #    ancienneValeur = propriete.GetValue()
        #    propriete.SetValue(valeur)
        pass

    def Sauvegarde(self, forcer=False):
        """
        Mémorisation des valeurs du contrôle
        TODO: Remettre les fonctions de sauvegarde une fois qu'on l'aura intégré.
        """
        pass
        #dictValeurs = copy.deepcopy(self.GetPropertyValues())
        #UTILS_Parametres.ParametresCategorie(mode="set", categorie="impression_facture", dictParametres=dictValeurs)

    def GetValeurs(self):
        return self.GetPropertyValues()


#-----------------------------------------------------------------------------------------------------------------------

class CTRL(wx.Panel):
    def __init__(self, parent, dictOptions={}):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Orientation
        self.box_orientation_staticbox = wx.StaticBox(self, -1, ORIENTATION_LABEL)
        self.ctrl_radio_portrait = wx.RadioButton(self, -1, u"", style=wx.RB_GROUP)
        self.ctrl_image_portrait = wx.StaticBitmap(self, -1, wx.Bitmap(ORIENTATION_VER_32X32_IMG, wx.BITMAP_TYPE_ANY))
        self.ctrl_radio_paysage = wx.RadioButton(self, -1, u"")
        self.ctrl_image_paysage = wx.StaticBitmap(self, -1, wx.Bitmap(ORIENTATION_HOR_32X32_IMG, wx.BITMAP_TYPE_ANY))

        # Textes
        self.box_document_staticbox = wx.StaticBox(self, -1, "Document")
        self.label_titre = wx.StaticText(self, -1, "Titre :")
        self.ctrl_titre = wx.TextCtrl(self, -1, u"")
        self.label_introduction = wx.StaticText(self, -1, "Introduction :")
        self.ctrl_introduction = wx.TextCtrl(self, -1, u"")
        self.label_conclusion = wx.StaticText(self, -1, "Conclusion :")
        self.ctrl_conclusion = wx.TextCtrl(self, -1, u"")

        # Paramètres généraux
        self.box_options_staticbox = wx.StaticBox(self, -1, "Options d'impression")
        self.ctrl_parametres = CTRL_Parametres(self)
        self.ctrl_parametres.Importation()
        #self.bouton_reinitialisation = CTRL_Propertygrid.Bouton_reinitialisation(self, self.ctrl_parametres)
        #self.bouton_sauvegarde = CTRL_Propertygrid.Bouton_sauvegarde(self, self.ctrl_parametres)
        self.ctrl_parametres.SetMinSize((440, 120))

        self.__do_layout()

        # Properties
        self.ctrl_radio_portrait.SetToolTip(ORIENTATION_PORTRAIT_HELP)
        self.ctrl_image_portrait.SetToolTip(ORIENTATION_PORTRAIT_HELP)
        self.ctrl_radio_paysage.SetToolTip(ORIENTATION_PAYSAGE_HELP)
        self.ctrl_image_paysage.SetToolTip(ORIENTATION_PAYSAGE_HELP)
        self.ctrl_titre.SetToolTip(MODIFIER_TITRE_DOC_HELP)
        self.ctrl_introduction.SetToolTip(MODIFIER_INTRO_DOC_HELP)
        self.ctrl_conclusion.SetToolTip(MODIFIER_CONCL_DOC_HELP)

        # Bind
        self.ctrl_image_portrait.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDownPortrait)
        self.ctrl_image_paysage.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDownPaysage)

        # Init contrôle
        if "titre" in dictOptions and dictOptions["titre"] != None:
            self.ctrl_titre.SetValue(dictOptions["titre"])
        if "introduction" in dictOptions and dictOptions["introduction"] != None:
            self.ctrl_introduction.SetValue(dictOptions["introduction"])
        if "conclusion" in dictOptions and dictOptions["conclusion"] != None:
            self.ctrl_conclusion.SetValue(dictOptions["conclusion"])
        if "orientation" in dictOptions and dictOptions["orientation"] != None:
            self.SetOrientation(dictOptions["orientation"])

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=20)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)

        grid_sizer_haut = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)

        # Orientation
        box_orientation = wx.StaticBoxSizer(self.box_orientation_staticbox, wx.VERTICAL)
        grid_sizer_orientation = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_orientation.Add(self.ctrl_radio_portrait, 0, wx.EXPAND, 0)
        grid_sizer_orientation.Add(self.ctrl_image_portrait, 0, wx.EXPAND, 0)
        grid_sizer_orientation.Add(self.ctrl_radio_paysage, 0, wx.EXPAND, 0)
        grid_sizer_orientation.Add(self.ctrl_image_paysage, 0, wx.EXPAND, 0)
        box_orientation.Add(grid_sizer_orientation, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_haut.Add(box_orientation, 0, wx.EXPAND, 0)

        # Paramètres du document
        box_document = wx.StaticBoxSizer(self.box_document_staticbox, wx.VERTICAL)
        grid_sizer_document = wx.FlexGridSizer(rows=3, cols=2, vgap=2, hgap=10)
        grid_sizer_document.Add(self.label_titre, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_document.Add(self.ctrl_titre, 0, wx.EXPAND, 0)
        grid_sizer_document.Add(self.label_introduction, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_document.Add(self.ctrl_introduction, 0, wx.EXPAND, 0)
        grid_sizer_document.Add(self.label_conclusion, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_document.Add(self.ctrl_conclusion, 0, wx.EXPAND, 0)
        grid_sizer_document.AddGrowableCol(1)
        box_document.Add(grid_sizer_document, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_haut.Add(box_document, 1, wx.EXPAND, 0)

        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.EXPAND | wx.ALL, 0)

        # Paramètres généraux
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_parametres.Add(self.ctrl_parametres, 1, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        #grid_sizer_boutons.Add(self.bouton_reinitialisation, 0, 0, 0)
        #grid_sizer_boutons.Add(self.bouton_sauvegarde, 0, 0, 0)

        grid_sizer_parametres.Add(grid_sizer_boutons, 0, 0, 0)
        grid_sizer_parametres.AddGrowableRow(0)
        grid_sizer_parametres.AddGrowableCol(0)
        box_options.Add(grid_sizer_parametres, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_base.Add(box_options, 1, wx.EXPAND, 0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def OnLeftDownPortrait(self, event):
        self.ctrl_radio_portrait.SetValue(True)

    def OnLeftDownPaysage(self, event):
        self.ctrl_radio_paysage.SetValue(True)

    def MemoriserParametres(self):
        self.ctrl_parametres.Sauvegarde()

    def SetOrientation(self, orientation=wx.PORTRAIT):
        if orientation == wx.PORTRAIT:
            self.ctrl_radio_portrait.SetValue(True)
        else:
            self.ctrl_radio_paysage.SetValue(True)

    def GetOrientation(self):
        if self.ctrl_radio_portrait.GetValue() == True:
            return wx.PORTRAIT
        else:
            return wx.LANDSCAPE

    def GetOptions(self):
        dictOptions = {}

        # Orientation
        dictOptions["orientation"] = self.GetOrientation()

        # Document
        dictOptions["titre"] = self.ctrl_titre.GetValue()
        dictOptions["introduction"] = self.ctrl_introduction.GetValue()
        dictOptions["conclusion"] = self.ctrl_conclusion.GetValue()

        # Récupération des paramètres
        if self.ctrl_parametres.Validation() == False:
            return False
        for nom, valeur in list(self.ctrl_parametres.GetValeurs().items()):
            dictOptions[nom] = valeur

        return dictOptions


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, dictOptions={}):
        wx.Dialog.__init__(self, parent, -1,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent

        # Bandeau
        titre = PARAM_IMP_TITRE
        intro = PARAM_IMP_INTRO
        self.SetTitle(titre)
        self.ctrl_bandeau = Bandeau(self, titre=titre, texte=intro, hauteurHtml=30,
                                                 nomImage=DOCUMENT_PARAM_32X32_IMG)

        # Paramètres
        self.ctrl_parametres = CTRL(self, dictOptions=dictOptions)

        # Boutons
        self.bouton_ok = xctrlbi.CTRL(self, texte="Ok", cheminImage=VALIDER_32X32_IMG)
        self.bouton_annuler = xctrlbi.CTRL(self, texte="Annuler", cheminImage=ANNULER_32X32_IMG)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

        self.bouton_ok.SetFocus()

    def __set_properties(self):
        self.bouton_ok.SetToolTip(VALIDER_BTN_HELP)
        self.bouton_annuler.SetToolTip(ANNULER_BTN_HELP)
        self.SetMinSize((550, 550))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_base.Add(self.ctrl_parametres, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        dictOptions = self.ctrl_parametres.GetOptions()
        if dictOptions == False:
            return

            # Fermeture
        self.EndModal(wx.ID_OK)

    def GetOptions(self):
        return self.ctrl_parametres.GetOptions()


if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()


