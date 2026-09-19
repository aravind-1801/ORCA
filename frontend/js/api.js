/**
 * ORCA Frontend API Client & State Synchronizer
 * Connects UI components to the FastAPI backend with timeout, cancellation,
 * error normalization, and caching.
 */

class OrcaAPI {
  constructor() {
    this.apiBase = window.ORCA_API_BASE || '/api';
    this.apiMode = localStorage.getItem('orca_api_mode') || 'live';
    this.isOnline = navigator.onLine;
    this.lastSynced = localStorage.getItem('orca_last_synced') || null;

    window.addEventListener('online', () => {
      this.isOnline = true;
      this.broadcastConnectivity(true);
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.broadcastConnectivity(false);
    });
  }

  broadcastConnectivity(isOnline) {
    window.dispatchEvent(new CustomEvent('orca:connectivity', { detail: { isOnline } }));
  }

  setMode(mode) {
    this.apiMode = mode;
    localStorage.setItem('orca_api_mode', mode);
  }

  async _request(endpoint, options = {}) {
    const timeoutMs = options.timeout || 15000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const reqId = 'req_' + Math.random().toString(36).substring(2, 9);
    const headers = {
      'Accept': 'application/json',
      'X-Request-ID': reqId,
      ...(options.headers || {})
    };

    // Only set Content-Type to JSON if body is not FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const fetchOptions = {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    };

    // If offline, check localStorage cache first
    if (!navigator.onLine) {
      clearTimeout(timeoutId);
      const cached = localStorage.getItem(`orca_cache_${endpoint}`);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          parsed.data_mode = 'cached';
          parsed.connectivity = 'offline';
          return parsed;
        } catch (e) {
          // ignore
        }
      }
    }

    try {
      const res = await fetch(`${this.apiBase}${endpoint}`, fetchOptions);
      clearTimeout(timeoutId);

      if (!res.ok) {
        let errBody = null;
        try {
          errBody = await res.json();
        } catch (e) {
          errBody = await res.text();
        }
        const error = new Error(`HTTP ${res.status}: ${res.statusText}`);
        error.status = res.status;
        error.details = errBody;
        throw error;
      }

      const data = await res.json();
      // Cache successful GET responses for offline resilience
      if (!options.method || options.method === 'GET') {
        try {
          localStorage.setItem(`orca_cache_${endpoint}`, JSON.stringify(data));
          localStorage.setItem('orca_last_synced', new Date().toISOString());
          this.lastSynced = new Date().toISOString();
        } catch (e) {
          console.warn('LocalStorage write failed:', e);
        }
      }
      return data;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        console.warn(`Request to ${endpoint} timed out after ${timeoutMs}ms.`);
        err.message = `Request timed out after ${Math.round(timeoutMs / 1000)}s.`;
      }

      // Fall back to cache if available
      const cached = localStorage.getItem(`orca_cache_${endpoint}`);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          parsed.data_mode = 'cached';
          parsed.is_cached_fallback = true;
          return parsed;
        } catch (e) {
          // ignore
        }
      }
      throw err;
    }
  }

  // HTTP Helper methods
  async get(endpoint) {
    return this._request(endpoint, { method: 'GET' });
  }

  async post(endpoint, body) {
    return this._request(endpoint, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  async put(endpoint, body) {
    return this._request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  // Runtime Configuration
  async getConfig() {
    return this._request('/config');
  }

  // Health & Diagnostics
  async getHealthDashboard() {
    return this._request('/health/dashboard');
  }

  // Marine Status
  async getMarineStatus(lat, lon) {
    const qLat = lat !== undefined ? lat : '';
    const qLon = lon !== undefined ? lon : '';
    return this._request(`/marine/status?lat=${qLat}&lon=${qLon}`);
  }

  // Weather
  async getWeather(lat, lon) {
    return this._request(`/weather?lat=${lat || ''}&lon=${lon || ''}`);
  }

  // Ocean
  async getOcean(lat, lon) {
    return this._request(`/ocean?lat=${lat || ''}&lon=${lon || ''}`);
  }

  // Fishing Zones
  async getFishingZones(lat, lon) {
    return this._request(`/fishing-zones?lat=${lat || ''}&lon=${lon || ''}`);
  }

  async getFishingZoneDetail(zoneId, lat, lon) {
    return this._request(`/fishing-zones/${encodeURIComponent(zoneId)}?lat=${lat || ''}&lon=${lon || ''}`);
  }

  // Recommendations
  async getRecommendation(lat, lon) {
    return this._request(`/recommendation?lat=${lat || ''}&lon=${lon || ''}`);
  }

  async submitRecommendationQuery(queryText, language = 'en', lat, lon) {
    return this.post('/recommendation/query', {
      query: queryText,
      language,
      latitude: lat,
      longitude: lon,
    });
  }

  // Alerts
  async getAlerts(lat, lon) {
    return this._request(`/alerts?lat=${lat || ''}&lon=${lon || ''}`);
  }

  async getAlertDetail(alertId, lat, lon) {
    return this._request(`/alerts/${encodeURIComponent(alertId)}?lat=${lat || ''}&lon=${lon || ''}`);
  }

  // AI Chat & Reasoning
  async sendAIChat(message, language = 'en', lat, lon, conversationId) {
    return this.post('/ai/chat', {
      message,
      query: message,
      language,
      latitude: lat,
      longitude: lon,
      conversation_id: conversationId,
    });
  }

  async getExplanation(queryId) {
    return this._request(`/orca/explanation/${encodeURIComponent(queryId)}`);
  }

  // Speech-to-Text (Real Groq Whisper Backend API)
  async transcribeAudio(audioBlob, mimeType = 'audio/webm', language = 'en') {
    const formData = new FormData();
    const ext = mimeType.includes('mp4') ? 'mp4' : (mimeType.includes('ogg') ? 'ogg' : (mimeType.includes('wav') ? 'wav' : 'webm'));
    formData.append('file', audioBlob, `speech.${ext}`);
    formData.append('language', language);

    return this.post('/voice/transcribe', formData);
  }

  // Text-to-Speech (Real Fish Audio Backend API)
  async synthesizeSpeech(text, language = 'en', voiceId = null) {
    return this.post('/voice/synthesize', {
      text,
      language,
      voice_id: voiceId,
    });
  }

  // Location APIs
  async getLocation() {
    return this._request('/location');
  }

  async updateLocation(payload) {
    return this.put('/location', payload);
  }

  async setGpsLocation(lat, lon, locationName = null) {
    return this.post('/location/current', {
      latitude: lat,
      longitude: lon,
      location_name: locationName,
    });
  }

  // Profile APIs
  async getProfile() {
    return this._request('/profile');
  }

  async updateProfile(updates) {
    return this.put('/profile', updates);
  }

  async uploadProfileImage(avatarUrlOrBase64) {
    return this.post('/profile/image', {
      image: avatarUrlOrBase64,
      avatar_url: avatarUrlOrBase64,
    });
  }

  // Language Preference
  async getLanguage() {
    return this._request('/language');
  }

  async updateLanguage(language) {
    return this.put('/language', { language });
  }

  // Map Data
  async getMapData(lat, lon) {
    return this._request(`/map/data?lat=${lat || ''}&lon=${lon || ''}`);
  }

  // Refresh
  async refreshData(lat, lon) {
    const qLat = lat !== undefined ? `?lat=${lat}&lon=${lon}` : '';
    return this.post(`/refresh${qLat}`, {});
  }

  // RAG / Local Intelligence
  async getRagStatus() {
    return this._request('/rag/status');
  }

  async searchRag(query, language = 'en', topK = 5) {
    return this.post('/rag/search', {
      query,
      language,
      top_k: topK,
    });
  }
}

window.orcaApi = new OrcaAPI();
