Installer Noexpy sur Windows
===========================

Pour Windows, vous devez aller sur les sites des auteurs pour 
rechercher et installer les bibliothèques suivantes.
- Python 3+ avec pip (http://www.python.org/)
- wxPython 3+ - version unicode (http://www.wxpython.org/)
- git https://git-scm.com/download/win

#Cloner les sources via git qui céera le répertoire NoeXpy (shell en mode administrateur)
git clone https://github.com/BrunelJacques/NoeXpy

#### dans un terminal shell dans /NoeXpy lancez le chargement des packages
pip install -r requirements.txt'

#  fatal error: "detected dubious ownership" =>lancer en mode administrateur par shell
git config --system --add safe.directory '*' # For all users and all repositories
