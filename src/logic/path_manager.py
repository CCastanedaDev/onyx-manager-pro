import os

def find_server_directory(base_path=None):
    """
    Busca la carpeta SCUM_Server en (en orden de prioridad):
    1. Carpeta del .exe  (ONYX_EXE_DIR) – para modo onefile
    2. Dentro de base_path
    3. Hermano de base_path (../SCUM_Server)

    Retorna la ruta absoluta encontrada o la ruta por defecto.
    """
    if base_path is None:
        base_path = os.getcwd()

    # Colectar directorios candidatos (sin duplicados)
    candidates = []
    exe_dir = os.environ.get("ONYX_EXE_DIR")
    if exe_dir:
        candidates.append(exe_dir)
    candidates.append(base_path)
    parent_dir = os.path.dirname(base_path)
    if parent_dir and parent_dir not in candidates:
        candidates.append(parent_dir)

    for d in candidates:
        p = os.path.join(d, "SCUM_Server")
        if os.path.isdir(p):
            return p

    # Default: junto al .exe o dentro de base_path
    default_root = exe_dir if exe_dir else base_path
    return os.path.join(default_root, "SCUM_Server")
