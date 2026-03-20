from utils.isl_animator import get_frames_for_word
import os

def save_sample():
    frames = get_frames_for_word("HELLO")
    if frames:
        # Create artifacts directory if it doesn't exist
        os.makedirs("artifacts", exist_ok=True)
        frames[0].save("artifacts/sample_gesture.png")
        print("Saved artifacts/sample_gesture.png")

if __name__ == "__main__":
    save_sample()
