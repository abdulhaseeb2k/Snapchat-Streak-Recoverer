"""
AppSettingsWindow — dialog for global application settings.
"""

import customtkinter as ctk
from src.constants import COLORS, font_heading, font_body_bold, font_button
from src.core.chrome_profiles import get_chrome_profiles


class AppSettingsWindow(ctk.CTkToplevel):
    """Modal dialog for global app settings (appearance, view mode, browser profile)."""

    def __init__(self, parent, app_settings: dict, save_callback):
        super().__init__(parent)
        self.title("App Global Settings")
        self.geometry("460x560")
        self.grab_set()

        self._save_callback = save_callback

        ctk.CTkLabel(self, text="Global Settings", font=font_heading()).pack(pady=20)

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ── Appearance Mode ──
        ctk.CTkLabel(frame, text="Appearance Mode", font=font_body_bold()).pack(
            pady=(15, 0), anchor="w", padx=20
        )
        self._appearance_menu = ctk.CTkOptionMenu(
            frame, values=["System", "Light", "Dark"], width=360
        )
        self._appearance_menu.pack(pady=5)
        self._appearance_menu.set(app_settings.get("appearance_mode", "System"))

        # ── View Mode ──
        ctk.CTkLabel(frame, text="Friends List Style", font=font_body_bold()).pack(
            pady=(10, 0), anchor="w", padx=20
        )
        self._view_menu = ctk.CTkOptionMenu(
            frame, values=["Grid", "List"], width=360
        )
        self._view_menu.pack(pady=5)
        self._view_menu.set(app_settings.get("view_mode", "Grid"))

        # ── Browser Profile ──
        ctk.CTkLabel(frame, text="Chrome Browser Profile", font=font_body_bold()).pack(
            pady=(10, 0), anchor="w", padx=20
        )
        self._available_profiles = get_chrome_profiles()
        self._profile_options = list(self._available_profiles.keys())
        self._profile_menu = ctk.CTkOptionMenu(
            frame, values=self._profile_options, width=360
        )
        self._profile_menu.pack(pady=5)

        current = app_settings.get("browser_profile", "Test Browser (No Profile)")
        if current not in self._profile_options:
            current = self._profile_options[0]
        self._profile_menu.set(current)

        # ── Utility buttons ──
        from src.ui.dialogs.help_window import HelpWindow
        from src.ui.dialogs.about_window import AboutWindow

        ctk.CTkButton(
            frame, text="❓ How to Use (Help)",
            fg_color=COLORS["btn_secondary"], hover_color=COLORS["btn_secondary_hover"],
            height=40, command=lambda: HelpWindow(self),
        ).pack(pady=(20, 10), padx=20, fill="x")

        ctk.CTkButton(
            frame, text="👨‍💻 About Developer",
            fg_color=COLORS["btn_secondary"], hover_color=COLORS["btn_secondary_hover"],
            height=40, command=lambda: AboutWindow(self),
        ).pack(pady=(0, 15), padx=20, fill="x")

        # ── Save button ──
        ctk.CTkButton(
            self, text="Save Settings", height=42, font=font_button(),
            command=self._save,
        ).pack(pady=10)

    def _save(self):
        selected_display = self._profile_menu.get()
        folder_name = self._available_profiles.get(selected_display)

        new_settings = {
            "appearance_mode": self._appearance_menu.get(),
            "view_mode": self._view_menu.get(),
            "browser_profile": selected_display,
            "browser_profile_folder": folder_name,
        }
        self._save_callback(new_settings)
        self.destroy()
