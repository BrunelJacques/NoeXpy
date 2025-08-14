#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------- Variables globales à appeler

# Trame des formats d'imports pour transpose, inclu le pointeur de la fonction Compose
def GetFormatsImport(ComposeFuncImp = None):
    # utiliser les mêmes codes des champs pour les 'UtilCompta.ComposeFuncExp'
    return {"LCL Credit Lyonnais":{
                'champs':['date','montant','mode','libelle','codenat','nature',],
                'fonction':ComposeFuncImp,
                'table':'fournisseurs'},
            "LBP Banque Postale": {
                'champs': ['date','libelle','montant'],
                'fonction': ComposeFuncImp,
                'table': 'fournisseurs'},
            "Crédit Mutuel importé d'internet": {
                'champs': ['Date', None, 'Libelle', '-debit','credit'],
                'champsCB': ['Date','Commerce','Ville', 'montant','Carte'],
                'fonction': ComposeFuncImp,
                'table': 'fournisseurs'},
            "Crédit Mutuel relevé papier": {
                'champs': ['date',None,'operation', 'debit','credit'],
                'champsCB': ['date','commerce','ville', '-MontantEuro','carte'],
                'fonction': ComposeFuncImp,
                'table': 'fournisseurs'}
            }

DIC_OPTIONS = { 'nomFichier': "",
                'isXlsx': False,
                'ixSheet': 0,
                'nomBanque':"",
                'typeCB': True,
                'lstColonnesLues': []}
