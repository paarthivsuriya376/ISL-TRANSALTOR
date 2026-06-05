// Mock Eel implementation for static web demo mode (e.g., GitHub Pages)
if (typeof window.eel === 'undefined') {
    window.eel = {
        is_mock: true,
        expose: function(func, name) {
            console.log("Mock exposing function:", name);
            if (!window.eel_exposed) window.eel_exposed = {};
            window.eel_exposed[name] = func;
        },
        toggle_camera: function(state) {
            console.log("Mock toggle_camera:", state);
            if (state) {
                // If starting camera in demo mode, update with a mock feed/placeholder
                setTimeout(() => {
                    if (window.eel_exposed && window.eel_exposed.update_camera_frame) {
                        // We will notify the user they need the local backend
                    }
                }, 500);
            }
            return function() { return Promise.resolve(true); };
        },
        login_user: function(user, pass) {
            console.log("Mock login_user:", user);
            return function() {
                return Promise.resolve([true, "Login successful (Demo Mode)"]);
            };
        },
        register_user: function(user, pass) {
            console.log("Mock register_user:", user);
            return function() {
                return Promise.resolve([true, "Registration successful (Demo Mode)"]);
            };
        },
        get_user_data: function() {
            return function() {
                return Promise.resolve({ username: "Demo User" });
            };
        },
        handle_backspace: function() {
            return function() { return Promise.resolve(); };
        },
        handle_speak_and_clear: function() {
            return function() { return Promise.resolve(); };
        },
        handle_start_listening: function() {
            return function() {
                // Mock speech recognition result after 2 seconds
                setTimeout(() => {
                    if (window.eel_exposed && window.eel_exposed.update_speech_result) {
                        window.eel_exposed.update_speech_result("HELLO FRIEND");
                    }
                    if (window.eel_exposed && window.eel_exposed.update_animation_stage) {
                        // Use a blank or placeholder animation
                        window.eel_exposed.update_animation_stage("", "HELLO");
                    }
                }, 2000);
                return Promise.resolve();
            };
        },
        handle_clear_history: function() {
            return function() { return Promise.resolve(true); };
        },
        handle_delete_history_item: function(id) {
            return function() { return Promise.resolve(true); };
        },
        get_translation_history: function() {
            return function() {
                return Promise.resolve([
                    { id: 0, text: "[Sign→Speech] HELLO" },
                    { id: 1, text: "[Speech→Sign] GOOD" },
                    { id: 2, text: "[Sign→Speech] THANK YOU" }
                ]);
            };
        }
    };
}

function app() {
    return {
        isDemoMode: false,

        tab: 'login', // Initial tab for auth
        tabTitle: 'Welcome to ISL Pro',
        isLoggedIn: false,
        username: 'Guest',
        authMode: 'login', // 'login' or 'register'
        loginUser: '',
        loginPass: '',
        authMessage: '',
        isCapturing: false,
        isListening: false,
        currentSign: '',
        signProgress: 0,
        sentence: '',
        recognizedText: '',
        signLabel: '',
        showGuide: false,
        historyRecords: [],
        gestures: [
            { sign: "🖐️", label: "Open Palm", meaning: "HELLO / STOP" },
            { sign: "🌊", label: "Open Palm + Wave", meaning: "GOODBYE" },
            { sign: "☝️", label: "Index Up", meaning: "YES / ATTENTION" },
            { sign: "✊", label: "Fist + Nod", meaning: "YES (emphatic)" },
            { sign: "👍", label: "Thumb Up", meaning: "GOOD" },
            { sign: "👎", label: "Thumb Down", meaning: "BAD" },
            { sign: "🤟", label: "ILY Sign", meaning: "I LOVE YOU" },
            { sign: "🤙", label: "Index + Pinky", meaning: "CALL ME" },
            { sign: "🤚", label: "4 Fingers", meaning: "HELP / B" },
            { sign: "🕷️", label: "Spider-Man", meaning: "SPIDER-MAN" }
        ],

        init() {
            this.isDemoMode = !!window.eel.is_mock;
            lucide.createIcons();

            // Expose named functions to Eel (more reliable than anonymous closures)
            window.eel.expose(this.updateCamera.bind(this), 'update_camera_frame');
            window.eel.expose(this.updateProgress.bind(this), 'update_sign_progress');
            window.eel.expose(this.updateSentence.bind(this), 'update_sentence');
            window.eel.expose(this.updateSpeech.bind(this), 'update_speech_result');
            window.eel.expose(this.updateAnimation.bind(this), 'update_animation_stage');
        },

        // --- Explicit Named Callbacks for Eel ---
        updateCamera(base64) {
            const img = document.getElementById('camera-feed');
            if (img) img.src = "data:image/jpeg;base64," + base64;
        },
        updateProgress(pct, sign) {
            this.signProgress = pct || 0;
            this.currentSign = sign || '';
        },
        updateSentence(text) {
            this.sentence = text;
        },
        updateSpeech(text) {
            this.recognizedText = text;
            this.isListening = false;
        },
        updateAnimation(base64, label) {
            if (!base64) {
                const img = document.getElementById('sign-animation');
                if (img) img.src = "assets/sign-placeholder.png";
            } else {
                const img = document.getElementById('sign-animation');
                if (img) img.src = "data:image/jpeg;base64," + base64;
            }
            this.signLabel = label;
        },

        async setTab(newTab) {
            this.tab = newTab;
            this.tabTitle = {
                'sign': '📷 Sign Language → Text & Speech',
                'speech': '🎤 Speech → Text & Sign Language',
                'history': '📜 Translation History'
            }[newTab];

            if (newTab === 'history') {
                await this.fetchHistory();
            }

            window.eel.toggle_camera(false); // Auto-stop camera on tab switch
            this.isCapturing = false;
            this.$nextTick(() => lucide.createIcons());
        },

        async fetchHistory() {
            const records = await window.eel.get_translation_history()();
            this.historyRecords = (records || []).map(item => {
                const typeSign = item.text.includes("[Sign→Speech]");
                return {
                    id: item.id,
                    text: item.text.split('] ')[1] || item.text,
                    type: typeSign ? "sign" : "mic",
                    time: "Recent"
                };
            });
        },

        async fetchUserData() {
            const data = await window.eel.get_user_data()();
            if (data) this.username = data.username;
        },

        toggleCamera() {
            this.isCapturing = !this.isCapturing;
            window.eel.toggle_camera(this.isCapturing);
        },

        backspace() {
            window.eel.handle_backspace()();
        },

        speakAndClear() {
            window.eel.handle_speak_and_clear()();
        },

        startListening() {
            this.isListening = true;
            this.recognizedText = 'Listening...';
            window.eel.handle_start_listening()();
        },

        async clearHistory() {
            if (confirm("Are you sure you want to clear your entire translation history?")) {
                const success = await window.eel.handle_clear_history()();
                if (success) {
                    this.historyRecords = [];
                    this.$nextTick(() => lucide.createIcons());
                }
            }
        },

        async deleteHistoryItem(id) {
            const success = await window.eel.handle_delete_history_item(id)();
            if (success) {
                await this.fetchHistory();
                this.$nextTick(() => lucide.createIcons());
            }
        },

        async performAuth() {
            if (!this.loginUser || !this.loginPass) {
                this.authMessage = "Please fulfill all fields.";
                return;
            }
            this.authMessage = "Processing...";

            if (this.authMode === 'login') {
                const [success, msg] = await window.eel.login_user(this.loginUser, this.loginPass)();
                if (success) {
                    this.isLoggedIn = true;
                    this.username = this.loginUser;
                    this.setTab('sign');
                } else {
                    this.authMessage = msg;
                }
            } else {
                const [success, msg] = await window.eel.register_user(this.loginUser, this.loginPass)();
                this.authMessage = msg;
                if (success) {
                    this.authMode = 'login';
                    this.loginPass = '';
                }
            }
        },

        toggleAuthMode() {
            this.authMode = this.authMode === 'login' ? 'register' : 'login';
            this.authMessage = '';
        },

        logout() {
            window.location.reload();
        }
    }
}
