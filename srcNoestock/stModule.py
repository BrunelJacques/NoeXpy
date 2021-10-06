#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# stModule: fonctions pour gestion des stocks
# ------------------------------------------------------------------------
import datetime
import copy
from  UTILS_Stocks import SqlMouvementsPeriode as GetMouvements

class Inventaire(object):
    # calculs d'inventaire FIFO à une date donnée dite clôture
    def __init__(self,cloture=None,entree='achat'):
        self.cloture = cloture
        # libellé désignant l'origine du mouvement principale pour entrées
        self.entree = entree
        self.dicPrixAchats = {}
        self.mvtsInitiaux = []
        self.mvtsCorriges = []

    def CalculInventaire(self,debut=None,fin=None):
        if fin == None: fin = self.cloture

        #['jour', 'origine', 'nomArticle', 'qteMouvement','prixUnit']
        llMouvements = GetMouvements(debut=debut,fin=fin)

        lstArticles = []
        for jour,origine,article,qte,pu in llMouvements:
            if not article in lstArticles:
                lstArticles.append(article)
        lstArticles.sort()
        if lstArticles == None:
            raise Exception("Aucun mouvement dans la période du %s au %s"\
                  %(debut,fin))

        inventaire = []
        for article in lstArticles:
            lstMvts = [x[0:2]+x[3:] for x in llMouvements if x[2] == article]
            qte, mtt = self._CalculInventaireUnArticle(lstMvts)
            if qte == 0:
                pu = 0.0
            else: pu = round(mtt/qte,4)
            inventaire.append([article,
                               round(qte,4),
                               pu,
                               round(mtt,4)])
        return inventaire

    def _CalculInventaireUnArticle(self,mvts=[[],]):
        # mouvements en tuple (date,origine, qte,pu) qte est signé
        mttFin = 0.0
        qteProgress = 0.0
        qteFin = sum([qte for dte,origine,qte,pu in mvts])
        lstPU = [pu for dte,origine,qte,pu in mvts if origine == self.entree and pu > 0]
        if len(lstPU) == 0:
            # si pas d'entrée principale: moyenne des prix présents
            lstPU = [pu for dte, origine, qte, pu in mvts if pu > 0]
            
        # calcul d'une valeur par défaut de prix unitaire
        if len(lstPU) > 0:
            pu = sum(lstPU) / len(lstPU)
        else: pu = 1

        # recherche des derniers achats (reverse), pour calcul du reste final
        for dte,origine,qte,pu in sorted(mvts,reverse=True):
            # ne prend que les achats
            if origine != self.entree:
                continue
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
        return qteFin,mttFin

    def RecalculPrixSortis(self,debut=None,fin=None):
        if fin == None: fin = self.cloture

        #['jour', 'origine', 'nomArticle', 'qteMouvement','prixUnit']
        self.mvtsCorriges = sorted(GetMouvements(debut=debut,fin=fin))
        self.mvtsInitiaux = copy.deepcopy([x for x in self.mvtsCorriges])

        lstArticles = []
        for jour,origine,article,qte,pu in self.mvtsCorriges:
            if not article in lstArticles:
                lstArticles.append(article)
        lstArticles.sort()
        if lstArticles == None:
            raise Exception("Aucun mouvement dans la période du %s au %s"\
                  %(debut,fin))

        for article in lstArticles:
            mvtsArticle = []
            for mvt in self.mvtsCorriges:
                if mvt[2] != article:
                    continue
                mvtsArticle.append(mvt)
            self._RecalculPrixSortisUnArticle(mvtsArticle)
        return self.mvtsCorriges

    def _RecalculPrixSortisUnArticle(self, mvts=[[], ]):
        # mouvements en tuple (date,origine, qte,pu) qte est signé
        sorted(mvts, reverse=False)
        lstDtesEntrees = [dte for dte, origine, article, qte, pu in mvts if qte > 0]
        if len(lstDtesEntrees) == 0:
            # si pas d'entrée : abandon
            return
        def mvtsAnterieurs(dte):
            return [x[0:2]+x[3:] for x in mvts if x[0] <= dte]
        ix = 0
        qteFin = 0
        while qteFin == 0:
            if ix > len(lstDtesEntrees)-1:
                return
            premiereEntree = lstDtesEntrees[ix]
            qteFin,mttFin = self._CalculInventaireUnArticle(mvtsAnterieurs(premiereEntree))
            ix += 1
        ix -= 1
        if qteFin == 0:
            return
        prixMoyenCeJour = mttFin / qteFin

        dteEntree = None
        for mvt in mvts:
            dte, origine, article, qte, pu = mvt
            if (not dteEntree) and qte < 0:
                    # sortie qui précède toute entrée
                    mvt[4] = prixMoyenCeJour
            elif (qte < 0) and (dteEntree <= dte):
                # les sorties postérieures à l'entrée prennent le prix moyen
                mvt[4] = prixMoyenCeJour
            elif (qte > 0) and ((not dteEntree) or (dteEntree < dte)):
                # nouvelle entrée à cette date
                ix += 1
                if ix < len(lstDtesEntrees):
                    dteEntree = lstDtesEntrees[ix]
                    qteFin, mttFin = self._CalculInventaireUnArticle(mvtsAnterieurs(dteEntree))
                    if qteFin != 0:
                        prixMoyenCeJour = mttFin / qteFin
                continue
        return


if __name__ == '__main__':
    import os
    os.chdir("..")
    """mvts =[
        ["2021-07-01", "repas", -72, 0.75, ],
        ["2021-07-05", "achat", 36, 0.745534, ],
        ["2021-07-08", "achat", 72, 0.745709, ],
        ["2021-07-09", "achat", 72, 1.10775, ],
        ["2021-07-10", "repas", -36, 0.89049, ],
        ["2021-07-19", "achat", 180, 1.29, ],
        ["2021-07-19", "repas", -108, 1.288569, ],
        ["2021-07-29", "achat", 180, 1.2871, ],
        ["2021-07-30", "od_in", 90, 1.28857, ],
        ["2021-08-02", "repas", -180, 1.287753, ],
        ["2021-08-16", "repas", -140, 1.287753, ],
        ["2021-08-21", "od_in", 140, 1.28778, ],
        ["2021-08-23", "achat", 144, 0.7385, ],
        ["2021-08-23", "repas", -144, 1.01314, ],
        ["2021-09-05", "repas", -44, 1.01314, ],
    ]"""
    clôture = datetime.date.today()
    inv = Inventaire(clôture)
    ret = inv.CalculInventaire(fin=clôture)
    dicmodifie = inv.RecalculPrixSortis()
    avant = [x for x in inv.mvtsInitiaux if x[2] == "ABRICOTS FRAIS KG"]
    apres = [x for x in inv.mvtsCorriges if x[2] == "ABRICOTS FRAIS KG"]
    print(ret)
