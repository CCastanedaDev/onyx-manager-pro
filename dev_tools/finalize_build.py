import shutil
import os

DIST_ROOT = r"c:\Users\stink\Desktop\VOID_SCUM_MANAGER\dist\ONYX_MANAGER"
INTERNAL = os.path.join(DIST_ROOT, "_internal")

FOLDERS_TO_MOVE = ["data", "steamcmd", "favicon_io"]

def move_folders():
    if not os.path.exists(DIST_ROOT):
        print(f"Error: {DIST_ROOT} does not exist.")
        return

    for folder in FOLDERS_TO_MOVE:
        src = os.path.join(INTERNAL, folder)
        dst = os.path.join(DIST_ROOT, folder)
        
        if os.path.exists(src):
            print(f"Moving {folder} to root...")
            if os.path.exists(dst):
                shutil.rmtree(dst) # Remove existing if any
            shutil.move(src, dst)
        else:
            print(f"Warning: {folder} not found in _internal.")

if __name__ == "__main__":
    move_folders()
