/**
 * ORCA Speech & Voice Interface (Clean State Machine)
 * States: IDLE | LISTENING | PROCESSING | RESPONDING | ERROR
 * Synchronized with global application language (en-IN, ml-IN, ta-IN).
 * Prevents stuck mic, race conditions, and handles audio cancellation on screen switch.
 */

class OrcaVoiceManager {
  constructor() {
    this.state = 'IDLE'; // 'IDLE' | 'LISTENING' | 'PROCESSING' | 'RESPONDING' | 'ERROR'
    this.recognition = null;
    this.synthesis = window.speechSynthesis || null;
    this.currentLanguage = 'ml-IN';
    this.isListening = false;
    this.hasPermission = false;
    this.lastTranscript = '';
    this.initRecognition();
  }

  setLanguage(langCode) {
    if (!langCode) return;
    const l = langCode.toLowerCase();
    if (l.startsWith('ta')) {
      this.currentLanguage = 'ta-IN';
    } else if (l.startsWith('en')) {
      this.currentLanguage = 'en-IN';
    } else {
      this.currentLanguage = 'ml-IN';
    }

    if (this.recognition) {
      this.recognition.lang = this.currentLanguage;
    }

    // If currently speaking, cancel TTS on language switch
    if (this.synthesis && this.state === 'RESPONDING') {
      this.synthesis.cancel();
      this.transitionTo('IDLE');
    }
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = this.currentLanguage;

        this.recognition.onstart = () => {
          this.isListening = true;
          this.hasPermission = true;
          this.transitionTo('LISTENING');
        };

        this.recognition.onresult = (event) => {
          if (!event.results || !event.results[0] || !event.results[0][0]) return;
          const transcript = event.results[0][0].transcript.trim();
          this.lastTranscript = transcript;
          this.isListening = false;
          this.transitionTo('PROCESSING', transcript);
        };

        this.recognition.onerror = (event) => {
          console.warn('Speech recognition event notice:', event.error);
          this.isListening = false;
          if (event.error === 'not-allowed') {
            this.hasPermission = false;
            this.transitionTo('ERROR', 'Microphone permission denied.');
          } else if (event.error === 'no-speech') {
            this.transitionTo('IDLE');
          } else {
            this.transitionTo('ERROR', event.error);
          }
        };

        this.recognition.onend = () => {
          this.isListening = false;
          if (this.state === 'LISTENING') {
            this.transitionTo('IDLE');
          }
        };
      } catch (err) {
        console.warn('SpeechRecognition initialization notice:', err);
        this.recognition = null;
      }
    }
  }

  async requestMicPermission() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        this.hasPermission = true;
        return true;
      } catch (e) {
        this.hasPermission = false;
        return false;
      }
    }
    return true;
  }

  async startListening() {
    // If already listening, stop
    if (this.state === 'LISTENING') {
      this.stopListening();
      return;
    }

    // Cancel any active TTS speech
    if (this.synthesis) {
      this.synthesis.cancel();
    }

    // Check permission
    const granted = await this.requestMicPermission();
    if (!granted && !this.recognition) {
      this.transitionTo('ERROR', 'Microphone access is required for voice input.');
      return;
    }

    if (this.recognition) {
      try {
        this.recognition.lang = this.currentLanguage;
        this.recognition.start();
      } catch (e) {
        console.warn('Recognition start exception, resetting:', e);
        try {
          this.recognition.abort();
          this.recognition.start();
        } catch (retryErr) {
          // Fallback simulation for unsupported browsers/environments
          this._simulateVoiceCapture();
        }
      }
    } else {
      this._simulateVoiceCapture();
    }
  }

  _simulateVoiceCapture() {
    this.isListening = true;
    this.transitionTo('LISTENING');
    setTimeout(() => {
      if (this.state === 'LISTENING') {
        const sample = this.currentLanguage.startsWith('ml')
          ? 'ഇന്ന് മീൻപിടിക്കാൻ പോകാമോ?'
          : (this.currentLanguage.startsWith('ta') ? 'இன்று கடலுக்கு செல்லலாமா?' : 'Is it safe to go fishing today?');
        this.isListening = false;
        this.transitionTo('PROCESSING', sample);
      }
    }, 2500);
  }

  stopListening() {
    this.isListening = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {
        // ignore
      }
    }
    if (this.state === 'LISTENING') {
      this.transitionTo('IDLE');
    }
  }

  cancel() {
    this.isListening = false;
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (e) {
        // ignore
      }
    }
    if (this.synthesis) {
      try {
        this.synthesis.cancel();
      } catch (e) {
        // ignore
      }
    }
    this.transitionTo('IDLE');
  }

  speak(text, lang = null) {
    if (!this.synthesis || !text) return;
    this.synthesis.cancel();

    const targetLang = lang || this.currentLanguage;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = targetLang;
    utterance.rate = 0.92;
    utterance.pitch = 1.0;

    this.transitionTo('RESPONDING');

    utterance.onend = () => {
      this.transitionTo('IDLE');
    };

    utterance.onerror = (e) => {
      console.warn('TTS playback notice:', e);
      this.transitionTo('IDLE');
    };

    this.synthesis.speak(utterance);
  }

  transitionTo(newState, payload = null) {
    this.state = newState;
    window.dispatchEvent(new CustomEvent('orca:voiceState', {
      detail: { state: newState, payload: payload, language: this.currentLanguage }
    }));
  }
}

window.orcaVoice = new OrcaVoiceManager();
