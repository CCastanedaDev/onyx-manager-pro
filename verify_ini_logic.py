import os

# 1. Crear un archivo INI de prueba con comentarios y datos extra
test_file = "test_server_settings.ini"
initial_content = """[General]
scum.ServerName=Old Name
; Este es un comentario importante
scum.MaxPlayers=64
scum.SomeOtherSetting=DontTouchMe
"""

with open(test_file, "w") as f:
    f.write(initial_content)

print("Archivo original creado:")
print(initial_content)
print("-" * 20)

# 2. Simular la lógica de ConfigEditor.guardar_configuracion
cambios = {
    "scum.ServerName": "New Onyx Server",
    "scum.MaxPlayers": "100"
}

print(f"Aplicando cambios: {cambios}")

# Lógica extraída de file_editor.py
nuevas_lineas = []
claves_procesadas = []

with open(test_file, 'r') as f:
    lineas = f.readlines()

for linea in lineas:
    linea_procesada = linea
    linea_limpia = linea.strip()
    
    if "=" in linea_limpia and not linea_limpia.startswith("[") and not linea_limpia.startswith(";"):
        clave_actual = linea_limpia.split("=", 1)[0].strip()
        
        if clave_actual in cambios:
            nuevo_valor = cambios[clave_actual]
            linea_procesada = f"{clave_actual}={nuevo_valor}\n"
            claves_procesadas.append(clave_actual)
            print(f"   -> Modificando linea: '{linea.strip()}' a '{linea_procesada.strip()}'")

    nuevas_lineas.append(linea_procesada)

with open(test_file, 'w') as f:
    f.writelines(nuevas_lineas)

# 3. Verificar resultado
print("-" * 20)
with open(test_file, "r") as f:
    final_content = f.read()

print("Archivo final:")
print(final_content)

# Validaciones
assert "scum.ServerName=New Onyx Server" in final_content
assert "scum.MaxPlayers=100" in final_content
assert "; Este es un comentario importante" in final_content
assert "scum.SomeOtherSetting=DontTouchMe" in final_content

print("\nPRUEBA EXITOSA: Solo se cambiaron las lineas indicadas. Comentarios y otros ajustes intactos.")

# Limpieza
os.remove(test_file)
