#!/bin/bash
# installation sous linux
# lancer:$ sudo bash install_auto.sh
cd /home
if [ ! -d noegest ]; then
	mkdir noegest; fi
cd noegest
if [ ! -d Noexpy ]; then
	mkdir Noexpy ; fi
if ! getent group noegest >/dev/null; then
	sudo groupadd noegest; fi
sudo apt install python3.10-venv >/dev/null
python3 -m venv envnoexpy
source envnoexpy/bin/activate
sudo apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 python3-pip python3-pyscard python3-dev default-libmysqlclient-dev build-essential
sudo apt install pkg-config
pip3 install --upgrade pip
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython
sudo chgrp -R noegest /home/noegest
sudo chmod 775 -R /home/noegest
cd /home/noegest
git clone https://github.com/BrunelJacques/Noexpy
cd Noexpy
pip3 install -r requirements.txt
cp services/doc/lancer_noestock.sh ./
cp services/doc/lancer_noelite.sh ./
chmod +x ./lancer_noe*.sh
sudo chgrp -R noegest /home/noegest
sudo chmod 775 -R /home/noegest
if [ ! -d Noexpy ]; then
	sudo mkdir /usr/local/share/applications; fi
sudo cp /home/noegest/Noexpy/services/doc/lancer_noestock.desktop  /usr/local/share/applications/
sudo cp /home/noegest/Noexpy/services/doc/lancer_noelite.desktop  /usr/local/share/applications/
sudo chmod +x /usr/local/share/applications/lancer_noe*.desktop
sudo chgrp noegest /usr/local/share/applications/lancer_noe*.desktop

