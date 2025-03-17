import os
import importlib

# Exposer les noms publics
__all__ = []

# Obtenir le chemin du dossier courant
current_dir = os.path.dirname(__file__)

# Parcourir tous les fichiers Python dans le dossier, sauf __init__.py
for filename in os.listdir(current_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        # Extraire le nom du module sans l'extension .py
        module_name = filename[:-3]
        # Importer dynamiquement le module
        module = importlib.import_module(f".{module_name}", package=__name__)
        # Ajouter toutes les classes/fonctions du module aux exports publics
        for attr in dir(module):
            if not attr.startswith("_"):  # Ignorer les privés
                globals()[attr] = getattr(module, attr)
                __all__.append(attr)
