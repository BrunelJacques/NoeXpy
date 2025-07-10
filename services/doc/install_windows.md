Installer Noexpy sur Windows
===========================

Pour Windows, vous devez aller sur les sites des auteurs pour 
rechercher et installer les bibliothèques suivantes.
- Python 311 avec pip (http://www.python.org/)
- dans un terminal shell lancez 'pip install -U wxPython'
- git (https://git-scm.com/download/win)

# vérification git pour un user non administrateur qui n'a pas fait l'installation de git
- dans une console commande tester git.exe
- Vérifier dans le path la présence de C:\Program Files\Git et Git.cmd 
- Créer un répertoire NoeXpy dans c:\Program Files (suppose de connaître le mot de passe admin si on ne l'est pas)
- Vérifier l'accès en CONTROLE TOTAL DE TOUS LES UTILISATEURS sur NoeXpy et Git directories

# Cloner les sources via git qui céera le répertoire NoeXpy (shell en utilisateur NoeXpy pour les releases ultèrieures)
- cd c:\Program Files\
- git clone https://github.com/BrunelJacques/NoeXpy 

## Par Windows étendre les droits 'controle total' aux utilisateurs pour dir NoeXpy et git

### dans un terminal shell dans /NoeXpy lancez le chargement des packages (=-lancer en mode administrateur par shell pour release pip)
- cd c:\Program Files\NoeXpy
- pip install -r requirements.txt' # pour - pip install GitHub

# Si le pull est refusé car des modifications locales sont constatées
- git stash
- git reset --hard

# Tester GitHub à partir de répertoire NoeXpy
- git fetch -v origin 

# Créer un raccouri sur le bureau pour Noestock
- cible: "C:\Program Files\Python311\python.exe" Noestock.py" 
- démarrer: "C:\Program Files\NoeXpy\"
- avec image "C:\Program Files\NoeXpy\xpy\Images\Noestock.ico"


# compléments
#! pour créer un lien git sur un répertoire existant, se placer dans le répertoire, puis
- git init
- git add .
- git remote add origin https://github.com/BrunelJacques/NoeXpy
 ( si erreur de saisie refaire - git remote set-url origine https:...)
- git pull origin master --allow-unrelated-histories

# si fatal error: "detected dubious ownership" =>lancer en mode administrateur par shell
- cd "C:\Program File\NoeXpy"
- git config --global --add safe.directory "C:\Program File\NoeXpy"
