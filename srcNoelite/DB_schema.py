#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
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
                ("IDclient", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID de la famille"),
                ("libelle", "VARCHAR(40)", u"libellé de la famille pour les adresses"),
                ("rue", "VARCHAR(255)", u"Adresse de la personne"),
                ("cp", "VARCHAR(10)", u"Code postal de la personne"),
                ("ville", "VARCHAR(100)", u"Ville de la personne"),
                ("fixe", "VARCHAR(50)", u"Tel domicile de la personne"),
                ("mobile", "VARCHAR(50)", u"Tel mobile perso de la personne"),
                ("mail", "VARCHAR(50)", u"Email perso de la personne"),
                ("refus_pub", "INTEGER", u"Refus de publicités papier"),
                ("refus_mel", "INTEGER", u"Refus de publicités demat"),
                ], #Coordonnées clients, remplacé par une vue dans Noethys

    "modes_reglements":[
                ("IDmode", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID mode de règlement"),
                ("label", "VARCHAR(100)", u"Label du mode"),
                ("image", "LONGBLOB", u"Image du mode"),
                ("numero_piece", "VARCHAR(10)", u"Numéro de pièce (None|ALPHA|NUM)"),
                ("nbre_chiffres", "INTEGER", u"Nbre de chiffres du numéro"),
                ("frais_gestion", "VARCHAR(10)", u"Frais de gestion None|LIBRE|FIXE|PRORATA"),
                ("frais_montant", "FLOAT", u"Montant fixe des frais"),
                ("frais_pourcentage", "FLOAT", u"Prorata des frais"),
                ("frais_arrondi", "VARCHAR(20)", u"Méthode d'arrondi"),
                ("frais_label", "VARCHAR(200)", u"Label de la prestation"),
                ("type_comptable", "VARCHAR(200)", u"Type comptable (banque ou caisse)"),
                ("code_compta", "VARCHAR(200)", u"Code comptable pour export vers logiciels de compta"),
                        ], # Modes de règlements

    "emetteurs":[
                ("IDemetteur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Emetteur"),
                ("IDmode", "INTEGER", u"ID du mode concerné"),
                ("nom", "VARCHAR(200)", u"Nom de l'émetteur"),
                ("image", "LONGBLOB", u"Image de l'emetteur"),
                ], # Emetteurs bancaires pour les modes de règlements

    "payeurs":[
                ("IDpayeur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Payeur"),
                ("IDcompte_payeur", "INTEGER", u"ID du compte payeur concerné"),
                ("nom", "VARCHAR(100)", u"Nom du payeur"),
                ], # Payeurs apparaissant sur les règlements reçus pour un compte payeur-client

    "comptes_bancaires":[
                ("IDcompte", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Compte"),
                ("nom", "VARCHAR(100)", u"Intitulé du compte"),
                ("numero", "VARCHAR(50)", u"Numéro du compte"),
                ("defaut", "INTEGER", u"(0/1) Compte sélectionné par défaut"),
                ("raison", "VARCHAR(400)", u"Raison sociale"),
                ("code_etab", "VARCHAR(400)", u"Code établissement"),
                ("code_guichet", "VARCHAR(400)", u"Code guichet"),
                ("code_nne", "VARCHAR(400)", u"Code NNE pour prélèvements auto."),
                ("cle_rib", "VARCHAR(400)", u"Clé RIB pour prélèvements auto."),
                ("cle_iban", "VARCHAR(400)", u"Clé IBAN pour prélèvements auto."),
                ("iban", "VARCHAR(400)", u"Numéro IBAN pour prélèvements auto."),
                ("bic", "VARCHAR(400)", u"Numéro BIC pour prélèvements auto."),
                ("code_ics", "VARCHAR(400)", u"Code NNE pour prélèvements auto."),
            ], # Comptes bancaires de l'organisateur
                                    
    "reglements":[
                ("IDreglement", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Règlement"),
                ("IDcompte_payeur", "INTEGER", u"ID compte du payeur(client par simplification, Noethys les distingue"),
                ("date", "DATE", u"Date d'émission du règlement"),
                ("IDmode", "INTEGER", u"ID du mode de règlement"),
                ("IDemetteur", "INTEGER", u"ID de l'émetteur du règlement"),
                ("numero_piece", "VARCHAR(30)", u"Numéro de pièce"),
                ("montant", "FLOAT", u"Montant du règlement"),
                ("IDpayeur", "INTEGER", u"ID du payeur"),
                ("observations", "VARCHAR(200)", u"Observations"),
                ("numero_quittancier", "VARCHAR(30)", u"Numéro de quittancier"),
                ("IDprestation_frais", "INTEGER", u"ID de la prestation de frais de gestion"),
                ("IDcompte", "INTEGER", u"ID du compte bancaire pour l'encaissement"),
                ("date_differe", "DATE", u"Date de l'encaissement différé"),
                ("encaissement_attente", "INTEGER", u"(0/1) Encaissement en attente"),
                ("IDdepot", "INTEGER", u"ID du dépôt"),
                ("date_saisie", "DATE", u"Date de saisie du règlement"),
                ("IDutilisateur", "INTEGER", u"Utilisateur qui a fait la saisie"),
                ("IDprelevement", "INTEGER", u"ID du prélèvement"),
                ("avis_depot", "DATE", u"Date de l'envoi de l'avis de dépôt"),
                ("IDpiece", "INTEGER", u"IDpiece pour PES V2 ORMC"),
                ("compta", "INTEGER", u"Pointeur de transfert en compta"),
                ], # Règlements

    "parametres":[
                ("IDparametre", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID parametre"),
                ("categorie", "VARCHAR(200)", u"Catégorie"),
                ("nom", "VARCHAR(200)", u"Nom"),
                ("parametre", "VARCHAR(30000)", u"Parametre"),
                ], # Paramètres du contexte ou options choisies

    "secteurs":[
                ("IDsecteur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID pays postal"),
                ("nom", "VARCHAR(255)", u"Nom du pays postal"),
                                    ], # pays postaux inclus à la suite de la ville (après une fin de ligne)

    "utilisateurs":[
                ("IDutilisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDutilisateur"),
                ("sexe", "VARCHAR(5)", u"Sexe de l'utilisateur"),
                ("nom", "VARCHAR(200)", u"Nom de l'utilisateur"),
                ("prenom", "VARCHAR(200)", u"Prénom de l'utilisateur"),
                ("mdp", "VARCHAR(100)", u"Mot de passe"),
                ("profil", "VARCHAR(100)", u"Profil (Administrateur ou utilisateur)"),
                ("actif", "INTEGER", u"Utilisateur actif"),
                ("image", "VARCHAR(200)", u"Images"),
                                    ], # Utilisateurs identifiables

    "sauvegardes_auto":[ ("IDsauvegarde", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDsauvegarde"),
                ("nom", "VARCHAR(455)", u"Nom de la procédure de sauvegarde auto"),
                ("observations", "VARCHAR(455)", u"Observations"),
                ("date_derniere", "DATE", u"Date de la dernière sauvegarde"),
                ("sauvegarde_nom", "VARCHAR(455)", u"Sauvegarde Nom"),
                ("sauvegarde_motdepasse", "VARCHAR(455)", u"Sauvegarde mot de passe"),
                ("sauvegarde_repertoire", "VARCHAR(455)", u"sauvegarde Répertoire"),
                ("sauvegarde_emails", "VARCHAR(455)", u"Sauvegarde Emails"),
                ("sauvegarde_fichiers_locaux", "VARCHAR(455)", u"Sauvegarde fichiers locaux"),
                ("sauvegarde_fichiers_reseau", "VARCHAR(455)", u"Sauvegarde fichiers réseau"),
                ("condition_jours_scolaires", "VARCHAR(455)", u"Condition Jours scolaires"),
                ("condition_jours_vacances", "VARCHAR(455)", u"Condition Jours vacances"),
                ("condition_heure", "VARCHAR(455)", u"Condition Heure"),
                ("condition_poste", "VARCHAR(455)", u"Condition Poste"),
                ("condition_derniere", "VARCHAR(455)", u"Condition Date dernière sauvegarde"),
                ("condition_utilisateur", "VARCHAR(455)", u"Condition Utilisateur"),
                ("option_afficher_interface", "VARCHAR(455)", u"Option Afficher interface (0/1)"),
                ("option_demander", "VARCHAR(455)", u"Option Demander (0/1)"),
                ("option_confirmation", "VARCHAR(455)", u"Option Confirmation (0/1)"),
                ("option_suppression", "VARCHAR(455)", u"Option Suppression sauvegardes obsolètes"),
                                    ], # procédures de sauvegardes automatiques

    "droits":[                   ("IDdroit", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDdroit"),
                ("IDutilisateur", "INTEGER", u"IDutilisateur"),
                ("IDmodele", "INTEGER", u"IDmodele"),
                ("categorie", "VARCHAR(200)", u"Catégorie de droits"),
                ("action", "VARCHAR(200)", u"Type d'action"),
                ("etat", "VARCHAR(455)", u"Etat"),
                                    ], # Droits des utilisateurs

    "modeles_droits":[     ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDmodele"),
                ("nom", "VARCHAR(455)", u"Nom du modèle"),
                ("observations", "VARCHAR(455)", u"Observations"),
                ("defaut", "INTEGER", u"Modèle par défaut (0/1)"),
                                    ], # Modèles de droits

    "cpta_exercices":[("IDexercice", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Exercice"),
                ("nom", "VARCHAR(400)", u"Nom de l'exercice"),
                ("date_debut", "DATE", u"Date de début"),
                ("date_fin", "DATE", u"Date de fin"),
                ("defaut", "INTEGER", u"Proposé par défaut (0/1)"),
                ("actif", "INTEGER", u"Actif pour écritures nouvelles (0/1)"),
                ("cloture", "INTEGER", u"Clôturé, l'exercice ne peut plus être actif(0/1)"),
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
    }

# index clé unique
DB_PK = {
        "PK_vehiculesCouts_IDanalytique_cloture": {"table": "vehiculesCouts", "champ": "IDanalytique, cloture"},}

# index sans contrainte
DB_IX = {
        "index_reglements_IDcompte_payeur": {"table": "reglements", "champ": "IDcompte_payeur"},#index de Noethys
        "IX_immobilisations_compteImmo_IDanalytique": {"table": "immobilisations", "champ": "compteImmo,IDanalytique"},
        "IX_immosComposants_IDimmo": {"table": "immosComposants", "champ": "IDimmo"},
        "IX_vehiculesConsos_IDanalytique_cloture": {"table": "vehiculesConsos",
                                                    "champ": "IDanalytique, cloture, typeTiers, IDtiers"},}

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    """ Affichage de stats sur les tables """
    nbreChamps = 0
    for nomTable, lstChamps in DB_TABLES.items() :
        nbreChamps += len(lstChamps)
    print("Nbre de champs DATA =", nbreChamps)
    print("Nbre de tables DATA =", len(DB_TABLES.keys()))