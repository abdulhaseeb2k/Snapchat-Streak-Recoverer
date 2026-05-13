"""
StatusBar — a slim progress/status bar at the bottom of the main window.
Shows real-time automation progress instead of popup dialogs.
"""

import customtkinter as ctk
from src.constants import COLORS, font_small


class StatusBar(ctk.CTkFrame):
    """A slim status bar showing app state and automation progress."""

    def __init__(self, master):
        super().__init__(master, height=32, fg_color=COLORS["status_bg"], corner_radius=8)
        self.pack_propagate(False)

        self._label = ctk.CTkLabel(
            self, text="Ready", font=font_small(),
            text_color=COLORS["status_text"],
        )
        self._label.pack(side="left", padx=12)

        self._progress = ctk.CTkProgressBar(
            self, width=150, height=10,
            progress_color=COLORS["status_progress"],
        )
        self._progress.pack(side="right", padx=12, pady=8)
        self._progress.set(0)
        self._progress.pack_forget()  # Hidden by default

    def set_ready(self):
        self._label.configure(text="✅ Ready")
        self._progress.pack_forget()

    def set_processing(self, current: int, total: int, friend: str):
        truncated = friend if len(friend) <= 20 else friend[:17] + "..."
        # Format as [2/10] for better visibility
        self._label.configure(text=f"⏳ [{current+1}/{total}] Processing: {truncated}")
        self._progress.pack(side="right", padx=12, pady=8)
        self._progress.set((current + 1) / total)

    def set_done(self):
        self._label.configure(text="🎉 All friends processed!")
        self._progress.set(1.0)

    def set_error(self, msg: str):
        truncated = msg if len(msg) <= 50 else msg[:47] + "..."
        self._label.configure(text=f"❌ {truncated}")
        self._progress.pack_forget()
