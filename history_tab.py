"""
history_tab.py — Translation history view.
"""

import customtkinter as ctk
from utils.user_data import get_history


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, username: str, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(self, text="Translation History 📜",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=0, column=0, pady=(20, 10))

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(
            self, corner_radius=12, fg_color="#13132b")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 10))
        self.scroll.grid_columnconfigure(0, weight=1)

        # Refresh button
        ctk.CTkButton(self, text="🔄 Refresh",
                      command=self.refresh,
                      height=38, corner_radius=10,
                      fg_color="#2a2a4a", hover_color="#3a3a6a"
                      ).grid(row=2, column=0, pady=(0, 16))

        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        entries = get_history(self.username)
        if not entries:
            ctk.CTkLabel(self.scroll,
                         text="No history yet. Start translating!",
                         text_color="#8890b5"
                         ).grid(row=0, column=0, pady=30)
            return

        for i, entry in enumerate(reversed(entries[-50:])):
            row_frame = ctk.CTkFrame(self.scroll, corner_radius=8,
                                      fg_color="#1a1a35", height=44)
            row_frame.grid(row=i, column=0, sticky="ew",
                           padx=10, pady=4)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_propagate(False)

            # Number badge
            ctk.CTkLabel(row_frame, text=f"#{len(entries)-i}",
                         text_color="#5865f2",
                         font=ctk.CTkFont(size=11, weight="bold"), width=36
                         ).grid(row=0, column=0, padx=(8, 6), sticky="w")

            ctk.CTkLabel(row_frame, text=entry, anchor="w",
                         font=ctk.CTkFont(size=13), text_color="#e8eaf6",
                         wraplength=500
                         ).grid(row=0, column=1, sticky="ew", padx=(0, 8))
