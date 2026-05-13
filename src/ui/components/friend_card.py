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
        on_open,
    ):
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=12,
            width=adaptive_width,
            height=126,
        )
        self.pack_propagate(False)

        self._index = index
        self._on_toggle = on_toggle
        self._on_open = on_open

        # ── Hover effect ──
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Double-Button-1>", self._handle_open)

        # ── Selection + title ──
        self._selected = friend.get('selected', False)
        display_name = self._format_display_name(friend, adaptive_width)
        self._last_display_name = display_name
        self._last_uname = None
        self._last_selected = self._selected
        self._last_width = adaptive_width
        self._last_username = friend.get("username", "")

        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(14, 2))
        header_row.bind("<Double-Button-1>", self._handle_open)

        self._toggle_label = ctk.CTkLabel(
            header_row,
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
            header_row,
            text=display_name,
            font=font_body_bold(),
            anchor="w",
            justify="left",
        )
        self._name_label.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._name_label.bind("<Button-1>", self._handle_toggle)
        self._name_label.bind("<Double-Button-1>", self._handle_open)

        # ── Username subtitle ──
        # Create it anyway but only pack if needed
        self._uname_label = ctk.CTkLabel(
            self, text="", text_color=COLORS["muted_text"],
            font=font_tiny(),
        )
        if friend.get('name') and friend.get('name') != friend['username']:
            uname = self._format_username(friend, adaptive_width)
            self._uname_label.configure(text=uname)
            self._uname_label.pack(anchor="w", padx=36)
            self._last_uname = uname
        self._uname_label.bind("<Double-Button-1>", self._handle_open)

    def set_selected(self, value: bool):
        """Update the checkbox state without rebuilding the widget."""
        self._selected = value
        self._last_selected = value
        self._apply_selection_visuals()

    def update_data(self, friend: dict, index: int, adaptive_width: int = None):
        """Update existing card only if data has actually changed."""
        self._index = index
        # Note: width is NOT set here — grid geometry (sticky=nsew) controls actual size.
        
        # 1. Check selection state
        new_selected = friend.get('selected', False)
        if new_selected != self._last_selected:
            self._selected = new_selected
            self._last_selected = new_selected
            self._apply_selection_visuals()

        # 2. Check name
        display_name = self._format_display_name(friend, adaptive_width)

        if display_name != self._last_display_name:
            self._name_label.configure(text=display_name)
            self._last_display_name = display_name

        # 3. Check username subtitle
        if hasattr(self, '_uname_label'):
            has_name = bool(friend.get('name') and friend.get('name') != friend['username'])
            
            if has_name:
                uname = self._format_username(friend, adaptive_width)

                if uname != self._last_uname:
                    self._uname_label.configure(text=uname)
                    self._last_uname = uname
                
                # Only pack if not already visible
                if not self._uname_label.winfo_manager():
                    self._uname_label.pack(anchor="w", padx=36)
            else:
                if self._uname_label.winfo_manager():
                    self._uname_label.pack_forget()
                self._last_uname = None

        self._last_username = friend.get("username", "")

    @staticmethod
    def _format_display_name(friend: dict, adaptive_width: int) -> str:
        display_name = friend.get('name') or friend['username']
        limit = 22
        if len(display_name) > limit:
            return display_name[:limit - 3] + "..."
        return display_name

    @staticmethod
    def _format_username(friend: dict, adaptive_width: int) -> str:
        uname = f"@{friend['username']}"
        if len(uname) > 24:
            return uname[:21] + "..."
        return uname

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
