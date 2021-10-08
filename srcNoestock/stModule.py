#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# stModule: fonctions pour gestion des stocks
# ------------------------------------------------------------------------
import copy
import datetime
from  UTILS_Stocks import SqlMouvementsPeriode as GetMouvements
from  UTILS_Stocks import SqlLastInventaire as GetLastInventaire
from  UTILS_Stocks import PostInventaire as PostInventaire
from xpy.outils    import xformat


class Inventaire:
    # calculs d'inventaire FIFO à une date donnée dite clôture
    def __init__(self,
                 cloture=datetime.date.today(),
                 achat='achat'):
        # 'achat' origine avec prix s'appliquant aux autres mvts
        self.achat = achat
        self.cloture = cloture
        self.mvtsCorriges = []
        self.lastInventaire = GetLastInventaire(cloture)
        if len(self.lastInventaire) == 0:
            self.lastInventaire = None
        else:
            for ligne in self.lastInventaire:
                mvtInv = ligne
        self.dicPrixAchats = {}

    def _IsAchat(self,origine):
        ok = False
        if origine.find(self.achat): ok = True
        if origine.find('invent'): ok = True
        return ok

    def PostInventaire(self):
        # Enregistre les lignes d'inventaire à la date cloture
        ok = False
        ret = self.RecalculPrixSorties()
        if ret: llinventaire = self.CalculInventaire()
        ok = PostInventaire(self.cloture, llinventaire)
        return ok

    def _xAjoutInventaire(self,lstMmouvements):
        # ajout de la reprise d'inventaire
        if not self.lastInventaire: return
        for ligne in self.lastInventaire:
            jour, article, qte, pxMoyen = ligne[:4]
            lstMmouvements.append([jour,"inventaire",article,qte,pxMoyen])
        return

    def CalculInventaire(self,fin=None):
        # retourne un inventaire: liste de liste
        if fin == None: fin = self.cloture

        debut = None
        if self.lastInventaire:
            # présence d'un inventaire antérieur
            debut = xformat.DateSqlToDatetime(self.lastInventaire[0][0])

        #['jour', 'origine', 'nomArticle', 'qteMouvement','prixUnit']
        llMouvements = GetMouvements(debut=debut,fin=fin)
        self._xAjoutInventaire(llMouvements)

        # liste préalable pour traitement par article
        lstArticles = []
        for jour,origine,article,qte,pu in llMouvements:
            if not article:
                raise Exception("Article disparu! mvt du %s qte= %d"%(jour,qte))
            if not article in lstArticles:
                lstArticles.append(article)
        lstArticles.sort()
        if lstArticles == None:
            raise Exception("Aucun mouvement dans la période du %s au %s"\
                  %(debut,fin))

        # composition de l'inventaire
        llinventaire= []
        for article in lstArticles:
            lstMvts = [x[0:2]+x[3:] for x in llMouvements if x[2] == article]
            qte, mtt, lastPrix = self._CalculInventaireUnArticle(lstMvts)
            if qte == 0:
                pu = 0.0
            else: pu = round(mtt/qte,4)
            if qte != 0 and mtt != 0:
                # compose [dte,article,qte,prixMoyen,montant,lastPrix]
                llinventaire.append([
                    xformat.DatetimeToStr(fin,iso=True),
                    article,
                    round(qte,4),
                    pu,
                    round(mtt,4),
                    lastPrix,
                    ])
        return llinventaire

    def _CalculInventaireUnArticle(self,mvts=[[],]):
        # mouvements en tuple (date,origine, qte,pu) qte est signé
        mttFin = 0.0
        qteProgress = 0.0
        qteFin = sum([qte for dte,origine,qte,pu in mvts])

        lstPU = [pu for dte,origine,qte,pu in mvts if origine == self.achat]
        if len(lstPU) == 0:
            # si pas d'entrée principale: moyenne des prix présents
            lstPU = [pu for dte, origine, qte, pu in mvts if pu > 0]
            
        # calcul d'une valeur par défaut de prix unitaire
        if len(lstPU) > 0:
            pu = sum(lstPU) / len(lstPU)
        else: pu = 1

        # recherche des derniers achats (reverse), pour calcul du reste final
        lastPrix = None
        for dte,origine,qte,pu in sorted(mvts,reverse=True):
            # ne prend que les achats
            if origine != self.achat:
                continue
            if not lastPrix:
                lastPrix = pu
            # cet achat n'a pas été consommé, inférieur au reste en stock
            if qteProgress + qte < qteFin:
                mttFin += qte * pu
                qteProgress += qte
            else:
                break
        # ajuste la dernière part
        if qteProgress != qteFin:
            # prend une part de cet achat restant partiellement
            part = qteFin - qteProgress
            mttFin += (part * pu)

        # retour : qte, mttTotal à la date de clôture
        return qteFin,mttFin,lastPrix

    def RecalculPrixSorties(self,fin=None):
        ok = False
        if fin == None: fin = self.cloture
        debut = None
        if self.lastInventaire:
            # présence d'un inventaire antérieur
            debut = xformat.DateSqlToDatetime(self.lastInventaire[0][0])

        #['jour', 'origine', 'nomArticle', 'qteMouvement','prixUnit']
        self.mvtsCorriges = sorted(GetMouvements(debut=debut,fin=fin))
        self._xAjoutInventaire(self.mvtsCorriges)

        lstArticles = []
        # listes préalable, chaque article est traité à part
        for jour,origine,article,qte,pu in self.mvtsCorriges:
            if not article in lstArticles:
                lstArticles.append(article)
        lstArticles.sort()
        if lstArticles == None:
            raise Exception("Aucun mouvement dans la période du %s au %s"\
                  %(debut,fin))

        for article in lstArticles:
            mvtsArticle = []
            # isole les mouvements de l'article
            for mvt in self.mvtsCorriges:
                if mvt[2] != article:
                    continue
                mvtsArticle.append(mvt)
            self._xRecalculPrixSortiesUnArticle(mvtsArticle)
            ok = True
        return ok

    def _xRecalculPrixSortiesUnArticle(self, mvts=[[], ]):
        # mouvements en liste (date,origine, qte,pu) qte est signé
        sorted(mvts, reverse=False)

        # sépare les entrées des sorties
        dicAchats = {}
        lstSorties = []
        for mvt in mvts:
            dte, origine, article, qte, pu = mvt
            if origine in (self.achat, "inventaire"):
                if not dte in dicAchats:
                    dicAchats[dte] = {'qteIn':0, 'mttIn':0}
                dicAchats[dte]['qteIn'] += qte
                dicAchats[dte]['mttIn'] += qte * pu
            else:
                lstSorties.append(mvt)

        # si pas d'entrée ou pas de sortie : abandon
        if len(dicAchats) == 0: return
        if len(lstSorties) == 0: return

        # stockage  de l'affectation qte et montants, entrées sur sorties
        tmpAffect = {}
        ix = -1
        for sortie in lstSorties:
            ix +=1
            tmpAffect[ix] = {'qteAff':0,'mttAff':0}

        # affectation du prix d'entrée sur les sorties plus anciennes
        for dteIn,achat in dicAchats.items():
            qteIn = achat['qteIn']
            if qteIn == 0: continue
            mttIn = achat['mttIn']
            puIn = mttIn / qteIn
            ix = -1
            # recherche des sorties encore non affectées à une entrée
            for dateOut,origine,article,qteOut,puOut in lstSorties:
                ix += 1
                qteAffecte = tmpAffect[ix]['qteAff']
                if qteAffecte >= -qteOut: continue

                mttAffecte = tmpAffect[ix]['mttAff']
                # l'entrée imputer son prix sur la sortie
                qte = min(qteIn, -qteOut - qteAffecte)
                prix = (puIn * qte + mttAffecte)  / (qte + qteAffecte)
                montant = prix * qte
                tmpAffect[ix]['qteAff'] += qteIn
                tmpAffect[ix]['mttAff'] += montant
                qteIn -= qte
                # ici le prix de la sortie est actualisé (élément de liste)
                puOut = prix
                if qteIn == 0:
                    break
                if qteIn < 0:
                    raise Exception("SurAffectation de l'entrée %s:%s"%(
                        dteIn,achat))
        return

class Tests:
    def __init__(self,name=None):
        ok =True
        if not name:
            for method in [
                self.CalculInventaire,
                self.RecalculPrixSorties,
            ]:
                ok = ok & method()
                del method
        else:
            ok = eval("self.%s()"%(name))
        self.ok = ok

    def CalculInventaire(self):
        ret = Inventaire().CalculInventaire()
        if len(ret) > 0: return True
        return False

    def RecalculPrixSorties(self):
        ret = Inventaire().RecalculPrixSorties()
        return ret

if __name__ == '__main__':
    import os
    os.chdir("..")
    inv = Inventaire(datetime.date(2021,9,30))
    #test = Tests()
    test = Tests("CalculInventaire")
    #test = inv.RecalculPrixSorties()
    print(test)
