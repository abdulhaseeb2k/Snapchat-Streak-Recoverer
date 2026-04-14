"""
AboutWindow — dialog showing developer and version info.
"""

import webbrowser
import customtkinter as ctk
from src.constants import VERSION, APP_NAME, DEVELOPER, GITHUB_URL, font_heading, font_body, font_small


class AboutWindow(ctk.CTkToplevel):
    """Modal dialog showing app info and developer credit."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("About Developer")
        self.geometry("420x360")
        self.grab_set()

        ctk.CTkLabel(self, text=APP_NAME, font=font_heading()).pack(pady=(30, 10))
        ctk.CTkLabel(self, text=f"Version {VERSION}", font=font_small(), text_color="gray").pack()

        info_text = (
            "This software is designed to automate repetitive\n"
            "Snapchat support requests safely and efficiently.\n\n"
            f"Developed by: {DEVELOPER}\n\n"
            "For updates and support, visit our GitHub."
        )
        ctk.CTkLabel(self, text=info_text, font=font_body(), pady=20).pack()

        ctk.CTkButton(
            self, text="Visit GitHub",
            command=lambda: webbrowser.open(GITHUB_URL),
        ).pack(pady=10)
