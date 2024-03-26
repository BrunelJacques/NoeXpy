Installer Noethys sur Linux
===========================
L'installation de Noethys sur Linux se fait obligatoirement depuis les sources.
Ci-dessous vous allez cloner le code source depuis Github et installer les dépendances.

Installation pas à pas sur Ubuntu 22.04 Noexpy
---------------------------------------------------------
Lancez dans votre terminal Linux les commandes suivantes :

L'environnement virtuel peut être commun à Noethys-Matthania ou distinct
ici il serait distinct
```
# creation d'un groupe pour les applications de gestion et autorisation rwx au groupe
sudo groupadd noegest
sudo usermod -aG noegest <myname>
sudo mkdir /home/noegest
# creation d'un environnement de travail selon ma version de python
sudo apt install python3.10-venv
python3 -m venv envnoexpy
source envnoexpy/bin/activate
# le prompt affiche l'environnement activé
cd /home/noegest
# installation des paquets
sudo apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 python3-pip python3-pyscard python3-dev default-libmysqlclient-dev build-essential
sudo apt install pkg-config
pip3 install --upgrade pip
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython
sudo chgrp -R noegest /home/noegest
sudo chmod 775 -R /home/noegest

```
Spécifique Noexpy
```
cd /home/noegest
git clone https://github.com/BrunelJacques/Noexpy
cd Noexpy
pip3 install -r requirements.txt
cp services/doc/lancer_noestock.sh ./
cp services/doc/lancer_noelite.sh ./
chmod +x ./lancer_noe*.sh
sudo chgrp -R noegest /home/noegest
sudo chmod 775 -R /home/noegest
deactivate
# lancement de noestock ou noelite
source ../envnoexpy/bin/activate
python3 Noestock.py
python3 Noelite.py
```
pour un lien dans la barre 'activités'
```
sudo mkdir /usr/local/share/applications
sudo cp /home/noegest/Noexpy/services/doc/lancer_noestock.desktop  /usr/local/share/applications/
sudo cp /home/noegest/Noexpy/services/doc/lancer_noelite.desktop  /usr/local/share/applications/
sudo chmod +x /usr/local/share/applications/lancer_noe*.desktop
sudo chgrp noegest /usr/local/share/applications/lancer_noe*.desktop
```
Chaque user pourra ainsi 'voir' Noestock ou Noelite et le mettre dans les favoris
ou lancer comme un programme '/home/noegest/Noexpy/lancer_noestock.sh'

pour un update des appplis Noexpy
```
cd /home/noegest/Noexpy
source ../envnoexpy/bin/activate
# supprime d'éventuelles modifs locales
git stash
git reset --hard
# update proprement dit
git pull
chgrp -R noegest *.*
#sudo chmod -R 775 noegest *
```

Installation manuelle sur Linux
-------------------------------
si échec du 'git clone' télécharger les sources et extraire les fichiers

'mysqlclient' peut être enlevé de requirements.txt pour installer le reste.
Si echec pip3 install mysqlclient
```
sudo apt-get install python-mysqldb
pip3 install mysql-connector-python
```