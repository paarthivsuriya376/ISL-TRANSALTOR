"""
login_screen.py  — Premium login / register UI for the ISL Translator App.
"""

import customtkinter as ctk
from utils.user_data import login, register

# Palette
BG      = "#0d0d1a"
CARD    = "#13132b"
ACCENT  = "#5865f2"
ACCENT2 = "#7983f5"
SUCCESS = "#2ecc71"
ERROR   = "#e74c3c"
BORDER  = "#2a2a4a"
TXT     = "#e8eaf6"
MUTED   = "#8890b5"


class LoginScreen(ctk.CTkToplevel):
    """
    Modal login/register window.
    Calls `on_login_success(username)` when the user authenticates.
    """

    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.title("ISL Communicator — Sign In")
        self.geometry("480x600")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()          # modal
        self.focus_force()

        self._mode = "login"     # or "register"
        self._build()

    # ------------------------------------------------------------------ #
    def _build(self):
        # App title
        ctk.CTkLabel(self, text="🤟", font=ctk.CTkFont(size=54)
                     ).pack(pady=(40, 4))
        ctk.CTkLabel(self, text="ISL Communicator",
                     font=ctk.CTkFont(family="Segoe UI", size=26,
                                      weight="bold"),
                     text_color=TXT).pack()
        ctk.CTkLabel(self, text="Bridging voices and hands",
                     font=ctk.CTkFont(size=13), text_color=MUTED).pack(pady=(2, 24))

        # Card frame
        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16,
                             border_width=1, border_color=BORDER)
        card.pack(padx=40, fill="x")
        card.grid_columnconfigure(0, weight=1)

        # Tab buttons
        tab_bar = ctk.CTkFrame(card, fg_color="transparent")
        tab_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
        tab_bar.grid_columnconfigure((0, 1), weight=1)

        self.lbl_login_tab = ctk.CTkButton(
            tab_bar, text="Sign In", command=lambda: self._switch("login"),
            fg_color=ACCENT, hover_color=ACCENT2, corner_radius=8, height=34,
            font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_login_tab.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.lbl_reg_tab = ctk.CTkButton(
            tab_bar, text="Register", command=lambda: self._switch("register"),
            fg_color="transparent", hover_color=BORDER, corner_radius=8, height=34,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=14))
        self.lbl_reg_tab.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # Fields
        ctk.CTkLabel(card, text="Username", text_color=MUTED,
                     font=ctk.CTkFont(size=12), anchor="w"
                     ).grid(row=1, column=0, sticky="w", padx=24, pady=(22, 2))
        self.ent_user = ctk.CTkEntry(
            card, placeholder_text="Enter username",
            height=42, corner_radius=8,
            border_color=BORDER, fg_color="#1a1a35",
            font=ctk.CTkFont(size=14))
        self.ent_user.grid(row=2, column=0, sticky="ew", padx=22)

        ctk.CTkLabel(card, text="Password", text_color=MUTED,
                     font=ctk.CTkFont(size=12), anchor="w"
                     ).grid(row=3, column=0, sticky="w", padx=24, pady=(14, 2))
        self.ent_pass = ctk.CTkEntry(
            card, placeholder_text="Enter password", show="•",
            height=42, corner_radius=8,
            border_color=BORDER, fg_color="#1a1a35",
            font=ctk.CTkFont(size=14))
        self.ent_pass.grid(row=4, column=0, sticky="ew", padx=22)

        # Status label
        self.lbl_status = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12), height=22)
        self.lbl_status.grid(row=5, column=0, pady=(8, 4))

        # Action button
        self.btn_action = ctk.CTkButton(
            card, text="Sign In",
            command=self._handle_action,
            fg_color=ACCENT, hover_color=ACCENT2,
            height=46, corner_radius=10,
            font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_action.grid(row=6, column=0, sticky="ew",
                              padx=22, pady=(4, 22))

        # Bind Enter key
        self.ent_pass.bind("<Return>", lambda e: self._handle_action())
        self.ent_user.bind("<Return>", lambda e: self.ent_pass.focus())

        ctk.CTkLabel(self, text="© 2026 ISL Communicator — All Rights Reserved",
                     font=ctk.CTkFont(size=10), text_color=MUTED
                     ).pack(pady=(18, 0))

    # ------------------------------------------------------------------ #
    def _switch(self, mode):
        self._mode = mode
        if mode == "login":
            self.btn_action.configure(text="Sign In")
            self.lbl_login_tab.configure(fg_color=ACCENT)
            self.lbl_reg_tab.configure(fg_color="transparent")
        else:
            self.btn_action.configure(text="Create Account")
            self.lbl_reg_tab.configure(fg_color=ACCENT)
            self.lbl_login_tab.configure(fg_color="transparent")
        self.lbl_status.configure(text="", text_color=MUTED)

    def _handle_action(self):
        user = self.ent_user.get().strip()
        pw   = self.ent_pass.get().strip()

        if self._mode == "login":
            ok, msg = login(user, pw)
        else:
            ok, msg = register(user, pw)

        if ok:
            self.lbl_status.configure(text=f"✓ {msg}", text_color=SUCCESS)
            self.after(500, lambda: self._proceed(user))
        else:
            self.lbl_status.configure(text=f"✗ {msg}", text_color=ERROR)
            self.ent_pass.delete(0, "end")

    def _proceed(self, username):
        self.grab_release()
        self.destroy()
        self.on_login_success(username)
