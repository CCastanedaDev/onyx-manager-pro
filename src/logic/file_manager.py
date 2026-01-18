import os

class FileManager:
    def __init__(self, log_callback):
        self.log = log_callback
        self.base_dir = os.getcwd()
        # Path to SCUM config: SCUM_Server/SCUM/Saved/Config/WindowsServer
        # Adjusting based on project structure where SCUM_Server is in root
        self.root_path = os.path.join(self.base_dir, "SCUM_Server", "SCUM", "Saved", "Config", "WindowsServer")
        
        # Ensure directory exists to avoid errors if server not installed yet
        if not os.path.exists(self.root_path):
            try:
                os.makedirs(self.root_path)
            except: pass

    def get_root_path(self):
        return self.root_path

    def list_files(self, relative_path=""):
        """
        Returns a list of items in the directory.
        Each item is a dict: {'name': str, 'is_dir': bool, 'path': str}
        """
        target_path = os.path.join(self.root_path, relative_path)
        if not os.path.exists(target_path):
            return []

        items = []
        try:
            # Add ".." for going up if not at root
            if relative_path and relative_path != ".":
                items.append({'name': '..', 'is_dir': True, 'path': os.path.dirname(relative_path)})

            for name in os.listdir(target_path):
                full_path = os.path.join(target_path, name)
                is_dir = os.path.isdir(full_path)
                rel_path = os.path.join(relative_path, name)
                items.append({'name': name, 'is_dir': is_dir, 'path': rel_path})
            
            # Sort: Directories first, then files
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        except Exception as e:
            self.log(f"Error listing files: {e}")
            
        return items

    def read_file(self, relative_path):
        target_path = os.path.join(self.root_path, relative_path)
        try:
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            self.log(f"Error reading file {relative_path}: {e}")
            return None

    def save_file(self, relative_path, content):
        target_path = os.path.join(self.root_path, relative_path)
        try:
            # Create backup
            if os.path.exists(target_path):
                backup_path = target_path + ".bak"
                with open(target_path, 'rb') as f_src:
                    with open(backup_path, 'wb') as f_dst:
                        f_dst.write(f_src.read())

            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.log(f"Error saving file {relative_path}: {e}")
            return False
