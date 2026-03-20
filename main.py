"""
main.py — ISL Communicator  (premium edition with login)
"""

import customtkinter as ctk
from login_screen      import LoginScreen
from sign_to_speech_tab import SignToSpeechTab
from speech_to_sign_tab import SpeechToSignTab
from history_tab        import HistoryTab
from utils.speech_handler import SpeechHandler

# ── Colour palette ──────────────────────────────────────────────────────────
BG      = "#0b0b18"
SIDEBAR = "#12122b"
CARD    = "#1a1a3a"
ACCENT  = "#6366f1"
ACCENT2 = "#a5b4fc"
TXT     = "#f8fafc"
MUTED   = "#94a3b8"
BORDER  = "#2e2e5a"
# ────────────────────────────────────────────────────────────────────────────


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ISLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ISL Communicator")
        self.geometry("1100x720")
        self.minsize(900, 640)
        self.configure(fg_color=BG)

        self.speech_handler = SpeechHandler()
        self.username       = None
        self._content_frame = None

        # Start with splash / hidden, then show login
        self.withdraw()             # hide until login done
        self.after(100, self._show_login)

    # ------------------------------------------------------------------ #
    def _show_login(self):
        LoginScreen(self, self._on_login)

    def _on_login(self, username):
        self.username = username
        self.deiconify()
        self._build_main_ui()

    # ------------------------------------------------------------------ #
    def _build_main_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──
        self._sidebar = ctk.CTkFrame(self, width=220, corner_radius=0,
                                      fg_color=SIDEBAR)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_rowconfigure(10, weight=1)

        # Logo section with subtle glow styling
        logo_area = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_area.grid(row=0, column=0, pady=(32, 20), padx=25, sticky="w")
        
        ctk.CTkLabel(logo_area, text="🤟 ISL",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=ACCENT
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(logo_area, text="Communicator Pro",
                     font=ctk.CTkFont(size=13), text_color=MUTED
                     ).grid(row=1, column=0, sticky="w")

        # User badge — premium card look
        user_badge = ctk.CTkFrame(self._sidebar, fg_color=CARD,
                                   corner_radius=12, border_width=1,
                                   border_color=BORDER)
        user_badge.grid(row=2, column=0, padx=16, pady=(10, 24), sticky="ew")
        ctk.CTkLabel(user_badge, text="👤", font=ctk.CTkFont(size=24)
                     ).grid(row=0, column=0, padx=(12, 6), pady=10)
        ctk.CTkLabel(user_badge, text=self.username.upper(), anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TXT
                     ).grid(row=0, column=1, sticky="w")

        # Separator
        ctk.CTkLabel(self._sidebar, text="NAVIGATION",
                     font=ctk.CTkFont(size=10), text_color=MUTED
                     ).grid(row=3, column=0, padx=22, pady=(6, 4), sticky="w")

        # Nav buttons
        self._nav_btns = {}
        nav_items = [
            ("sign",    "📷  Sign → Speech",   self._show_sign_tab),
            ("speech",  "🎤  Speech → Sign",   self._show_speech_tab),
            ("history", "📜  History",          self._show_history_tab),
        ]
        for r, (key, label, cmd) in enumerate(nav_items, start=4):
            btn = ctk.CTkButton(
                self._sidebar, text=label, command=cmd,
                fg_color="transparent", hover_color=BORDER,
                anchor="w", height=42, corner_radius=8,
                font=ctk.CTkFont(size=14),
                text_color=TXT)
            btn.grid(row=r, column=0, padx=10, pady=3, sticky="ew")
            self._nav_btns[key] = btn

        # Logout at bottom
        ctk.CTkButton(
            self._sidebar, text="⇠  Log Out",
            command=self._logout,
            fg_color="transparent", hover_color="#2a1a1a",
            anchor="w", height=40, corner_radius=8,
            font=ctk.CTkFont(size=13), text_color="#e57373"
        ).grid(row=11, column=0, padx=10, pady=(0, 20), sticky="ew")

        # ── Header bar ──
        header = ctk.CTkFrame(self, fg_color=BG, height=64,
                               corner_radius=0, border_width=0)
        header.grid(row=0, column=1, sticky="new")
        
        inner_header = ctk.CTkFrame(header, fg_color=CARD, height=52, corner_radius=12)
        inner_header.pack(fill="x", padx=15, pady=(12, 0))

        self._header_title = ctk.CTkLabel(
            inner_header, text="Sign Language → Speech",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=TXT)
        self._header_title.pack(side="left", padx=24, pady=12)

        # Gesture guide chip
        ctk.CTkButton(
            inner_header, text="📖  How to Gesture",
            command=self._show_guide,
            height=32, corner_radius=10,
            fg_color=BORDER, hover_color="#3a3a5a",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT2
        ).pack(side="right", padx=16, pady=10)

        # ── Content area ──
        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew", pady=(52, 0))
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        # Show default tab
        self._show_sign_tab()
        self._set_active("sign")

    # ------------------------------------------------------------------ #
    def _clear_content(self):
        if self._content_frame:
            self._content_frame.destroy()
            self._content_frame = None

    def _set_active(self, key):
        for k, btn in self._nav_btns.items():
            btn.configure(fg_color=ACCENT if k == key else "transparent")

    def _show_sign_tab(self):
        self._clear_content()
        self._set_active("sign")
        self._header_title.configure(text="📷  Sign Language → Text & Speech")
        self._content_frame = SignToSpeechTab(
            self._content, self.speech_handler,
            username=self.username)
        self._content_frame.grid(row=0, column=0, sticky="nsew")

    def _show_speech_tab(self):
        self._clear_content()
        self._set_active("speech")
        self._header_title.configure(text="🎤  Speech → Text & Sign Language")
        self._content_frame = SpeechToSignTab(
            self._content, self.speech_handler,
            username=self.username)
        self._content_frame.grid(row=0, column=0, sticky="nsew")

    def _show_history_tab(self):
        self._clear_content()
        self._set_active("history")
        self._header_title.configure(text="📜  Translation History")
        self._content_frame = HistoryTab(
            self._content, username=self.username)
        self._content_frame.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------ #
    def _show_guide(self):
        guide = ctk.CTkToplevel(self)
        guide.title("Gesture Guide")
        guide.geometry("520x560")
        guide.configure(fg_color=BG)
        guide.grab_set()

        ctk.CTkLabel(guide, text="ISL Gesture Guide 🤟",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TXT).pack(pady=(24, 4))
        ctk.CTkLabel(guide, text="Hold each gesture for 1 second to confirm",
                     font=ctk.CTkFont(size=12), text_color=MUTED).pack()

        scroll = ctk.CTkScrollableFrame(guide, fg_color=CARD, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=20, pady=16)
        scroll.grid_columnconfigure((0, 1), weight=1)

        gestures = [
            ("🖐️ Open Palm",          "HELLO / STOP"),
            ("🌊 Open Palm + Wave",   "GOODBYE"),
            ("☝️ Index Finger Up",    "YES / ATTENTION"),
            ("✊ Fist + Nod",         "YES (emphatic)"),
            ("☝️ + Wave Side",        "NO"),
            ("👍 Thumb Up",           "GOOD"),
            ("👎 Thumb Down",         "BAD"),
            ("✊ Fist",               "S / NO"),
            ("✌️ Index + Middle",     "PEACE"),
            ("🤟 Thumb+Index+Pinky",  "I LOVE YOU"),
            ("🤙 Index + Pinky",      "CALL ME"),
            ("🖐️ Palm Up + Wave up",  "COME HERE"),
            ("🖐️ Palm Down + push",   "GO AWAY"),
            ("✊ Fist + circle",       "SORRY"),
            ("🤚 4 Fingers Up",       "HELP / B"),
            ("🕷️ Thumb+Mid+Pinky",    "SPIDER-MAN"),
        ]

        for i, (sign, meaning) in enumerate(gestures):
            r, c = divmod(i, 2)
            box = ctk.CTkFrame(scroll, fg_color="#1a1a35", corner_radius=8)
            box.grid(row=r, column=c, padx=6, pady=5, sticky="ew")
            ctk.CTkLabel(box, text=sign, font=ctk.CTkFont(size=14),
                         text_color=TXT, anchor="w"
                         ).pack(padx=10, pady=(8, 0), anchor="w")
            ctk.CTkLabel(box, text=meaning, font=ctk.CTkFont(size=11),
                         text_color=ACCENT2, anchor="w"
                         ).pack(padx=10, pady=(0, 8), anchor="w")

    # ------------------------------------------------------------------ #
    def _logout(self):
        self._clear_content()
        for w in self.winfo_children():
            w.destroy()
        self._content_frame = None
        self._show_login()

    def on_closing(self):
        if self._content_frame and hasattr(self._content_frame, "release_camera"):
            self._content_frame.release_camera()
        self.destroy()


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ISLApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
