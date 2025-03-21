#!/bin/bash

# Chemin vers le répertoire contenant le script Python
PYTHON_SCRIPT_DIR="models"

# Chemin vers le script Python
PYTHON_SCRIPT="$PYTHON_SCRIPT_DIR/main.py"

# Chemin vers l'exécutable
EXECUTABLE="Reseau/boucle/proxy_v3.exe"

# Vérifiez si Python est installé
if ! command -v python3 &> /dev/null
then
    echo "Python n'est pas installé. Veuillez installer Python pour continuer."
    exit 1
fi

# Changer de répertoire vers le dossier contenant le script Python
cd "$PYTHON_SCRIPT_DIR" || { echo "Impossible de changer de répertoire vers $PYTHON_SCRIPT_DIR"; exit 1; }

# Lancer le script Python
echo "Lancement du script Python..."
python3 "$PYTHON_SCRIPT"

# Revenir au répertoire d'origine
cd - || { echo "Impossible de revenir au répertoire d'origine"; exit 1; }

# Lancer l'exécutable
echo "Lancement de l'exécutable..."
wine "$EXECUTABLE"
