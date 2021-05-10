#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania ajout des tables spécifiques
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

# description des tables de l'application
DB_TABLES = {
    "v_clients":[
                ("IDclient", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la famille"),
                ("libelle", "VARCHAR(40)", "libellé de la famille pour les adresses"),
                ("rue", "VARCHAR(255)", "Adresse de la personne"),
                ("cp", "VARCHAR(10)", "Code postal de la personne"),
                ("ville", "VARCHAR(100)", "Ville de la personne"),
                ("fixe", "VARCHAR(50)", "Tel domicile de la personne"),
                ("mobile", "VARCHAR(50)", "Tel mobile perso de la personne"),
                ("mail", "VARCHAR(50)", "Email perso de la personne"),
                ("refus_pub", "INTEGER", "Refus de publicités papier"),
                ("refus_mel", "INTEGER", "Refus de publicités demat"),
                ], #Coordonnées clients, remplacé par une vue dans Noethys

    "modes_reglements":[
                ("IDmode", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID mode de règlement"),
                ("label", "VARCHAR(100)", "Label du mode"),
                ("image", "LONGBLOB", "Image du mode"),
                ("numero_piece", "VARCHAR(10)", "Numéro de pièce (None|ALPHA|NUM)"),
                ("nbre_chiffres", "INTEGER", "Nbre de chiffres du numéro"),
                ("frais_gestion", "VARCHAR(10)", "Frais de gestion None|LIBRE|FIXE|PRORATA"),
                ("frais_montant", "FLOAT", "Montant fixe des frais"),
                ("frais_pourcentage", "FLOAT", "Prorata des frais"),
                ("frais_arrondi", "VARCHAR(20)", "Méthode d'arrondi"),
                ("frais_label", "VARCHAR(200)", "Label de la prestation"),
                ("type_comptable", "VARCHAR(200)", "Type comptable (banque ou caisse)"),
                ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
                        ], # Modes de règlements

    "emetteurs":[
                ("IDemetteur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Emetteur"),
                ("IDmode", "INTEGER", "ID du mode concerné"),
                ("nom", "VARCHAR(200)", "Nom de l'émetteur"),
                ("image", "LONGBLOB", "Image de l'emetteur"),
                ], # Emetteurs bancaires pour les modes de règlements

    "payeurs":[
                ("IDpayeur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Payeur"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur concerné"),
                ("nom", "VARCHAR(100)", "Nom du payeur"),
                ], # Payeurs apparaissant sur les règlements reçus pour un compte payeur-client

    "comptes_bancaires":[
                ("IDcompte", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Compte"),
                ("nom", "VARCHAR(100)", "Intitulé du compte"),
                ("numero", "VARCHAR(50)", "Numéro du compte"),
                ("defaut", "INTEGER", "(0/1) Compte sélectionné par défaut"),
                ("raison", "VARCHAR(400)", "Raison sociale"),
                ("code_etab", "VARCHAR(400)", "Code établissement"),
                ("code_guichet", "VARCHAR(400)", "Code guichet"),
                ("code_nne", "VARCHAR(400)", "Code NNE pour prélèvements auto."),
                ("cle_rib", "VARCHAR(400)", "Clé RIB pour prélèvements auto."),
                ("cle_iban", "VARCHAR(400)", "Clé IBAN pour prélèvements auto."),
                ("iban", "VARCHAR(400)", "Numéro IBAN pour prélèvements auto."),
                ("bic", "VARCHAR(400)", "Numéro BIC pour prélèvements auto."),
                ("code_ics", "VARCHAR(400)", "Code NNE pour prélèvements auto."),
            ], # Comptes bancaires de l'organisateur

    "prestations": [
                ("IDprestation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID prestation"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("date", "DATE", "Date de la prestation"),
                ("categorie", "VARCHAR(50)", "Catégorie de la prestation"),
                ("label", "VARCHAR(200)", "Label de la prestation"),
                ("montant_initial", "FLOAT", "Montant de la prestation AVANT déductions"),
                ("montant", "FLOAT", "Montant de la prestation"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("IDfacture", "INTEGER", "ID de la facture"),
                ("IDfamille", "INTEGER", "ID de la famille concernée"),
                ("IDindividu", "INTEGER", "ID de l'individu concerné"),
                ("forfait", "INTEGER", "Type de forfait : 0 : Aucun | 1 : Suppr possible | 2 : Suppr impossible"),
                ("temps_facture", "DATE", "Temps facturé format 00:00"),
                ("IDcategorie_tarif", "INTEGER", "ID de la catégorie de tarif"),
                ("forfait_date_debut", "DATE", "Date de début de forfait"),
                ("forfait_date_fin", "DATE", "Date de fin de forfait"),
                ("reglement_frais", "INTEGER", "ID du règlement"),
                ("tva", "FLOAT", "Taux TVA"),
                ("code_compta", "VARCHAR(16)", "Code comptable pour export vers logiciels de compta"),
                ("IDcontrat", "INTEGER", "ID du contrat associé"),
                ("compta", "INTEGER", "Pointeur de transfert en compta"),
                ],  # Prestations

    "reglements":[
                ("IDreglement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Règlement"),
                ("IDcompte_payeur", "INTEGER", "ID compte du payeur(client par simplification, Noethys les distingue"),
                ("date", "DATE", "Date d'émission du règlement"),
                ("IDmode", "INTEGER", "ID du mode de règlement"),
                ("IDemetteur", "INTEGER", "ID de l'émetteur du règlement"),
                ("numero_piece", "VARCHAR(30)", "Numéro de pièce"),
                ("montant", "FLOAT", "Montant du règlement"),
                ("IDpayeur", "INTEGER", "ID du payeur"),
                ("observations", "VARCHAR(200)", "Observations"),
                ("numero_quittancier", "VARCHAR(30)", "Numéro de quittancier"),
                ("IDprestation_frais", "INTEGER", "ID de la prestation de frais de gestion"),
                ("IDcompte", "INTEGER", "ID du compte bancaire pour l'encaissement"),
                ("date_differe", "DATE", "Date de l'encaissement différé"),
                ("encaissement_attente", "INTEGER", "(0/1) Encaissement en attente"),
                ("IDdepot", "INTEGER", "ID du dépôt"),
                ("date_saisie", "DATE", "Date de saisie du règlement"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a fait la saisie"),
                ("IDprelevement", "INTEGER", "ID du prélèvement"),
                ("avis_depot", "DATE", "Date de l'envoi de l'avis de dépôt"),
                ("IDpiece", "INTEGER", "IDpiece pour PES V2 ORMC"),
                ("compta", "INTEGER", "Pointeur de transfert en compta"),
                ], # Règlements

    "parametres":[
                ("IDparametre", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID parametre"),
                ("categorie", "VARCHAR(200)", "Catégorie"),
                ("nom", "VARCHAR(200)", "Nom"),
                ("parametre", "MEDIUMTEXT", "Parametre en forme de texte"),
                ], # Paramètres du contexte ou options choisies

    "secteurs":[
                ("IDsecteur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID pays postal"),
                ("nom", "VARCHAR(255)", "Nom du pays postal"),
                                    ], # pays postaux inclus à la suite de la ville (après une fin de ligne)

    "utilisateurs":[
                ("IDutilisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDutilisateur"),
                ("sexe", "VARCHAR(5)", "Sexe de l'utilisateur"),
                ("nom", "VARCHAR(200)", "Nom de l'utilisateur"),
                ("prenom", "VARCHAR(200)", "Prénom de l'utilisateur"),
                ("mdp", "VARCHAR(100)", "Mot de passe"),
                ("profil", "VARCHAR(100)", "Profil (Administrateur ou utilisateur)"),
                ("actif", "INTEGER", "Utilisateur actif"),
                ("image", "VARCHAR(200)", "Images"),
                                    ], # Utilisateurs identifiables

    "sauvegardes_auto":[ ("IDsauvegarde", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDsauvegarde"),
                ("nom", "VARCHAR(455)", "Nom de la procédure de sauvegarde auto"),
                ("observations", "VARCHAR(455)", "Observations"),
                ("date_derniere", "DATE", "Date de la dernière sauvegarde"),
                ("sauvegarde_nom", "VARCHAR(455)", "Sauvegarde Nom"),
                ("sauvegarde_motdepasse", "VARCHAR(455)", "Sauvegarde mot de passe"),
                ("sauvegarde_repertoire", "VARCHAR(455)", "sauvegarde Répertoire"),
                ("sauvegarde_emails", "VARCHAR(455)", "Sauvegarde Emails"),
                ("sauvegarde_fichiers_locaux", "VARCHAR(455)", "Sauvegarde fichiers locaux"),
                ("sauvegarde_fichiers_resea", "VARCHAR(455)", "Sauvegarde fichiers résea"),
                ("condition_jours_scolaires", "VARCHAR(455)", "Condition Jours scolaires"),
                ("condition_jours_vacances", "VARCHAR(455)", "Condition Jours vacances"),
                ("condition_heure", "VARCHAR(455)", "Condition Heure"),
                ("condition_poste", "VARCHAR(455)", "Condition Poste"),
                ("condition_derniere", "VARCHAR(455)", "Condition Date dernière sauvegarde"),
                ("condition_utilisateur", "VARCHAR(455)", "Condition Utilisateur"),
                ("option_afficher_interface", "VARCHAR(455)", "Option Afficher interface (0/1)"),
                ("option_demander", "VARCHAR(455)", "Option Demander (0/1)"),
                ("option_confirmation", "VARCHAR(455)", "Option Confirmation (0/1)"),
                ("option_suppression", "VARCHAR(455)", "Option Suppression sauvegardes obsolètes"),
                                    ], # procédures de sauvegardes automatiques

    "droits":[                   ("IDdroit", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDdroit"),
                ("IDutilisateur", "INTEGER", "IDutilisateur"),
                ("IDmodele", "INTEGER", "IDmodele"),
                ("categorie", "VARCHAR(200)", "Catégorie de droits"),
                ("action", "VARCHAR(200)", "Type d'action"),
                ("etat", "VARCHAR(455)", "Etat"),
                                    ], # Droits des utilisateurs

    "modeles_droits":[     ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmodele"),
                ("nom", "VARCHAR(455)", "Nom du modèle"),
                ("observations", "VARCHAR(455)", "Observations"),
                ("defaut", "INTEGER", "Modèle par défaut (0/1)"),
                                    ], # Modèles de droits

    "cpta_exercices":[("IDexercice", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Exercice"),
                ("nom", "VARCHAR(400)", "Nom de l'exercice"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("defaut", "INTEGER", "Proposé par défaut (0/1)"),
                ("actif", "INTEGER", "Actif pour écritures nouvelles (0/1)"),
                ("cloture", "INTEGER", "Clôturé, l'exercice ne peut plus être actif(0/1)"),
                                    ], # Compta : Exercices

    'cpta_analytiques': [
        ('IDanalytique', 'VARCHAR(8)', "Clé Unique alphanumérique"),
        ('abrege', 'VARCHAR(16)', "cle d'appel ou libelle court du code analytique"),
        ('nom', 'VARCHAR(200)', "Libellé long du code analytique"),
        ('params', 'VARCHAR(400)', "liste texte de paramétrages constructeurs, pour le calcul coût"),
        ('axe', 'VARCHAR(24)', "axe analytique 'VEHICULES' 'CONVOIS' 'PRIXJOUR', defaut = vide")
    ],

    'immobilisations':[
                ('IDimmo','INTEGER PRIMARY KEY AUTOINCREMENT',"Clé Unique"),
                ('compteImmo','VARCHAR(10)',"compte comptable de l'immobilisation"),
                ('IDanalytique','VARCHAR(8)',"Section analytique"),
                ('compteDotation','VARCHAR(10)',"compte comptable de la dotation aux immos"),
                ('libelle','VARCHAR(200)',"texte pour les édition ou choix de ligne "),
                ('nbrePlaces','INTEGER',"capacité d'accueil pour véhicules,tentes, batiment "),
                ('noSerie','VARCHAR(32)',"Immatriculation ou no identifiant"),
                ],# fiches immobilisations

    'immosComposants':[
                ('IDcomposant', 'INTEGER PRIMARY KEY AUTOINCREMENT',"Clé Unique"),
                ('IDimmo', 'INTEGER', "reprise de l'entête immo"),
                ('dteAcquisition','DATE',"date de l'acquisition de l'élément"),
                ('libComposant','VARCHAR(200)',"texte pour les édition en ligne"),
                ('quantite','FLOAT',"quantités fractionnables à la cession"),
                ('valeur','FLOAT',"valeur d'acquisition"),
                ('dteMiseEnService','DATE',"date de mise en service pour début amort"),
                ('compteFrn','VARCHAR(10)',"contrepartie de l'écriture d'acquisition"),
                ('libelleFrn','VARCHAR(200)',"libellé modifiable"),
                ('type','VARCHAR(1)',"Dégressif Linéaire Nonamort"),
                ('tauxAmort','FLOAT',"taux d'amortissement à appliquer chaque année"),
                ('amortAnterieur','FLOAT',"cumul des amortissements à l'ouverture"),
                ('dotation','FLOAT',"dotation de l'exercice"),
                ('etat', 'VARCHAR(5)', "'E'n cours, 'A'mortie, 'C'édée, 'R'ebut,"),
                ('cessionType','VARCHAR(5)',"type de cession (cession partielle crée un nouvel élément)"),
                ('cessionDate','DATE',"date de la cession"),
                ('cessionQte','FLOAT',"qté cédée"),
                ('cessionValeur','FLOAT',"valeur de la cession"),
                ('descriptif','TEXT',"déscriptif libre"),
                ('dtMaj','DATE',"Date de dernière modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# subdivisions des fiches immobilisations
    
    'vehiculesCouts':[
                ('IDcout','INTEGER PRIMARY KEY AUTOINCREMENT',"Clé Unique"),
                ('IDanalytique','VARCHAR(8)',"clé usuelle d'appel, identifie l'composant principal 0 par son libelle"),
                ('cloture','DATE',"Date de clôture de l'exercice"),
                ('prixKmVte','FLOAT',"Prix de base du km facturé avant remise"),
                ('carburants','FLOAT',"Coût des carburants pour l'exercice"),
                ('entretien','FLOAT',"Coût de l'entretien (charges variables selon km)"),
                ('servicesFixes','FLOAT',"Autres coûts fixes à l'année"),
                ('dotation','FLOAT',"Dotation aux amortissments"),
                ('grossesRep','FLOAT',"Grosses réparations immobilisées (détaillées dans la fiche immo)"),
                ('plusValue','FLOAT',"Résultat du calcul sur la cession dans fiche immo"),
                ('kmDebut','INTEGER',"Kilométrage en début d'exercice"),
                ('kmFin','INTEGER',"Kilométrage en fin d'exercice"),
                ('dtMaj','DATE',"Date de dernière modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# Eléments de coûts annuels
    
    'vehiculesConsos':[
                ('IDconso','INTEGER PRIMARY KEY AUTOINCREMENT',"Clé Unique"),
                ('IDanalytique','VARCHAR(8)',"Id du véhicule"),
                ('cloture','DATE',"Date de clôture de l'exercice"),
                ('typeTiers','VARCHAR(1)',"'C'lient, 'A'analytique,'P'partenaires,'E'mployés"),
                ('IDtiers','VARCHAR(8)',"Section analytique consommatrice ou no client"),
                ('dteKmDeb','DATE',"Date du relevé km début"),
                ('kmDeb','INTEGER',"kilométrage de départ"),
                ('dteKmFin','DATE',"Date du relevé km fin"),
                ('kmFin','INTEGER',"kilométrage de fin"),
                ('observation','VARCHAR(80)', "Décrit les cas particuliers"),
                ('dtFact','DATE',"Date de facturation"),
                ('compta','DATE',"Date de transert en compta"),
                ('dtMaj','DATE',"Date de dernière modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# affectation des consommations internes par section

    'stArticles':[
                ('IDarticle', 'VARCHAR(32)', "PK Désignation du produit"),
                ('rations', 'FLOAT', "Nombre de ration pour une unité"),
                ('fournisseur', 'VARCHAR(32)', "Fournisseur habituel"),
                ('txTva', 'FLOAT', "tx de TVA en %"),
                ('magasin', 'VARCHAR(32)', "Lieu de stockage: réserve, congel,frigo"),
                ('rayon', 'VARCHAR(32)', "rayon ou famille produit: type de produit dans le magasin"),
                ('qteStock', 'INTEGER', "Stock en live"),
                ('qteMini', 'INTEGER', "Seuil déclenchant une alerte rouge"),
                ('qteSaison', 'INTEGER', "Seuil souhaitable en haute saison"),
                ('prixMoyen', 'FLOAT', "Prix unitaire moyen historique du stock"),
                ('prixActuel', 'FLOAT', "Dernier prix TTC unitaire livré ou de réappro"),
                ('dernierAchat', 'DATE', "Date de dernière entrée avec prix saisi"),],# stocks: articles en stock

    'stEffectifs':[
                ('IDdate', 'DATE', "PK Date de la situation de l'effectif"),
                ('IDanalytique', 'VARCHAR(8)', "PK Section analytique du camp à facturer, null pour Cuisine"),
                ('midiClients', 'INTEGER', "Nbre de repas midi clients facturés "),
                ('midiRepas', 'INTEGER', "Nbre de repas midi pour le staff et les clients"),
                ('soirClients', 'INTEGER', "Nbre de repas aux clients présents le soir "),
                ('soirRepas', 'INTEGER', "Nbre de repas pour le staff et les clients le soir"),
                ('prevuClients', 'INTEGER', "Nbre d'inscrits payants "),
                ('prevuRepas', 'INTEGER', "Nbre d'inscrits staff inclus"),
                ('modifiable', 'TINYINT', "0/1 Marque un transfert export  réussi ou import"),],# stocks: repas servis

    'stMouvements':[
                ('IDmouvement', 'INTEGER PRIMARY KEY AUTOINCREMENT', "Clé primaire"),
                ('date', 'DATE', "date du mouvement de stock"),
                ('fournisseur', 'VARCHAR(32)', "Fournisseur de l'entrée"),
                ('origine', 'VARCHAR(8)', "achat; retour; od_in; repas; camp; od_out"),
                ('IDarticle', 'VARCHAR(32)', "clé dans gstArticles"),
                ('qte', 'INTEGER', "Quantitée mouvementée signée"),
                ('prixUnit', 'FLOAT', "Prix moyen pour sorties et retour, Prix revient pour achats"),
                ('IDanalytique', 'VARCHAR(8)', "Section analytique du camp à facturer"),
                ('ordi', 'VARCHAR(16)', "Nom de l'ordi utilisé pour l'entrée ou la modif"),
                ('dateSaisie', 'DATE', "Date de l'entrée ou la modif"),
                ('modifiable', 'INTEGER', "0/1 Marque un transfert export  réussi ou import"),],# stocks: entrées sorties

    'stInventaires':[
                ('IDdate', 'DATE', "PK Date de l'inventaire copie des stocks"),
                ('IDarticle', 'VARCHAR(32)', "PK Désignation du produit"),
                ('qteStock', 'INTEGER', "Qté reportée"),
                ('qteConstat', 'INTEGER', "Qté constatée"),
                ('prixActuel', 'FLOAT', "Dernier prix unitaire livré ou de réappro"),
                ('prixMoyen', 'FLOAT', "Prix unitaire moyen historique du stock"),
                ('modifiable', 'INTEGER', "0/1 Marque un transfert export  réussi ou import"),], # stocks: inventaire à une date
    }

# index clé unique
DB_PK = {
        'PK_vehiculesCouts_IDanalytique_cloture': {'table': 'vehiculesCouts', 'champ': 'IDanalytique, cloture'},
        'PK_stArticles_IDarticle': {'table': 'stArticles', 'champ': 'IDarticle'},
        'PK_stEffectifs_date_IDanalytique': {'table': 'stEffectifs', 'champ': 'IDdate,IDanalytique'},
        'PK_stInventaires_date_IDarticle': {'table': 'stInventaires', 'champ': 'IDdate,IDarticle'},
        }

# index sans contrainte
DB_IX = {
        'index_reglements_IDcompte_payeur': {'table': 'reglements', 'champ': 'IDcompte_payeur'},#index de Noethys
        'IX_immobilisations_compteImmo_IDanalytique': {'table': 'immobilisations', 'champ': 'compteImmo,IDanalytique'},
        'IX_immosComposants_IDimmo': {'table': 'immosComposants', 'champ': 'IDimmo'},
        'IX_vehiculesConsos_IDanalytique_cloture': {'table': 'vehiculesConsos',
                                                    'champ': 'IDanalytique, cloture, typeTiers, IDtiers'},
        'IX_stArticles_fournisseur': {'table': 'stArticles', 'champ': 'fournisseur'},
        'IX_stArticles_magasin_rayon': {'table': 'stArticles', 'champ': 'magasin,rayon'},
        'IX_stMouvements_date_origine': {'table': 'stMouvements', 'champ': 'date,origine'},
        'IX_stMouvements_IDanalytique_date': {'table': 'stMouvements', 'champ': 'IDanalytique,date'}
        }

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    """ Affichage de stats sur les tables """
    nbreChamps = 0
    for nomTable, lstChamps in DB_TABLES.items() :
        nbreChamps += len(lstChamps)
    print("Nbre de champs DATA =", nbreChamps)
    print("Nbre de tables DATA =", len(DB_TABLES.keys()))