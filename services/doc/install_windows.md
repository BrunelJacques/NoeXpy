Installer Noexpy sur Windows
===========================

Pour Windows, vous devez aller sur les sites des auteurs pour 
rechercher et installer les bibliothèques suivantes.
- Python 3+ avec pip (http://www.python.org/)
- wxPython 3+ - version unicode (http://www.wxpython.org/)
- git (https://git-scm.com/download/win)

# vérification git pour un user non administrateur qui n'a pas fait l'installation de git
- dans une console commande tester git.exe
- Vérifier dans le path la présence de C:\Program Files\Git et Git.cmd 
- Vérifier l'accès en controle totale de tous les utilisateurs sur NoeXpy et Git directories

# Cloner les sources via git qui céera le répertoire NoeXpy (shell en mode administrateur)
> git clone https://github.com/BrunelJacques/NoeXpy 

## Par Windows étendre les droits 'controle total' aux utilisateurs pour dir NoeXpy

### dans un terminal shell dans /NoeXpy lancez le chargement des packages
> pip install -r requirements.txt' # pour > pip install GitHub

#! pour créer un lien git sur un répertoire existant, se placer dans le répertoire, puis
> git init
> git add .
> git remote add origin https://github.com/BrunelJacques/NoeXpy
( si erreur de saisie refaire > git remote set-url origine https:...)
> git pull origin master --allow-unrelated-histories

# Si le pull est refusé car des modifications locales sont constatées
> git stash
> git reset --hard

# Tester GitHub à partir de répertoire NoeXpy
> git fetch -v origin 

# si fatal error: "detected dubious ownership" =>lancer en mode administrateur par shell
> cd "C:\Program File\NoeXpy"
> git config --global --add safe.directory "C:\Program File\NoeXpy"


