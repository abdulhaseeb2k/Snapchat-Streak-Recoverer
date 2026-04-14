"""
ProfileMenu — dialog for switching between profiles.
"""

import customtkinter as ctk
from src.constants import COLORS, font_heading, font_small, font_button


class ProfileMenu(ctk.CTkToplevel):
    """Modal dialog to switch between user profiles."""

    def __init__(self, parent, profiles: dict, current_name: str,
                 on_switch, on_edit, on_add_new):
        super().__init__(parent)
        self.title("Switch Profile")
        self.geometry("380x420")
        self.grab_set()

        self._on_switch = on_switch
        self._on_edit = on_edit
        self._on_add_new = on_add_new

        ctk.CTkLabel(
            self, text="Accounts", font=font_heading(),
        ).pack(pady=15)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        for p_name in profiles.keys():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)

            is_active = (p_name == current_name)
            fg = COLORS["profile_active"] if is_active else COLORS["profile_inactive"]

            ctk.CTkButton(
                row, text=p_name, fg_color=fg, height=38, anchor="w",
                command=lambda name=p_name: self._switch(name),
            ).pack(side="left", expand=True, fill="x", padx=(5, 5))

            ctk.CTkButton(
                row, text="✎ Edit", width=60, height=38,
                fg_color=COLORS["btn_secondary"],
                hover_color=COLORS["btn_secondary_hover"],
                font=font_small(),
                command=lambda name=p_name: self._on_edit(name),
            ).pack(side="right", padx=(0, 5))

        # Separator
        ctk.CTkFrame(self, height=2, fg_color=COLORS["separator"]).pack(
            fill="x", pady=10, padx=20
        )

        ctk.CTkButton(
            self, text="+ Add New Account",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            height=42, font=font_button(),
            command=self._add_new,
        ).pack(pady=15, padx=20, fill="x")

    def _switch(self, name):
        self._on_switch(name)
        self.destroy()

    def _add_new(self):
        self._on_add_new()
        self.destroy()
