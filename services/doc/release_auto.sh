#!/bin/bash

# lancer:$ sudo bash install_auto.sh
cd /home/noegest
git clone https://github.com/BrunelJacques/Noexpy
cd Noexpy
chmod +x ./lancer_noe*.sh
sudo chgrp -R noegest /home/noegest/Noexpy
sudo chmod 775 -R /home/noegest

