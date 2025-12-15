import re
import json
import os

def check_translations():
    # 1. Extract keys from main_window.py
    keys_in_code = set()
    with open(os.path.join("src", "ui", "main_window.py"), "r", encoding="utf-8") as f:
        content = f.read()
        # Regex to find self.lang.get("KEY") or self.lang.get('KEY')
        matches = re.findall(r'self\.lang\.get\s*\(\s*["\']([^"\']+)["\']\s*\)', content)
        keys_in_code.update(matches)
        
    print(f"Found {len(keys_in_code)} keys in code.")

    # 2. Load es.json as baseline
    lang_dir = os.path.join("data", "lang")
    if not os.path.exists(lang_dir):
        print("Error: data/lang directory not found.")
        return

    json_files = [f for f in os.listdir(lang_dir) if f.endswith(".json")]
    
    for json_file in json_files:
        file_path = os.path.join(lang_dir, json_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            missing_keys = [k for k in keys_in_code if k not in data]
            
            if missing_keys:
                print(f"\nMissing keys in {json_file}:")
                for k in missing_keys:
                    print(f"  - {k}")
            else:
                print(f"\n{json_file} is complete.")
                
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

if __name__ == "__main__":
    check_translations()
