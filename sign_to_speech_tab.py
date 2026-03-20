import customtkinter as ctk
import cv2
from PIL import Image
from utils.hand_tracking import HandSignDetector
from utils.user_data import save_history
import time


class SignToSpeechTab(ctk.CTkFrame):
    """
    Tab for Deaf/Mute → Normal communication.
    
    The user shows ISL signs to the camera.
    - Signs are detected live using MediaPipe.
    - Hold a sign for ~1.5 s to confirm a letter/word.
    - A 2-second pause between signs adds a SPACE.
    - Press "Speak & Clear" to TTS the accumulated sentence.
    """

    HOLD_SECONDS   = 1.0   # seconds to hold a sign before it's confirmed
    PAUSE_SECONDS  = 2.5   # seconds of no hand to insert a space

    def __init__(self, master, speech_handler, username="", **kwargs):
        super().__init__(master, **kwargs)
        self.speech_handler = speech_handler
        self.username = username

        # Camera state
        self.cap              = None
        self.is_camera_on     = False
        self.hand_detector    = HandSignDetector()

        # Sentence‑building state
        self.sentence         = ""      # accumulated sentence
        self.current_sign     = None    # sign being held right now
        self.sign_start_time  = None    # when the current sign started
        self.last_sign_time   = None    # last time ANY sign was seen
        self.confirmed_sign   = None    # last confirmed sign (prevents repeats)
        self.history          = []      # list of (sign_text, is_space) for accurate backspace

        # ---------- Layout -------------------------------------------------
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Header
        ctk.CTkLabel(self, text="Sign → Text & Speech",
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, pady=(20, 4))
        ctk.CTkLabel(self,
                     text="Show your ISL sign for 1.5 s to confirm a letter.",
                     text_color="gray"
                     ).grid(row=1, column=0, columnspan=2, pady=(0, 14))

        # Camera view
        self.camera_frame = ctk.CTkFrame(self, corner_radius=15,
                                          fg_color="#2b2b2b")
        self.camera_frame.grid(row=2, column=0, columnspan=2,
                               sticky="nsew", padx=40, pady=6)
        self.camera_frame.grid_rowconfigure(0, weight=1)
        self.camera_frame.grid_columnconfigure(0, weight=1)

        self.lbl_camera = ctk.CTkLabel(
            self.camera_frame, text="Camera Offline",
            font=ctk.CTkFont(size=20))
        self.lbl_camera.grid(row=0, column=0)

        # Live‑sign indicator (shows interim sign + hold progress)
        self.lbl_current_sign = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#f0c040")
        self.lbl_current_sign.grid(row=3, column=0, columnspan=2)

        # Accumulated sentence
        self.txt_sentence = ctk.CTkTextbox(self, height=100,
                                            corner_radius=15, border_width=2,
                                            border_color="#3a3a5a",
                                            fg_color="#1a1a2e",
                                            font=ctk.CTkFont(size=20))
        self.txt_sentence.grid(row=4, column=0, columnspan=2,
                               sticky="ew", padx=40, pady=12)
        self.txt_sentence.insert("0.0", "Your sentence will appear here...")
        self.txt_sentence.configure(state="disabled")

        # Camera toggle
        self.btn_camera = ctk.CTkButton(
            self, text="Turn On Camera",
            command=self.toggle_camera,
            font=ctk.CTkFont(size=16), height=50,
            corner_radius=25,
            fg_color="#2b8a3e", hover_color="#186227")
        self.btn_camera.grid(row=5, column=0, pady=20,
                             padx=(40, 10), sticky="ew")

        # Speak button
        self.btn_speak = ctk.CTkButton(
            self, text="🔊 Speak & Clear",
            command=self.speak_and_clear,
            font=ctk.CTkFont(size=16), height=50,
            corner_radius=25,
            fg_color="#1f538d", hover_color="#14375e",
            state="disabled")
        self.btn_speak.grid(row=5, column=1, pady=20,
                            padx=(10, 40), sticky="ew")

        # Backspace button
        self.btn_back = ctk.CTkButton(
            self, text="⌫ Backspace",
            command=self.backspace,
            font=ctk.CTkFont(size=14), height=36,
            corner_radius=18,
            fg_color="#555", hover_color="#333")
        self.btn_back.grid(row=6, column=0, columnspan=2, pady=(0, 16))

    # -----------------------------------------------------------------
    # Camera controls
    # -----------------------------------------------------------------

    def toggle_camera(self):
        if self.is_camera_on:
            self.release_camera()
            self.is_camera_on = False
            self.btn_camera.configure(text="Turn On Camera",
                                       fg_color="#2b8a3e",
                                       hover_color="#186227")
            self.lbl_camera.configure(image="", text="Camera Offline")
            self.lbl_current_sign.configure(text="")
            self.btn_speak.configure(state="disabled")
        else:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.lbl_camera.configure(
                    text="Error: Cannot access camera.")
                self.cap = None
                return
            self.is_camera_on    = True
            self.last_sign_time  = time.time()
            self.btn_camera.configure(text="Turn Off Camera",
                                       fg_color="#c93434",
                                       hover_color="#8f2323")
            self.lbl_camera.configure(text="")
            self.btn_speak.configure(state="normal")
            self._update_frame()

    def _update_frame(self):
        if not (self.is_camera_on and self.cap):
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame = self.hand_detector.find_hands(frame)

            now = time.time()

            if self.hand_detector.num_hands() > 0:
                sign = self.hand_detector.recognize_both_hands(frame)
                self.last_sign_time = now

                if sign:
                    sign_str = " + ".join(sign)
                    if sign == self.current_sign:
                        # Same signs – check hold duration
                        held = now - self.sign_start_time
                        remaining = self.HOLD_SECONDS - held
                        pct = min(int((held / self.HOLD_SECONDS) * 100), 100)
                        self.lbl_current_sign.configure(
                            text=f"Holding: [ {sign_str} ]  {pct}%")

                        if held >= self.HOLD_SECONDS and sign != self.confirmed_sign:
                            # ✅ Confirmed! Append to sentence
                            self.confirmed_sign = sign
                            # Join without space for multi-hand letters
                            self._append_to_sentence("".join(sign))
                    else:
                        # New sign state – reset hold timer
                        self.current_sign    = sign
                        self.sign_start_time = now
                        self.confirmed_sign  = None
                        self.lbl_current_sign.configure(
                            text=f"Detecting: [ {sign_str} ]  0%")
                else:
                    self.current_sign    = None
                    self.sign_start_time = None
                    self.lbl_current_sign.configure(text="Hands detected – unclear sign")
            else:
                # No hand
                if self.last_sign_time and \
                   (now - self.last_sign_time) > self.PAUSE_SECONDS and \
                   self.sentence and not self.sentence.endswith(" "):
                    self._append_to_sentence(" ")
                self.current_sign    = None
                self.sign_start_time = None
                self.lbl_current_sign.configure(text="")

            # Display frame
            rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img  = Image.fromarray(rgb)
            cimg = ctk.CTkImage(light_image=img, dark_image=img,
                                size=(640, 480))
            self.lbl_camera.configure(image=cimg)
            self.lbl_camera.image = cimg

        self.after(30, self._update_frame)

    # -----------------------------------------------------------------
    # Sentence helpers
    # -----------------------------------------------------------------

    def _append_to_sentence(self, char):
        if char == " " and (not self.sentence or self.sentence.endswith(" ")):
            return
        
        self.history.append(char)
        self.sentence += char
        self._refresh_text()

    def _refresh_text(self):
        self.txt_sentence.configure(state="normal")
        self.txt_sentence.delete("0.0", "end")
        self.txt_sentence.insert("0.0",
                                  self.sentence if self.sentence
                                  else "Your sentence will appear here...")
        self.txt_sentence.configure(state="disabled")

    def speak_and_clear(self):
        text = self.sentence.strip()
        if text:
            self.speech_handler.speak(text)
            save_history(self.username, f"[Sign→Speech] {text}")
            self.sentence      = ""
            self.history       = []
            self.confirmed_sign = None
            self._refresh_text()

    def backspace(self):
        """Corrected Backspace: removes the last FULL sign added from history."""
        if self.history:
            last_entry = self.history.pop()
            # Rebuild sentence from history to be 100% accurate
            self.sentence = "".join(self.history)
            
            # Reset confirmed_sign so user can immediately re-do the same sign if they want
            self.confirmed_sign = None 
            self._refresh_text()

    def release_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None
