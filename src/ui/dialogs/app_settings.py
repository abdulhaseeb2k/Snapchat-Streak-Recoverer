"""
AppSettingsWindow — dialog for global application settings.
"""

import customtkinter as ctk
from src.constants import COLORS, font_heading, font_body_bold, font_button
class AppSettingsWindow(ctk.CTkToplevel):
    """Modal dialog for global app settings (appearance, view mode)."""

    def __init__(self, parent, app_settings: dict, save_callback):
        super().__init__(parent)
        self.title("App Global Settings")
        self.geometry("460x490")
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

        # ── Browser Extension ──
        ctk.CTkLabel(frame, text="Browser Extension Path", font=font_body_bold()).pack(
            pady=(10, 0), anchor="w", padx=20
        )
        ext_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ext_frame.pack(fill="x", padx=20, pady=5)
        
        from src.constants import DEFAULT_EXTENSION_DIR
        default_ext = app_settings.get("extension_path", "").strip()
        if not default_ext:
            default_ext = DEFAULT_EXTENSION_DIR
            
        self._ext_path_var = ctk.StringVar(value=default_ext)
        ctk.CTkEntry(
            ext_frame, textvariable=self._ext_path_var, state="readonly"
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            ext_frame, text="Browse...", width=60,
            fg_color=COLORS["btn_secondary"], hover_color=COLORS["btn_secondary_hover"],
            command=self._browse_extension
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            ext_frame, text="Clear", width=50,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=lambda: self._ext_path_var.set("")
        ).pack(side="left")

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
        settings = {
            "appearance_mode": self._appearance_menu.get(),
            "view_mode": self._view_menu.get(),
            "extension_path": self._ext_path_var.get()
        }
        self._save_callback(settings)
        self.destroy()

    def _browse_extension(self):
        path = ctk.filedialog.askdirectory(title="Select Unpacked Extension Folder")
        if path:
            self._ext_path_var.set(path)
