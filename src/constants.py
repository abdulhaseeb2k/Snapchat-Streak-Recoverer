"""
Centralised constants for the Snapchat Streak Recoverer application.
All paths, colours, fonts, and version info live here.
"""

import os
import customtkinter as ctk

# ──────────────────────────── Paths ────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROFILES_FILE = os.path.join(DATA_DIR, 'profiles.json')
APP_SETTINGS_FILE = os.path.join(DATA_DIR, 'app_settings.json')

# ──────────────────────────── Version ──────────────────────────
VERSION = "3.0"
APP_NAME = "Snapchat Streak Recoverer"
APP_SUBTITLE = "Automated Support Form Submitter"
DEVELOPER = "Abdul Haseeb"
GITHUB_URL = "https://github.com/abdulhaseeb2k/Snapchat-Streak-Recoverer"

# ──────────────────────────── Colour Palette ───────────────────
# A curated dark-mode-friendly palette
COLORS = {
    # Primary accent (Snapchat-inspired yellow-green)
    "primary":          "#FFFC00",
    "primary_hover":    "#E6E300",

    # Action green (for CTA buttons)
    "accent":           "#10A37F",
    "accent_hover":     "#0D8A6B",

    # Danger / delete
    "danger":           "#EF4444",
    "danger_hover":     "#DC2626",
    "danger_subtle_bg": ("#FEE2E2", "#450A0A"),
    "danger_text":      "#EF4444",

    # Profile avatar
    "avatar":           "#DB4437",
    "avatar_hover":     "#C33D31",

    # Neutral surfaces
    "card_bg":          ("gray88", "gray17"),
    "card_hover":       ("gray82", "gray22"),
    "surface":          ("gray92", "gray14"),
    "muted_text":       ("gray45", "gray55"),
    "separator":        ("gray75", "gray35"),

    # Buttons
    "btn_secondary":    ("gray72", "gray30"),
    "btn_secondary_hover": ("gray62", "gray40"),

    # Profile menu
    "profile_active":   "#16A34A",
    "profile_inactive": ("#3B8ED0", "#1F6AA5"),

    # Status bar
    "status_bg":        ("gray85", "gray20"),
    "status_progress":  "#10A37F",
    "status_text":      ("gray30", "gray70"),
}

# ──────────────────────────── Font Presets (Cached) ─────────────
# Fonts are created lazily and cached to avoid re-allocation on every widget.
_font_cache: dict[str, ctk.CTkFont] = {}

def _get_font(key: str, **kwargs) -> ctk.CTkFont:
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(**kwargs)
    return _font_cache[key]

def font_title():
    return _get_font("title", family="Inter", size=24, weight="bold")

def font_heading():
    return _get_font("heading", family="Inter", size=18, weight="bold")

def font_subheading():
    return _get_font("subheading", family="Inter", size=14, weight="bold")

def font_body():
    return _get_font("body", family="Inter", size=14)

def font_body_bold():
    return _get_font("body_bold", family="Inter", size=14, weight="bold")

def font_small():
    return _get_font("small", family="Inter", size=12)

def font_tiny():
    return _get_font("tiny", family="Inter", size=11)

def font_button():
    return _get_font("button", family="Inter", size=14, weight="bold")

def font_avatar():
    return _get_font("avatar", size=20, weight="bold")

def font_large_button():
    return _get_font("large_button", family="Inter", size=16, weight="bold")

# ──────────────────────────── Default Settings ─────────────────
DEFAULT_APP_SETTINGS = {
    "appearance_mode": "System",
    "view_mode": "Grid",
    "browser_profile": "Test Browser (No Profile)",
    "browser_profile_folder": None
}

DEFAULT_PROFILE_SETTINGS = {
    "username": "",
    "email": "",
    "mobile_number": "",
    "device": "",
    "refresh_delay": 1.0
}

# ──────────────────────────── Snapchat Form URL ────────────────
SNAPCHAT_FORM_URL = "https://help.snapchat.com/hc/en-us/requests/new?co=true&ticket_form_id=149423"
