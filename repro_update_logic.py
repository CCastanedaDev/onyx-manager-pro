
import json

def mock_get_remote_build(scenario):
    if scenario == "api_fail":
        return None
    elif scenario == "int_return":
        return 123456
    elif scenario == "str_return":
        return "123456"

def mock_get_local_build():
    return "123456"

def check_update(scenario):
    remota = mock_get_remote_build(scenario)
    local = mock_get_local_build()
    
    print(f"Scenario: {scenario}")
    print(f"Remote ({type(remota)}): {remota}")
    print(f"Local ({type(local)}): {local}")
    
    # Original Logic from steam_handler.py
    if remota and local and remota == local and local != "0":
        print("✅ Versión al día.")
        return
    
    if remota != local:
        print("🚨 NUEVA VERSIÓN. Actualizando... (BUG TRIGGERED)")
    else:
        print("No update triggered.")
    print("-" * 20)

print("--- Testing Current Logic ---")
check_update("int_return") # Hypothesis 1: Type mismatch
check_update("api_fail")   # Hypothesis 2: API failure triggers update
check_update("str_return") # Control: Should work if types match
