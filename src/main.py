"""
Entry point for the Snapchat Streak Recoverer application.
"""

import customtkinter as ctk
from src.core.data_manager import DataManager
from src.ui.app_window import AppWindow


def run():
    """Initialise data layer, create the UI, and start the event loop."""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    data = DataManager()
    app = AppWindow(data)
    app.update()
    app.mainloop()


if __name__ == "__main__":
    run()
