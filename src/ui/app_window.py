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
    font_avatar, font_large_button, font_button,
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

        ctk.set_appearance_mode(self.data.app_settings.get("appearance_mode", "System"))
        self.view_mode = self.data.app_settings.get("view_mode", "Grid")

        # ── Responsive tracking ──
        self._resize_timer = None

        # ── Build UI ──
        self._build_header()
        self._build_friends_list()
        self._build_footer()
        self._build_status_bar()

        # ── Load initial state ──
        self._refresh_profile_ui()

        # ── Bind resize ──
        self.bind("<Configure>", self._on_window_resize)

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
        self._friends_frame = ctk.CTkScrollableFrame(
            self, label_text="My Friends",
            label_font=font_subheading(),
        )
        self._friends_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self._friend_widgets: list[ctk.CTkFrame] = []

    def _refresh_friends_list(self):
        self._friends_frame.configure(
            label_text=f"Friends ({self.data.current_profile_name})"
        )

        # Destroy old widgets
        for w in self._friend_widgets:
            w.destroy()
        self._friend_widgets.clear()

        friends = self.data.get_friends()
        width = self._friends_frame.winfo_width()
        if width <= 1:
            width = 740

        if self.view_mode == "Grid":
            self._render_grid(friends, width)
        else:
            self._render_list(friends)

    def _render_grid(self, friends: list, width: int):
        cols = max(1, width // 210)
        usable_width = width - (cols * 10) - 25
        card_w = max(180, usable_width // cols)

        for i in range(cols):
            self._friends_frame.grid_columnconfigure(i, weight=1)

        for idx, friend in enumerate(friends):
            card = FriendCard(
                self._friends_frame, friend, idx, card_w,
                on_toggle=self._on_friend_toggle,
                on_edit=self._open_edit_friend,
                on_delete=self._delete_friend,
            )
            card.grid(row=idx // cols, column=idx % cols, pady=5, padx=5, sticky="nsew")
            self._friend_widgets.append(card)

    def _render_list(self, friends: list):
        self._friends_frame.grid_columnconfigure(0, weight=1)

        for idx, friend in enumerate(friends):
            row = FriendRow(
                self._friends_frame, friend, idx,
                on_toggle=self._on_friend_toggle,
                on_edit=self._open_edit_friend,
                on_delete=self._delete_friend,
            )
            row.grid(row=idx, column=0, pady=4, padx=5, sticky="ew")
            self._friend_widgets.append(row)

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
            command=self._start_recovery,
        )
        self._recover_btn.pack(fill="x")

    # ═══════════════════════════════════════════════════════════
    #  STATUS BAR
    # ═══════════════════════════════════════════════════════════

    def _build_status_bar(self):
        self._status_bar = StatusBar(self)
        self._status_bar.pack(fill="x", padx=20, pady=(4, 12))

    # ═══════════════════════════════════════════════════════════
    #  RESPONSIVE RESIZE
    # ═══════════════════════════════════════════════════════════

    def _on_window_resize(self, event):
        if event.widget == self and self.view_mode == "Grid":
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, self._check_layout)

    def _check_layout(self):
        if self.data.current_profile_name:
            self._refresh_friends_list()

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

    # ═══════════════════════════════════════════════════════════
    #  FRIEND MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def _on_friend_toggle(self, index: int, selected: bool):
        self.data.toggle_friend(index, selected)

    def _open_edit_friend(self, index: int):
        FriendEditWindow(
            self, self.data.get_friends()[index],
            lambda updated: self._handle_friend_update(index, updated),
        )

    def _handle_friend_update(self, index: int, data: dict):
        self.data.update_friend(index, data)
        self._refresh_friends_list()

    def _delete_friend(self, index: int):
        self.data.delete_friend(index)
        self._refresh_friends_list()

    def _add_friend(self):
        if not self.data.current_profile_name:
            messagebox.showerror("Error", "Please create a profile first.")
            return

        username = self._username_entry.get().strip()
        name = self._name_entry.get().strip()
        if not username:
            return

        if not self.data.add_friend(username, name):
            messagebox.showerror("Error", "Friend already exists in the list.")
            return

        self._refresh_friends_list()
        self._username_entry.delete(0, 'end')
        self._name_entry.delete(0, 'end')

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
