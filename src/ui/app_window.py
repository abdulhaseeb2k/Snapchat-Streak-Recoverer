"""
AppWindow — the main application window.
Handles layout, event wiring, and delegates data to DataManager.
"""

import customtkinter as ctk
from tkinter import messagebox
import asyncio
import threading

from src.constants import (
    APP_NAME, APP_SUBTITLE, COLORS,
    font_title, font_subheading, font_body, font_body_bold,
    font_avatar, font_large_button, font_button, font_tiny,
    font_small, APP_ICON_PATH,
)
from src.core.data_manager import DataManager
from src.automation.recovery import run_recovery

from src.ui.components.friend_card import FriendCard
from src.ui.components.friend_row import FriendRow
from src.ui.components.status_bar import StatusBar

from src.ui.dialogs.profile_menu import ProfileMenu
from src.ui.dialogs.profile_details import ProfileDetailsWindow
from src.ui.dialogs.friend_edit import FriendEditWindow
from src.ui.dialogs.app_settings import AppSettingsWindow


class AppWindow(ctk.CTk):
    """Main application window."""

    def __init__(self, data: DataManager):
        super().__init__()
        self.data = data

        # ── Window setup ──
        self.title(APP_NAME)
        self.geometry("780x680")
        self.minsize(660, 560)
        
        import os
        if os.path.exists(APP_ICON_PATH):
            self.iconbitmap(APP_ICON_PATH)

        ctk.set_appearance_mode(self.data.app_settings.get("appearance_mode", "System"))
        self.view_mode = self.data.app_settings.get("view_mode", "Grid")

        # ── Responsive tracking ──
        self._resize_timer = None
        self._current_cols = 0
        self._current_card_w = 0
        self._last_layout_width = 0
        self._save_timer = None
        self._search_query = ""

        # ── Build UI ──
        self._build_header()
        self._build_friends_list()
        self._build_footer()
        self._build_status_bar()

        # ── Build initial state ──
        self.update_idletasks()
        self._refresh_profile_ui()

        # ── Bind resize ──
        self.bind("<Configure>", self._on_window_resize)
        self.after(0, self._ensure_window_visible)

    # ═══════════════════════════════════════════════════════════
    #  HEADER
    # ═══════════════════════════════════════════════════════════

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        # Title
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_box, text=APP_NAME, font=font_title(),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box, text=APP_SUBTITLE, font=font_subheading(),
            text_color=COLORS["muted_text"],
        ).pack(anchor="w")

        # Profile avatar button
        self._profile_btn = ctk.CTkButton(
            header, text="", width=48, height=48, corner_radius=24,
            font=font_avatar(),
            fg_color=COLORS["avatar"], hover_color=COLORS["avatar_hover"],
            command=self._open_profile_menu,
        )
        self._profile_btn.grid(row=0, column=1, padx=(10, 6), sticky="e")

        # Settings button
        ctk.CTkButton(
            header, text="⚙ Settings", width=110, height=42,
            font=font_button(),
            command=self._open_app_settings,
        ).grid(row=0, column=2, padx=5, sticky="e")

    # ═══════════════════════════════════════════════════════════
    #  FRIENDS LIST
    # ═══════════════════════════════════════════════════════════

    def _build_friends_list(self):
        # ── Selection Controls Row (Professional Header) ──
        self._controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._controls_frame.pack(fill="x", padx=25, pady=(8, 0))

        # Left: Selection Counter
        self._sel_count_var = ctk.StringVar(value="0 Selected")
        self._sel_count_label = ctk.CTkLabel(
            self._controls_frame, textvariable=self._sel_count_var,
            font=font_tiny(), text_color=COLORS["muted_text"],
        )
        self._sel_count_label.pack(side="left")

        # Center: Search Bar
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)
        self._search_entry = ctk.CTkEntry(
            self._controls_frame, 
            placeholder_text="🔍 Search friends...",
            textvariable=self._search_var,
            width=220, height=30,
            font=font_small(),
            fg_color=COLORS["surface"],
            border_color=COLORS["separator"],
        )
        self._search_entry.pack(side="left", padx=15)

        # Right: Aesthetic Icon Buttons
        btn_box = ctk.CTkFrame(self._controls_frame, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box, text="✓", width=32, height=32, 
            font=font_body_bold(),
            fg_color="transparent", border_width=1,
            border_color=COLORS["accent"], text_color=COLORS["accent"],
            hover_color=COLORS["danger_subtle_bg"], # Using subtle bg from colors
            command=lambda: self._bulk_select_friends(True),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box, text="✕", width=32, height=32, 
            font=font_body_bold(),
            fg_color="transparent", border_width=1,
            border_color=COLORS["danger"], text_color=COLORS["danger"],
            hover_color=COLORS["danger_subtle_bg"],
            command=lambda: self._bulk_select_friends(False),
        ).pack(side="left", padx=4)

        # ── Scrollable List ──
        self._friends_frame = ctk.CTkScrollableFrame(
            self, label_text="My Friends",
            label_font=font_subheading(),
        )
        self._friends_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        self._friend_widgets: list[ctk.CTkFrame] = []
        self._frame_label_cache: str = "My Friends"  # Avoid redundant label redraws

    def _on_search_change(self, *args):
        """Callback when the search query changes."""
        self._search_query = self._search_var.get().lower().strip()
        self._refresh_friends_list()

    def _update_selection_counter(self, filtered_count: int = None):
        """Update the label showing how many friends are selected."""
        selected_count = self.data.get_selected_friend_count()
        total = len(self.data.get_friends())
        
        text = f"{selected_count} / {total} Selected"
        if filtered_count is not None and filtered_count != total:
            text += f" ({filtered_count} matching)"
            
        self._sel_count_var.set(text)

    def _set_frame_label(self, text: str):
        """Only update frame label text when it has actually changed — avoids costly CTk redraws."""
        if text != self._frame_label_cache:
            self._friends_frame.configure(label_text=text)
            self._frame_label_cache = text

    def _refresh_friends_list(self):
        label = f"Friends ({self.data.current_profile_name})" if self.data.current_profile_name else "My Friends"
        self._set_frame_label(label)

        all_friends = self.data.get_friends()
        
        # Filter if search query exists
        if self._search_query:
            indexed_friends = [
                (i, f) for i, f in enumerate(all_friends)
                if self._search_query in f.get('username', '').lower() or 
                   self._search_query in f.get('name', '').lower()
            ]
        else:
            indexed_friends = list(enumerate(all_friends))

        self._update_selection_counter(len(indexed_friends))

        width = self._friends_frame.winfo_width()
        if width <= 1:
            width = 740

        # Check if we need to purge widgets due to view mode change
        is_grid = (self.view_mode == "Grid")
        needs_purge = False
        if self._friend_widgets:
            first_w = self._friend_widgets[0]
            current_is_grid = isinstance(first_w, FriendCard)
            if current_is_grid != is_grid:
                needs_purge = True

        if needs_purge:
            for w in self._friend_widgets:
                w.destroy()
            self._friend_widgets.clear()

        if is_grid:
            self._render_grid(indexed_friends, width)
        else:
            self._render_list(indexed_friends)

    def _render_grid(self, indexed_friends: list[tuple[int, dict]], width: int):
        cols, card_w = self._get_grid_metrics(width)

        self._configure_grid_columns(cols)

        # 1. Sync widgets count
        while len(self._friend_widgets) > len(indexed_friends):
            self._friend_widgets.pop().destroy()

        widgets_to_position: list[tuple[ctk.CTkFrame, tuple[int, int]]] = []

        # 2. Update existing or create new
        for display_idx, (original_idx, friend) in enumerate(indexed_friends):
            if display_idx < len(self._friend_widgets):
                # Reuse
                widget = self._friend_widgets[display_idx]
                widget.update_data(friend, original_idx, card_w)
            else:
                # Create
                widget = FriendCard(
                    self._friends_frame, friend, original_idx, card_w,
                    on_toggle=self._on_friend_toggle,
                    on_open=self._open_edit_friend,
                )
                self._friend_widgets.append(widget)

            new_pos = (display_idx // cols, display_idx % cols)
            widgets_to_position.append((widget, new_pos))

        # 3. Lay out widgets only after they are all updated
        for widget, new_pos in widgets_to_position:
            if getattr(widget, '_last_pos', None) != new_pos:
                widget.grid(
                    row=new_pos[0], column=new_pos[1], 
                    pady=5, padx=5, sticky="nsew"
                )
                widget._last_pos = new_pos

        self._current_cols = cols
        self._current_card_w = card_w
        self._last_layout_width = width

    def _render_list(self, indexed_friends: list[tuple[int, dict]]):
        self._friends_frame.grid_columnconfigure(0, weight=1)

        # 1. Sync widgets count
        while len(self._friend_widgets) > len(indexed_friends):
            self._friend_widgets.pop().destroy()

        widgets_to_position: list[tuple[ctk.CTkFrame, tuple[int, int]]] = []

        # 2. Update existing or create new
        for display_idx, (original_idx, friend) in enumerate(indexed_friends):
            if display_idx < len(self._friend_widgets):
                # Reuse
                widget = self._friend_widgets[display_idx]
                widget.update_data(friend, original_idx)
            else:
                # Create
                widget = FriendRow(
                    self._friends_frame, friend, original_idx,
                    on_toggle=self._on_friend_toggle,
                    on_open=self._open_edit_friend,
                )
                self._friend_widgets.append(widget)

            new_pos = (display_idx, 0)
            widgets_to_position.append((widget, new_pos))

        # 3. Lay out widgets only after they are all updated
        for widget, new_pos in widgets_to_position:
            if getattr(widget, '_last_pos', None) != new_pos:
                widget.grid(row=new_pos[0], column=0, pady=4, padx=5, sticky="ew")
                widget._last_pos = new_pos

    # ═══════════════════════════════════════════════════════════
    #  FOOTER (Add Friend + Recover Button)
    # ═══════════════════════════════════════════════════════════

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(10, 8))

        # Add friend row
        add_frame = ctk.CTkFrame(footer)
        add_frame.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        inner.pack(pady=12)

        self._name_entry = ctk.CTkEntry(
            inner, placeholder_text="Contact Name (e.g. Ali)",
            width=200, height=38,
        )
        self._name_entry.pack(side="left", padx=8)

        self._username_entry = ctk.CTkEntry(
            inner, placeholder_text="Friend Username",
            width=200, height=38,
        )
        self._username_entry.pack(side="left", padx=8)

        ctk.CTkButton(
            inner, text="+ Add Friend", height=38,
            font=font_body_bold(),
            command=self._add_friend,
        ).pack(side="left", padx=8)

        # Recover button
        self._recover_btn = ctk.CTkButton(
            footer, text="🚀 RECOVER SELECTED STREAKS",
            height=52, font=font_large_button(),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._start_recovery, state="disabled",
        )
        self._recover_btn.pack(fill="x")

    # ═══════════════════════════════════════════════════════════
    #  STATUS BAR
    # ═══════════════════════════════════════════════════════════

    def _build_status_bar(self):
        self._status_bar = StatusBar(self)
        self._status_bar.pack(fill="x", padx=20, pady=(4, 12))

    def _ensure_window_visible(self):
        try:
            self.deiconify()
        except Exception:
            pass

        try:
            self.lift()
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════
    #  RESPONSIVE RESIZE
    # ═══════════════════════════════════════════════════════════

    def _on_window_resize(self, event):
        if event.widget != self or self.view_mode != "Grid":
            return

        if self.state() == "iconic":
            return

        if self._resize_timer:
            self.after_cancel(self._resize_timer)

        delay_ms = 140 if self.state() == "zoomed" else 60
        self._resize_timer = self.after(delay_ms, self._check_layout)

    def _check_layout(self):
        self._resize_timer = None
        if not self.data.current_profile_name or self.view_mode != "Grid":
            return
        width = self._friends_frame.winfo_width()
        if width <= 1:
            return

        friends = self.data.get_friends()
        cols, card_w = self._get_grid_metrics(width)

        # If widget pool is out of sync with data, do a full refresh
        has_wrong_types = any(not isinstance(w, FriendCard) for w in self._friend_widgets)
        if len(friends) != len(self._friend_widgets) or has_wrong_types:
            self._refresh_friends_list()
            return

        # Only re-layout if column count changed OR card width changed
        if cols != self._current_cols or card_w != self._current_card_w:
            self._relayout_grid(friends, cols, card_w, width)

    def _get_grid_metrics(self, width: int) -> tuple[int, int]:
        cols = max(1, width // 210)
        usable_width = width - (cols * 10) - 25
        card_w = max(180, usable_width // cols)
        return cols, card_w

    def _configure_grid_columns(self, cols: int):
        previous_cols = self._current_cols or cols
        for i in range(max(previous_cols, cols)):
            self._friends_frame.grid_columnconfigure(i, weight=1 if i < cols else 0)

    def _relayout_grid(self, friends: list, cols: int, card_w: int, width: int):
        """Reposition cards in the grid. Does NOT update widget data — resize doesn't change friend data."""
        self._configure_grid_columns(cols)

        for idx, widget in enumerate(self._friend_widgets):
            new_pos = (idx // cols, idx % cols)
            if getattr(widget, "_last_pos", None) != new_pos:
                widget.grid(row=new_pos[0], column=new_pos[1], pady=5, padx=5, sticky="nsew")
                widget._last_pos = new_pos

        self._current_cols = cols
        self._current_card_w = card_w
        self._last_layout_width = width

    def _queue_profiles_save(self, delay_ms: int = 300):
        if self._save_timer:
            self.after_cancel(self._save_timer)
        self._save_timer = self.after(delay_ms, self._flush_profiles_save)

    def _flush_profiles_save(self):
        self._save_timer = None
        self.data.save_profiles_async()

    # ═══════════════════════════════════════════════════════════
    #  PROFILE MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def _refresh_profile_ui(self):
        if not self.data.current_profile_name:
            self._profile_btn.configure(text="+")
            self._friends_frame.configure(label_text="No Profile Selected")
            for w in self._friend_widgets:
                w.destroy()
            self._friend_widgets.clear()
            self._recover_btn.configure(state="disabled")
            return

        letter = self.data.current_profile_name[0].upper()
        self._profile_btn.configure(text=letter)
        self._recover_btn.configure(state="normal")
        self._refresh_friends_list()

    def _open_profile_menu(self):
        ProfileMenu(
            self, self.data.profiles, self.data.current_profile_name,
            on_switch=self._switch_profile,
            on_edit=self._edit_profile,
            on_add_new=self._add_new_profile,
            on_export=self._export_profile,
            on_import=self._import_profile,
        )

    def _switch_profile(self, name):
        self.data.switch_profile(name)
        self._refresh_profile_ui()

    def _edit_profile(self, name):
        ProfileDetailsWindow(
            self, self.data.profiles[name]["settings"],
            save_callback=lambda s: self._save_profile(name, s),
            profile_name=name,
            delete_callback=lambda: self._delete_profile(name),
        )

    def _save_profile(self, name, new_settings):
        self.data.update_profile_settings(name, new_settings)
        self._refresh_profile_ui()

    def _delete_profile(self, name):
        self.data.delete_profile(name)
        self._refresh_profile_ui()

    def _add_new_profile(self):
        ProfileDetailsWindow(
            self, {}, self._finalize_new_profile, is_new=True,
        )

    def _finalize_new_profile(self, details: dict):
        name = details.get("_profile_name_", "").strip()
        if not name:
            messagebox.showerror("Error", "Account name is required.")
            return False
        if name in self.data.profiles:
            messagebox.showerror("Error", "A profile with this name already exists.")
            return False

        details.pop("_profile_name_")
        self.data.add_profile(name, details)
        self.data.switch_profile(name)
        self._refresh_profile_ui()
        return True

    def _export_profile(self, profile_names: list[str]):
        default_name = "multiple_profiles" if len(profile_names) > 1 else profile_names[0]
        filepath = ctk.filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=f"{default_name}_export.json",
            title="Export Profile(s)",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            success = self.data.export_profiles(profile_names, filepath)
            if success:
                messagebox.showinfo("Export Successful", f"Successfully exported {len(profile_names)} profile(s).")
            else:
                messagebox.showerror("Export Failed", "Could not export profiles.")

    def _import_profile(self):
        filepath = ctk.filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            success, msg = self.data.import_profiles(filepath)
            if success:
                messagebox.showinfo("Import Successful", msg)
                self._refresh_profile_ui()
            else:
                messagebox.showerror("Import Failed", msg)

    def _bulk_select_friends(self, selected: bool):
        """Toggle all friends in the current (possibly filtered) list instantly."""
        all_friends = self.data.get_friends()
        if not all_friends:
            return

        # 1. Update internal data (respect search filter)
        for f in all_friends:
            matches_search = not self._search_query or (
                self._search_query in f.get('username', '').lower() or 
                self._search_query in f.get('name', '').lower()
            )
            if matches_search:
                f['selected'] = selected
        
        # 2. Update existing UI widgets directly (No Rebuild!)
        # self._friend_widgets always contains the currently displayed (filtered) widgets
        for widget in self._friend_widgets:
            if hasattr(widget, 'set_selected'):
                widget.set_selected(selected)

        # 3. Update counter and save
        self._update_selection_counter()

        self._queue_profiles_save(500)

    # ═══════════════════════════════════════════════════════════
    #  FRIEND MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def _on_friend_toggle(self, index: int, selected: bool):
        # Update in-memory immediately, debounce disk write
        friends = self.data.get_friends()
        if 0 <= index < len(friends):
            friends[index]['selected'] = selected
        
        self._update_selection_counter()

        # Debounce save to avoid blocking UI on rapid clicks
        self._queue_profiles_save(500)

    def _open_edit_friend(self, index: int):
        FriendEditWindow(
            self, self.data.get_friends()[index],
            lambda updated: self._handle_friend_update(index, updated),
            delete_callback=lambda: self._delete_friend(index),
        )

    def _handle_friend_update(self, index: int, data: dict):
        username = data.get("username", "").strip()
        if any(
            friend["username"].lower() == username.lower() and idx != index
            for idx, friend in enumerate(self.data.get_friends())
        ):
            messagebox.showerror("Error", "Username already exists in the list.")
            return False

        self.data.update_friend(index, data, save=False)
        # Only update the single affected widget, not the whole list
        if 0 <= index < len(self._friend_widgets):
            friend = self.data.get_friends()[index]
            width = self._friends_frame.winfo_width() or 740
            cols, card_w = self._get_grid_metrics(width)
            self._friend_widgets[index].update_data(friend, index, card_w)
        self._queue_profiles_save()
        return True

    def _delete_friend(self, index: int):
        self.data.delete_friend(index, save=False)
        # Surgical remove: destroy one widget, re-index the rest cheaply
        if 0 <= index < len(self._friend_widgets):
            self._friend_widgets[index].destroy()
            self._friend_widgets.pop(index)
            # Re-index remaining widgets and reposition
            friends = self.data.get_friends()
            width = self._friends_frame.winfo_width() or 740
            is_grid = self.view_mode == "Grid"
            if is_grid:
                cols, _ = self._get_grid_metrics(width)
                self._configure_grid_columns(cols)
                for idx in range(index, len(self._friend_widgets)):
                    self._friend_widgets[idx]._index = idx
                    new_pos = (idx // cols, idx % cols)
                    self._friend_widgets[idx].grid(row=new_pos[0], column=new_pos[1], pady=5, padx=5, sticky="nsew")
                    self._friend_widgets[idx]._last_pos = new_pos
            else:
                for idx in range(index, len(self._friend_widgets)):
                    self._friend_widgets[idx]._index = idx
                    new_pos = (idx, 0)
                    self._friend_widgets[idx].grid(row=idx, column=0, pady=4, padx=5, sticky="ew")
                    self._friend_widgets[idx]._last_pos = new_pos
        self._update_selection_counter()
        self._queue_profiles_save()

    def _add_friend(self):
        if not self.data.current_profile_name:
            messagebox.showerror("Error", "Please create a profile first.")
            return

        username = self._username_entry.get().strip()
        name = self._name_entry.get().strip()
        if not username:
            return

        if not self.data.add_friend(username, name, save=False):
            messagebox.showerror("Error", "Friend already exists in the list.")
            return

        # Surgical add: create one new widget without refreshing the whole list
        friends = self.data.get_friends()
        idx = len(friends) - 1
        friend = friends[idx]
        width = self._friends_frame.winfo_width() or 740
        is_grid = self.view_mode == "Grid"

        if is_grid:
            cols, card_w = self._get_grid_metrics(width)
            self._configure_grid_columns(cols)
            widget = FriendCard(
                self._friends_frame, friend, idx, card_w,
                on_toggle=self._on_friend_toggle,
                on_open=self._open_edit_friend,
            )
            new_pos = (idx // cols, idx % cols)
            widget.grid(row=new_pos[0], column=new_pos[1], pady=5, padx=5, sticky="nsew")
            widget._last_pos = new_pos
        else:
            widget = FriendRow(
                self._friends_frame, friend, idx,
                on_toggle=self._on_friend_toggle,
                on_open=self._open_edit_friend,
            )
            widget.grid(row=idx, column=0, pady=4, padx=5, sticky="ew")
            widget._last_pos = (idx, 0)

        self._friend_widgets.append(widget)
        self._update_selection_counter()
        self._username_entry.delete(0, 'end')
        self._name_entry.delete(0, 'end')
        self._queue_profiles_save()

    # ═══════════════════════════════════════════════════════════
    #  APP SETTINGS
    # ═══════════════════════════════════════════════════════════

    def _open_app_settings(self):
        AppSettingsWindow(self, self.data.app_settings, self._save_app_settings)

    def _save_app_settings(self, new_settings: dict):
        old_view = self.data.app_settings.get("view_mode")
        self.data.app_settings = new_settings
        self.data.save_app_settings()

        ctk.set_appearance_mode(new_settings.get("appearance_mode", "System"))
        self.view_mode = new_settings.get("view_mode", "Grid")

        if old_view != self.view_mode:
            self._refresh_friends_list()

        messagebox.showinfo("Settings", "App settings saved successfully!")

    # ═══════════════════════════════════════════════════════════
    #  RECOVERY AUTOMATION
    # ═══════════════════════════════════════════════════════════

    def _start_recovery(self):
        selected = self.data.get_selected_friends()
        if not selected:
            messagebox.showwarning("Warning", "No friends selected for recovery.")
            return

        settings = self.data.get_current_settings()
        if not all([settings.get('username'), settings.get('email')]):
            messagebox.showwarning(
                "Warning",
                "Please complete your account details via Profile > Edit."
            )
            return

        self._recover_btn.configure(state="disabled", text="⏳ Running...")
        self._status_bar.set_processing(0, len(selected), selected[0])

        thread = threading.Thread(
            target=self._run_automation,
            args=(settings, selected, dict(self.data.app_settings)),
            daemon=True,
        )
        thread.start()

    def _run_automation(self, settings, friends, app_settings):
        def on_progress(idx, total, friend):
            self.after(0, self._status_bar.set_processing, idx, total, friend)

        def on_complete():
            self.after(0, self._on_automation_done)

        def on_error(msg):
            self.after(0, self._on_automation_error, msg)

        asyncio.run(run_recovery(
            settings, friends, app_settings,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
        ))

        # Fallback if callbacks weren't triggered
        self.after(0, self._on_automation_done)

    def _on_automation_done(self):
        self._recover_btn.configure(
            state="normal", text="🚀 RECOVER SELECTED STREAKS"
        )
        self._status_bar.set_done()

    def _on_automation_error(self, msg):
        self._recover_btn.configure(
            state="normal", text="🚀 RECOVER SELECTED STREAKS"
        )
        self._status_bar.set_error(msg)
        messagebox.showerror("Automation Error", msg)
