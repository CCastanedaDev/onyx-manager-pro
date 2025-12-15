
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())
sys.modules['customtkinter'] = MagicMock()

try:
    from src.logic.steam_handler import SteamHandler
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def run_test():
    print("Starting manual verification...")
    
    # Mock 'esta_corriendo' on the class to avoid subprocess in __init__
    with patch.object(SteamHandler, 'esta_corriendo', return_value=False):
        mock_log = MagicMock()
        handler = SteamHandler(mock_log)
        
        # Mock methods
        handler._secuencia_update = MagicMock()
        handler.iniciar_servidor = MagicMock()
        handler.detener_servidor = MagicMock()
        
        # TEST 1: API Failure
        print("Test 1: API Failure (None)...")
        with patch.object(handler, '_get_remote_build', return_value=None):
            handler._logica_smart_update()
            if handler._secuencia_update.called:
                print("FAIL: Update triggered on API failure")
            else:
                print("PASS: No update on API failure")

        # TEST 2: Type Mismatch (Int vs Str)
        print("Test 2: Type Mismatch (Int vs Str)...")
        # Mock _get_remote_build to return "123456" (as if fixed)
        # But wait, the fix is INSIDE _get_remote_build.
        # So we should mock requests.get to return int, and check if _get_remote_build returns str.
        
        with patch('src.logic.steam_handler.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": { "3792580": { "depots": { "branches": { "public": { "buildid": 123456 } } } } }
            }
            mock_get.return_value = mock_response
            
            remota = handler._get_remote_build()
            print(f"Remote build type: {type(remota)}")
            if isinstance(remota, str) and remota == "123456":
                print("PASS: Remote build is string")
            else:
                print(f"FAIL: Remote build is {type(remota)}: {remota}")

            # Now check logic with matching strings
            with patch.object(handler, '_get_local_build', return_value="123456"):
                # We need to mock _get_remote_build to return the string "123456" 
                # OR rely on the real method we just tested.
                # Let's mock it to be safe and isolate logic.
                with patch.object(handler, '_get_remote_build', return_value="123456"):
                    handler._logica_smart_update()
                    if handler._secuencia_update.called:
                        print("FAIL: Update triggered on matching strings")
                    else:
                        print("PASS: No update on matching strings")

        # TEST 3: Actual Update
        print("Test 3: Actual Update Needed...")
        with patch.object(handler, '_get_remote_build', return_value="999999"), \
             patch.object(handler, '_get_local_build', return_value="123456"):
            handler._logica_smart_update()
            if handler._secuencia_update.called:
                print("PASS: Update triggered correctly")
            else:
                print("FAIL: Update NOT triggered when needed")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
