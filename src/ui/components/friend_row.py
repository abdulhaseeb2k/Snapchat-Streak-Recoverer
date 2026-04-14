"""
FriendRow — a self-contained list row widget for a single friend.
Supports hover effects for a premium feel.
"""

import customtkinter as ctk
from src.constants import COLORS, font_body_bold, font_small


class FriendRow(ctk.CTkFrame):
    """A row widget displaying a friend in list view."""

    def __init__(
        self,
        master,
        friend: dict,
        index: int,
        on_toggle,
        on_edit,
        on_delete,
    ):
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=8,
        )
        self._index = index
        self._on_toggle = on_toggle
        self._on_edit = on_edit
        self._on_delete = on_delete

        # ── Hover effect ──
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # ── Left side: info ──
        self._var = ctk.BooleanVar(value=friend.get('selected', False))
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=10)

        display_name = friend.get('name') or friend['username']
        chk = ctk.CTkCheckBox(
            info_frame, text=display_name, variable=self._var,
            font=font_body_bold(),
            command=self._handle_toggle,
        )
        chk.pack(anchor="w")

        if friend.get('name') and friend.get('name') != friend['username']:
            ctk.CTkLabel(
                info_frame, text=f"@{friend['username']}",
                text_color=COLORS["muted_text"], font=font_small(),
            ).pack(anchor="w", padx=30)

        # ── Right side: actions ──
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(side="right", padx=15)

        ctk.CTkButton(
            action_frame, text="✎ Edit", width=65,
            fg_color=COLORS["btn_secondary"],
            hover_color=COLORS["btn_secondary_hover"],
            command=self._handle_edit,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_frame, text="🗑 Delete", width=75,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=self._handle_delete,
        ).pack(side="left", padx=4)

    def _on_enter(self, _event):
        self.configure(fg_color=COLORS["card_hover"])

    def _on_leave(self, _event):
        self.configure(fg_color=COLORS["card_bg"])

    def _handle_toggle(self):
        self._on_toggle(self._index, self._var.get())

    def _handle_edit(self):
        self._on_edit(self._index)

    def _handle_delete(self):
        self._on_delete(self._index)
