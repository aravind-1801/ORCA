/**
 * ORCA Master Mobile Application Controller
 * ==========================================
 * Single Global State Architecture:
 *  - 100% Consistent Centralized i18n (en-IN | ta-IN | ml-IN)
 *  - Interactive Marine Chart Engine with Leaflet and Vector Fallback
 *  - Multi-Location System with instant Coastal Presets (Kollam, Kochi, Alappuzha, TVM, Chennai, Custom)
 *  - Persistent Editable Fisherman Profile with Avatar Management
 *  - Working Voice & Speech Integration with Multi-Agent Orchestration
 *  - Working Emergency & Hazard Alerts Flow
 *  - Zero dead buttons
 */

(function () {
  'use strict';

  // ── Global Application State ──────────────────────────────────────────────
  let currentScreen = 'home';
  let currentSelectedZone = 'A12';
  let latestQueryId = null;
  let sessionConversationId = 'orca_sess_' + Math.random().toString(36).substring(2, 9);
  let cachedZonesData = {};
  let currentCoords = {
    lat: 8.88,
    lon: 76.59,
    name: 'Kollam Coast',
    harbor: 'Neendakara Harbor',
  };

  // Coastal Presets for quick switching during presentation
  const LOCATION_PRESETS = {
    'kollam': {
      name: 'Kollam Coast',
      harbor: 'Neendakara Harbor',
      lat: 8.88,
      lon: 76.59,
      state: 'Kerala',
    },
    'kochi': {
      name: 'Kochi Coast',
      harbor: 'Cochin Fisheries Harbor',
      lat: 9.93,
      lon: 76.26,
      state: 'Kerala',
    },
    'alappuzha': {
      name: 'Alappuzha Coast',
      harbor: 'Thottappally Spillway Harbor',
      lat: 9.49,
      lon: 76.32,
      state: 'Kerala',
    },
    'thiruvananthapuram': {
      name: 'Vizhinjam Coast',
      harbor: 'Vizhinjam International Harbor',
      lat: 8.52,
      lon: 76.94,
      state: 'Kerala',
    },
    'chennai': {
      name: 'Chennai Coast',
      harbor: 'Kasimedu Fishing Harbor',
      lat: 13.08,
      lon: 80.27,
      state: 'Tamil Nadu',
    },
  };

  // Language state (single source of truth)
  let rawStoredLang = localStorage.getItem('orca_language') || 'en-IN';
  let currentLanguage = normalizeLanguage(rawStoredLang);

  function normalizeLanguage(lang) {
    if (!lang) return 'en-IN';
    const l = lang.toString().toLowerCase();
    if (l.startsWith('ta') || l.includes('tamil') || l.includes('தமிழ்')) return 'ta-IN';
    if (l.startsWith('ml') || l.includes('malayalam') || l.includes('മലയ')) return 'ml-IN';
    return 'en-IN';
  }

  function formatDistance(distKm) {
    const rounded = Math.round(distKm || 12);
    if (currentLanguage.startsWith('ta')) return `${rounded} கி.மீ`;
    if (currentLanguage.startsWith('ml')) return `${rounded} കി.മീ`;
    return `${rounded} km`;
  }

  function formatDirection(dir) {
    if (!dir) return '';
    const d = dir.toString().toLowerCase();
    if (currentLanguage.startsWith('ta')) {
      if (d.includes('southwest') || d === 'sw') return 'தென்மேற்கு';
      if (d.includes('northwest') || d === 'nw') return 'வடமேற்கு';
      if (d.includes('southeast') || d === 'se') return 'தென்கிழக்கு';
      if (d.includes('northeast') || d === 'ne') return 'வடகிழக்கு';
      if (d.includes('south') || d === 's') return 'தெற்கு';
      if (d.includes('north') || d === 'n') return 'வடக்கு';
      if (d.includes('west') || d === 'w') return 'மேற்கு';
      if (d.includes('east') || d === 'e') return 'கிழக்கு';
      if (d.includes('ssw')) return 'தெற்கு-தென்மேற்கு';
      if (d.includes('wsw')) return 'மேற்கு-தென்மேற்கு';
      return dir;
    }
    if (currentLanguage.startsWith('ml')) {
      if (d.includes('southwest') || d === 'sw') return 'തെക്കുപടിഞ്ഞാറ്';
      if (d.includes('northwest') || d === 'nw') return 'വടക്കുപടിഞ്ഞാറ്';
      if (d.includes('southeast') || d === 'se') return 'തെക്കുകിഴക്ക്';
      if (d.includes('northeast') || d === 'ne') return 'വടക്കുകിഴക്ക്';
      if (d.includes('south') || d === 's') return 'തെക്ക്';
      if (d.includes('north') || d === 'n') return 'വടക്ക്';
      if (d.includes('west') || d === 'w') return 'പടിഞ്ഞാറ്';
      if (d.includes('east') || d === 'e') return 'കിഴക്ക്';
      if (d.includes('ssw')) return 'തെക്ക്-തെക്കുപടിഞ്ഞാറ്';
      if (d.includes('wsw')) return 'പടിഞ്ഞാറ്-തെക്കുപടിഞ്ഞാറ്';
      return dir;
    }
    return dir;
  }

  function formatMinutes(min) {
    const m = Math.round(min || 0);
    if (currentLanguage.startsWith('ta')) return `${m} நிமிடங்கள்`;
    if (currentLanguage.startsWith('ml')) return `${m} മിനിറ്റ്`;
    return `${m} min`;
  }

  function formatDepth(depthM) {
    const d = Math.round(depthM || 0);
    if (currentLanguage.startsWith('ta')) return `${d} மீ`;
    if (currentLanguage.startsWith('ml')) return `${d} മീറ്റർ`;
    return `${d}m`;
  }

  function t(k) {
    return window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;
  }

  // ── Centralized Reactive Application Store ───────────────────────────────
  const savedProfile = (() => {
    try { return JSON.parse(localStorage.getItem('orca_profile') || '{}'); } catch (e) { return {}; }
  })();
  const savedLocation = (() => {
    try { return JSON.parse(localStorage.getItem('orca_location') || '{}'); } catch (e) { return {}; }
  })();

  window.orcaState = {
    language: normalizeLanguage(localStorage.getItem('orca_language') || 'en-IN'),
    profile: {
      name: savedProfile.name || 'Rajan Kumar',
      vessel_name: savedProfile.vessel_name || 'Sea King II',
      registration_no: savedProfile.registration_no || 'KL-02-F-491',
      vessel_type: savedProfile.vessel_type || 'Motorized Craft (28ft)',
      base_port: savedProfile.base_port || 'Kollam, KL',
      harbor: savedProfile.harbor || 'Neendakara Harbor',
      location_name: savedProfile.location_name || 'Kollam Coast',
      preferred_language: savedProfile.preferred_language || 'en',
      avatar_url: savedProfile.avatar_url || 'assets/fisherman.png',
    },
    location: {
      latitude: savedLocation.latitude || 8.88,
      longitude: savedLocation.longitude || 76.59,
      location_name: savedLocation.location_name || 'Kollam Coast',
      harbor: savedLocation.harbor || 'Neendakara Harbor',
    },
    weather: null,
    ocean: null,
    zones: [],
    selectedZoneId: 'A12',
    alerts: [],
    recommendation: null,

    subscribers: [],
    subscribe(fn) {
      this.subscribers.push(fn);
    },
    set(updates) {
      Object.assign(this, updates);
      if (updates.language) {
        localStorage.setItem('orca_language', updates.language);
      }
      if (updates.profile) {
        localStorage.setItem('orca_profile', JSON.stringify(this.profile));
      }
      if (updates.location) {
        localStorage.setItem('orca_location', JSON.stringify(this.location));
      }
      this.subscribers.forEach(fn => fn(this));
      window.dispatchEvent(new CustomEvent('orca:stateChanged', { detail: this }));
    }
  };

  // ── DOM References ────────────────────────────────────────────────────────
  const screens = {
    'home': document.getElementById('screen-home'),
    'coastal-map': document.getElementById('screen-map'),
    'zone-details': document.getElementById('screen-zone-details'),
    'ask-orca': document.getElementById('screen-ask-orca'),
    'why-orca': document.getElementById('screen-why-orca'),
    'hazard-alerts': document.getElementById('screen-alerts'),
    'fisherman-profile': document.getElementById('screen-profile'),
  };


  const navLinks = document.querySelectorAll('nav [data-path]');
  const connText = document.getElementById('header-conn-text');
  const connectivityBadge = document.getElementById('header-conn-status');
  const modeBadge = document.getElementById('header-mode-badge');
  const langToggleBtn = document.getElementById('header-lang-btn');
  const locationTitle = document.getElementById('home-location-title');

  // ── Application Entry Point ───────────────────────────────────────────────
  async function init() {
    // 1. Load active location from backend or local storage
    try {
      const locData = await window.orcaApi.getLocation();
      if (locData && locData.latitude && locData.longitude) {
        currentCoords.lat = locData.latitude;
        currentCoords.lon = locData.longitude;
        currentCoords.name = locData.location_name || 'Kollam Coast';
        currentCoords.harbor = locData.harbor || 'Neendakara Harbor';
      }
    } catch (e) {
      console.warn('Backend location fetch notice:', e.message);
    }

    // 2. Setup navigation and listeners
    setupNavigation();
    setupEventListeners();
    setupVoiceHandlers();

    // 3. Initialize Marine Chart
    if (window.orcaMarineMap) {
      window.orcaMarineMap.init('marine-chart-container');
    }

    // 4. Apply initial language across all UI
    setGlobalLanguage(currentLanguage, false);

    // 5. Deep link check
    const hash = window.location.hash.replace('#', '');
    if (screens[hash]) {
      switchScreen(hash);
    } else {
      switchScreen('home');
    }

    // 6. Initial data fetch
    await refreshAllData();

    // 7. Sync profile preferences from backend
    try {
      const profile = await window.orcaApi.getProfile();
      if (profile && profile.preferred_language) {
        const backendLang = normalizeLanguage(profile.preferred_language);
        if (backendLang !== currentLanguage) {
          setGlobalLanguage(backendLang, false);
        }
      }
    } catch (e) {
      console.warn('Profile sync notice:', e.message);
    }
  }

  // ── Navigation Controller ─────────────────────────────────────────────────
  function setupNavigation() {
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const path = link.getAttribute('data-path');
        if (path) switchScreen(path);
      });
    });

    window.addEventListener('popstate', (e) => {
      if (e.state && e.state.screen && screens[e.state.screen]) {
        showScreen(e.state.screen, false);
      }
    });
  }

  function switchScreen(screenName) {
    if (!screens[screenName]) return;

    // Cancel voice when leaving ask-orca
    if (currentScreen === 'ask-orca' && screenName !== 'ask-orca') {
      if (window.orcaVoice) window.orcaVoice.cancel();
    }

    showScreen(screenName, true);

    if (screenName === 'home') loadHome();
    else if (screenName === 'coastal-map') loadMap();
    else if (screenName === 'zone-details') loadZoneDetails(currentSelectedZone);
    else if (screenName === 'why-orca') loadWhyOrca(latestQueryId);
    else if (screenName === 'hazard-alerts') loadAlerts();
    else if (screenName === 'fisherman-profile') loadProfile();
  }

  function showScreen(screenName, pushHistory = true) {
    currentScreen = screenName;
    Object.keys(screens).forEach(key => {
      if (screens[key]) {
        screens[key].classList.toggle('hidden', key !== screenName);
      }
    });

    // Update bottom nav active classes
    navLinks.forEach(link => {
      const path = link.getAttribute('data-path');
      const isSelected = path === screenName ||
        (screenName === 'zone-details' && path === 'coastal-map') ||
        (screenName === 'why-orca' && path === 'home');

      if (path === 'ask-orca') {
        // Center button highlight
        if (isSelected) {
          link.classList.add('ring-4', 'ring-secondary-container');
        } else {
          link.classList.remove('ring-4', 'ring-secondary-container');
        }
      } else {
        if (isSelected) {
          link.classList.add('text-primary-container', 'font-bold');
          link.classList.remove('text-on-surface-variant');
        } else {
          link.classList.remove('text-primary-container', 'font-bold');
          link.classList.add('text-on-surface-variant');
        }
      }
    });

    window.scrollTo(0, 0);
    if (pushHistory) {
      history.pushState({ screen: screenName }, '', `#${screenName}`);
    }
  }

  window.navigateToScreen = switchScreen;

  // ── GLOBAL INTERNATIONALIZATION CONTROLLER ────────────────────────────────
  function setGlobalLanguage(langCode, syncBackend = true) {
    currentLanguage = normalizeLanguage(langCode);
    localStorage.setItem('orca_language', currentLanguage);

    // 1. Update Voice Manager
    if (window.orcaVoice) window.orcaVoice.setLanguage(currentLanguage);

    // 2. Update Header Language Button
    updateHeaderLangButton();

    // 3. Update Profile Language Buttons
    updateProfileLangButtons();

    // 4. Apply Static UI Translations to ALL screens
    if (window.orcaI18n) {
      window.orcaI18n.applyTranslations(currentLanguage);
    }

    // 5. Update dynamic content for active screen & refresh all screen data
    refreshCurrentScreenLanguage();
    refreshAllData();

    // 6. Persist to Backend Profile & Language API
    if (syncBackend && window.orcaApi) {
      const apiCode = currentLanguage.startsWith('ta') ? 'ta' : (currentLanguage.startsWith('ml') ? 'ml' : 'en');
      window.orcaApi.updateLanguage(apiCode).catch(err => {
        console.warn('Backend language sync notice:', err.message);
      });
    }
  }

  function updateHeaderLangButton() {
    const btn = document.getElementById('header-lang-btn');
    const labelSpan = document.getElementById('header-lang-label');
    const labels = { 'ml-IN': 'മലയാളം', 'ta-IN': 'தமிழ்', 'en-IN': 'English' };
    const label = labels[currentLanguage] || 'English';
    if (labelSpan) {
      labelSpan.textContent = label;
    } else if (btn) {
      btn.innerHTML = `<span class="text-xs font-bold text-primary-container leading-none" id="header-lang-label">${label}</span>`;
    }
  }


  function updateProfileLangButtons() {
    const profileLangBtns = document.querySelectorAll('[data-profile-lang]');
    profileLangBtns.forEach(btn => {
      const btnLang = btn.getAttribute('data-profile-lang');
      const targetLang = btnLang === 'ta' ? 'ta-IN' : (btnLang === 'ml' ? 'ml-IN' : 'en-IN');
      const isActive = targetLang === currentLanguage;
      btn.className = isActive
        ? 'min-h-touch-target-min px-2 py-2 rounded-lg bg-primary-container text-on-primary flex flex-col items-center justify-center text-center shadow-sm active:scale-98 transition-transform'
        : 'min-h-touch-target-min px-2 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface flex flex-col items-center justify-center text-center active:scale-98 transition-transform';
    });
  }

  function refreshCurrentScreenLanguage() {
    if (!window.orcaI18n) return;
    const t = (k) => window.orcaI18n.t(k, currentLanguage);

    // Nav labels (ask-orca excluded — mic button is icon-only, no label)
    const navMap = {
      'home': 'nav.home',
      'coastal-map': 'nav.map',
      'hazard-alerts': 'nav.alerts',
      'fisherman-profile': 'nav.profile',
    };
    navLinks.forEach(link => {
      const path = link.getAttribute('data-path');
      const key = navMap[path];
      if (key) {
        const span = link.querySelector('span:last-child');
        if (span) span.textContent = t(key);
      }
    });

    // Update sea status
    const seaStatusEl = document.getElementById('home-sea-status');
    if (seaStatusEl) {
      const txt = (seaStatusEl.getAttribute('data-raw-status') || 'SAFE').toUpperCase();
      seaStatusEl.textContent = t(`home.${txt.toLowerCase()}`);
    }
  }

  // Expose global language methods on window for direct HTML inline callers
  window.cycleLanguage = function () {
    let next;
    if (currentLanguage === 'en-IN') next = 'ta-IN';
    else if (currentLanguage === 'ta-IN') next = 'ml-IN';
    else next = 'en-IN';
    setGlobalLanguage(next, true);
    const label = next === 'ta-IN' ? 'தமிழ்' : (next === 'ml-IN' ? 'മലയാളം' : 'English');
    showToast(`Language switched to ${label}`, 'success');
  };

  window.setGlobalLanguage = setGlobalLanguage;
  window.selectProfileLanguage = function (lang) {
    const target = lang === 'ta' ? 'ta-IN' : (lang === 'ml' ? 'ml-IN' : 'en-IN');
    setGlobalLanguage(target, true);
    const label = target === 'ta-IN' ? 'தமிழ்' : (target === 'ml-IN' ? 'മലയാളം' : 'English');
    showToast(`Language switched to ${label}`, 'success');
  };

  // ── EVENT LISTENERS ───────────────────────────────────────────────────────
  function setupEventListeners() {
    // Header language toggle
    const langBtn = document.getElementById('header-lang-btn');
    if (langBtn) {
      langBtn.addEventListener('click', () => window.cycleLanguage());
    }


    // Connectivity events
    window.addEventListener('orca:connectivity', (e) => {
      updateConnectivityUI(e.detail.isOnline);
    });

    // Home quick voice bar
    const homeVoiceBar = document.getElementById('home-voice-bar');
    if (homeVoiceBar) {
      homeVoiceBar.addEventListener('click', () => {
        switchScreen('ask-orca');
        setTimeout(() => {
          if (window.orcaVoice) window.orcaVoice.startListening();
        }, 350);
      });
    }

    // View on Map button on home screen
    const viewOnMapBtn = document.getElementById('home-view-map-btn');
    if (viewOnMapBtn) {
      viewOnMapBtn.addEventListener('click', () => switchScreen('coastal-map'));
    }

    // Why ORCA trigger
    const whyTrigger = document.getElementById('home-why-btn');
    if (whyTrigger) {
      whyTrigger.addEventListener('click', () => switchScreen('why-orca'));
    }

    // Location selector trigger in header
    const locHeader = document.getElementById('header-location-trigger');
    if (locHeader) {
      locHeader.addEventListener('click', () => window.openLocationModal());
    }

    // Emergency call modal triggers
    const radioTestBtn = document.getElementById('radio-test-btn');
    if (radioTestBtn) {
      radioTestBtn.addEventListener('click', () => {
        showToast('VHF Channel 16 test transmission: 156.8 MHz - All Clear');
        if (window.orcaVoice) {
          window.orcaVoice.speak('VHF Channel 16 radio check. Signal strength five by five. Channel clear.');
        }
      });
    }
  }

  function updateConnectivityUI(isOnline) {
    const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;
    if (connText) connText.textContent = isOnline ? t('header.online') : t('header.offline');
    if (connectivityBadge) {
      connectivityBadge.className = isOnline
        ? 'w-2 h-2 rounded-full bg-on-tertiary-container animate-pulse'
        : 'w-2 h-2 rounded-full bg-outline animate-none';
    }
  }

  async function refreshAllData() {
    try {
      await loadHome();
      if (currentScreen === 'coastal-map') await loadMap();
    } catch (e) {
      console.warn('Initial load notice:', e.message);
    }
  }

  // ── TOAST NOTIFICATIONS ───────────────────────────────────────────────────
  function showToast(message, type = 'info') {
    let toast = document.getElementById('orca-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'orca-toast';
      toast.className = 'fixed top-20 left-1/2 -translate-x-1/2 z-[100] px-4 py-2.5 rounded-xl shadow-lg font-headline-sm text-xs font-semibold flex items-center gap-2 transition-all duration-300 opacity-0 pointer-events-none';
      document.body.appendChild(toast);
    }

    const bgClass = type === 'success' ? 'bg-primary-container text-on-primary border border-tertiary-fixed'
      : (type === 'error' ? 'bg-error text-on-error' : 'bg-surface-container-highest text-primary-container');

    toast.className = `fixed top-20 left-1/2 -translate-x-1/2 z-[100] px-4 py-2.5 rounded-xl shadow-lg font-headline-sm text-xs font-semibold flex items-center gap-2 transition-all duration-300 ${bgClass} opacity-100 pointer-events-auto`;
    toast.innerHTML = `<span class="material-symbols-outlined text-[18px]">${type === 'success' ? 'check_circle' : 'info'}</span><span>${message}</span>`;

    setTimeout(() => {
      toast.classList.add('opacity-0', 'pointer-events-none');
    }, 3500);
  }

  window.showToast = showToast;

  // ── SCREEN 1: HOME ────────────────────────────────────────────────────────
  async function loadHome() {
    try {
      const data = await window.orcaApi.getMarineStatus(currentCoords.lat, currentCoords.lon);
      if (!data) return;

      const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;

      if (locationTitle) locationTitle.textContent = currentCoords.name || data.location.name;

      const harborEl = document.getElementById('home-harbor-title');
      if (harborEl) harborEl.textContent = currentCoords.harbor || 'Neendakara Harbor';

      const statusEl = document.getElementById('home-sea-status');
      if (statusEl) {
        const st = (data.safety.status || 'SAFE').toLowerCase();
        statusEl.setAttribute('data-raw-status', st);
        statusEl.textContent = t(`home.${st}`);
      }

      const favorableEl = document.getElementById('home-sea-favorable');
      if (favorableEl) favorableEl.textContent = t('home.favorable');

      if (window.orcaCompanion) window.orcaCompanion.setSeaCondition(data.safety.status);

      // Weather metrics
      const windEl = document.getElementById('home-metric-wind');
      const waveEl = document.getElementById('home-metric-wave');
      const rainEl = document.getElementById('home-metric-rain');
      const waterEl = document.getElementById('home-metric-water');

      if (windEl) windEl.innerHTML = `${Math.round(data.weather.wind_kmh)} <span class="text-[11px] font-normal text-on-surface-variant">km/h</span>`;
      if (waveEl) waveEl.innerHTML = `${data.weather.wave_m.toFixed(1)} <span class="text-[11px] font-normal text-on-surface-variant">m</span>`;
      if (rainEl) rainEl.textContent = t('home.metric.rainLow');
      if (waterEl) waterEl.innerHTML = `${data.weather.water_temp_c.toFixed(1)}<span class="text-[11px] font-normal text-on-surface-variant">°C</span>`;

      // Best zone
      const zoneTitle = document.getElementById('home-zone-title');
      const zoneSpecies = document.getElementById('home-zone-species');
      const zoneHeading = document.getElementById('home-zone-heading');
      const zoneDepth = document.getElementById('home-zone-depth');
      const zoneRunTime = document.getElementById('home-zone-runtime');

      if (zoneTitle) zoneTitle.textContent = `${formatDistance(data.best_zone.distance_km)} ${formatDirection(data.best_zone.direction)}`;
      if (zoneSpecies) zoneSpecies.textContent = t('zone.targetSpecies');
      if (zoneHeading) zoneHeading.textContent = `${t('home.course')} ${data.best_zone.course}°`;
      if (zoneDepth) zoneDepth.textContent = `${t('home.depth')} ${formatDepth(data.best_zone.depth_m)}`;
      if (zoneRunTime) zoneRunTime.textContent = `${t('home.runtime')} ${formatMinutes(data.best_zone.est_run_time_min)}`;

      // Recommendation text — dynamically built using live zone data + localized helpers
      const recText = document.getElementById('home-recommendation-text');
      if (recText) {
        const dist = formatDistance(data.best_zone.distance_km);
        const dir = formatDirection(data.best_zone.direction || 'Southwest');
        const apiRec = data.recommendation && data.recommendation.text;
        if (currentLanguage.startsWith('ta')) {
          recText.textContent = `இன்று கடல் நிலை உகந்தது. பரிந்துரைக்கப்பட்ட பகுதி: ${dist} ${dir}. மீன்பிடிக்க சிறந்த வாய்ப்பு உள்ளது.`;
        } else if (currentLanguage.startsWith('ml')) {
          recText.textContent = `ഇന്ന് കടൽ ശാന്തമാണ്. ശുപാർശ ചെയ്ത മേഖല: ${dist} ${dir}. മീൻപിടുത്തത്തിന് ഉത്തമ സമയം.`;
        } else {
          recText.textContent = apiRec || `Sea conditions are favorable. Recommended zone: ${dist} ${dir}. High catch probability.`;
        }
      }


      if (modeBadge) modeBadge.textContent = (data.data_mode || 'DEMO').toUpperCase();
    } catch (e) {
      console.warn('loadHome error:', e);
    }
  }

  // ── SCREEN 2: MAP ─────────────────────────────────────────────────────────
  async function loadMap() {
    try {
      if (window.orcaMarineMap) {
        if (!window.orcaMarineMap.isInitialized) {
          window.orcaMarineMap.init('marine-chart-container');
        }
        window.orcaMarineMap.setCenter(currentCoords.lat, currentCoords.lon);
        if (typeof window.orcaMarineMap.resize === 'function') {
          window.orcaMarineMap.resize();
        }
      }

      const data = await window.orcaApi.getFishingZones(currentCoords.lat, currentCoords.lon);
      if (!data || !data.zones) return;

      data.zones.forEach(z => {
        cachedZonesData[z.id || z.code] = z;
      });

      // Update interactive Marine Chart
      if (window.orcaMarineMap) {
        window.orcaMarineMap.setZones(data.zones, data.recommended_zone_id || 'A12');
      }

      selectMapZone(currentSelectedZone || 'A12');
    } catch (err) {
      console.error('Failed to load map data:', err);
    }
  }


  function selectMapZone(zoneId) {
    currentSelectedZone = zoneId;
    const data = cachedZonesData[zoneId] || {
      id: 'A12',
      code: 'Zone A-12',
      distance_km: 12.0,
      direction: 'Southwest',
      course_deg: 218,
      bottom_depth_m: 44,
      potential: 'high',
      target_species: 'Indian Mackerel & Sardines',
    };

    if (window.orcaMarineMap) {
      window.orcaMarineMap.selectZone(zoneId);
    }

    const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;

    const sheetId = document.getElementById('sheet-zone-id');
    const sheetDist = document.getElementById('sheet-distance');
    const sheetBadge = document.getElementById('sheet-badge');
    const telCourse = document.getElementById('telemetry-course');
    const telDepth = document.getElementById('telemetry-depth');

    if (sheetId) sheetId.textContent = data.code || `ZONE ${data.id}`;
    if (sheetDist) {
      sheetDist.textContent = `${formatDistance(data.distance_km || 12)} ${formatDirection(data.direction || 'SW')}`;
    }
    if (sheetBadge) {
      sheetBadge.textContent = t('home.highPotential');
    }
    if (telCourse) telCourse.textContent = `${t('home.course')} ${data.course_deg || 218}° ${formatDirection('SSW')}`;
    if (telDepth) telDepth.textContent = `${formatDepth(data.bottom_depth_m || 44)} ${t('home.depth')}`;
  }

  window.selectZone = selectMapZone;
  window.handleViewDetails = function () { switchScreen('zone-details'); };
  window.handleStartNavigation = function () {
    const data = cachedZonesData[currentSelectedZone] || { code: 'Zone A-12', course_deg: 218 };
    const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;
    const msg = `${t('common.navStarted')} ${data.code || 'Zone A-12'} (${data.course_deg || 218}° SSW)`;
    showToast(msg, 'success');
    if (window.orcaVoice) {
      window.orcaVoice.speak(msg);
    }
  };

  // ── SCREEN 3: ZONE DETAILS ────────────────────────────────────────────────
  async function loadZoneDetails(zoneId) {
    try {
      const data = await window.orcaApi.getFishingZoneDetail(zoneId, currentCoords.lat, currentCoords.lon);
      if (!data) return;

      const title = document.getElementById('detail-zone-distance');
      const badge = document.getElementById('detail-zone-badge');
      const course = document.getElementById('detail-course');
      const depth = document.getElementById('detail-depth');
      const sst = document.getElementById('detail-sst');
      const chloro = document.getElementById('detail-chlorophyll');
      const wind = document.getElementById('detail-wind');
      const wave = document.getElementById('detail-wave');

      if (title) title.textContent = `${formatDistance(data.distance_km)} ${formatDirection(data.direction)}`;
      if (badge) badge.textContent = data.potential === 'high' ? t('home.highPotential') : data.potential.toUpperCase();
      if (course) course.textContent = `${data.course_deg}° ${formatDirection('SW')}`;
      if (depth) depth.textContent = `${formatDepth(data.bottom_depth_m)}`;

      if (data.diagnostics) {
        if (sst) sst.textContent = `${data.diagnostics.sea_surface_temp_c}°C`;
        if (chloro) chloro.textContent = data.diagnostics.chlorophyll_density;
        if (wind) wind.textContent = `${Math.round(data.diagnostics.surface_wind_kmh)} km/h`;
        if (wave) wave.textContent = `${data.diagnostics.wave_height_m.toFixed(1)} m`;
      }
    } catch (err) {
      console.error('Failed to load zone detail:', err);
    }
  }

  // ── SCREEN 4: ASK ORCA ────────────────────────────────────────────────────
  function setupVoiceHandlers() {
    const micBtn = document.getElementById('orca-mic-trigger');
    const micStatus = document.getElementById('mic-status-label');
    const statusBeacon = document.getElementById('status-beacon');
    const waveOuter = document.getElementById('wave-ring-outer');

    if (micBtn) {
      micBtn.addEventListener('click', () => {
        if (window.orcaVoice && window.orcaVoice.isListening) {
          window.orcaVoice.stopListening();
        } else if (window.orcaVoice) {
          window.orcaVoice.startListening();
        }
      });
    }

    window.addEventListener('orca:voiceState', (e) => {
      const { state, payload } = e.detail;
      const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;

      switch (state) {
        case 'LISTENING':
          if (micStatus) micStatus.textContent = t('ask.listening');
          if (statusBeacon) statusBeacon.className = 'w-2.5 h-2.5 rounded-full bg-error animate-ping';
          if (waveOuter) waveOuter.classList.add('animate-ping');
          break;
        case 'PROCESSING':
          if (micStatus) micStatus.textContent = t('ask.processing');
          if (statusBeacon) statusBeacon.className = 'w-2.5 h-2.5 rounded-full bg-secondary animate-pulse';
          if (waveOuter) waveOuter.classList.remove('animate-ping');
          if (payload) {
            executeOrcaQuery(payload);
          }
          break;
        case 'RESPONDING':
          if (micStatus) micStatus.textContent = 'Speaking...';
          if (statusBeacon) statusBeacon.className = 'w-2.5 h-2.5 rounded-full bg-on-tertiary-container animate-pulse';
          break;
        case 'IDLE':
        default:
          if (micStatus) micStatus.textContent = t('ask.micPrompt');
          if (statusBeacon) statusBeacon.className = 'w-2.5 h-2.5 rounded-full bg-on-tertiary-container animate-pulse';
          if (waveOuter) waveOuter.classList.remove('animate-ping');
          break;
      }
    });
  }

  async function executeOrcaQuery(queryText) {
    const answerEl = document.getElementById('orca-answer-text');
    const safetyToken = document.getElementById('orca-response-safety-token');
    const zoneLabel = document.getElementById('orca-rec-zone-label');
    const micStatus = document.getElementById('mic-status-label');

    const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;

    if (micStatus) micStatus.textContent = t('ask.processing');
    if (answerEl) answerEl.textContent = t('common.loading');

    try {
      const langCode = currentLanguage.startsWith('ta') ? 'ta' : (currentLanguage.startsWith('ml') ? 'ml' : 'en');
      const res = await window.orcaApi.sendAIChat(queryText, langCode, currentCoords.lat, currentCoords.lon, sessionConversationId);

      latestQueryId = res.query_id || 'latest';

      if (answerEl) answerEl.textContent = res.response;
      const sourceEl = document.getElementById('orca-response-source');
      if (sourceEl) {
        let parts = [];
        if (res.rag_used) parts.push(`📚 RAG (${res.rag_chunks || 1} chunks)`);
        if (res.llm_paraphrase_used) parts.push('Gemini AI');
        else if (res.llm_used) parts.push('Gemini AI (structured)');
        else parts.push('Multi-Agent Engine');
        sourceEl.textContent = 'Source: ' + parts.join(' + ');
      }
      if (safetyToken) {
        const s = (res.safety_status || 'safe').toLowerCase();
        safetyToken.textContent = s === 'danger' ? t('home.danger') : (s === 'caution' ? t('home.caution') : t('home.safe'));
      }

      if (zoneLabel && res.best_zone) {
        zoneLabel.innerHTML = `<span class="material-symbols-outlined text-[20px]">near_me</span><span>${t('home.bestZone')}: ${res.best_zone.code || 'Zone A-12'} (${formatDistance(res.best_zone.distance_km)})</span>`;
      }

      // Automatically speak the response
      if (window.orcaVoice) {
        window.orcaVoice.speak(res.response);
      }
    } catch (e) {
      console.error('Query execution error:', e);
      if (answerEl) answerEl.textContent = t('common.error');
    } finally {
      if (micStatus) micStatus.textContent = t('ask.micPrompt');
    }
  }

  window.simulateOrcaQuery = function (text) {
    executeOrcaQuery(text);
  };

  window.handleTextInput = function () {
    const input = document.getElementById('orca-text-field');
    if (input && input.value.trim()) {
      const q = input.value.trim();
      input.value = '';
      executeOrcaQuery(q);
    }
  };

  // ── SCREEN 5: WHY ORCA ────────────────────────────────────────────────────
  async function loadWhyOrca(queryId) {
    try {
      const explanation = await window.orcaApi.getExplanation(queryId || 'latest');
      if (!explanation || !explanation.factors) return;

      const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;

      // Update factor cards
      explanation.factors.forEach((factor, idx) => {
        const factorCard = document.getElementById(`why-factor-${idx + 1}`);
        if (factorCard) {
          const title = factorCard.querySelector('.factor-name');
          const status = factorCard.querySelector('.factor-status');
          const desc = factorCard.querySelector('.factor-desc');
          if (title) title.textContent = t(`why.agent${idx + 1}Name`);
          if (status) status.textContent = t(`why.agent${idx + 1}Status`);
          if (desc) desc.textContent = t(`why.agent${idx + 1}Desc`);
        }
      });
    } catch (e) {
      console.warn('loadWhyOrca notice:', e);
    }
  }

  // ── SCREEN 6: HAZARD ALERTS ───────────────────────────────────────────────
  async function loadAlerts() {
    try {
      const data = await window.orcaApi.getAlerts(currentCoords.lat, currentCoords.lon);
      const listContainer = document.getElementById('alerts-list-container');
      if (!listContainer) return;

      const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;

      if (!data || !data.alerts || data.alerts.length === 0) {
        listContainer.innerHTML = `
          <div class="bg-surface-container-lowest rounded-xl p-5 shadow-sm text-center flex flex-col items-center">
            <span class="material-symbols-outlined text-on-tertiary-container text-[40px] mb-2">verified</span>
            <h3 class="font-headline-sm text-base text-primary-container font-bold">${t('alerts.noAlerts')}</h3>
            <p class="font-body-sm text-on-surface-variant mt-1">${t('alerts.clearNote')}</p>
          </div>
        `;
        return;
      }

      listContainer.innerHTML = data.alerts.map(a => `
        <div class="bg-surface-container-lowest rounded-xl p-4 shadow-sm border-l-4 ${a.severity === 'danger' ? 'border-error' : 'border-secondary'} flex flex-col gap-1.5 cursor-pointer hover:bg-surface-container-low transition-colors" onclick="alert('${a.description}')">
          <div class="flex items-center justify-between">
            <span class="font-headline-sm text-sm font-bold text-primary-container">${a.title}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${a.severity === 'danger' ? 'bg-error/20 text-error' : 'bg-secondary/20 text-secondary'}">${a.severity}</span>
          </div>
          <p class="font-body-sm text-xs text-on-surface-variant">${a.description}</p>
          <div class="flex items-center justify-between pt-1 text-[10px] text-on-surface-variant">
            <span>📍 ${a.area || currentCoords.name}</span>
            <span>🏛 ${a.source || 'INCOIS'}</span>
          </div>
        </div>
      `).join('');
    } catch (e) {
      console.warn('loadAlerts error:', e);
    }
  }

  // ── SCREEN 7: PROFILE & EDIT PROFILE ──────────────────────────────────────
  function syncProfileDOM() {
    const p = window.orcaState.profile;
    const loc = window.orcaState.location;

    // Header avatar & location
    const headerAvatar = document.getElementById('header-avatar-img');
    if (headerAvatar && p.avatar_url) headerAvatar.src = p.avatar_url;

    const locTitle = document.getElementById('home-location-title');
    if (locTitle) locTitle.textContent = loc.location_name || p.location_name || 'Kollam Coast';

    // Home skipper banner
    const homeName = document.getElementById('profile-name');
    if (homeName) homeName.textContent = p.name || 'Rajan Kumar';

    const homeReg = document.getElementById('profile-reg');
    if (homeReg) homeReg.textContent = `Reg #${p.registration_no || 'KL-02-F-491'} • ${p.vessel_type || 'Motorized Craft (28ft)'}`;

    const homeAvatar = document.getElementById('home-profile-avatar');
    if (homeAvatar && p.avatar_url) homeAvatar.src = p.avatar_url;

    // Profile screen
    const profAvatar = document.getElementById('profile-avatar-img');
    if (profAvatar && p.avatar_url) profAvatar.src = p.avatar_url;

    const editName = document.getElementById('profile-edit-name');
    if (editName && p.name) editName.value = p.name;

    const editVessel = document.getElementById('profile-edit-vessel');
    if (editVessel && p.vessel_name) editVessel.value = p.vessel_name;

    const editReg = document.getElementById('profile-edit-reg');
    if (editReg && p.registration_no) editReg.value = p.registration_no;

    const editLoc = document.getElementById('profile-edit-location');
    if (editLoc) editLoc.value = p.location_name || loc.location_name || 'Kollam Coast';

    updateProfileLangButtons();
  }

  async function loadProfile() {
    try {
      const profile = await window.orcaApi.getProfile();
      if (profile) {
        window.orcaState.set({
          profile: {
            ...window.orcaState.profile,
            ...profile,
          }
        });
      }
      syncProfileDOM();
    } catch (e) {
      console.warn('loadProfile error:', e);
      syncProfileDOM();
    }
  }

  window.saveProfile = async function () {
    const editName = document.getElementById('profile-edit-name');
    const editVessel = document.getElementById('profile-edit-vessel');
    const editReg = document.getElementById('profile-edit-reg');
    const editLoc = document.getElementById('profile-edit-location');
    const avatarImg = document.getElementById('profile-avatar-img');

    const updates = {
      name: editName ? editName.value.trim() : window.orcaState.profile.name,
      vessel_name: editVessel ? editVessel.value.trim() : window.orcaState.profile.vessel_name,
      registration_no: editReg ? editReg.value.trim() : window.orcaState.profile.registration_no,
      location_name: editLoc ? editLoc.value.trim() : window.orcaState.profile.location_name,
      preferred_language: currentLanguage.startsWith('ta') ? 'ta' : (currentLanguage.startsWith('ml') ? 'ml' : 'en'),
      avatar_url: avatarImg ? avatarImg.src : window.orcaState.profile.avatar_url,
    };

    // If location changed, update coordinates
    const matchedPreset = Object.values(LOCATION_PRESETS).find(
      p => p.name.toLowerCase() === (updates.location_name || '').toLowerCase()
    );
    if (matchedPreset) {
      updates.latitude = matchedPreset.lat;
      updates.longitude = matchedPreset.lon;
      updates.harbor = matchedPreset.harbor;
      currentCoords.lat = matchedPreset.lat;
      currentCoords.lon = matchedPreset.lon;
      currentCoords.name = matchedPreset.name;
      currentCoords.harbor = matchedPreset.harbor;
      window.orcaState.set({
        location: {
          latitude: matchedPreset.lat,
          longitude: matchedPreset.lon,
          location_name: matchedPreset.name,
          harbor: matchedPreset.harbor,
        }
      });
    }

    try {
      await window.orcaApi.updateProfile(updates);
      window.orcaState.set({
        profile: {
          ...window.orcaState.profile,
          ...updates,
        }
      });
      syncProfileDOM();

      const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;
      showToast(t('profile.savedToast') || 'Profile saved successfully!', 'success');
      await refreshAllData();
    } catch (e) {
      console.error('Failed to save profile:', e);
      showToast('Error saving profile', 'error');
    }
  };

  window.cancelProfileEdit = function () {
    loadProfile();
    showToast('Changes discarded');
  };

  window.handleAvatarUpload = function (event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      const dataUrl = e.target.result;
      const avatarImg = document.getElementById('profile-avatar-img');
      if (avatarImg) avatarImg.src = dataUrl;

      // Also upload to backend
      try {
        await window.orcaApi.uploadProfileImage(dataUrl);
        showToast('Photo updated', 'success');
      } catch (err) {
        console.warn('Avatar upload error:', err);
      }
    };
    reader.readAsDataURL(file);
  };

  window.removeAvatar = async function () {
    const defaultImg = 'assets/fisherman.png';
    const avatarImg = document.getElementById('profile-avatar-img');
    if (avatarImg) avatarImg.src = defaultImg;
    try {
      await window.orcaApi.uploadProfileImage('');
      showToast('Photo removed');
    } catch (e) {
      console.warn('Remove avatar error:', e);
    }
  };

  window.selectProfileLanguage = function (lang) {
    setGlobalLanguage(lang, true);
  };

  // ── LOCATION MODAL & PRESETS CONTROLLER ───────────────────────────────────
  window.openLocationModal = function () {
    const modal = document.getElementById('orca-location-modal');
    if (modal) modal.classList.remove('hidden');
  };

  window.closeLocationModal = function () {
    const modal = document.getElementById('orca-location-modal');
    if (modal) modal.classList.add('hidden');
  };

  window.selectLocationPreset = async function (presetKey) {
    const preset = LOCATION_PRESETS[presetKey];
    if (!preset) return;

    currentCoords.lat = preset.lat;
    currentCoords.lon = preset.lon;
    currentCoords.name = preset.name;
    currentCoords.harbor = preset.harbor;

    try {
      await window.orcaApi.updateLocation({
        location_name: preset.name,
        harbor: preset.harbor,
        latitude: preset.lat,
        longitude: preset.lon,
        state: preset.state,
      });

      window.closeLocationModal();
      const t = (k) => window.orcaI18n ? window.orcaI18n.t(k, currentLanguage) : k;
      showToast(`${t('locModal.success') || 'Location updated to'} ${preset.name}`, 'success');

      // Update map center & reload all dependent data
      if (window.orcaMarineMap) {
        window.orcaMarineMap.setCenter(preset.lat, preset.lon);
      }
      await refreshAllData();
      if (currentScreen === 'coastal-map') await loadMap();
      if (currentScreen === 'fisherman-profile') await loadProfile();
    } catch (e) {
      console.error('Error selecting location preset:', e);
      showToast('Failed to update location', 'error');
    }
  };

  window.useDeviceGps = function () {
    if (!navigator.geolocation) {
      showToast('Geolocation is not supported by your browser', 'error');
      return;
    }

    showToast('Acquiring GPS fix...');
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(4));
        const lon = parseFloat(pos.coords.longitude.toFixed(4));
        const name = `GPS: ${lat}°N, ${lon}°E`;

        currentCoords.lat = lat;
        currentCoords.lon = lon;
        currentCoords.name = name;

        try {
          await window.orcaApi.setGpsLocation(lat, lon, name);
          window.closeLocationModal();
          showToast(`GPS Position Locked: ${lat}, ${lon}`, 'success');

          if (window.orcaMarineMap) {
            window.orcaMarineMap.setCenter(lat, lon);
          }
          await refreshAllData();
          if (currentScreen === 'coastal-map') await loadMap();
        } catch (e) {
          console.error('GPS update failed:', e);
        }
      },
      (err) => {
        showToast(`GPS error: ${err.message}`, 'error');
      },
      { timeout: 8000 }
    );
  };

  window.applyCustomLocation = async function () {
    const latInput = document.getElementById('custom-loc-lat');
    const lonInput = document.getElementById('custom-loc-lon');
    const nameInput = document.getElementById('custom-loc-name');

    const lat = parseFloat(latInput ? latInput.value : NaN);
    const lon = parseFloat(lonInput ? lonInput.value : NaN);
    const name = nameInput && nameInput.value.trim() ? nameInput.value.trim() : 'Custom Coast';

    if (isNaN(lat) || isNaN(lon)) {
      showToast('Please enter valid Latitude and Longitude', 'error');
      return;
    }

    currentCoords.lat = lat;
    currentCoords.lon = lon;
    currentCoords.name = name;

    try {
      await window.orcaApi.updateLocation({
        location_name: name,
        latitude: lat,
        longitude: lon,
      });

      window.closeLocationModal();
      showToast(`Location set to ${name}`, 'success');

      if (window.orcaMarineMap) {
        window.orcaMarineMap.setCenter(lat, lon);
      }
      await refreshAllData();
      if (currentScreen === 'coastal-map') await loadMap();
    } catch (e) {
      showToast('Failed to apply custom coordinates', 'error');
    }
  };

  // Launch on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
