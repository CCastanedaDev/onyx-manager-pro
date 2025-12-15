import os

def find_server_directory(base_path=None):
    """
    Busca la carpeta SCUM_Server en:
    1. Dentro del directorio actual (Portable/Default)
    2. En el directorio hermano (Sibling - para actualizaciones seguras)
    
    Retorna la ruta absoluta encontrada o la ruta por defecto (interna).
    """
    if base_path is None:
        base_path = os.getcwd()
        
    # 1. Check Internal (Default)
    internal_path = os.path.join(base_path, "SCUM_Server")
    if os.path.exists(internal_path):
        return internal_path
        
    # 2. Check Sibling (../SCUM_Server)
    # Subimos un nivel desde base_path
    parent_dir = os.path.dirname(base_path)
    sibling_path = os.path.join(parent_dir, "SCUM_Server")
    if os.path.exists(sibling_path):
        return sibling_path
        
    # Default: Return internal path so it gets created there if installed fresh
    return internal_path
