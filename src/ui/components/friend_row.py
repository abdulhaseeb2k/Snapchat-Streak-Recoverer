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
        on_open,
    ):
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=8,
        )
        self._index = index
        self._on_toggle = on_toggle
        self._on_open = on_open

        # ── State Tracking (Value Auditing) ──
        display_name = friend.get('name') or friend['username']
        self._last_display_name = display_name
        self._last_uname = None
        self._last_selected = friend.get('selected', False)

        # ── Hover effect ──
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Double-Button-1>", self._handle_open)

        # ── Left side: info ──
        self._selected = friend.get('selected', False)
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=10, fill="x", expand=True)
        info_frame.bind("<Double-Button-1>", self._handle_open)

        title_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_row.pack(fill="x")
        title_row.bind("<Double-Button-1>", self._handle_open)

        self._toggle_label = ctk.CTkLabel(
            title_row,
            text=self._selection_text(),
            width=24,
            font=font_body_bold(),
            text_color=COLORS["accent"] if self._selected else COLORS["muted_text"],
            cursor="hand2",
        )
        self._toggle_label.pack(side="left")
        self._toggle_label.bind("<Button-1>", self._handle_toggle)
        self._toggle_label.bind("<Double-Button-1>", self._handle_open)

        self._name_label = ctk.CTkLabel(
            title_row,
            text=display_name,
            font=font_body_bold(),
            anchor="w",
            justify="left",
        )
        self._name_label.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._name_label.bind("<Button-1>", self._handle_toggle)
        self._name_label.bind("<Double-Button-1>", self._handle_open)

        # Create username label (packed conditionally)
        self._uname_label = ctk.CTkLabel(
            info_frame, text="",
            text_color=COLORS["muted_text"], font=font_small(),
        )
        if friend.get('name') and friend.get('name') != friend['username']:
            uname = f"@{friend['username']}"
            self._uname_label.configure(text=uname)
            self._uname_label.pack(anchor="w", padx=30)
            self._last_uname = uname
        self._uname_label.bind("<Double-Button-1>", self._handle_open)

    def set_selected(self, value: bool):
        """Update the checkbox state without rebuilding the widget."""
        self._selected = value
        self._last_selected = value
        self._apply_selection_visuals()

    def update_data(self, friend: dict, index: int):
        """Update existing row only if data has actually changed."""
        self._index = index
        
        # 1. Check selection
        new_selected = friend.get('selected', False)
        if new_selected != self._last_selected:
            self._selected = new_selected
            self._last_selected = new_selected
            self._apply_selection_visuals()

        # 2. Check name
        display_name = friend.get('name') or friend['username']
        if display_name != self._last_display_name:
            self._name_label.configure(text=display_name)
            self._last_display_name = display_name
        
        # 3. Check username subtitle
        if hasattr(self, '_uname_label'):
            has_name = bool(friend.get('name') and friend.get('name') != friend['username'])
            
            if has_name:
                uname = f"@{friend['username']}"
                if uname != self._last_uname:
                    self._uname_label.configure(text=uname)
                    self._last_uname = uname
                
                if not self._uname_label.winfo_manager():
                    self._uname_label.pack(anchor="w", padx=30)
            else:
                if self._uname_label.winfo_manager():
                    self._uname_label.pack_forget()
                self._last_uname = None

    def _selection_text(self) -> str:
        return "[x]" if self._selected else "[ ]"

    def _apply_selection_visuals(self):
        self._toggle_label.configure(
            text=self._selection_text(),
            text_color=COLORS["accent"] if self._selected else COLORS["muted_text"],
        )

    def _on_enter(self, _event):
        self.configure(fg_color=COLORS["card_hover"])

    def _on_leave(self, _event):
        self.configure(fg_color=COLORS["card_bg"])

    def _handle_toggle(self, _event=None):
        self._selected = not self._selected
        self._last_selected = self._selected
        self._apply_selection_visuals()
        self._on_toggle(self._index, self._selected)

    def _handle_open(self, _event=None):
        self._on_open(self._index)
