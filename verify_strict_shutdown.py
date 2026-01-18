import sys
import os
import unittest.mock
import time

sys.path.append(os.getcwd())

# Mock ctypes before importing steam_handler
sys.modules['ctypes'] = unittest.mock.Mock()
sys.modules['ctypes'].windll.kernel32.AttachConsole.return_value = True
sys.modules['ctypes'].windll.kernel32.GenerateConsoleCtrlEvent.return_value = True

from src.logic.steam_handler import SteamHandler

def log_callback(msg):
    print(f"[LOG] {msg}")

def test_strict_shutdown():
    print("--- Testing Strict Safe Shutdown Logic ---")
    
    handler = SteamHandler(log_callback)
    
    # 1. Test: External Process (Should Fail)
    print("\n[TEST 1] External Process (Not launched by Antigravity)")
    handler.process = None
    # Mock psutil finding an external process
    with unittest.mock.patch('psutil.process_iter') as mock_iter:
        mock_p = unittest.mock.Mock()
        mock_p.info = {'name': 'SCUMServer.exe'}
        mock_p.pid = 9999
        mock_iter.return_value = [mock_p]
        
        result = handler.detener_servidor()
        if result is False:
            print("PASS: Correctly rejected external process.")
        else:
            print("FAIL: Should have returned False for external process.")

    # 2. Test: Console Attach Failure (Should Fail)
    print("\n[TEST 2] Console Attach Failure")
    handler.process = unittest.mock.Mock()
    handler.process.pid = 12345
    handler.process.poll.return_value = None
    
    sys.modules['ctypes'].windll.kernel32.AttachConsole.return_value = False # Fail attach
    
    result = handler.detener_servidor()
    if result is False:
        print("PASS: Correctly rejected shutdown when AttachConsole fails.")
    else:
        print("FAIL: Should have returned False when AttachConsole fails.")

    # 3. Test: Success Path
    print("\n[TEST 3] Successful Safe Shutdown")
    sys.modules['ctypes'].windll.kernel32.AttachConsole.return_value = True # Success attach
    
    # Mock time.sleep and esta_corriendo to simulate exit
    with unittest.mock.patch('time.sleep'):
        with unittest.mock.patch.object(SteamHandler, 'esta_corriendo', side_effect=[True, True, False]):
            result = handler.detener_servidor()
            if result is True:
                print("PASS: Successful shutdown returned True.")
            else:
                print("FAIL: Should have returned True for successful shutdown.")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_strict_shutdown()
