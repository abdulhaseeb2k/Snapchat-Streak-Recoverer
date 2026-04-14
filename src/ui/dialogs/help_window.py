"""
HelpWindow — dialog showing usage instructions.
"""

import customtkinter as ctk
from src.constants import font_heading, font_body


class HelpWindow(ctk.CTkToplevel):
    """Modal dialog with help and instructions."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("How to Use")
        self.geometry("520x560")
        self.grab_set()

        ctk.CTkLabel(self, text="Help & Instructions", font=font_heading()).pack(pady=20)

        help_text = (
            "1. Create a Profile:\n"
            "   Click the circular profile icon and '+ Add New Account'.\n\n"
            "2. Fill Details:\n"
            "   In the setup window, enter your Snapchat Username, Email, etc.\n\n"
            "3. Add Friends:\n"
            "   In the bottom section, enter a contact name and their Snapchat username.\n\n"
            "4. Selection:\n"
            "   Tick the checkbox next to the friends you want to recover streaks for.\n\n"
            "5. Run Recovery:\n"
            "   Click '🚀 RECOVER SELECTED STREAKS'.\n\n"
            "6. Browser Automation:\n"
            "   A browser will open. Solve the Captcha if prompted and click 'Submit'.\n"
            "   Don't close the browser! It will auto-refresh for the next friend.\n\n"
            "7. Done:\n"
            "   The status bar will show 'All friends processed!' when finished."
        )

        msg_box = ctk.CTkTextbox(self, width=470, height=370, font=font_body())
        msg_box.pack(padx=20, pady=10)
        msg_box.insert("1.0", help_text)
        msg_box.configure(state="disabled")
