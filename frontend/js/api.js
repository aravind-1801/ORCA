/**
 * ORCA Frontend API Client & State Synchronizer
 * Connects UI components to the FastAPI backend.
 * Provides offline persistence via localStorage and Live vs Mock toggle.
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
    // If offline, check localStorage cache first
    if (!navigator.onLine) {
      const cached = localStorage.getItem(`orca_cache_${endpoint}`);
      if (cached) {
        const parsed = JSON.parse(cached);
        parsed.data_mode = 'cached';
        parsed.connectivity = 'offline';
        return parsed;
      }
    }

    try {
      const res = await fetch(`${this.apiBase}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(options.headers || {})
        },
        ...options
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
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
      console.warn(`Fetch to ${endpoint} failed, checking local cache:`, err);
      const cached = localStorage.getItem(`orca_cache_${endpoint}`);
      if (cached) {
        const parsed = JSON.parse(cached);
        parsed.data_mode = 'cached';
        parsed.connectivity = 'offline';
        return parsed;
      }
      throw err;
    }
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
    return this._request('/recommendation/query', {
      method: 'POST',
      body: JSON.stringify({
        query: queryText,
        language,
        latitude: lat,
        longitude: lon,
      })
    });
  }

  // Alerts
  async getAlerts(lat, lon) {
    return this._request(`/alerts?lat=${lat || ''}&lon=${lon || ''}`);
  }

  async getAlertDetail(alertId, lat, lon) {
    return this._request(`/alerts/${encodeURIComponent(alertId)}?lat=${lat || ''}&lon=${lon || ''}`);
  }

  // AI Chat & Query
  async sendAIChat(message, language = 'en', lat, lon, conversationId) {
    return this._request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        language,
        latitude: lat,
        longitude: lon,
        conversation_id: conversationId
      })
    });
  }

  async submitQuery(queryText, language = 'en', lat, lon, conversationId = null) {
    return this._request('/orca/query', {
      method: 'POST',
      body: JSON.stringify({
        query: queryText,
        language: language,
        latitude: lat,
        longitude: lon,
        conversation_id: conversationId
      })
    });
  }

  async getExplanation(queryId) {
    return this._request(`/orca/explanation/${encodeURIComponent(queryId)}`);
  }

  // Voice
  async sendVoiceQuery(queryText, language = 'en', lat, lon) {
    return this._request('/voice/query', {
      method: 'POST',
      body: JSON.stringify({
        query: queryText,
        language,
        latitude: lat,
        longitude: lon
      })
    });
  }

  // Location
  async getLocation() {
    return this._request('/location');
  }

  async updateLocation(payload) {
    return this._request('/location', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  async setGpsLocation(lat, lon, locationName = null) {
    return this._request('/location/current', {
      method: 'POST',
      body: JSON.stringify({ latitude: lat, longitude: lon, location_name: locationName })
    });
  }

  // Profile
  async getProfile() {
    return this._request('/profile');
  }

  async updateProfile(updates) {
    return this._request('/profile', {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async uploadProfileImage(avatarUrlOrBase64) {
    return this._request('/profile/image', {
      method: 'POST',
      body: JSON.stringify({ image: avatarUrlOrBase64, avatar_url: avatarUrlOrBase64 })
    });
  }

  // Language
  async getLanguage() {
    return this._request('/language');
  }

  async updateLanguage(language) {
    return this._request('/language', {
      method: 'PUT',
      body: JSON.stringify({ language })
    });
  }

  // Map Data
  async getMapData(lat, lon) {
    return this._request(`/map/data?lat=${lat || ''}&lon=${lon || ''}`);
  }
}

window.orcaApi = new OrcaAPI();
