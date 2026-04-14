"""
Chrome profile detection for Windows.
Reads the Chrome 'Local State' file to get user-defined profile names.
"""

import os
import json


def get_chrome_profiles() -> dict[str, str | None]:
    """
    Detect Google Chrome profiles on Windows.

    Returns:
        dict mapping display names to folder names.
        Example: {"Test Browser (No Profile)": None, "Chrome: Personal (Profile 1)": "Profile 1"}
    """
    base_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
    local_state_path = os.path.join(base_path, 'Local State')
    profiles: dict[str, str | None] = {"Test Browser (No Profile)": None}

    # Read friendly names from Local State
    info_cache = {}
    if os.path.exists(local_state_path):
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                info_cache = state.get('profile', {}).get('info_cache', {})
        except Exception:
            pass

    # Scan for profile directories
    if os.path.exists(base_path):
        try:
            for item in os.listdir(base_path):
                profile_path = os.path.join(base_path, item)
                if not os.path.isdir(profile_path):
                    continue
                if item != 'Default' and not item.startswith('Profile '):
                    continue
                if not os.path.exists(os.path.join(profile_path, 'Preferences')):
                    continue

                # Build display name
                display_name = item
                if item in info_cache:
                    friendly_name = info_cache[item].get('name')
                    if friendly_name:
                        display_name = f"{friendly_name} ({item})"

                profiles[f"Chrome: {display_name}"] = item
        except Exception:
            pass

    return profiles
