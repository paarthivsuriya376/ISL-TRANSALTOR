import customtkinter as ctk
import threading
from PIL import Image, ImageDraw, ImageFont
from utils.user_data import save_history
from utils.isl_animator import get_frames_for_sentence


class SpeechToSignTab(ctk.CTkFrame):
    """
    Tab: Normal person speaks → text shown + spoken back + ISL letters displayed.
    
    Fixes:
    - phrase_time_limit raised to 15s so long sentences are fully captured
    - Recognized text is automatically spoken out loud immediately
    - Transcript box wraps and shows the complete sentence
    - ISL visualiser shows word-by-word (not letter-by-letter) for readability
    """

    def __init__(self, master, speech_handler, username="", **kwargs):
        super().__init__(master, **kwargs)
        self.speech_handler = speech_handler
        self.username       = username
        self.is_listening   = False
        self.animation_id   = None

        # Layout
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Header ---
        ctk.CTkLabel(self, text="Speech → Text & Sign",
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, pady=(20, 4))
        ctk.CTkLabel(self,
                     text="Press the button, speak your full sentence, then wait — it will be translated & read aloud.",
                     text_color="gray", wraplength=700
                     ).grid(row=1, column=0, pady=(0, 14))

        # --- ISL Visual Display ---
        self.sign_frame = ctk.CTkFrame(self, corner_radius=20, 
                                       fg_color="#12122b",
                                       border_width=2,
                                       border_color="#2e2e5a")
        self.sign_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=12)
        self.sign_frame.grid_rowconfigure(0, weight=1)
        self.sign_frame.grid_columnconfigure(0, weight=1)

        self.lbl_sign = ctk.CTkLabel(
            self.sign_frame, text="Your ISL translation will appear here",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#a5b4fc",
            wraplength=600)
        self.lbl_sign.grid(row=0, column=0, padx=20, pady=20)

        # --- Full Transcript Box ---
        ctk.CTkLabel(self, text="Recognised Text:",
                     font=ctk.CTkFont(size=13), text_color="gray"
                     ).grid(row=3, column=0, sticky="w", padx=44)

        self.txt_transcript = ctk.CTkTextbox(
            self, height=100, corner_radius=15,
            border_width=2, border_color="#3a3a5a",
            fg_color="#1a1a2e",
            font=ctk.CTkFont(size=18), wrap="word")
        self.txt_transcript.grid(row=4, column=0, sticky="ew",
                                  padx=40, pady=(4, 20))
        self.txt_transcript.insert("0.0", "Transcript will appear here...")
        self.txt_transcript.configure(state="disabled")

        # --- Listen Button ---
        self.btn_listen = ctk.CTkButton(
            self,
            text="🎧  Start Listening",
            command=self.toggle_listen,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=58,
            corner_radius=29,
            fg_color="#6366f1",
            hover_color="#4f46e5"
        )
        self.btn_listen.grid(row=5, column=0, pady=(0, 32))

    # ------------------------------------------------------------------ #
    # Listening logic
    # ------------------------------------------------------------------ #

    def toggle_listen(self):
        if self.is_listening:
            return   # already listening — ignore extra clicks

        self.is_listening = True
        self.btn_listen.configure(text="🔴  Listening... Speak now!",
                                   fg_color="#c93434", hover_color="#8f2323")
        self._update_transcript("🎙️  Listening… speak your full sentence.")
        self.lbl_sign.configure(text="", image="")

        thread = threading.Thread(target=self._listen_worker, daemon=True)
        thread.start()

    def _listen_worker(self):
        """Runs in background thread — calls speech handler."""
        success, text = self.speech_handler.listen()   # up to 15 s
        self.after(0, self._on_result, success, text)

    def _on_result(self, success, text):
        """Back on UI thread after recognition finishes."""
        self.is_listening = False
        self.btn_listen.configure(text="🎤  Start Listening",
                                   fg_color="#1f538d", hover_color="#14375e")

        if success:
            self._update_transcript(f'You said: "{text}"')
            # Auto-speak and save history
            self.speech_handler.speak(text)
            save_history(self.username, f"[Speech→Sign] {text}")
            self._show_isl_words(text)
        else:
            self._update_transcript(f"⚠️  {text}")
            self.lbl_sign.configure(text="Please try again.", image="")

    # ------------------------------------------------------------------ #
    # UI helpers
    # ------------------------------------------------------------------ #

    def _update_transcript(self, text):
        self.txt_transcript.configure(state="normal")
        self.txt_transcript.delete("0.0", "end")
        self.txt_transcript.insert("0.0", text)
        self.txt_transcript.configure(state="disabled")

    def _show_isl_words(self, sentence):
        """Fetches frames from isl_animator and plays the animation."""
        # Cancel any active animation loop
        if self.animation_id:
            try: self.after_cancel(self.animation_id)
            except: pass
            self.animation_id = None

        word_data = get_frames_for_sentence(sentence)
        if not word_data:
            self.lbl_sign.configure(text="(No signs found)", image="")
            return

        self.lbl_sign.configure(text="", image="")

        def play_animation(w_idx=0, f_idx=0):
            if w_idx < len(word_data):
                word, frames = word_data[w_idx]
                if f_idx < len(frames):
                    img = frames[f_idx]
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(360, 360))
                    self.lbl_sign.configure(image=ctk_img, text="")
                    self.lbl_sign.image = ctk_img
                    
                    self.animation_id = self.after(180, play_animation, w_idx, f_idx + 1)
                else:
                    # Next word in sequence
                    self.animation_id = self.after(400, play_animation, w_idx + 1, 0)
            else:
                # Finished all words -> loop back to the start after a pause
                self.animation_id = self.after(1200, play_animation, 0, 0)

        play_animation(0, 0)
