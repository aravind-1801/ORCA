/**
 * ORCA Speech & Voice Interface (Clean State Machine)
 * States: IDLE | LISTENING | TRANSCRIBING | THINKING | SPEAKING | ERROR
 * 
 * Pipeline:
 *  Microphone -> MediaRecorder -> POST /api/voice/transcribe (Groq Whisper)
 *  -> AI Reasoner -> POST /api/voice/synthesize (Fish Audio MP3) -> HTMLAudioElement Playback
 *  -> Seamless browser SpeechSynthesis fallback if offline or Fish Audio fails.
 */

class OrcaVoiceManager {
  constructor() {
    this.state = 'IDLE'; // 'IDLE' | 'LISTENING' | 'TRANSCRIBING' | 'THINKING' | 'SPEAKING' | 'ERROR'
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioStream = null;
    this.currentAudioElement = null;
    this.synthesis = window.speechSynthesis || null;
    this.currentLanguage = 'en'; // 'en' | 'ta' | 'ml'
    this.supportedMimeType = this.detectSupportedMimeType();
  }

  detectSupportedMimeType() {
    if (typeof MediaRecorder === 'undefined') return 'audio/webm';
    const candidates = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/wav',
    ];
    for (const c of candidates) {
      if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(c)) {
        return c;
      }
    }
    return 'audio/webm';
  }

  setLanguage(langCode) {
    if (!langCode) return;
    const l = langCode.toLowerCase();
    if (l.startsWith('ta')) {
      this.currentLanguage = 'ta';
    } else if (l.startsWith('ml')) {
      this.currentLanguage = 'ml';
    } else {
      this.currentLanguage = 'en';
    }

    // Stop speaking if language switched
    if (this.state === 'SPEAKING') {
      this.stopPlayback();
      this.transitionTo('IDLE');
    }
  }

  async startListening() {
    if (this.state === 'LISTENING') {
      this.stopListening();
      return;
    }

    // Stop any active audio
    this.stopPlayback();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.transitionTo('ERROR', 'Microphone access is not supported in this browser.');
      return;
    }

    try {
      this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];

      this.mediaRecorder = new MediaRecorder(this.audioStream, {
        mimeType: this.supportedMimeType,
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        this.cleanupStream();
        if (this.audioChunks.length === 0) {
          this.transitionTo('IDLE');
          return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: this.supportedMimeType });
        this.audioChunks = [];

        // Begin Transcription
        this.transitionTo('TRANSCRIBING');
        try {
          const res = await window.orcaApi.transcribeAudio(audioBlob, this.supportedMimeType, this.currentLanguage);
          if (res && res.success && res.text && res.text.trim()) {
            this.transitionTo('THINKING', res.text.trim());
          } else {
            console.warn('Groq STT returned no text or error:', res ? res.error : 'empty');
            // Check browser recognition as fallback if present
            this.transitionTo('ERROR', res && res.error ? res.error.message : 'No speech recognized. Please try again.');
          }
        } catch (err) {
          console.error('STT API failure:', err);
          this.transitionTo('ERROR', 'Voice transcription service unavailable.');
        }
      };

      this.mediaRecorder.start();
      this.transitionTo('LISTENING');
    } catch (err) {
      console.error('Microphone permission or start error:', err);
      this.cleanupStream();
      this.transitionTo('ERROR', 'Microphone permission denied or device not found.');
    }
  }

  stopListening() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      try {
        this.mediaRecorder.stop();
      } catch (e) {
        console.warn('MediaRecorder stop error:', e);
      }
    }
  }

  cleanupStream() {
    if (this.audioStream) {
      try {
        this.audioStream.getTracks().forEach(track => track.stop());
      } catch (e) {
        // ignore
      }
      this.audioStream = null;
    }
  }

  stopPlayback() {
    if (this.currentAudioElement) {
      try {
        this.currentAudioElement.pause();
        this.currentAudioElement.currentTime = 0;
      } catch (e) {
        // ignore
      }
      this.currentAudioElement = null;
    }

    if (this.synthesis && this.synthesis.speaking) {
      try {
        this.synthesis.cancel();
      } catch (e) {
        // ignore
      }
    }
  }

  cancel() {
    this.stopListening();
    this.cleanupStream();
    this.stopPlayback();
    this.transitionTo('IDLE');
  }

  async speak(text, lang = null) {
    if (!text || !text.trim()) return;
    this.stopPlayback();

    const targetLang = lang || this.currentLanguage;
    this.transitionTo('SPEAKING');

    // 1. PRIMARY: Fish Audio Backend TTS
    try {
      if (window.orcaApi) {
        const ttsRes = await window.orcaApi.synthesizeSpeech(text, targetLang);
        if (ttsRes && ttsRes.success && ttsRes.audio_base64) {
          const audioFormat = ttsRes.audio_format || 'mp3';
          const audio = new Audio(`data:audio/${audioFormat};base64,${ttsRes.audio_base64}`);
          this.currentAudioElement = audio;

          audio.onended = () => {
            this.currentAudioElement = null;
            this.transitionTo('IDLE');
          };

          audio.onerror = (e) => {
            console.warn('Audio playback error, falling back to browser SpeechSynthesis:', e);
            this.fallbackBrowserSpeak(text, targetLang);
          };

          await audio.play();
          return;
        }
      }
    } catch (ttsErr) {
      console.warn('Fish Audio synthesis failed, trying browser TTS fallback:', ttsErr);
    }

    // 2. FALLBACK: Browser SpeechSynthesis
    this.fallbackBrowserSpeak(text, targetLang);
  }

  fallbackBrowserSpeak(text, lang) {
    if (!this.synthesis) {
      this.transitionTo('IDLE');
      return;
    }

    try {
      this.synthesis.cancel();
      const locale = lang.startsWith('ta') ? 'ta-IN' : (lang.startsWith('ml') ? 'ml-IN' : 'en-IN');
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = locale;
      utterance.rate = 0.95;
      utterance.pitch = 1.0;

      utterance.onend = () => {
        this.transitionTo('IDLE');
      };

      utterance.onerror = () => {
        this.transitionTo('IDLE');
      };

      this.synthesis.speak(utterance);
    } catch (e) {
      console.warn('Browser SpeechSynthesis failed:', e);
      this.transitionTo('IDLE');
    }
  }

  transitionTo(newState, payload = null) {
    this.state = newState;
    window.dispatchEvent(new CustomEvent('orca:voiceState', {
      detail: { state: newState, payload: payload, language: this.currentLanguage }
    }));
  }
}

window.orcaVoice = new OrcaVoiceManager();
