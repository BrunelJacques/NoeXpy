#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques Brunel, janvier 2020
# Licence:         Licence GNU GPL
# Permet une saisie d'adresse Noethys
#------------------------------------------------------------------------

import wx
import xpy.outils.xbandeau      as xbd
import srcNoelite.DLG_Villes    as ndv
import srcNoelite.UTILS_Adresses as nua
import xpy.outils.xchoixListe   as xcl

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", image=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if image:
            self.SetBitmap(wx.Bitmap(image))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class CTRL_champ(wx.Panel):
    # Gestion d'une ligne de l'adresse; composée de label, bouton et ctrl
    def __init__(self,parent,nom,label,aide="",valdef="",choices=[""],btntip=u"Gestion",btnonclic=None):
        wx.Panel.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.choices = choices
        self.label = wx.StaticText(self, -1, label + u" :", style=wx.ALIGN_RIGHT,size=(140,20))
        if nom == 'ville':
            self.ctrl = wx.ComboBox(self,-1,value=valdef,choices=choices,style=wx.TE_PROCESS_ENTER)
            self.ctrl.SetSelection(0)
            self.ctrl.Bind(wx.EVT_COMBOBOX,self.parent.OnChoixVille)
            self.bouton = wx.Button(self, -1, "...", size=(20, 20))
            self.bouton.SetToolTip(btntip)
            self.bouton.Bind(wx.EVT_BUTTON, btnonclic)
        elif nom == 'designIndiv':
            self.ctrl = wx.TextCtrl(self, -1, valdef,style=wx.TE_PROCESS_ENTER, size=(230,20))
            self.ctrl.SetMaxLength(38)
            self.bouton = wx.Button(self, -1, "...", size=(20, 20))
            self.bouton.SetToolTip(btntip)
            self.bouton.Bind(wx.EVT_BUTTON, btnonclic)
        elif nom in ('forcer'):
            self.ctrl = wx.CheckBox(self, -1)
        else:
            self.ctrl = wx.TextCtrl(self, -1, valdef,style=wx.TE_PROCESS_ENTER, size=(230,20))
            self.ctrl.SetMaxLength(38)
        self.ctrl.Bind(wx.EVT_TEXT_ENTER, self.parent.OnKeyEnter)
        self.ctrl.Bind(wx.EVT_KILL_FOCUS, self.parent.OnKillFocusChamp)
        self.ctrl.Bind(wx.EVT_SET_FOCUS, self.parent.OnSetFocusChamp)
        self.ctrl.nom = nom
        self.label.SetToolTip(aide)
        self.ctrl.SetToolTip(aide)
        if nom in ('designIndiv','pays','forcer'):
            self.ctrl.Enable(False)
        self.__do_layout()

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_base.Add(self.label, 1, wx.ALIGN_CENTRE_VERTICAL| wx.ALIGN_RIGHT | wx.TOP|wx.RIGHT, 5)
        if self.ctrl.nom in ("designIndiv","ville"):
            gridsizer_base.Add(self.bouton, 0, wx.ALIGN_CENTRE_VERTICAL| wx.ALIGN_RIGHT | wx.TOP|wx.RIGHT, 5)
        else:
            gridsizer_base.Add((10,10), 0, wx.TOP | wx.RIGHT, 5)
        gridsizer_base.Add(self.ctrl, 1, wx.TOP| wx.RIGHT | wx.EXPAND, 5)
        gridsizer_base.AddGrowableCol(2)
        gridsizer_base.AddGrowableRow(0)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        self.Layout()

class PnlAdresse(wx.Panel):
    # Gestion des lignes composant l'adresse
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.lstCpVillesPays = []
        self.parent = parent
        self.oldCp = ""
        self.oldVille = ""
        self.goEvent = None
        if self.parent.mode == "familles":
            lstLignes = [
            ['designation', u"Désignation de la famille",   u"Libellé de l'adresse du courrier pour la famille", u"Obligatoire"],
            ['designIndiv', u"Individu correspondant", u"Individu dont l'adresse est utilisée pour correspondre", u"Obligatoire",
             ["Choisir..."], u"Changement du correspondant de la famille", self.OnClicCorrespondant],
            ]
            self.posAdresse = 2
        else:
            lstLignes = []
            self.posAdresse = 0

        lstLignes += [
            ['appart',  u"Appart,Esc,Etage|Service",
             u"Réservé au numéro de l'appartement, escalier ou étage\nPour une administration le nom du service est accepté"],
            ['batiment',u"Bâtiment, Résidence", u"Un numéro une lettre doivent être précédés de BATIMENT, zone optionnelle"],
            ['rue',     u"No et nom de rue",   u"Aucun caractère spécial ou ponctuation n'est accepté", u"Obligatoire"],
            ['bp',      u"BP, CS, TSA, lieu dit",     u"Uniquement pour préciser une distribution spéciale ou un lieu dit"],
            ['cp', u"Code Postal", u"Saisir le début du code postal ou a blanc pour client parti", u""],
            ['ville', u"Ville", u"Choix de la ville ou gestion par '...'", u"Obligatoire",["Choisir ou saisir..."],
            u"Gestion des villes et des codes postaux",self.OnClicVille],
            ['pays', u"Pays étranger",
                    u"Seulement pour l'étranger, à blanc pour le pays national\nGestion des pays par les villes", "",],
            ['forcer', u"Forcer la saisie", u"Permet de passer outre les contrôles de sortie, procédure exceptionnelle!", ],
        ]
        self.lstColonnes = ["Ville","Code Postal   Pays"]
        self.lstCtrl = []
        self.lstNomsChamps = []
        for ligne in lstLignes:
            self.lstCtrl.append(CTRL_champ(self,*ligne))
            self.lstNomsChamps.append(ligne[0])
        self.__do_layout()

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=len(self.lstCtrl), cols=1, vgap=0, hgap=0)
        for ligne in self.lstCtrl:
            gridsizer_base.Add(ligne, 1, wx.ALL | wx.EXPAND, 5)

        gridsizer_base.AddGrowableCol(0)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        self.Layout()

    def SetVilles(self):
        # pose les choices pour ville
        self.oldVille = self.lstCtrl[self.lstNomsChamps.index("ville")].ctrl.GetValue()
        self.oldPays = self.lstCtrl[self.lstNomsChamps.index("pays")].ctrl.GetValue()
        if len(self.lstCpVillesPays)>0:
            self.lstVilles = []
            self.lstPays = []
            for cp,ville,pays in self.lstCpVillesPays:
                self.lstVilles.append(ville.upper())
                self.lstPays.append(pays.upper())
            ville = self.lstVilles[0]
            if self.oldVille.upper() in self.lstVilles:
                ville = self.oldVille
            self.SetChoices("ville",self.lstVilles)
            self.SetValue("ville",self.lstVilles[self.lstVilles.index(ville)])
            self.SetValue("pays",self.lstPays[self.lstVilles.index(ville)])
        else:
            self.SetValue("ville",u"Gérer la ville")

    def GetVillesDuCp(self,filtrecp,mute=False):
        # Appelle les villes du code postal et prépare les listes des choices de villes
        self.lstCpVillesPays = nua.GetVilles("cp",filtrecp)
        if self.lstCpVillesPays == [("","","")]:
            self.lstCpVillesPays = [("","",filtrecp)]
            return
        self.lstVilles = []
        lstCp = []
        lstChoix = []
        self.lstPays = []
        for cp, ville, pays in self.lstCpVillesPays:
            lstChoix.append((ville, cp +u"\t        " +  pays))
            lstCp.append(cp)
            self.lstVilles.append(ville)
            self.lstPays.append(pays)
        if len(lstChoix)>1 and not mute:
            # le cp  saisi est ambigu ou plusieurs occurences de la ville
            dlg = xcl.DialogAffiche(titre=u"Précisez votre choix",intro=u"Sinon allez choisir la ville par '...'",
                                        lstDonnees=lstChoix,lstColonnes=self.lstColonnes)
            ret = dlg.ShowModal()
            choix = dlg.GetChoix()
            if ret == wx.OK and choix:
                ix = lstChoix.index(dlg.GetChoix())
                ville = self.lstVilles[ix]
                pays = self.lstPays[ix]
                cp = lstCp[ix]
                self.SetValue("ville", ville)
                self.SetValue("cp", cp)
                self.SetValue("pays", pays)
                # Relance sur le code postal pour alimenter correctement la liste des villes et sortie par elif suivant
                ret = self.GetVillesDuCp(cp, mute=True)
            dlg.Destroy()
        elif len(lstChoix) == 1:
            self.SetValue("ville", ville)
            self.SetValue("cp", cp)
            self.SetValue("pays", pays)
        elif not mute:
            wx.MessageBox(u"Code postal inconnu\n\nPassez par la gestion des villes pour le créer")
        self.SetVilles()

    def GetVilleDuNom(self,ville):
        # Appelle les villes correspondant au nom partiellement fourni
        self.lstCpVillesPays = nua.GetVilles("ville",ville)
        if self.lstCpVillesPays == [("","","")]:
            self.lstCpVillesPays = [("", ville, "")]
            return
        lstChoix = []
        self.lstVilles = []
        lstCp = []
        self.lstPays = []
        for cp, ville, pays in self.lstCpVillesPays:
            lstChoix.append((ville, cp +u"\t        " +  pays))
            lstCp.append(cp)
            self.lstVilles.append(ville)
            self.lstPays.append(pays)
        if len(lstChoix)>1:
            # la ville  saisie est ambigue ou plusieurs occurences de la ville
            dlg = xcl.DialogAffiche(lstDonnees=lstChoix,titre=u"Précisez la ville",
                                          intro=u"Sinon allez choisir la ville par '...'")
            ret = dlg.ShowModal()
            if ret == wx.OK and dlg.GetChoix():
                ix = lstChoix.index(dlg.GetChoix())
                ville = self.lstVilles[ix]
                pays = self.lstPays[ix]
                cp = lstCp[ix]
            dlg.Destroy()
        self.SetValue("ville", ville)
        self.SetValue("cp", cp)
        self.SetValue("pays", pays)
        self.GetVillesDuCp(cp,mute=True)

    def SetAdresse(self,adresse=[]):
        # met l'adresse en sept lignes, dans les champs de saisie
        if len(adresse) != 7:
            mess = u"PnlAdresse.SetAdresse: Adresse n'ayant pas 7 lignes!\n\n%s"%str(adresse)
            wx.MessageBox(mess)
            return
        cp = adresse[4]
        self.lstCpVillesPays = nua.GetVilles("cp", cp)
        self.lstVilles= [vil for cp,vil,pays in self.lstCpVillesPays]
        self.lstPays= [pays for cp,vil,pays in self.lstCpVillesPays]
        self.SetChoices("ville", self.lstVilles)
        for ix in range(7):
            self.lstCtrl[ix+self.posAdresse].ctrl.SetValue(adresse[ix])
        return

    def SetCorrespondant(self,dicCorrespondant):
        # met les champs deu correspondant dans la grille
        self.dicCorrespondant = dicCorrespondant
        ix = 0
        for champ in ('designation','designIndiv'):
            if not dicCorrespondant[champ]:
                dicCorrespondant[champ] = ''
            value = str(dicCorrespondant[champ])
            if not isinstance(value,str): value = str(value)
            self.lstCtrl[ix].ctrl.SetValue(value)
            ix += 1
        return

    def GetAdresse(self):
        # retourne l'adresse saisie dans les champs
        adresse = []
        for ix in range(7):
            adresse.append(self.lstCtrl[ix+self.posAdresse].ctrl.GetValue())
        return adresse

    def MAJ(self,nomEvent=None):
        if self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.GetValue(): return
        cp = self.lstCtrl[self.lstNomsChamps.index("cp")].ctrl.GetValue()
        if nomEvent == "cp":
            if self.oldCp != cp and len(cp)>1:
                # Le code postal a été modifié, recherche des villes associées
                self.GetVillesDuCp(cp)
        if nomEvent == "ville" :
            ville = self.lstCtrl[self.lstNomsChamps.index("ville")].ctrl.GetValue()
            if self.oldVille != ville and len(ville) > 1:
                # Le nom de la ville a été modifié recherche des ambigus
                self.GetVilleDuNom(ville)

    def OnKillFocusChamp(self,event):
        if not self.goEvent:
            self.goEvent = event.EventObject.nom
            # Gestion de la sortie de certains champs
            if event.EventObject.nom in ("cp","ville"):
                self.MAJ(event.EventObject.nom)
            self.goEvent = None
        event.Skip()

    def OnSetFocusChamp(self,event):
        event.Skip()

    def OnKeyEnter(self,event):
        if not self.goEvent:
            # blocage pour ne gérer qu'un seul évènement et non la rafale
            self.goEvent = event.EventObject.nom
            nom = event.EventObject.nom
            if nom in ("cp","ville"):
                # seuls ces deux champs font l'objet d'un traitement
                self.MAJ(nom)
            ix = self.lstNomsChamps.index(nom) +1
            if len(self.lstNomsChamps)>ix:
                self.lstCtrl[ix].ctrl.SetFocus()
            self.goEvent = None
        event.Skip()

    def OnChoixVille(self,event):
        event.Skip()
        ix = self.lstNomsChamps.index("ville")
        ville = self.lstCtrl[ix].ctrl.GetValue()
        self.SetValue("pays", self.lstPays[self.lstVilles.index(ville)])
        self.SetValue("ville",ville)
        self.lstCtrl[0].ctrl.SetFocus()

    def OnClicVille(self,event):
        event.Skip()
        dlg = ndv.Dialog(None, modeImportation=True)
        ret = dlg.ShowModal()
        if  ret == wx.OK:
            cp, ville, pays = dlg.GetVille()
            self.SetValue("cp",cp)
            self.SetValue("ville",ville)
            self.SetValue("pays", pays)
        dlg.Destroy()

    def OnClicCorrespondant(self,event):
        event.Skip()
        ret  = nua.GetDBCorrespondant(self.parent.IDfamille)
        if ret == wx.ID_ABORT:
            return
        elif isinstance(ret,tuple):
            # cas d'absence d'adresse saisie dans la famille, on prépare la saisie d'une adresse propre
            #flag = ret[0]
            IDindividu = ret[1]
            designIndiv = ret[2]
            self.dicCorrespondant['IDindividu'] = IDindividu
            self.dicCorrespondant['designIndiv'] = designIndiv
            self.SetValue('designIndiv',designIndiv)
            return
        IDindividu = ret

        lstAdresse, IDindividuLu,(nom,prenom) = nua.GetDBadresse(IDindividu,retNom=True)
        if IDindividu  and IDindividu != IDindividuLu:
            if not nom or nom == "":
                mess = "Adresse perdue,\n\nvous pouvez affecter un autre correspondant"
                ret = wx.MessageBox(mess, "Pas d'adresse", style=wx.OK_DEFAULT | wx.CENTER)
                return
            else:
                mess = "Cette personne avait l'adresse de %s %s\n\nChoisissez un autre correspondant," % (
                prenom, nom)
                mess += "\nou gérez préalablement les adresses des individus de la famille"
                ret = wx.MessageBox(mess, "Pas d'adresse personnelle", style=wx.OK_DEFAULT | wx.CENTER)
                return
        if IDindividu  and IDindividu != self.dicCorrespondant['IDindividu']:
            designIndiv = "%d - %s %s"%(IDindividu,prenom,nom)
            self.dicCorrespondant['IDindividu'] = IDindividu
            self.dicCorrespondant['designIndiv'] = designIndiv
            self.SetAdresse(lstAdresse)
            self.SetValue('designIndiv',designIndiv)

    def SetValue(self,champ,valeur):
        # SetValue de 'valeur' sur le ctrl de la ligne nommée par 'champ'
        ixChamp = self.lstNomsChamps.index(champ)
        self.lstCtrl[ixChamp].ctrl.SetValue(valeur)

    def SetString(self,champ,valeur):
        # SetValue de 'valeur' sur le ctrl de la ligne nommée par 'champ'
        ixChamp = self.lstNomsChamps.index(champ)
        self.lstCtrl[ixChamp].ctrl.SetValue(valeur)

    def SetChoices(self,champ,lstval,pos=0):
        # SetChoices de 'valeur' sur le wx.Choice de la ligne nommée par 'champ'
        ixChamp = self.lstNomsChamps.index(champ)
        self.lstCtrl[ixChamp].ctrl.Set(lstval)

class DlgAdresses_saisie(wx.Dialog):
    # Gestion de l'adresse dans sa fenêtre
    def __init__(self,ID,mode='individus',LargeurCode=180,LargeurLib=100,minSize=(180, 350),
                 titre=u"Saisie d'une adresse normalisée",intro=u"Lignes limitées à 38 caractères"):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle("aDLG_Adresses_saisie")
        self.mode = mode
        self.choix= None
        if self.mode == 'familles':
            self.dicCorrespondant = nua.GetDBfamille(ID)
            self.IDfamille = ID
            self.IDindividu = self.dicCorrespondant['IDindividu']
        else:
            self.dicCorrespondant = {'IDindividu':ID}
            self.IDindividu = ID
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=15, nomImage="xpy/Images/32x32/Matth.png")
        # conteneur des données
        self.panelAdresse = PnlAdresse(self)
        self.lstCtrl = self.panelAdresse.lstCtrl
        self.lstNomsChamps = self.panelAdresse.lstNomsChamps

        if self.mode == 'familles':
            self.panelAdresse.SetCorrespondant(self.dicCorrespondant)
        self.lstAdresse, self.IDindividuLu,(nom,prenom) = nua.GetDBadresse(self.IDindividu,retNom=True)
        if self.IDindividu == self.IDindividuLu:
            self.panelAdresse.SetAdresse(self.lstAdresse)
        elif not nom or nom == "":
            mess = "Cette adresse est perdue,\n\nVoulez-vous créer une nouvelle adresse?"
            ret = wx.MessageBox(mess, "Pas d'adresse personnelle", style=wx.YES_NO | wx.CENTER)
            if ret == wx.YES:
                self.panelAdresse.SetAdresse(self.lstAdresse)
            else: self.Destroy()
        else:
            mess = "Cette personne avait l'adresse de %s %s\n\nVoulez-vous lui créer une adresse personnelle?"%(prenom,nom)
            mess += "\nSinon changez l'adresse de l'individu %s"%self.IDindividuLu
            ret = wx.MessageBox(mess,"Pas d'adresse personnelle",style=wx.YES_NO|wx.CENTER)
            if ret != wx.YES:
                self.Destroy()

        # Boutons
        self.bouton_remonte = CTRL_Bouton_image(self, texte=u"Remonte\nex adr.", image="xpy/Images/32x32/Actualiser.png",)
        self.bouton_ok = CTRL_Bouton_image(self, texte=u"Valider", image="xpy/Images/32x32/Valider.png")
        self.bouton_fermer = CTRL_Bouton_image(self, texte=u"Abandon", image="xpy/Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_remonte.SetToolTip(u"Cliquez ici pour remonter la première saisie")
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour abandonner la saisie")
        self.bouton_ok.SetToolTip(u"Cliquez ici pour enregistrer les modifications")
        # Binds
        self.bouton_remonte.Bind(wx.EVT_BUTTON, self.OnClicRemonte)
        self.bouton_ok.Bind(wx.EVT_BUTTON, self.OnClicOk)
        self.bouton_fermer.Bind(wx.EVT_BUTTON, self.OnClicFermer)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.panelAdresse, 1, wx.LEFT|wx.EXPAND, 10)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=0, hgap=0)
        gridsizer_boutons.Add(self.bouton_remonte, 0, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(1)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnClicRemonte(self, event):
        event.Skip()
        self.lstAdresse = nua.GetDBoldAdresse(IDindividu=self.IDindividu)
        if not self.lstAdresse :
            wx.MessageBox(u"Pas d'adresse antérieure stockée!")
        else:
            self.panelAdresse.SetAdresse(self.lstAdresse)
            #self.panelAdresse.MAJ()

    def OnClicFermer(self, event):
        # Abandon
        if event : event.Skip()
        self.EndModal(wx.ID_CANCEL)

    def Enregistre(self):
        self.IDindividu = self.dicCorrespondant['IDindividu']
        # Enregistrement de l'adresse et sortie
        ret = nua.SetDBadresse(None,self.IDindividu,self.lstAdresse)
        if ret != "ok":
            wx.MessageBox("Pas d'écriture possible !\nAbandon de la modification\n%s"%ret)
            self.EndModal(wx.ID_ABORT)
        else:
            # archive cette adresse s'il n'y en a pas d'autre
            exadresse = nua.GetDBoldAdresse(self.IDindividu)
            if not exadresse:
                ret = nua.SetDBoldAdresse(None,self.IDindividu, self.lstAdresse)
            self.EndModal(wx.OK)
        if self.mode == 'familles':
            ret = nua.SetDBcorrespondant(self.dicCorrespondant)
            if ret[:2] != "ok":
                wx.MessageBox("Pas d'écriture possible du correspondant !\n%s"%ret)

    def OnClicOk(self, event):
        event.Skip()
        forcer = self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.Value
        mess = ""
        saisie = self.panelAdresse.GetAdresse()
        if not forcer:
            self.lstAdresse = nua.TransposeAdresse(saisie)
            self.panelAdresse.SetAdresse(self.lstAdresse)
        else: self.lstAdresse = saisie
        if self.mode == 'familles':
            self.dicCorrespondant = self.panelAdresse.dicCorrespondant
        nonmodifiee=True
        for i in range(len(saisie)):
            if saisie[i].upper() != self.lstAdresse[i].upper():
                nonmodifiee = False
        validee = False
        if not forcer:
            mess = nua.Validation(self.lstAdresse)
            if mess == wx.OK:
                validee = True
        self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.Enable(True)
        self.lstCtrl[self.lstNomsChamps.index("pays")].ctrl.Enable(True)

        if (validee and nonmodifiee) or forcer:
            self.Enregistre()
        elif validee:
            self.panelAdresse.SetAdresse(self.lstAdresse)
            mess = ""
            for x in self.lstAdresse:
                mess += "      %s\n" % (x)
            mess += "             'Oui' pour Accepter\n"
            mess += "             'Non' pour forcer"
            mesdlg = wx.MessageDialog(None,
                                      "L'adresse vient d'être reformatée !\n\n%s" % mess,
                                      caption="aDLG_SaisieAdresse: Validation",
                                      style=wx.YES_NO | wx.ICON_QUESTION, pos=(20, 20), )
            ret = mesdlg.ShowModal()
            if ret == wx.ID_YES:
                self.Enregistre()
            if ret == wx.ID_NO:
                self.panelAdresse.SetAdresse(saisie)
                self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.Enable(True)
                self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.SetValue(True)
        elif nonmodifiee:
            wx.MessageBox(mess+"\n\nPour sortir quand même sans abandonner, vous pouvez cocher la case 'Forcer la saisie'")

if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    dlg = wx.Frame(None)
    dlg.ID = 60
    dlg2 = DlgAdresses_saisie(dlg.ID, mode='familles', titre="Adresse de %d"%dlg.ID)
    dlg2.ShowModal()
    app.MainLoop()
