#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania ajout des tables sp�cifiques
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

# description des tables de l'application
DB_TABLES = {
    "v_clients":[
                ("IDclient", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la famille"),
                ("libelle", "VARCHAR(40)", "libell� de la famille pour les adresses"),
                ("rue", "VARCHAR(255)", "Adresse de la personne"),
                ("cp", "VARCHAR(10)", "Code postal de la personne"),
                ("ville", "VARCHAR(100)", "Ville de la personne"),
                ("fixe", "VARCHAR(50)", "Tel domicile de la personne"),
                ("mobile", "VARCHAR(50)", "Tel mobile perso de la personne"),
                ("mail", "VARCHAR(50)", "Email perso de la personne"),
                ("refus_pub", "INTEGER", "Refus de publicit�s papier"),
                ("refus_mel", "INTEGER", "Refus de publicit�s demat"),
                ], #Coordonn�es clients, remplac� par une vue dans Noethys

    "modes_reglements":[
                ("IDmode", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID mode de r�glement"),
                ("label", "VARCHAR(100)", "Label du mode"),
                ("image", "LONGBLOB", "Image du mode"),
                ("numero_piece", "VARCHAR(10)", "Num�ro de pi�ce (None|ALPHA|NUM)"),
                ("nbre_chiffres", "INTEGER", "Nbre de chiffres du num�ro"),
                ("frais_gestion", "VARCHAR(10)", "Frais de gestion None|LIBRE|FIXE|PRORATA"),
                ("frais_montant", "FLOAT", "Montant fixe des frais"),
                ("frais_pourcentage", "FLOAT", "Prorata des frais"),
                ("frais_arrondi", "VARCHAR(20)", "M�thode d'arrondi"),
                ("frais_label", "VARCHAR(200)", "Label de la prestation"),
                ("type_comptable", "VARCHAR(200)", "Type comptable (banque ou caisse)"),
                ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
                        ], # Modes de r�glements

    "emetteurs":[
                ("IDemetteur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Emetteur"),
                ("IDmode", "INTEGER", "ID du mode concern�"),
                ("nom", "VARCHAR(200)", "Nom de l'�metteur"),
                ("image", "LONGBLOB", "Image de l'emetteur"),
                ], # Emetteurs bancaires pour les modes de r�glements

    "payeurs":[
                ("IDpayeur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Payeur"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur concern�"),
                ("nom", "VARCHAR(100)", "Nom du payeur"),
                ], # Payeurs apparaissant sur les r�glements re�us pour un compte payeur-client

    "comptes_bancaires":[
                ("IDcompte", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Compte"),
                ("nom", "VARCHAR(100)", "Intitul� du compte"),
                ("numero", "VARCHAR(50)", "Num�ro du compte"),
                ("defaut", "INTEGER", "(0/1) Compte s�lectionn� par d�faut"),
                ("raison", "VARCHAR(400)", "Raison sociale"),
                ("code_etab", "VARCHAR(400)", "Code �tablissement"),
                ("code_guichet", "VARCHAR(400)", "Code guichet"),
                ("code_nne", "VARCHAR(400)", "Code NNE pour pr�l�vements auto."),
                ("cle_rib", "VARCHAR(400)", "Cl� RIB pour pr�l�vements auto."),
                ("cle_iban", "VARCHAR(400)", "Cl� IBAN pour pr�l�vements auto."),
                ("iban", "VARCHAR(400)", "Num�ro IBAN pour pr�l�vements auto."),
                ("bic", "VARCHAR(400)", "Num�ro BIC pour pr�l�vements auto."),
                ("code_ics", "VARCHAR(400)", "Code NNE pour pr�l�vements auto."),
            ], # Comptes bancaires de l'organisateur

    "prestations": [
                ("IDprestation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID prestation"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("date", "DATE", "Date de la prestation"),
                ("categorie", "VARCHAR(50)", "Cat�gorie de la prestation"),
                ("label", "VARCHAR(200)", "Label de la prestation"),
                ("montant_initial", "FLOAT", "Montant de la prestation AVANT d�ductions"),
                ("montant", "FLOAT", "Montant de la prestation"),
                ("IDactivite", "INTEGER", "ID de l'activit�"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("IDfacture", "INTEGER", "ID de la facture"),
                ("IDfamille", "INTEGER", "ID de la famille concern�e"),
                ("IDindivid", "INTEGER", "ID de l'individu concern�"),
                ("forfait", "INTEGER", "Type de forfait : 0 : Aucun | 1 : Suppr possible | 2 : Suppr impossible"),
                ("temps_facture", "DATE", "Temps factur� format 00:00"),
                ("IDcategorie_tarif", "INTEGER", "ID de la cat�gorie de tarif"),
                ("forfait_date_debut", "DATE", "Date de d�but de forfait"),
                ("forfait_date_fin", "DATE", "Date de fin de forfait"),
                ("reglement_frais", "INTEGER", "ID du r�glement"),
                ("tva", "FLOAT", "Taux TVA"),
                ("code_compta", "VARCHAR(16)", "Code comptable pour export vers logiciels de compta"),
                ("IDcontrat", "INTEGER", "ID du contrat associ�"),
                ("compta", "INTEGER", "Pointeur de transfert en compta"),
                ],  # Prestations

    "reglements":[
                ("IDreglement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID R�glement"),
                ("IDcompte_payeur", "INTEGER", "ID compte du payeur(client par simplification, Noethys les distingue"),
                ("date", "DATE", "Date d'�mission du r�glement"),
                ("IDmode", "INTEGER", "ID du mode de r�glement"),
                ("IDemetteur", "INTEGER", "ID de l'�metteur du r�glement"),
                ("numero_piece", "VARCHAR(30)", "Num�ro de pi�ce"),
                ("montant", "FLOAT", "Montant du r�glement"),
                ("IDpayeur", "INTEGER", "ID du payeur"),
                ("observations", "VARCHAR(200)", "Observations"),
                ("numero_quittancier", "VARCHAR(30)", "Num�ro de quittancier"),
                ("IDprestation_frais", "INTEGER", "ID de la prestation de frais de gestion"),
                ("IDcompte", "INTEGER", "ID du compte bancaire pour l'encaissement"),
                ("date_differe", "DATE", "Date de l'encaissement diff�r�"),
                ("encaissement_attente", "INTEGER", "(0/1) Encaissement en attente"),
                ("IDdepot", "INTEGER", "ID du d�p�t"),
                ("date_saisie", "DATE", "Date de saisie du r�glement"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a fait la saisie"),
                ("IDprelevement", "INTEGER", "ID du pr�l�vement"),
                ("avis_depot", "DATE", "Date de l'envoi de l'avis de d�p�t"),
                ("IDpiece", "INTEGER", "IDpiece pour PES V2 ORMC"),
                ("compta", "INTEGER", "Pointeur de transfert en compta"),
                ], # R�glements

    "parametres":[
                ("IDparametre", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID parametre"),
                ("categorie", "VARCHAR(200)", "Cat�gorie"),
                ("nom", "VARCHAR(200)", "Nom"),
                ("parametre", "VARCHAR(30000)", "Parametre"),
                ], # Param�tres du contexte ou options choisies

    "secteurs":[
                ("IDsecteur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID pays postal"),
                ("nom", "VARCHAR(255)", "Nom du pays postal"),
                                    ], # pays postaux inclus � la suite de la ville (apr�s une fin de ligne)

    "utilisateurs":[
                ("IDutilisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDutilisateur"),
                ("sexe", "VARCHAR(5)", "Sexe de l'utilisateur"),
                ("nom", "VARCHAR(200)", "Nom de l'utilisateur"),
                ("prenom", "VARCHAR(200)", "Pr�nom de l'utilisateur"),
                ("mdp", "VARCHAR(100)", "Mot de passe"),
                ("profil", "VARCHAR(100)", "Profil (Administrateur ou utilisateur)"),
                ("actif", "INTEGER", "Utilisateur actif"),
                ("image", "VARCHAR(200)", "Images"),
                                    ], # Utilisateurs identifiables

    "sauvegardes_auto":[ ("IDsauvegarde", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDsauvegarde"),
                ("nom", "VARCHAR(455)", "Nom de la proc�dure de sauvegarde auto"),
                ("observations", "VARCHAR(455)", "Observations"),
                ("date_derniere", "DATE", "Date de la derni�re sauvegarde"),
                ("sauvegarde_nom", "VARCHAR(455)", "Sauvegarde Nom"),
                ("sauvegarde_motdepasse", "VARCHAR(455)", "Sauvegarde mot de passe"),
                ("sauvegarde_repertoire", "VARCHAR(455)", "sauvegarde R�pertoire"),
                ("sauvegarde_emails", "VARCHAR(455)", "Sauvegarde Emails"),
                ("sauvegarde_fichiers_locaux", "VARCHAR(455)", "Sauvegarde fichiers locaux"),
                ("sauvegarde_fichiers_resea", "VARCHAR(455)", "Sauvegarde fichiers r�sea"),
                ("condition_jours_scolaires", "VARCHAR(455)", "Condition Jours scolaires"),
                ("condition_jours_vacances", "VARCHAR(455)", "Condition Jours vacances"),
                ("condition_heure", "VARCHAR(455)", "Condition Heure"),
                ("condition_poste", "VARCHAR(455)", "Condition Poste"),
                ("condition_derniere", "VARCHAR(455)", "Condition Date derni�re sauvegarde"),
                ("condition_utilisateur", "VARCHAR(455)", "Condition Utilisateur"),
                ("option_afficher_interface", "VARCHAR(455)", "Option Afficher interface (0/1)"),
                ("option_demander", "VARCHAR(455)", "Option Demander (0/1)"),
                ("option_confirmation", "VARCHAR(455)", "Option Confirmation (0/1)"),
                ("option_suppression", "VARCHAR(455)", "Option Suppression sauvegardes obsol�tes"),
                                    ], # proc�dures de sauvegardes automatiques

    "droits":[                   ("IDdroit", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDdroit"),
                ("IDutilisateur", "INTEGER", "IDutilisateur"),
                ("IDmodele", "INTEGER", "IDmodele"),
                ("categorie", "VARCHAR(200)", "Cat�gorie de droits"),
                ("action", "VARCHAR(200)", "Type d'action"),
                ("etat", "VARCHAR(455)", "Etat"),
                                    ], # Droits des utilisateurs

    "modeles_droits":[     ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmodele"),
                ("nom", "VARCHAR(455)", "Nom du mod�le"),
                ("observations", "VARCHAR(455)", "Observations"),
                ("defaut", "INTEGER", "Mod�le par d�faut (0/1)"),
                                    ], # Mod�les de droits

    "cpta_exercices":[("IDexercice", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Exercice"),
                ("nom", "VARCHAR(400)", "Nom de l'exercice"),
                ("date_debut", "DATE", "Date de d�but"),
                ("date_fin", "DATE", "Date de fin"),
                ("defaut", "INTEGER", "Propos� par d�faut (0/1)"),
                ("actif", "INTEGER", "Actif pour �critures nouvelles (0/1)"),
                ("cloture", "INTEGER", "Cl�tur�, l'exercice ne peut plus �tre actif(0/1)"),
                                    ], # Compta : Exercices

    'cpta_analytiques': [
        ('IDanalytique', 'VARCHAR(8)', "Cl� Unique alphanum�rique"),
        ('abrege', 'VARCHAR(16)', "cle d'appel ou libelle court du code analytique"),
        ('nom', 'VARCHAR(200)', "Libell� long du code analytique"),
        ('params', 'VARCHAR(400)', "liste texte de param�trages constructeurs, pour le calcul co�t"),
        ('axe', 'VARCHAR(24)', "axe analytique 'VEHICULES' 'CONVOIS' 'PRIXJOUR', defaut = vide")
    ],

    'immobilisations':[
                ('IDimmo','INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('compteImmo','VARCHAR(10)',"compte comptable de l'immobilisation"),
                ('IDanalytique','VARCHAR(8)',"Section analytique"),
                ('compteDotation','VARCHAR(10)',"compte comptable de la dotation aux immos"),
                ('libelle','VARCHAR(200)',"texte pour les �dition ou choix de ligne "),
                ('nbrePlaces','INTEGER',"capacit� d'accueil pour v�hicules,tentes, batiment "),
                ('noSerie','VARCHAR(32)',"Immatriculation ou no identifiant"),
                ],# fiches immobilisations

    'immosComposants':[
                ('IDcomposant', 'INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('IDimmo', 'INTEGER', "reprise de l'ent�te immo"),
                ('dteAcquisition','DATE',"date de l'acquisition de l'�l�ment"),
                ('libComposant','VARCHAR(200)',"texte pour les �dition en ligne"),
                ('quantite','FLOAT',"quantit�s fractionnables � la cession"),
                ('valeur','FLOAT',"valeur d'acquisition"),
                ('dteMiseEnService','DATE',"date de mise en service pour d�but amort"),
                ('compteFrn','VARCHAR(10)',"contrepartie de l'�criture d'acquisition"),
                ('libelleFrn','VARCHAR(200)',"libell� modifiable"),
                ('type','VARCHAR(1)',"D�gressif Lin�aire Nonamort"),
                ('tauxAmort','FLOAT',"taux d'amortissement � appliquer chaque ann�e"),
                ('amortAnterieur','FLOAT',"cumul des amortissements � l'ouverture"),
                ('dotation','FLOAT',"dotation de l'exercice"),
                ('etat', 'VARCHAR(5)', "'E'n cours, 'A'mortie, 'C'�d�e, 'R'ebut,"),
                ('cessionType','VARCHAR(5)',"type de cession (cession partielle cr�e un nouvel �l�ment)"),
                ('cessionDate','DATE',"date de la cession"),
                ('cessionQte','FLOAT',"qt� c�d�e"),
                ('cessionValeur','FLOAT',"valeur de la cession"),
                ('descriptif','TEXT',"d�scriptif libre"),
                ('dtMaj','DATE',"Date de derni�re modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# subdivisions des fiches immobilisations
    
    'vehiculesCouts':[
                ('IDcout','INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('IDanalytique','VARCHAR(8)',"cl� usuelle d'appel, identifie l'composant principal 0 par son libelle"),
                ('cloture','DATE',"Date de cl�ture de l'exercice"),
                ('prixKmVte','FLOAT',"Prix de base du km factur� avant remise"),
                ('carburants','FLOAT',"Co�t des carburants pour l'exercice"),
                ('entretien','FLOAT',"Co�t de l'entretien (charges variables selon km)"),
                ('servicesFixes','FLOAT',"Autres co�ts fixes � l'ann�e"),
                ('dotation','FLOAT',"Dotation aux amortissments"),
                ('grossesRep','FLOAT',"Grosses r�parations immobilis�es (d�taill�es dans la fiche immo)"),
                ('plusValue','FLOAT',"R�sultat du calcul sur la cession dans fiche immo"),
                ('kmDebut','INTEGER',"Kilom�trage en d�but d'exercice"),
                ('kmFin','INTEGER',"Kilom�trage en fin d'exercice"),
                ('dtMaj','DATE',"Date de derni�re modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# El�ments de co�ts annuels
    
    'vehiculesConsos':[
                ('IDconso','INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('IDanalytique','VARCHAR(8)',"Id du v�hicule"),
                ('cloture','DATE',"Date de cl�ture de l'exercice"),
                ('typeTiers','VARCHAR(1)',"'C'lient, 'A'analytique,'P'partenaires,'E'mploy�s"),
                ('IDtiers','VARCHAR(8)',"Section analytique consommatrice ou no client"),
                ('dteKmDeb','DATE',"Date du relev� km d�but"),
                ('kmDeb','INTEGER',"kilom�trage de d�part"),
                ('dteKmFin','DATE',"Date du relev� km fin"),
                ('kmFin','INTEGER',"kilom�trage de fin"),
                ('observation','VARCHAR(80)', "D�crit les cas particuliers"),
                ('dtFact','DATE',"Date de facturation"),
                ('compta','DATE',"Date de transert en compta"),
                ('dtMaj','DATE',"Date de derni�re modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# affectation des consommations internes par section
    }

# index cl� unique
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