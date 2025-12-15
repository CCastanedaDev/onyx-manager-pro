
import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.getcwd())
sys.modules['customtkinter'] = MagicMock()

try:
    from src.logic.steam_handler import SteamHandler
    print("Import successful")
    print(f"Methods: {dir(SteamHandler)}")
    if hasattr(SteamHandler, 'esta_corriendo'):
        print("esta_corriendo found")
    else:
        print("esta_corriendo NOT found")
except Exception as e:
    print(f"Import failed: {e}")
