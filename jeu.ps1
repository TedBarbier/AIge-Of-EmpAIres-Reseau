# Chemin vers le répertoire contenant le script Python
$pythonScriptDirectory = ".\models"

# Chemin vers le script Python
$pythonScript = "main.py"

# Chemin vers l'exécutable
$executable = ".\Reseau\boucle\proxy_v3.exe"

# Vérifiez si Python est installé
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python n'est pas installé. Veuillez installer Python pour continuer."
    exit 1
}

# Sauvegarder le répertoire actuel
$originalDirectory = Get-Location

# Changer de répertoire vers le dossier contenant le script Python
Set-Location -Path $pythonScriptDirectory

# Lancer le script Python
Write-Host "Lancement du script Python..."
python $pythonScript

# Revenir au répertoire d'origine
Set-Location -Path $originalDirectory

# Lancer l'exécutable
Write-Host "Lancement de l'exécutable..."
Start-Process $executable
