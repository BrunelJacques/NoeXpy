#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------- Variables globales à appeler

# Trame des formats d'imports pour transpose
def GetFormatsImport(ComposeFuncImp = None):
    # utiliser les mêmes codes des champs pour les 'UtilCompta.ComposeFuncExp'
    return {"LCL Credit Lyonnais":{
                            'champs':['date','montant','mode',None,'libelle',None,None,
                                              'codenat','nature',],
                            'lignesentete':0,
                            'fonction':ComposeFuncImp,
                            'table':'fournisseurs'},
                      "LBP Banque Postale": {
                          'champs': ['date','libelle','montant'],
                          'fonction': ComposeFuncImp,
                          'table': 'fournisseurs'},
                      "Crédit Mutuel importé d'internet": {
                          'champs': ['date', None, 'libelle', '-debit','credit'],
                          'champsCB':['date','libelle','montant'],
                          'fonction': ComposeFuncImp,
                          'table': 'fournisseurs'},
                      "Crédit Mutuel relevé papier": {
                          'champs': ['date',None,'operation', 'debit','credit'],
                          'champsCB': ['date','commerce','ville', 'montant'],
                          'fonction': ComposeFuncImp,
                          'table': 'fournisseurs'}
                      }

DIC_OPTIONS = { 'nomFichier': "",
                'isXlsx': False,
                'ixSheet': 0,
                'nomBanque':"",
                'typeCB': True,
                'lstColonnesLues': []}
