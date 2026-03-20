import speech_recognition as sr
import pyttsx3
import threading
import queue
import time

class SpeechHandler:
    _instance = None
    _lock = threading.Lock()
    _queue = queue.Queue()
    _worker_thread = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SpeechHandler, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Start background worker for TTS
        if SpeechHandler._worker_thread is None:
            SpeechHandler._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            SpeechHandler._worker_thread.start()
            
        self._initialized = True

    def _speech_worker(self):
        """Single background worker for all SAPI5 operations on Windows."""
        import pythoncom
        import win32com.client
        
        pythoncom.CoInitialize()
        voice = None
        
        while True:
            try:
                # Wait for text to speak
                text, callback = SpeechHandler._queue.get(timeout=2)
                
                # Try to init or recover voice
                if voice is None:
                    try:
                        voice = win32com.client.Dispatch("SAPI.SpVoice")
                        # You can set rate here if needed: voice.Rate = 1
                    except Exception as e:
                        print(f"SAPI Init Error: {e}")
                        time.sleep(1)
                        continue

                # Speak the text
                try:
                    # SVSFDefault = 0 (Synchronous)
                    # SVSFlagsAsync = 1 (Asynchronous)
                    voice.Speak(text, 0) 
                    if callback:
                        callback()
                except Exception as e:
                    print(f"SAPI Speaker Error: {e}")
                    voice = None # Force re-init
                
                SpeechHandler._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"DEBUG SAPI Worker Critical: {e}")
                time.sleep(1)
                continue

    def speak(self, text, callback=None):
        """Add a speech request to the global queue."""
        if text.strip():
            SpeechHandler._queue.put((text, callback))

    def listen(self, timeout=8, phrase_time_limit=15):
        """Listens to microphone and returns the full recognized sentence."""
        try:
            with self.microphone as source:
                # Quick ambient noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self.recognizer.energy_threshold = 300   # more sensitive
                self.recognizer.pause_threshold  = 1.2   # wait 1.2s of silence before stopping
                
                # Listen – phrase_time_limit=15 allows long sentences
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                # Recognize using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                return True, text
        except sr.WaitTimeoutError:
            return False, "Listening timed out. Please try again."
        except sr.UnknownValueError:
            return False, "Could not understand audio. Please speak clearly."
        except sr.RequestError as e:
            return False, f"Network error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
