import py_compile
import sys
import os

file_path = 'src/ui/main_window.py'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

try:
    py_compile.compile(file_path, doraise=True)
    print("Syntax OK")
except Exception as e:
    print(f"Syntax Error: {e}")
    sys.exit(1)
