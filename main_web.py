import eel
import cv2
import base64
import threading
import time
import webview
from utils.hand_tracking import HandSignDetector
from utils.speech_handler import SpeechHandler
from utils.isl_animator import get_frames_for_word, get_frames_for_sentence
from utils.user_data import save_history, get_history
import numpy as np

# Settings
username = None
is_running = True
camera_active = False

# Global state for sentence
sentence = ""
history = []
confirmed_sign = None
current_sign = None
sign_start_time = None
HOLD_SECONDS = 1.0
PAUSE_SECONDS = 2.5
last_sign_time = None

# --- Helper: Convert CV2 Frame to Base64 ---
def frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    return base64.b64encode(buffer).decode('utf-8')

# --- Background Task: Camera Processor ---
def camera_loop():
    global camera_active, current_sign, sign_start_time, confirmed_sign
    global sentence, is_running, last_sign_time
    
    # Initialize inside thread for stability
    local_detector = HandSignDetector()
    cap = None
    last_frame_time = 0
    last_sign_time = time.time()
    
    print("AI: Background tracking engine initialized.")
    
    while is_running:
        try:
            if camera_active:
                if cap is None:
                    cap = cv2.VideoCapture(0)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                # FPS control (~25-30 FPS is plenty for tracking)
                if time.time() - last_frame_time < 0.04:
                    time.sleep(0.005)
                    continue
                last_frame_time = time.time()

                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    frame = local_detector.find_hands(frame)
                    now = time.time()

                    pct = 0
                    display_sign = ""

                    if local_detector.num_hands() > 0:
                        sign = local_detector.recognize_both_hands(frame)
                        last_sign_time = now # Update last seen time

                        if sign:
                            sign_str = " + ".join(sign)
                            if sign == current_sign:
                                held = now - sign_start_time
                                pct = min(int((held / HOLD_SECONDS) * 100), 100)
                                if held >= HOLD_SECONDS and sign != confirmed_sign:
                                    confirmed_sign = sign
                                    # Sign combination mapping
                                    if sign == ["S", "S"]:
                                        append_to_sentence(" SITTING ")
                                    elif sign == ["A", "A"]:
                                        append_to_sentence(" SITTING ") # User mentioned 'thumbnails closed'
                                    else:
                                        append_to_sentence("".join(sign)) 
                            else:
                                current_sign = sign
                                sign_start_time = now
                                confirmed_sign = None
                            display_sign = sign_str
                        else:
                            current_sign = None
                            sign_start_time = now
                            confirmed_sign = None
                            display_sign = "Unclear"
                    else:
                        # No hands - check for pause to add space
                        if last_sign_time and (now - last_sign_time) > PAUSE_SECONDS:
                            if sentence and not sentence.endswith(" "):
                                append_to_sentence(" ")
                            last_sign_time = now # Reset so it doesn't keep adding spaces
                        
                        current_sign = None
                        sign_start_time = None
                        display_sign = ""

                    # Push data to JS (Only if frontend is ready)
                    try:
                        if hasattr(eel, 'update_camera_frame'):
                            eel.update_camera_frame(frame_to_base64(frame))
                        if hasattr(eel, 'update_sign_progress'):
                            eel.update_sign_progress(pct, display_sign)
                    except Exception:
                        pass
                else:
                    time.sleep(0.1)
            else:
                if cap is not None:
                    cap.release()
                    cap = None
                time.sleep(0.1)
        except Exception as e:
            print(f"Camera Loop Error: {e}")
            time.sleep(0.1)
        
        time.sleep(0.001)

def append_to_sentence(text):
    global sentence, history
    if not text: return
    if text == " " and (not sentence or sentence.endswith(" ")):
        return
    history.append(text)
    sentence = "".join(history)
    if hasattr(eel, 'update_sentence'):
        eel.update_sentence(sentence)

# --- Eel Exposed Methods ---
@eel.expose
def login_user(user, pwd):
    global username
    from utils.user_data import login
    success, msg = login(user, pwd)
    if success:
        username = user
    return success, msg

@eel.expose
def register_user(user, pwd):
    from utils.user_data import register
    return register(user, pwd)

@eel.expose
def get_user_data():
    return {"username": username}

@eel.expose
def toggle_camera(state):
    global camera_active
    if not username: return False # Security check
    camera_active = state
    print(f"AI: Camera {'Active' if state else 'Paused'}")
    return True

@eel.expose
def handle_backspace():
    global sentence, history, confirmed_sign
    if history:
        history.pop()
        sentence = "".join(history)
        confirmed_sign = None
        if hasattr(eel, 'update_sentence'):
            eel.update_sentence(sentence)

@eel.expose
def handle_speak_and_clear():
    global sentence, history, confirmed_sign
    text = sentence.strip()
    if text:
        sh = SpeechHandler()
        sh.speak(text)
        save_history(username, f"[Sign\u2192Speech] {text}")
        sentence = ""
        history = []
        confirmed_sign = None
        if hasattr(eel, 'update_sentence'):
            eel.update_sentence(sentence)

@eel.expose
def handle_start_listening():
    global animation_stop_event
    animation_stop_event.set()
    
    if hasattr(eel, 'update_animation_stage'):
        eel.update_speech_result("Listening...")
        eel.update_animation_stage("", "System Ready")

    def listen_thread():
        sh = SpeechHandler()
        success, text = sh.listen()
        if success:
            print(f"AI: Recognized Speech -> {text}")
            save_history(username, f"[Speech\u2192Sign] {text}")
            if hasattr(eel, 'update_speech_result'):
                eel.update_speech_result(text)
            sh.speak(text)
            play_sign_animation(text)
        else:
            if hasattr(eel, 'update_speech_result'):
                eel.update_speech_result(f"Error: {text}")
    
    threading.Thread(target=listen_thread, daemon=True).start()

@eel.expose
def handle_clear_history():
    from utils.user_data import clear_history
    success = clear_history(username)
    return success

@eel.expose
def get_translation_history():
    from utils.user_data import get_history
    data = get_history(username)
    start_idx = max(0, len(data) - 20)
    result = []
    for i in range(len(data)-1, start_idx-1, -1):
        result.append({"id": i, "text": data[i]})
    return result

@eel.expose
def handle_delete_history_item(item_id):
    from utils.user_data import delete_history_item
    return delete_history_item(username, item_id)

# Animation Logic
animation_thread = None
animation_stop_event = threading.Event()

def play_sign_animation(text):
    global animation_thread, animation_stop_event
    if animation_thread and animation_thread.is_alive():
        animation_stop_event.set()
        animation_thread.join(timeout=0.3)
    
    animation_stop_event.clear()
    word_data = get_frames_for_sentence(text)
    if not word_data: return

    def runner():
        while not animation_stop_event.is_set():
            for word, frames in word_data:
                if animation_stop_event.is_set(): break
                for frame in frames:
                    if animation_stop_event.is_set(): break
                    cv_img = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                    if hasattr(eel, 'update_animation_stage'):
                        eel.update_animation_stage(frame_to_base64(cv_img), word)
                    time.sleep(0.08)
                time.sleep(0.4)
            time.sleep(1.5)
            
    animation_thread = threading.Thread(target=runner, daemon=True)
    animation_thread.start()

# --- Entry Point ---
if __name__ == "__main__":
    # Start AI Logic
    threading.Thread(target=camera_loop, daemon=True).start()
    
    # Initialize Web UI Bridge
    eel.init('web')
    
    # Start Eel as a server only (no browser popup)
    threading.Thread(target=lambda: eel.start('index.html', mode=None, port=8000), daemon=True).start()
    
    # Create NATIVE Standalone Window (Uses Edge Webview Engine)
    print("AI: Launching Native Standalone Window...")
    webview.create_window(
        'ISL Communicator Pro', 
        'http://localhost:8000/index.html',
        width=1000, height=720,
        resizable=True,
        background_color='#050510'
    )
    webview.start()
    
    # Cleanup
    is_running = False
