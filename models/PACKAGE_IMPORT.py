import os 
import importlib
import sys

def PACKAGE_DYNAMIC_IMPORT(package_name):
    """
    Dynamically imports all Python modules in the given package directory 
    and exposes their contents in the calling module's namespace, 
    similar to `from package import *`.

    Args:
        package_name (str): The name of the package (directory) containing the modules.
    """
    # Resolve the absolute path to the package directory
    package_path = os.path.join(os.getcwd(), *package_name.split('.'))

    # Ensure the directory exists and is a valid package
    if not os.path.isdir(package_path):
        raise ValueError(f"The directory '{package_path}' does not exist or is not a valid package.")

    # Get the calling module's namespace
    calling_module = sys._getframe(1).f_globals

    # Iterate through the files in the package directory
    for file in os.listdir(package_path):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]  # Remove the .py extension
            try:
                # Dynamically import the module
                module = importlib.import_module(f"{package_name}.{module_name}")
                print(f"Imported: {package_name}.{module_name}")

                # Add the module's symbols to the calling module's namespace
                for attr in dir(module):
                    if not attr.startswith("_"):  # Skip private/internal attributes
                        calling_module[attr] = getattr(module, attr)
            except Exception as e:
                print(f"Failed to import {package_name}.{module_name}: {e}")

