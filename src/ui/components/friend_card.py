"""
FriendCard — a self-contained grid card widget for a single friend.
Supports hover effects for a premium feel.
"""

import customtkinter as ctk
from src.constants import COLORS, font_body_bold, font_tiny


class FriendCard(ctk.CTkFrame):
    """A card widget displaying a friend in grid view."""

    def __init__(
        self,
        master,
        friend: dict,
        index: int,
        adaptive_width: int,
        on_toggle,
        on_edit,
        on_delete,
    ):
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=12,
            width=adaptive_width,
            height=140,
        )
        self.grid_propagate(False)

        self._index = index
        self._on_toggle = on_toggle
        self._on_edit = on_edit
        self._on_delete = on_delete

        # ── Hover effect ──
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # ── Checkbox ──
        self._var = ctk.BooleanVar(value=friend.get('selected', False))
        display_name = friend.get('name') or friend['username']
        limit = max(10, adaptive_width // 15)
        if len(display_name) > limit:
            display_name = display_name[:limit - 3] + "..."

        chk = ctk.CTkCheckBox(
            self, text=display_name, variable=self._var,
            font=font_body_bold(),
            command=self._handle_toggle,
        )
        chk.pack(pady=(14, 2), padx=12, anchor="w")

        # ── Username subtitle ──
        if friend.get('name') and friend.get('name') != friend['username']:
            uname = f"@{friend['username']}"
            if len(uname) > limit + 3:
                uname = uname[:limit] + "..."
            ctk.CTkLabel(
                self, text=uname, text_color=COLORS["muted_text"],
                font=font_tiny(),
            ).pack(anchor="w", padx=36)

        # ── Action buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=10, padx=10, fill="x")

        ctk.CTkButton(
            btn_frame, text="Edit", height=28,
            width=adaptive_width // 3,
            fg_color=COLORS["btn_secondary"],
            hover_color=COLORS["btn_secondary_hover"],
            command=self._handle_edit,
        ).pack(side="left", expand=True, padx=(0, 3))

        ctk.CTkButton(
            btn_frame, text="Delete", height=28,
            width=adaptive_width // 3,
            fg_color="transparent", border_width=1,
            border_color=COLORS["danger"],
            text_color=COLORS["danger_text"],
            hover_color=COLORS["danger_subtle_bg"],
            command=self._handle_delete,
        ).pack(side="right", expand=True, padx=(3, 0))

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
