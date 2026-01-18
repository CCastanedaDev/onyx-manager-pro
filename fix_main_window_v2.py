
import os

file_path = "c:/Users/stink/Desktop/VOID_SCUM_MANAGER/src/ui/main_window.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Identify the misplaced block in construir_dashboard
# Lines 338-341 (indices 337-340) are the misplaced frame_workbench code
# 337:         # --- ZONA B: MESA DE TRABAJO (Centro) ---
# 338:         # Aquí se listan las filas editables
# 339:         self.frame_workbench = ctk.CTkScrollableFrame(self.frame_profiles, fg_color="#151515", label_text=self.lang.get("prof_workbench"))
# 340:         self.frame_workbench.pack(fill="both", expand=True, padx=20, pady=5)

# We want to replace this block with the correct dashboard tail
dashboard_tail = [
    '        # --- RESTO DEL DASHBOARD ---\n',
    '        middle_container = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent"); middle_container.pack(fill="x", padx=20, pady=5)\n',
    '        panel_config = ctk.CTkFrame(middle_container, fg_color="transparent"); panel_config.pack(side="left", fill="both", expand=True, padx=(0, 10))\n',
    '        header_frame = ctk.CTkFrame(panel_config, fg_color="transparent"); header_frame.pack(fill="x", pady=(0, 2))\n',
    '        ctk.CTkLabel(header_frame, text=self.lang.get("header_config"), text_color=COLORS["text_dim"], font=("Roboto", 11, "bold")).pack(side="left")\n'
]

# 2. Identify where to put the frame_workbench code in construir_scheduler
# We look for "self.workbench_rows = []" which is around line 521
scheduler_workbench_code = [
    '        # --- ZONA B: MESA DE TRABAJO (Centro) ---\n',
    '        # Aquí se listan las filas editables\n',
    '        self.frame_workbench = ctk.CTkScrollableFrame(self.frame_profiles, fg_color="#151515", label_text=self.lang.get("prof_workbench"))\n',
    '        self.frame_workbench.pack(fill="both", expand=True, padx=20, pady=5)\n'
]

new_lines = []
inserted_scheduler_code = False

i = 0
while i < len(lines):
    line = lines[i]
    
    # Check for the misplaced block start
    if i == 337 and "ZONA B: MESA DE TRABAJO" in line:
        # Skip the 4 misplaced lines
        i += 4
        # Insert the correct dashboard tail
        new_lines.extend(dashboard_tail)
        continue
        
    # Check for the insertion point in construir_scheduler
    if "self.workbench_rows = []" in line and not inserted_scheduler_code:
        # Insert the workbench code before this line
        new_lines.extend(scheduler_workbench_code)
        new_lines.append(line)
        inserted_scheduler_code = True
        i += 1
        continue
        
    new_lines.append(line)
    i += 1

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("File fixed successfully.")
