echo off
c:
cd "c:\Program Files\Noethys-Matthania"
if not exist .\Test.py (
	dir
	echo --------------------------------------------------------
	echo Le programme Test.py semble absent de
	echo "c:\Program Files\Noethys-Matthania"
	echo probleme d'arborescence?
	echo --------------------------------------------------------
	pause
    exit /b
)	

python Test.py
echo ---------------------------------------------------
echo Test presence Python et Noethys: no error ci-dessus
echo ---------------------------------------------------

call .\venv\Scripts\activate
rem Check if the package installation was successful
if %errorlevel% neq 0 (
    echo Failed to install the required packages.
	dir
	echo --------------------------------------------------------
	echo L'environnement 'venv' est present, mais ne s'active pas
	echo ouvrez une fenetre en mode commande shell
	echo Executez les lignes ci dessous
	echo L'environnement actif, le prompt affiche  venv
	echo Les packages defilent lors de leur installation.
	echo --------------------------------------------------------
	echo cd  "c:\Program Files\Noethys-Matthania\Noethys"
	echo call venv\Scripts\activate
	echo pip install requirements
	echo ---------------------------------------------------
	pause
    exit /b
)
echo Environnement: actif ok
cd ..
cd NoeXpy-Matthania
if not exist .\Noestock.py (
	dir
	echo --------------------------------------------------------
	echo Le programme Noestock.py semble absent de
	echo "c:\Program Files\NoeXpy-Matthania"
	echo probleme d'arborescence?
	echo --------------------------------------------------------
	pause
    exit /b
)
python Noestock.py


