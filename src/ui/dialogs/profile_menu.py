"""
ProfileMenu — dialog for switching between profiles.
"""

import customtkinter as ctk
from src.constants import COLORS, font_heading, font_small, font_button


class ProfileMenu(ctk.CTkToplevel):
    """Modal dialog to switch between user profiles."""

    def __init__(self, parent, profiles: dict, current_name: str,
                 on_switch, on_edit, on_add_new, on_export, on_import):
        super().__init__(parent)
        self.title("Switch Profile")
        self.geometry("380x420")
        self.grab_set()

        self._on_switch = on_switch
        self._on_edit = on_edit
        self._on_add_new = on_add_new
        self._on_export = on_export
        self._on_import = on_import

        ctk.CTkLabel(
            self, text="Accounts", font=font_heading(),
        ).pack(pady=15)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        self._export_vars = {}

        for p_name in profiles.keys():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)

            is_active = (p_name == current_name)
            fg = COLORS["profile_active"] if is_active else COLORS["profile_inactive"]

            checkbox_var = ctk.BooleanVar(value=False)
            self._export_vars[p_name] = checkbox_var
            ctk.CTkCheckBox(
                row, text="", variable=checkbox_var, width=20,
                checkbox_height=20, checkbox_width=20,
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                border_color=COLORS["separator"]
            ).pack(side="left", padx=(5, 0))

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

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(
            bottom_frame, text="+ Add New Account",
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            height=42, font=font_button(),
            command=self._add_new,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            bottom_frame, text="⭳ Export", width=80,
            fg_color=COLORS["btn_secondary"], hover_color=COLORS["btn_secondary_hover"],
            height=42, font=font_button(),
            command=self._export_selected,
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            bottom_frame, text="⭱ Import", width=80,
            fg_color=COLORS["btn_secondary"], hover_color=COLORS["btn_secondary_hover"],
            height=42, font=font_button(),
            command=self._import,
        ).pack(side="right")

    def _switch(self, name):
        self._on_switch(name)
        self.destroy()

    def _add_new(self):
        self._on_add_new()
        self.destroy()

    def _export_selected(self):
        selected = [name for name, var in self._export_vars.items() if var.get()]
        if selected:
            self._on_export(selected)

    def _import(self):
        self._on_import()
        self.destroy()
