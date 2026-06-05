# 🤟 ISL Communicator Pro

An advanced **Indian Sign Language (ISL)** translation application built with Python and modern web technologies. This application enables seamless, real-time two-way communication between signers and non-signers.

---

## 🌟 Key Features

* **📷 Sign Language ➔ Text & Speech**: 
  Uses your webcam and **MediaPipe** AI hand tracking to translate Indian Sign Language gestures into text and speech in real-time.
* **🎤 Speech ➔ Sign Language**: 
  Translates spoken English words into smooth, illustrated 3D sign language animation sequences.
* **📜 Translation History**: 
  Tracks and saves past translations for quick retrieval.
* **📖 Gesture Guide**: 
  Built-in library illustrating the different signs and gestures supported by the application.
* **💻 Premium Desktop Interface**: 
  A native standalone desktop window styled with a sleek, interactive dark theme.

---

## 🛠️ System Prerequisites

Before running the application on a new PC, make sure you have:
1. **Windows OS** (64-bit).
2. **Python 3.10** (recommended).
   * ⚠️ **Important during Python installation:** Make sure to check the box that says **"Add Python to PATH"** in the installer window.

---

## 🚀 How to Install and Run

Follow these simple steps to set up and run the application on any PC:

### Step 1: Download the Files
1. At the top-right of this GitHub page, click the green **`Code`** button.
2. Select **`Download ZIP`**.
3. Extract the downloaded `.zip` file to a folder on your computer (e.g., your Desktop).

*Or, if you are a developer, clone the repository:*
```bash
git clone https://github.com/paarthivsuriya376/ISL-TRANSALTOR.git
```

### Step 2: One-Click Setup
1. Open the extracted project folder.
2. Locate and double-click the **`setup.bat`** file.
3. This script will automatically check for Python, set up a virtual environment (`venv`), and install all necessary AI/web libraries (Pillow, OpenCV, MediaPipe, Eel, etc.).
4. *Wait until the terminal screen says setup is complete and prompts you to press any key.*

### Step 3: Run the Application
1. Double-click the **`Run_App.bat`** file inside your folder.
2. The standalone desktop application will open and launch immediately!

---

## 📂 Project Structure

* **`main_web.py`**: The main application entry point (backend launcher).
* **`Run_App.bat`**: Shortcut to launch the application instantly.
* **`setup.bat`**: Automatic dependencies and virtual environment installer.
* **`web/`**: HTML/CSS/JavaScript files for the modern frontend user interface.
* **`utils/`**: Core helper modules for AI hand tracking, sign animation, and database records.
* **`requirements.txt`**: List of all required Python packages.
