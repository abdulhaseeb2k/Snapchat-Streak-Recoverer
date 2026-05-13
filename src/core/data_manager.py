"""
DataManager — handles all JSON persistence and profile/friend CRUD operations.
This is the single source of truth for application data.
"""

import copy
import os
import json
import threading
from src.constants import DATA_DIR, PROFILES_FILE, APP_SETTINGS_FILE, DEFAULT_APP_SETTINGS, DEFAULT_PROFILE_SETTINGS


class DataManager:
    """Manages profile data, friend lists, and app settings."""

    def __init__(self):
        self._ensure_data_dir()
        self.profiles: dict = {}
        self.current_profile_name: str | None = None
        self.app_settings: dict = {}
        self._save_queue_lock = threading.Lock()
        self._profiles_write_lock = threading.Lock()
        self._pending_profiles_snapshot: tuple[int, dict] | None = None
        self._profiles_save_worker: threading.Thread | None = None
        self._profiles_save_version = 0

        self._load_profiles()
        self._load_app_settings()

    # ──────────────────── File I/O ────────────────────

    @staticmethod
    def _ensure_data_dir():
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    @staticmethod
    def _load_json(path: str, default: dict | list) -> dict | list:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return default.copy() if isinstance(default, dict) else list(default)

    @staticmethod
    def _save_json(path: str, data):
        temp_path = f"{path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(temp_path, path)

    # ──────────────────── Profile Loading & Migration ────────────────────

    def _load_profiles(self):
        self.profiles = self._load_json(PROFILES_FILE, {})

        # Migration from old single-profile format
        if not self.profiles:
            self._migrate_old_format()

        self.current_profile_name = (
            list(self.profiles.keys())[0] if self.profiles else None
        )

    def _migrate_old_format(self):
        """Migrate from old settings.json + friends.json to profiles.json."""
        old_settings_path = os.path.join(DATA_DIR, 'settings.json')
        old_friends_path = os.path.join(DATA_DIR, 'friends.json')

        old_settings = dict(DEFAULT_PROFILE_SETTINGS)
        old_friends = []

        if os.path.exists(old_settings_path):
            try:
                with open(old_settings_path, 'r') as f:
                    old_settings.update(json.load(f))
            except Exception:
                pass

        if os.path.exists(old_friends_path):
            try:
                with open(old_friends_path, 'r') as f:
                    old_friends = json.load(f)
            except Exception:
                pass

        self.profiles = {
            "Profile 1": {
                "settings": old_settings,
                "friends": old_friends
            }
        }
        self.save_profiles()

    def _load_app_settings(self):
        self.app_settings = self._load_json(APP_SETTINGS_FILE, DEFAULT_APP_SETTINGS)
        # Ensure all keys exist (forward-compat)
        for key, val in DEFAULT_APP_SETTINGS.items():
            self.app_settings.setdefault(key, val)

    # ──────────────────── Profile CRUD ────────────────────

    def save_profiles(self):
        snapshot = copy.deepcopy(self.profiles)
        with self._save_queue_lock:
            self._profiles_save_version += 1
            self._pending_profiles_snapshot = None

        with self._profiles_write_lock:
            self._save_json(PROFILES_FILE, snapshot)

    def save_profiles_async(self):
        """Persist profiles in the background so the UI stays responsive."""
        snapshot = copy.deepcopy(self.profiles)
        with self._save_queue_lock:
            self._profiles_save_version += 1
            version = self._profiles_save_version
            self._pending_profiles_snapshot = (version, snapshot)
            worker_running = (
                self._profiles_save_worker is not None
                and self._profiles_save_worker.is_alive()
            )
            if worker_running:
                return

            self._profiles_save_worker = threading.Thread(
                target=self._profiles_save_loop,
                daemon=True,
            )
            self._profiles_save_worker.start()

    def _profiles_save_loop(self):
        while True:
            with self._save_queue_lock:
                pending = self._pending_profiles_snapshot
                self._pending_profiles_snapshot = None

            if pending is None:
                with self._save_queue_lock:
                    self._profiles_save_worker = None
                return

            version, snapshot = pending

            with self._profiles_write_lock:
                with self._save_queue_lock:
                    if version < self._profiles_save_version:
                        continue
                self._save_json(PROFILES_FILE, snapshot)

            with self._save_queue_lock:
                if self._pending_profiles_snapshot is None:
                    self._profiles_save_worker = None
                    return

    def save_app_settings(self):
        self._save_json(APP_SETTINGS_FILE, self.app_settings)

    def get_current_settings(self) -> dict:
        if not self.current_profile_name:
            return {}
        return self.profiles[self.current_profile_name]["settings"]

    def set_current_settings(self, new_settings: dict):
        if not self.current_profile_name:
            return
        self.profiles[self.current_profile_name]["settings"] = new_settings
        self.save_profiles()

    def add_profile(self, name: str, settings: dict | None = None) -> bool:
        """Add a new profile. Returns False if name already exists."""
        if name in self.profiles:
            return False
        self.profiles[name] = {
            "settings": settings or dict(DEFAULT_PROFILE_SETTINGS),
            "friends": []
        }
        self.save_profiles()
        return True

    def delete_profile(self, name: str):
        if name in self.profiles:
            del self.profiles[name]
        self.save_profiles()

        if self.profiles:
            self.current_profile_name = list(self.profiles.keys())[0]
        else:
            self.current_profile_name = None

    def update_profile_settings(self, name: str, new_settings: dict):
        if name in self.profiles:
            self.profiles[name]["settings"] = new_settings
            self.save_profiles()

    def switch_profile(self, name: str):
        if name in self.profiles:
            self.current_profile_name = name

    # ──────────────────── Friend CRUD ────────────────────

    def get_friends(self) -> list:
        if not self.current_profile_name:
            return []
        return self.profiles[self.current_profile_name]["friends"]

    def add_friend(self, username: str, name: str = "", save: bool = True) -> bool:
        """Add friend. Returns False if username already exists."""
        friends = self.get_friends()
        if any(f['username'].lower() == username.lower() for f in friends):
            return False
        friends.append({"username": username, "name": name, "selected": True})
        if save:
            self.save_profiles()
        return True

    def update_friend(self, index: int, data: dict, save: bool = True):
        friends = self.get_friends()
        if 0 <= index < len(friends):
            friends[index].update(data)
            if save:
                self.save_profiles()

    def delete_friend(self, index: int, save: bool = True):
        friends = self.get_friends()
        if 0 <= index < len(friends):
            del friends[index]
            if save:
                self.save_profiles()

    def toggle_friend(self, index: int, selected: bool):
        friends = self.get_friends()
        if 0 <= index < len(friends):
            friends[index]['selected'] = selected
            self.save_profiles()

    def get_selected_friends(self) -> list[str]:
        """Return list of usernames that are selected."""
        return [f['username'] for f in self.get_friends() if f.get('selected')]

    def get_selected_friend_count(self) -> int:
        """Return how many friends are currently selected."""
        return sum(1 for f in self.get_friends() if f.get('selected'))

    # ──────────────────── Profile Export / Import ────────────────────

    def export_profiles(self, profile_names: list[str], filepath: str) -> bool:
        """Export multiple profiles to a JSON file."""
        export_data = {}
        for name in profile_names:
            if name in self.profiles:
                export_data[name] = self.profiles[name]
                
        if not export_data:
            return False
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            return True
        except Exception:
            return False

    def import_profiles(self, filepath: str) -> tuple[bool, str]:
        """Import one or more profiles from a JSON file. Returns (success, message)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or not data:
                return False, "Invalid profile format."
            
            imported_count = 0
            for original_name, profile_data in data.items():
                if not isinstance(profile_data, dict) or "settings" not in profile_data or "friends" not in profile_data:
                    continue # Skip invalid
                
                new_name = original_name
                count = 1
                while new_name in self.profiles:
                    new_name = f"{original_name} (Imported {count})" if count > 1 else f"{original_name} (Imported)"
                    count += 1
                
                self.profiles[new_name] = profile_data
                imported_count += 1
            
            if imported_count > 0:
                self.save_profiles()
                return True, f"Successfully imported {imported_count} account(s)."
            else:
                return False, "No valid profiles found in file."
        except Exception as e:
            return False, f"Import failed: {str(e)}"
