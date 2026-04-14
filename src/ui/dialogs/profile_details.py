"""
ProfileDetailsWindow — dialog for creating or editing a profile's account details.
"""

import customtkinter as ctk
from tkinter import messagebox
from src.constants import COLORS, font_heading, font_body_bold, font_button


class ProfileDetailsWindow(ctk.CTkToplevel):
    """Modal dialog to create or edit profile settings."""

    def __init__(self, parent, settings: dict, save_callback,
                 profile_name: str = None, delete_callback=None, is_new=False):
        super().__init__(parent)
        self.title("Account Setup" if is_new else "Edit Account Details")
        self.geometry("460x620")
        self.grab_set()

        self._save_callback = save_callback
        self._delete_callback = delete_callback
        self._is_new = is_new

        header = "New Account" if is_new else f"Edit '{profile_name}'"
        ctk.CTkLabel(self, text=header, font=font_heading()).pack(pady=(20, 15))

        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ── Account Name ──
        ctk.CTkLabel(frame, text="Account Name", font=font_body_bold()).pack(
            pady=(15, 0), anchor="w", padx=20
        )
        self._name_entry = ctk.CTkEntry(frame, width=360, height=38)
        self._name_entry.pack(pady=(5, 10))
        if not is_new:
            self._name_entry.insert(0, profile_name)
            self._name_entry.configure(state="disabled")

        # ── Fields ──
        field_specs = [
            ("Snapchat Username", "username"),
            ("Account Email", "email"),
            ("Mobile Number (inc Country Code)", "mobile_number"),
            ("Device (e.g. iPhone 14, Galaxy S23)", "device"),
            ("Refresh Delay (seconds)", "refresh_delay"),
        ]
        self._entries = {}
        for label_text, key in field_specs:
            ctk.CTkLabel(frame, text=label_text, font=font_body_bold()).pack(
                pady=(10, 0), anchor="w", padx=20
            )
            entry = ctk.CTkEntry(frame, width=360, height=38)
            entry.pack(pady=(5, 10))
            entry.insert(0, str(settings.get(key, "")))
            self._entries[key] = entry

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        save_text = "Create Account" if is_new else "Save Details"
        ctk.CTkButton(
            btn_frame, text=save_text, height=42, font=font_button(),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._save,
        ).pack(side="left", expand=True, fill="x", padx=(0, 10))

        if not is_new:
            ctk.CTkButton(
                btn_frame, text="Delete", width=90, height=42,
                fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                command=self._delete,
            ).pack(side="right")

    def _save(self):
        try:
            delay = float(self._entries["refresh_delay"].get())
            if delay < 0:
                delay = 1.0
        except ValueError:
            delay = 1.0

        data = {
            "username": self._entries["username"].get().strip(),
            "email": self._entries["email"].get().strip(),
            "mobile_number": self._entries["mobile_number"].get().strip(),
            "device": self._entries["device"].get().strip(),
            "refresh_delay": delay,
        }

        if self._is_new:
            data["_profile_name_"] = self._name_entry.get().strip()
            if not data["_profile_name_"]:
                messagebox.showerror("Error", "Please enter an account name.")
                return

        success = self._save_callback(data)
        if success is not False:
            self.destroy()

    def _delete(self):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this profile?"):
            self._delete_callback()
            self.destroy()
