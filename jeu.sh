#!/bin/bash

# Chemin vers le script Python
PYTHON_SCRIPT="models/main.py"

# Chemin vers l'exécutable
EXECUTABLE="Reseau/boucle/proxy_v3.exe"

# Vérifiez si Python est installé
if ! command -v python3 &> /dev/null
then
    echo "Python n'est pas installé. Veuillez installer Python pour continuer."
    exit 1
fi

# Lancer le script Python
echo "Lancement du script Python..."
python3 "$PYTHON_SCRIPT"

# Vérifiez si Wine est installé (nécessaire pour exécuter des .exe sous Linux)
if ! command -v wine &> /dev/null
then
    echo "Wine n'est pas installé. Veuillez installer Wine pour exécuter des fichiers .exe sous Linux."
    exit 1
fi

# Lancer l'exécutable avec Wine
echo "Lancement de l'exécutable..."
wine "$EXECUTABLE"