import json
import os

class RaidEditor:
    def __init__(self, log_callback, base_path=None):
        self.log = log_callback
        root_dir = base_path if base_path else os.getcwd()
        self.config_path = os.path.join(root_dir, "scum_server", "SCUM", "Saved", "Config", "WindowsServer", "RaidTimes.json")
        
        self.days_map = {
            "Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday",
            "Thursday": "Thursday", "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday",
            "Weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "Weekend": ["Saturday", "Sunday"]
        }
        self.ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def load_raid_times(self):
        """
        Loads raid times and normalizes them into a dictionary keyed by day name.
        Returns: { "Monday": { "active": True, "time": "...", ... }, ... }
        """
        default_structure = {day: {"active": False, "time": "00:00-00:00", "start-announcement-time": "30", "end-announcement-time": "30"} for day in self.ordered_days}
        
        if not os.path.exists(self.config_path):
            self.log("⚠ WARNING: RaidTimes.json not found. Using defaults.")
            return default_structure
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_list = data.get("raiding-times", [])
                
            for entry in raw_list:
                days_str = entry.get("day", "")
                # Handle comma separated days "Monday,Wednesday"
                raw_days = [d.strip() for d in days_str.split(",")]
                
                for raw_day in raw_days:
                    target_days = []
                    if raw_day in self.days_map:
                        val = self.days_map[raw_day]
                        if isinstance(val, list): target_days.extend(val)
                        else: target_days.append(val)
                    else:
                        # Fallback for direct match or unknown
                        if raw_day in self.ordered_days: target_days.append(raw_day)
                        
                    for day in target_days:
                        if day in default_structure:
                            default_structure[day]["active"] = True
                            default_structure[day]["time"] = entry.get("time", "00:00-00:00")
                            default_structure[day]["start-announcement-time"] = entry.get("start-announcement-time", "30")
                            default_structure[day]["end-announcement-time"] = entry.get("end-announcement-time", "30")
                            
            return default_structure
            
        except Exception as e:
            self.log(f"❌ Error loading RaidTimes.json: {e}")
            return default_structure

    def save_raid_times(self, raid_data_dict):
        """
        Saves the dictionary back to JSON, creating individual entries for each active day.
        raid_data_dict: { "Monday": { "active": True, ... }, ... }
        """
        output_list = []
        
        for day in self.ordered_days:
            info = raid_data_dict.get(day)
            if info and info.get("active"):
                entry = {
                    "day": day,
                    "time": info.get("time"),
                    "start-announcement-time": info.get("start-announcement-time"),
                    "end-announcement-time": info.get("end-announcement-time")
                }
                output_list.append(entry)
                
        data = {"raiding-times": output_list}
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.log(">> ✅ RAID TIMES UPDATED (Separated Days).")
            return True
        except Exception as e:
            self.log(f"❌ Error saving RaidTimes.json: {e}")
            return False
