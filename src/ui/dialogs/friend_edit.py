"""
FriendEditWindow — dialog for editing a friend's contact details.
"""

import customtkinter as ctk
from tkinter import messagebox
from src.constants import COLORS, font_heading, font_body_bold, font_button


class FriendEditWindow(ctk.CTkToplevel):
    """Modal dialog to edit a friend's name and username."""

    def __init__(self, parent, friend_data: dict, save_callback):
        super().__init__(parent)
        self.title("Edit Friend")
        self.geometry("400x320")
        self.grab_set()

        self._save_callback = save_callback

        ctk.CTkLabel(self, text="Edit Contact Details", font=font_heading()).pack(pady=20)

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(frame, text="Contact Name", font=font_body_bold()).pack(
            pady=(15, 0), anchor="w", padx=20
        )
        self._name_entry = ctk.CTkEntry(frame, width=320, height=38)
        self._name_entry.pack(pady=5)
        self._name_entry.insert(0, friend_data.get('name', ''))

        ctk.CTkLabel(frame, text="Snapchat Username", font=font_body_bold()).pack(
            pady=(10, 0), anchor="w", padx=20
        )
        self._user_entry = ctk.CTkEntry(frame, width=320, height=38)
        self._user_entry.pack(pady=5)
        self._user_entry.insert(0, friend_data.get('username', ''))

        ctk.CTkButton(
            self, text="Update Friend", height=42, font=font_button(),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._save,
        ).pack(pady=20)

    def _save(self):
        new_data = {
            "name": self._name_entry.get().strip(),
            "username": self._user_entry.get().strip(),
        }
        if not new_data["username"]:
            messagebox.showerror("Error", "Username is required.")
            return
        self._save_callback(new_data)
        self.destroy()
