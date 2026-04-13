import customtkinter as ctk
import json
import os
from tkinter import messagebox
from automation import run_recovery
import asyncio
import threading
import webbrowser

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PROFILES_FILE = os.path.join(DATA_DIR, 'profiles.json')
APP_SETTINGS_FILE = os.path.join(DATA_DIR, 'app_settings.json')

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Snapchat Streak Recoverer")
        self.geometry("750x650")
        self.minsize(650, 550)
        
        self.ensure_files()
        
        # Load App Global Settings
        self.app_settings = self.load_json(APP_SETTINGS_FILE, {
            "appearance_mode": "System", 
            "view_mode": "Grid"
        })
        ctk.set_appearance_mode(self.app_settings.get("appearance_mode", "System"))
        self.view_mode = self.app_settings.get("view_mode", "Grid")
        
        # Responsive tracking
        self.current_cols = 0
        self.resize_timer = None
        
        # Build UI structure
        self.build_header()
        self.build_friends_list()
        self.build_footer()
        
        # Load Data and State
        self.refresh_profile_ui()
        
        # Bind resize event for responsive grid
        self.bind("<Configure>", self.on_window_resize)

    def ensure_files(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        self.profiles = {}
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, 'r') as f:
                    self.profiles = json.load(f)
            except Exception:
                pass
                
        # Migration from old format
        OLD_SETTINGS = os.path.join(DATA_DIR, 'settings.json')
        OLD_FRIENDS = os.path.join(DATA_DIR, 'friends.json')
        if not self.profiles:
            old_settings = {"username": "", "email": "", "mobile_number": "", "device": "", "refresh_delay": 1.0}
            old_friends = []
            if os.path.exists(OLD_SETTINGS):
                try:
                    with open(OLD_SETTINGS, 'r') as f:
                        old_settings.update(json.load(f))
                except: pass
            if os.path.exists(OLD_FRIENDS):
                try:
                    with open(OLD_FRIENDS, 'r') as f:
                        old_friends = json.load(f)
                except: pass
                
            self.profiles = {
                "Profile 1": {
                    "settings": old_settings,
                    "friends": old_friends
                }
            }
            self.save_profiles()
            
        self.current_profile_name = list(self.profiles.keys())[0] if self.profiles else None

    def load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return default

    def save_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def save_profiles(self):
        self.save_json(PROFILES_FILE, self.profiles)

    @property
    def settings(self):
        if not self.current_profile_name: return {}
        return self.profiles[self.current_profile_name]["settings"]

    @settings.setter
    def settings(self, val):
        if not self.current_profile_name: return
        self.profiles[self.current_profile_name]["settings"] = val
        self.save_profiles()

    @property
    def friends(self):
        if not self.current_profile_name: return []
        return self.profiles[self.current_profile_name]["friends"]

    def save_friends(self):
        self.save_profiles()

    def build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_box, text="Snapchat Streak Recoverer", font=ctk.CTkFont(family="Inter", size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Automated Support Form Submitter", font=ctk.CTkFont(family="Inter", size=14), text_color="gray").pack(anchor="w")
        
        self.profile_btn = ctk.CTkButton(header_frame, text="", width=45, height=45, corner_radius=22, 
                                         font=ctk.CTkFont(size=20, weight="bold"), 
                                         fg_color="#db4437", hover_color="#c33d31", 
                                         command=self.open_profile_menu)
        self.profile_btn.grid(row=0, column=1, padx=(10, 5), sticky="e")
        
        settings_btn = ctk.CTkButton(header_frame, text="⚙ App Settings", width=120, height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.open_app_settings)
        settings_btn.grid(row=0, column=2, padx=5, sticky="e")

    def on_window_resize(self, event):
        if event.widget == self and self.view_mode == "Grid":
            if self.resize_timer:
                self.after_cancel(self.resize_timer)
            self.resize_timer = self.after(200, self.check_layout_update)

    def check_layout_update(self):
        if not self.current_profile_name: return
        width = self.friends_frame.winfo_width()
        new_cols = max(1, width // 200)
        # We always refresh in Grid mode now to ensure adaptive sizing works
        self.refresh_friends_list()

    def open_profile_menu(self):
        menu = ctk.CTkToplevel(self)
        menu.title("Switch Profile")
        menu.geometry("350x400")
        menu.grab_set()
        
        ctk.CTkLabel(menu, text="Accounts", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        scroll = ctk.CTkScrollableFrame(menu, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        for p_name in self.profiles.keys():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            btn_color = "darkgreen" if p_name == self.current_profile_name else ["#3B8ED0", "#1F6AA5"]
            btn = ctk.CTkButton(row, text=p_name, fg_color=btn_color, height=35, anchor="w",
                                command=lambda name=p_name, m=menu: self.switch_profile(name, m))
            btn.pack(side="left", expand=True, fill="x", padx=(5, 5))
            
            edit_btn = ctk.CTkButton(row, text="✎ Edit", width=60, height=35, fg_color="gray30", hover_color="gray40", font=ctk.CTkFont(size=12),
                                     command=lambda name=p_name: self.edit_profile_details(name))
            edit_btn.pack(side="right", padx=(0, 5))
            
        tk_sep = ctk.CTkFrame(menu, height=2, fg_color="gray")
        tk_sep.pack(fill="x", pady=10, padx=20)
        
        add_btn = ctk.CTkButton(menu, text="+ Add New Account", fg_color="#10A37F", hover_color="#0D8A6B", height=40,
                                font=ctk.CTkFont(weight="bold"), command=lambda m=menu: self.add_new_profile_dialog(m))
        add_btn.pack(pady=15, padx=20, fill="x")

    def switch_profile(self, name, menu_window):
        self.current_profile_name = name
        self.refresh_profile_ui()
        menu_window.destroy()

    def edit_profile_details(self, name):
        ProfileDetailsWindow(self, self.profiles[name]["settings"], lambda settings: self.save_profile_details(name, settings), name, lambda: self.delete_profile(name))

    def save_profile_details(self, name, new_settings):
        self.profiles[name]["settings"] = new_settings
        self.save_profiles()
        self.refresh_profile_ui()

    def add_new_profile_dialog(self, menu_window):
        menu_window.destroy()
        ProfileDetailsWindow(self, {}, self.finalize_new_profile, is_new=True)

    def finalize_new_profile(self, details_dict):
        name = details_dict.get("_profile_name_").strip()
        if not name:
            messagebox.showerror("Error", "Account/Profile name is required.")
            return False
            
        if name in self.profiles:
            messagebox.showerror("Error", "A profile with this name already exists.")
            return False
            
        profile_name = details_dict.pop("_profile_name_")
        self.profiles[profile_name] = {
            "settings": details_dict,
            "friends": []
        }
        self.save_profiles()
        self.current_profile_name = profile_name
        self.refresh_profile_ui()
        return True

    def refresh_profile_ui(self):
        if not self.current_profile_name:
            self.profile_btn.configure(text="+")
            self.friends_frame.configure(label_text="No Profile Selected")
            for row_frame in self.friend_checkboxes:
                row_frame.destroy()
            self.friend_checkboxes.clear()
            self.recover_btn.configure(state="disabled")
            return
            
        first_letter = self.current_profile_name[0].upper() if self.current_profile_name else "?"
        self.profile_btn.configure(text=first_letter)
        self.recover_btn.configure(state="normal")
        self.refresh_friends_list()

    def build_friends_list(self):
        self.friends_frame = ctk.CTkScrollableFrame(self, label_text="My Friends", label_font=ctk.CTkFont(size=14, weight="bold"))
        self.friends_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.friend_checkboxes = []

    def refresh_friends_list(self):
        self.friends_frame.configure(label_text=f"Friends ({self.current_profile_name})")
        for row_frame in self.friend_checkboxes:
            row_frame.destroy()
        self.friend_checkboxes.clear()
        
        width = self.friends_frame.winfo_width()
        if width <= 1: width = 710 # Initial fallback
        
        if self.view_mode == "Grid":
            # Adaptive Grid Logic: 
            # Calculate columns based on width, then divide space EQUALLY.
            cols = max(1, width // 210)
            self.current_cols = cols
            
            # Account for scrollbar and gaps
            usable_width = width - (cols * 10) - 25
            card_w = max(180, usable_width // cols)
            
            for i in range(cols):
                self.friends_frame.grid_columnconfigure(i, weight=1)
                
            for index, friend in enumerate(self.friends):
                row = index // cols
                col = index % cols
                self.add_friend_card(friend, index, row, col, card_w)
        else:
            self.friends_frame.grid_columnconfigure(0, weight=1)
            for index, friend in enumerate(self.friends):
                self.add_friend_list_row(friend, index)

    def add_friend_list_row(self, friend, index):
        row_frame = ctk.CTkFrame(self.friends_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        row_frame.grid(row=index, column=0, pady=5, padx=5, sticky="ew")
        
        var = ctk.BooleanVar(value=friend.get('selected', False))
        
        info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=8)
        
        display_name = friend.get('name') if friend.get('name') else friend['username']
        chk = ctk.CTkCheckBox(info_frame, text=display_name, variable=var, font=ctk.CTkFont(size=15, weight="bold"),
                              command=lambda v=var, idx=index: self.on_friend_toggle(idx, v))
        chk.pack(anchor="w")
        
        if friend.get('name') and friend.get('name') != friend['username']:
            ctk.CTkLabel(info_frame, text=f"@{friend['username']}", text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30)
            
        action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=15)
        
        edit_btn = ctk.CTkButton(action_frame, text="✎ Edit", width=60, fg_color="gray30", hover_color="gray40",
                                command=lambda idx=index: self.open_edit_friend(idx))
        edit_btn.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(action_frame, text="🗑 Delete", width=60, fg_color="#ff4d4d", hover_color="#cc0000",
                                command=lambda idx=index: self.delete_friend(idx))
        del_btn.pack(side="left", padx=5)
        
        self.friend_checkboxes.append(row_frame)

    def add_friend_card(self, friend, index, r, c, adaptive_width):
        # The card width is now passed dynamically to fill the screen gaps
        card = ctk.CTkFrame(self.friends_frame, fg_color=("gray85", "gray20"), corner_radius=10, width=adaptive_width, height=135)
        card.grid(row=r, column=c, pady=5, padx=5, sticky="nsew") 
        card.grid_propagate(False) 
        
        var = ctk.BooleanVar(value=friend.get('selected', False))
        
        display_name = friend.get('name') if friend.get('name') else friend['username']
        # Truncate if it's too long for the current adaptive width
        limit = max(10, adaptive_width // 15)
        if len(display_name) > limit: display_name = display_name[:limit-3] + "..."
        
        chk = ctk.CTkCheckBox(card, text=display_name, variable=var, font=ctk.CTkFont(size=14, weight="bold"),
                              command=lambda v=var, idx=index: self.on_friend_toggle(idx, v))
        chk.pack(pady=(12, 2), padx=10, anchor="w")
        
        if friend.get('name') and friend.get('name') != friend['username']:
            uname = f"@{friend['username']}"
            if len(uname) > limit + 3: uname = uname[:limit] + "..."
            ctk.CTkLabel(card, text=uname, text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=35)
            
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=10, padx=10, fill="x")
        
        edit_btn = ctk.CTkButton(btn_frame, text="Edit", height=28, width=adaptive_width//3, fg_color="gray30", hover_color="gray40", 
                                command=lambda idx=index: self.open_edit_friend(idx))
        edit_btn.pack(side="left", expand=True, padx=(0, 2))

        del_btn = ctk.CTkButton(btn_frame, text="Delete", height=28, width=adaptive_width//3, fg_color="transparent", border_width=1, 
                                border_color="#ff4d4d", text_color="#ff4d4d", hover_color=("#fee2e2", "#450a0a"),
                                command=lambda idx=index: self.delete_friend(idx))
        del_btn.pack(side="right", expand=True, padx=(2, 0))
        
        self.friend_checkboxes.append(card)

    def on_friend_toggle(self, index, var):
        self.friends[index]['selected'] = var.get()
        self.save_friends()

    def open_edit_friend(self, index):
        FriendEditWindow(self, self.friends[index], lambda updated: self.handle_friend_update(index, updated))

    def handle_friend_update(self, index, updated_data):
        self.friends[index].update(updated_data)
        self.save_friends()
        self.refresh_friends_list()

    def delete_friend(self, index):
        del self.friends[index]
        self.save_friends()
        self.refresh_friends_list()

    def build_footer(self):
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        add_frame = ctk.CTkFrame(footer_frame)
        add_frame.pack(fill="x", pady=(0, 15))
        
        inner_add = ctk.CTkFrame(add_frame, fg_color="transparent")
        inner_add.pack(pady=15)
        
        self.new_friend_name_entry = ctk.CTkEntry(inner_add, placeholder_text="Contact Name (e.g. Ali)", width=200, height=35)
        self.new_friend_name_entry.pack(side="left", padx=10)

        self.new_friend_entry = ctk.CTkEntry(inner_add, placeholder_text="Friend Username", width=200, height=35)
        self.new_friend_entry.pack(side="left", padx=10)
        
        add_btn = ctk.CTkButton(inner_add, text="+ Add Friend", height=35, command=self.add_friend)
        add_btn.pack(side="left", padx=10)
        
        self.recover_btn = ctk.CTkButton(footer_frame, text="🚀 RECOVER SELECTED STREAKS", 
                                    height=50, font=ctk.CTkFont(size=16, weight="bold"),
                                    fg_color="#10A37F", hover_color="#0D8A6B", command=self.start_recovery)
        self.recover_btn.pack(fill="x")

    def add_friend(self):
        if not self.current_profile_name:
            messagebox.showerror("Error", "Please create a profile first by clicking the '+' button above.")
            return
            
        username = self.new_friend_entry.get().strip()
        name = self.new_friend_name_entry.get().strip()
        if username:
            if any(f['username'] == username for f in self.friends):
                messagebox.showerror("Error", "Friend already exists in the list.")
                return
            self.friends.append({"username": username, "name": name, "selected": True})
            self.save_friends()
            self.refresh_friends_list()
            self.new_friend_entry.delete(0, 'end')
            self.new_friend_name_entry.delete(0, 'end')

    def delete_profile(self, name):
        if name in self.profiles:
            del self.profiles[name]
        self.save_profiles()
        
        if len(self.profiles) > 0:
            self.current_profile_name = list(self.profiles.keys())[0]
        else:
            self.current_profile_name = None
            
        self.refresh_profile_ui()

    def open_app_settings(self):
        AppSettingsWindow(self, self.app_settings, self.save_app_settings)

    def save_app_settings(self, new_app_settings):
        # Check if view mode changed
        old_view = self.app_settings.get("view_mode")
        self.app_settings = new_app_settings
        self.save_json(APP_SETTINGS_FILE, self.app_settings)
        
        ctk.set_appearance_mode(self.app_settings.get("appearance_mode", "System"))
        self.view_mode = self.app_settings.get("view_mode", "Grid")
        
        if old_view != self.view_mode:
            self.refresh_friends_list()
            
        messagebox.showinfo("Settings", "App settings saved successfully!")

    def start_recovery(self):
        selected_friends = [f['username'] for f in self.friends if f.get('selected')]
        if not selected_friends:
            messagebox.showwarning("Warning", "No friends selected for recovery.")
            return
            
        current_settings = self.settings
        if not all([current_settings.get('username'), current_settings.get('email')]):
            messagebox.showwarning("Warning", "Please complete your account details by clicking the profile circle > Edit.")
            return
            
        self.after(100, lambda: messagebox.showinfo("Starting", "Starting browser automation...\nPlease do not close the browser until you've submitted all forms."))
        thread = threading.Thread(target=self.run_automation_thread, args=(current_settings, selected_friends))
        thread.start()

    def run_automation_thread(self, current_settings, friends_list):
        asyncio.run(run_recovery(current_settings, friends_list))


class FriendEditWindow(ctk.CTkToplevel):
    def __init__(self, parent, friend_data, save_callback):
        super().__init__(parent)
        self.title("Edit Friend")
        self.geometry("380x300")
        self.grab_set()
        
        self.save_callback = save_callback
        
        ctk.CTkLabel(self, text="Edit Contact Details", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Contact Name (Ali, Usama etc.)", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 0), anchor="w", padx=20)
        self.name_entry = ctk.CTkEntry(frame, width=300, height=35)
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, friend_data.get('name', ''))
        
        ctk.CTkLabel(frame, text="Snapchat Username", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.user_entry = ctk.CTkEntry(frame, width=300, height=35)
        self.user_entry.pack(pady=5)
        self.user_entry.insert(0, friend_data.get('username', ''))
        
        save_btn = ctk.CTkButton(self, text="Update Friend", height=40, font=ctk.CTkFont(weight="bold"), fg_color="#10A37F", hover_color="#0D8A6B", command=self.save)
        save_btn.pack(pady=20)

    def save(self):
        new_data = {
            "name": self.name_entry.get().strip(),
            "username": self.user_entry.get().strip()
        }
        if not new_data["username"]:
            messagebox.showerror("Error", "Username is required.")
            return
            
        self.save_callback(new_data)
        self.destroy()


class ProfileDetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, settings, save_callback, profile_name=None, delete_callback=None, is_new=False):
        super().__init__(parent)
        self.title("Account Setup" if is_new else "Edit Account Details")
        self.geometry("450x600")
        self.grab_set()
        
        self.save_callback = save_callback
        self.delete_callback = delete_callback
        self.is_new = is_new
        
        header_text = "New Account" if is_new else f"Edit '{profile_name}'"
        ctk.CTkLabel(self, text=header_text, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 15))
        
        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Account Name (e.g. My Account)", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 0), anchor="w", padx=20)
        self.name_entry = ctk.CTkEntry(frame, width=350, height=35)
        self.name_entry.pack(pady=(5, 10))
        if not is_new:
            self.name_entry.insert(0, profile_name)
            self.name_entry.configure(state="disabled")
        
        ctk.CTkLabel(frame, text="Snapchat Username", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.username_entry = ctk.CTkEntry(frame, width=350, height=35)
        self.username_entry.pack(pady=(5, 10))
        self.username_entry.insert(0, settings.get("username", ""))
        
        ctk.CTkLabel(frame, text="Account Email", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.email_entry = ctk.CTkEntry(frame, width=350, height=35)
        self.email_entry.pack(pady=(5, 10))
        self.email_entry.insert(0, settings.get("email", ""))
        
        ctk.CTkLabel(frame, text="Mobile Number (inc Country Code)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.mobile_entry = ctk.CTkEntry(frame, width=350, height=35)
        self.mobile_entry.pack(pady=(5, 10))
        self.mobile_entry.insert(0, settings.get("mobile_number", ""))
        
        ctk.CTkLabel(frame, text="Device (e.g. iPhone 14, Galaxy S23)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.device_entry = ctk.CTkEntry(frame, width=350, height=35)
        self.device_entry.pack(pady=(5, 10))
        self.device_entry.insert(0, settings.get("device", ""))
        
        ctk.CTkLabel(frame, text="Refresh Delay (seconds)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.refresh_delay_entry = ctk.CTkEntry(frame, width=350, height=35)
        self.refresh_delay_entry.pack(pady=(5, 10))
        self.refresh_delay_entry.insert(0, str(settings.get("refresh_delay", "1.0")))
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        save_btn_text = "Create Account" if is_new else "Save Details"
        btn = ctk.CTkButton(btn_frame, text=save_btn_text, height=40, font=ctk.CTkFont(weight="bold"), fg_color="#10A37F", hover_color="#0D8A6B", command=self.save)
        btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        if not is_new:
            del_btn = ctk.CTkButton(btn_frame, text="Delete", width=80, height=40, fg_color="#ff4d4d", hover_color="#cc0000", command=self.delete)
            del_btn.pack(side="right")

    def save(self):
        try:
            delay = float(self.refresh_delay_entry.get())
            if delay < 0: delay = 1.0
        except ValueError:
            delay = 1.0
            
        data = {
            "username": self.username_entry.get().strip(),
            "email": self.email_entry.get().strip(),
            "mobile_number": self.mobile_entry.get().strip(),
            "device": self.device_entry.get().strip(),
            "refresh_delay": delay
        }
        
        if self.is_new:
            data["_profile_name_"] = self.name_entry.get().strip()
            if not data["_profile_name_"]:
                messagebox.showerror("Error", "Please enter an account name.")
                return
        
        success = self.save_callback(data)
        if success is not False:
            self.destroy()

    def delete(self):
        confirm = messagebox.askyesno("Delete", "Are you sure you want to delete this profile?")
        if confirm:
            self.delete_callback()
            self.destroy()


class AppSettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, app_settings, save_callback):
        super().__init__(parent)
        self.title("App Global Settings")
        self.geometry("450x520")
        self.grab_set()
        
        self.save_callback = save_callback
        
        ctk.CTkLabel(self, text="Global Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Appearance Mode", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 0), anchor="w", padx=20)
        self.appearance_menu = ctk.CTkOptionMenu(frame, values=["System", "Light", "Dark"], width=350)
        self.appearance_menu.pack(pady=5)
        self.appearance_menu.set(app_settings.get("appearance_mode", "System"))
        
        ctk.CTkLabel(frame, text="Friends List Style", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0), anchor="w", padx=20)
        self.view_menu = ctk.CTkOptionMenu(frame, values=["Grid", "List"], width=350)
        self.view_menu.pack(pady=5)
        self.view_menu.set(app_settings.get("view_mode", "Grid"))
        
        ctk.CTkButton(frame, text="❓ How to Use (Help)", fg_color="gray30", height=40, command=self.open_help).pack(pady=(20, 10), padx=20, fill="x")
        ctk.CTkButton(frame, text="👨‍💻 About Developer", fg_color="gray30", height=40, command=self.open_about).pack(pady=(0, 15), padx=20, fill="x")
        
        btn = ctk.CTkButton(self, text="Save Settings", height=40, font=ctk.CTkFont(weight="bold"), command=self.save)
        btn.pack(pady=10)

    def open_help(self):
        HelpWindow(self)

    def open_about(self):
        AboutWindow(self)

    def save(self):
        new_app_settings = {
            "appearance_mode": self.appearance_menu.get(),
            "view_mode": self.view_menu.get()
        }
        self.save_callback(new_app_settings)
        self.destroy()

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("How to Use")
        self.geometry("500x550")
        self.grab_set()
        
        ctk.CTkLabel(self, text="Help & Instructions", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        help_text = (
            "1. Create a Profile:\n   Click the circular profile icon and '+ Add New Account'.\n\n"
            "2. Fill Details:\n   In the setup window, enter your Snapchat Username, Email, etc.\n\n"
            "3. Add Friends:\n   In the bottom section, enter a contact name and their Snapchat username.\n\n"
            "4. Selection:\n   Tick the checkbox next to the friends you want to recover streaks for.\n\n"
            "5. Run Recovery:\n   Click '🚀 RECOVER SELECTED STREAKS'.\n\n"
            "6. Browser Automation:\n   A browser will open. Solve the Captcha if prompted and click 'Submit' on the website.\n"
            "   Don't close the browser! It will auto-refresh for the next friend once submitted.\n\n"
            "7. Done:\n   The tool will notify you once all selected friends are processed."
        )
        
        msg_box = ctk.CTkTextbox(self, width=450, height=350, font=ctk.CTkFont(size=14))
        msg_box.pack(padx=20, pady=10)
        msg_box.insert("1.0", help_text)
        msg_box.configure(state="disabled")

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About Developer")
        self.geometry("400x350")
        self.grab_set()
        
        ctk.CTkLabel(self, text="Snapchat Streak Recoverer", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30, 10))
        ctk.CTkLabel(self, text="Version 2.8", font=ctk.CTkFont(size=14), text_color="gray").pack()
        
        info_text = (
            "This software is designed to automate repetitive\n"
            "Snapchat support requests safely and efficiently.\n\n"
            "Developed by: Abdul Haseeb\n\n"
            "For updates and support, visit our GitHub."
        )
        
        ctk.CTkLabel(self, text=info_text, font=ctk.CTkFont(size=15), pady=20).pack()
        
        ctk.CTkButton(self, text="Visit Website", command=lambda: webbrowser.open("https://github.com")).pack(pady=10)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
