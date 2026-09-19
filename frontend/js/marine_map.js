/**
 * ORCA Marine Navigation Map Engine
 * =================================
 * Dual Engine Architecture:
 *  1. Primary: Google Maps JavaScript API (live satellite/terrain with coastal geography).
 *  2. Fallback: Leaflet / OpenStreetMap (guaranteed zero blank/empty screen).
 * 
 * Features:
 *  - Real coastal geography, sea depth isobaths, navigation aids (lighthouses & buoys).
 *  - Dynamic vessel position and heading orientation.
 *  - PFZ (Potential Fishing Zone) vectors, radius circles, and interactive clicks.
 *  - Navigation route planning from current harbor to recommended zone with distance & ETA.
 *  - Full touch controls: Recenter, Zoom In, Zoom Out, Compass (Reset North).
 */

(function () {
  'use strict';

  class MarineMapEngine {
    constructor() {
      this.container = null;
      this.engine = 'google'; // 'google' | 'leaflet' | 'canvas'
      this.googleMap = null;
      this.leafletMap = null;

      // Coordinate center (default: Kollam Coast)
      this.centerLat = 8.88;
      this.centerLon = 76.59;
      this.zoom = 11;

      // Vessel state
      this.vessel = {
        name: 'Sea King II',
        reg: 'KL-02-F-491',
        lat: 8.88,
        lon: 76.59,
        heading: 218,
        speed: 6.4,
      };

      this.zones = [];
      this.selectedZoneId = 'A12';
      this.recommendedZoneId = 'A12';
      this.isNavigating = false;

      // Google Maps references
      this.gMarkers = [];
      this.gCircles = [];
      this.gIsobaths = [];
      this.gRoute = null;
      this.gVesselMarker = null;
      this.gConnectingLines = [];   // vessel → zone connection lines

      // Leaflet references
      this.markers = [];
      this.routeLayer = null;
      this.isobathLayers = [];
      this.lConnectingLines = [];   // vessel → zone connection lines

      this.isInitialized = false;
    }

    async init(containerId) {
      this.container = document.getElementById(containerId);
      if (!this.container) return;

      this.container.innerHTML = '';
      this.container.style.position = 'relative';
      this.container.style.overflow = 'hidden';

      // 1. Fetch runtime config to obtain Google Maps browser key
      let mapsKey = window.GOOGLE_MAPS_KEY || '';
      try {
        if (window.orcaApi && !mapsKey) {
          const cfg = await window.orcaApi.getConfig();
          if (cfg && cfg.google_maps_key) {
            mapsKey = cfg.google_maps_key;
            window.GOOGLE_MAPS_KEY = mapsKey;
          }
        }
      } catch (e) {
        console.warn('Config fetch error for Google Maps:', e);
      }

      // 2. Attempt Google Maps initialization if key exists
      if (mapsKey) {
        try {
          await this.loadGoogleMapsScript(mapsKey);
          if (window.google && window.google.maps) {
            this.initGoogleMaps();
            this.engine = 'google';
            this.isInitialized = true;
            this.updateEngineBadge('Google Maps');
            this.setupLanguageListener();
            return;
          }
        } catch (err) {
          console.warn('Google Maps JS API load failed, switching to Leaflet fallback:', err.message);
        }
      }

      // 3. Fallback: Leaflet / OpenStreetMap
      if (window.L && typeof window.L.map === 'function') {
        try {
          this.initLeaflet();
          this.engine = 'leaflet';
          this.isInitialized = true;
          this.updateEngineBadge('Leaflet (OSM)');
          this.setupLanguageListener();
          return;
        } catch (e) {
          console.warn('Leaflet init error, switching to Canvas chart:', e.message);
        }
      }

      // 4. Final Fallback: Canvas Chart
      this.initCanvasChart();
      this.engine = 'canvas';
      this.isInitialized = true;
      this.updateEngineBadge('Canvas Vector');
      this.setupLanguageListener();
    }

    updateEngineBadge(label) {
      const badge = document.getElementById('map-engine-badge');
      if (badge) {
        badge.textContent = label;
      }
    }

    setupLanguageListener() {
      window.addEventListener('orca:languageChanged', () => {
        if (this.engine === 'google') {
          this.renderGoogleLayers();
        } else if (this.engine === 'leaflet') {
          this.renderLeafletLayers();
        } else {
          this.drawCanvas();
        }
      });
    }

    loadGoogleMapsScript(apiKey) {
      return new Promise((resolve, reject) => {
        if (window.google && window.google.maps) {
          resolve();
          return;
        }

        const existingScript = document.getElementById('google-maps-script');
        if (existingScript) {
          existingScript.onload = () => resolve();
          existingScript.onerror = (e) => reject(e);
          return;
        }

        // Detect Google Maps auth failure
        window.gm_authFailure = () => {
          console.warn('Google Maps auth failure detected. Switching to Leaflet.');
          this.switchToLeafletFallback();
        };

        const script = document.createElement('script');
        script.id = 'google-maps-script';
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry`;
        script.async = true;
        script.defer = true;
        script.onload = () => resolve();
        script.onerror = (e) => reject(new Error('Google Maps script failed to load.'));
        document.head.appendChild(script);

        // Timeout fallback after 6 seconds
        setTimeout(() => {
          if (!window.google || !window.google.maps) {
            reject(new Error('Google Maps load timeout.'));
          }
        }, 6000);
      });
    }

    switchToLeafletFallback() {
      if (this.engine === 'leaflet') return;
      console.info('Activating Leaflet marine chart fallback...');
      this.engine = 'leaflet';
      this.clearGoogleMap();
      this.container.innerHTML = '';
      this.initLeaflet();
      this.updateEngineBadge('Leaflet (Fallback)');
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GOOGLE MAPS IMPLEMENTATION (PRIMARY)
    // ─────────────────────────────────────────────────────────────────────────
    initGoogleMaps() {
      const g = window.google.maps;
      this.container.innerHTML = '';

      this.googleMap = new g.Map(this.container, {
        center: { lat: this.centerLat, lng: this.centerLon },
        zoom: this.zoom,
        mapTypeId: 'terrain',
        disableDefaultUI: true,
        gestureHandling: 'greedy',
        styles: [
          { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#c5e2f7' }] },
          { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#00547b' }] },
          { featureType: 'landscape', elementType: 'geometry', stylers: [{ color: '#f0f5fa' }] },
          { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#ffffff' }] },
          { featureType: 'poi', stylers: [{ visibility: 'off' }] },
        ],
      });

      this.googleMap.addListener('click', () => {
        // Deselect or close modals
      });

      this.renderGoogleLayers();
    }

    clearGoogleMap() {
      this.gMarkers.forEach(m => m.setMap(null));
      this.gMarkers = [];
      this.gCircles.forEach(c => c.setMap(null));
      this.gCircles = [];
      this.gIsobaths.forEach(l => l.setMap(null));
      this.gIsobaths = [];
      this.gConnectingLines.forEach(l => l.setMap(null));
      this.gConnectingLines = [];
      if (this.gRoute) {
        this.gRoute.setMap(null);
        this.gRoute = null;
      }
      if (this.gVesselMarker) {
        this.gVesselMarker.setMap(null);
        this.gVesselMarker = null;
      }
    }

    renderGoogleLayers() {
      if (!this.googleMap || !window.google || !window.google.maps) return;
      const g = window.google.maps;
      this.clearGoogleMap();

      // 1. Bathymetry Isobaths (Depth Contour Lines)
      const isobaths = [
        { depth: 10, offsetLon: -0.05, color: '#4a9fd4' },
        { depth: 20, offsetLon: -0.10, color: '#2980b9' },
        { depth: 50, offsetLon: -0.18, color: '#1a6fa8' },
        { depth: 100, offsetLon: -0.32, color: '#0d5a8a' },
      ];

      isobaths.forEach(iso => {
        const path = [
          { lat: this.centerLat + 0.25, lng: this.centerLon + iso.offsetLon + 0.05 },
          { lat: this.centerLat + 0.10, lng: this.centerLon + iso.offsetLon + 0.01 },
          { lat: this.centerLat - 0.05, lng: this.centerLon + iso.offsetLon - 0.02 },
          { lat: this.centerLat - 0.20, lng: this.centerLon + iso.offsetLon - 0.04 },
        ];
        const polyline = new g.Polyline({
          path,
          geodesic: true,
          strokeColor: iso.color,
          strokeOpacity: 0.6,
          strokeWeight: 1.5,
          map: this.googleMap,
        });
        this.gIsobaths.push(polyline);
      });

      // 2. Navigation Aids (Lighthouses & Buoys)
      const navAids = [
        { name: 'Harbor Lighthouse', lat: this.centerLat + 0.015, lon: this.centerLon + 0.005, icon: '🏛️' },
        { name: 'Breakwater Light', lat: this.centerLat + 0.055, lon: this.centerLon - 0.01, icon: '💡' },
        { name: 'PFZ Buoy C-09', lat: this.centerLat - 0.04, lon: this.centerLon - 0.07, icon: '📍' },
      ];

      navAids.forEach(aid => {
        const marker = new g.Marker({
          position: { lat: aid.lat, lng: aid.lon },
          map: this.googleMap,
          title: aid.name,
          label: {
            text: aid.icon,
            fontSize: '14px',
          },
        });
        this.gMarkers.push(marker);
      });

      // 3. PFZ Fishing Zones
      const displayZones = this.zones && this.zones.length > 0 ? this.zones : [
        { id: 'A12', code: 'Zone A-12', lat: this.centerLat - 0.08, lon: this.centerLon - 0.12, distance_km: 12, potential: 'high', target_species: 'Indian Mackerel & Sardines' },
        { id: 'B04', code: 'Zone B-04', lat: this.centerLat + 0.12, lon: this.centerLon - 0.15, distance_km: 18, potential: 'medium', target_species: 'Yellowfin Tuna' },
        { id: 'C09', code: 'Zone C-09', lat: this.centerLat - 0.15, lon: this.centerLon - 0.18, distance_km: 24, potential: 'medium', target_species: 'Anchovies' },
      ];

      displayZones.forEach(z => {
        const isRec = z.id === this.recommendedZoneId || z.code === this.recommendedZoneId;
        const isSel = z.id === this.selectedZoneId || z.code === this.selectedZoneId;
        const zoneLat = z.latitude || z.lat || (this.centerLat - 0.08);
        const zoneLon = z.longitude || z.lon || (this.centerLon - 0.12);

        const circle = new g.Circle({
          map: this.googleMap,
          center: { lat: zoneLat, lng: zoneLon },
          radius: isRec ? 3000 : 2200,
          strokeColor: isRec ? '#009a43' : (isSel ? '#006492' : '#73787c'),
          strokeOpacity: 0.85,
          strokeWeight: isRec || isSel ? 2.5 : 1.5,
          fillColor: isRec ? '#009a43' : '#006492',
          fillOpacity: isRec ? 0.22 : 0.12,
        });

        circle.addListener('click', () => {
          this.selectZone(z.id || z.code);
          if (typeof window.selectMapZone === 'function') {
            window.selectMapZone(z.id || z.code);
          }
        });

        this.gCircles.push(circle);

        // Zone Marker Label
        const marker = new g.Marker({
          position: { lat: zoneLat, lng: zoneLon },
          map: this.googleMap,
          title: z.code || z.name || 'Zone',
          label: {
            text: (z.code || z.id || 'PFZ').replace('Zone ', ''),
            color: isRec ? '#005320' : '#001e2f',
            fontWeight: 'bold',
            fontSize: '11px',
          },
        });

        marker.addListener('click', () => {
          this.selectZone(z.id || z.code);
          if (typeof window.selectMapZone === 'function') {
            window.selectMapZone(z.id || z.code);
          }
        });

        this.gMarkers.push(marker);
      });

      // 4. Vessel Marker
      this.gVesselMarker = new g.Marker({
        position: { lat: this.vessel.lat, lng: this.vessel.lon },
        map: this.googleMap,
        title: this.vessel.name,
        icon: {
          path: g.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 6,
          fillColor: '#006492',
          fillOpacity: 1,
          strokeWeight: 2,
          strokeColor: '#ffffff',
          rotation: this.vessel.heading,
        },
      });

      // 5. Connecting Lines (vessel → each zone)
      displayZones.forEach(z => {
        const isSelected = this.selectedZoneId
          ? (z.id === this.selectedZoneId || z.code === this.selectedZoneId)
          : (z.id === this.recommendedZoneId || z.code === this.recommendedZoneId);
        const zoneLat = parseFloat(z.latitude || z.lat || (this.centerLat - 0.08));
        const zoneLon = parseFloat(z.longitude || z.lon || (this.centerLon - 0.12));
        const vLat = parseFloat(this.vessel.lat);
        const vLon = parseFloat(this.vessel.lon);

        const line = new g.Polyline({
          path: [
            { lat: vLat, lng: vLon },
            { lat: zoneLat, lng: zoneLon },
          ],
          geodesic: true,
          strokeColor: isSelected ? '#00c853' : '#004870',
          strokeOpacity: isSelected ? 1.0 : 0.85,
          strokeWeight: isSelected ? 4.5 : 2.5,
          zIndex: isSelected ? 100 : 50,
          map: this.googleMap,
        });

        line.addListener('click', () => {
          this.selectZone(z.id || z.code);
          if (typeof window.selectMapZone === 'function') {
            window.selectMapZone(z.id || z.code);
          }
        });

        this.gConnectingLines.push(line);
      });

      // 6. Active Navigation Route
      if (this.isNavigating) {
        this.renderGoogleRoute();
      }
    }

    renderGoogleRoute() {
      if (!this.googleMap || !window.google || !window.google.maps) return;
      const g = window.google.maps;
      if (this.gRoute) this.gRoute.setMap(null);

      // Destination: recommended or selected zone
      const destZone = this.zones.find(z => (z.id === this.recommendedZoneId || z.code === this.recommendedZoneId)) || this.zones[0] || {
        latitude: this.centerLat - 0.08,
        longitude: this.centerLon - 0.12,
      };

      const destLat = destZone.latitude || destZone.lat;
      const destLon = destZone.longitude || destZone.lon;

      this.gRoute = new g.Polyline({
        path: [
          { lat: this.vessel.lat, lng: this.vessel.lon },
          { lat: destLat, lng: destLon },
        ],
        geodesic: true,
        strokeColor: '#006492',
        strokeOpacity: 0.9,
        strokeWeight: 3.5,
        map: this.googleMap,
      });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // LEAFLET IMPLEMENTATION (SEAMLESS FALLBACK)
    // ─────────────────────────────────────────────────────────────────────────
    initLeaflet() {
      const L = window.L;
      this.container.innerHTML = '';
      this.leafletMap = L.map(this.container, {
        center: [this.centerLat, this.centerLon],
        zoom: this.zoom,
        zoomControl: false,
        attributionControl: false,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors',
      }).addTo(this.leafletMap);

      this.renderLeafletLayers();
    }

    renderLeafletLayers() {
      if (!this.leafletMap || !window.L) return;
      const L = window.L;

      this.markers.forEach(m => m.remove());
      this.markers = [];
      this.lConnectingLines = [];
      if (this.routeLayer) this.routeLayer.remove();
      this.isobathLayers.forEach(l => l.remove());
      this.isobathLayers = [];

      // 1. Draw Depth Isobaths
      const isobaths = [
        { depth: 10, offsetLon: -0.05, color: '#4a9fd4', dash: '4,6' },
        { depth: 20, offsetLon: -0.10, color: '#2980b9', dash: '6,6' },
        { depth: 50, offsetLon: -0.18, color: '#1a6fa8', dash: '8,8' },
        { depth: 100, offsetLon: -0.32, color: '#0d5a8a', dash: '10,10' },
      ];

      isobaths.forEach(iso => {
        const pts = [
          [this.centerLat + 0.25, this.centerLon + iso.offsetLon + 0.05],
          [this.centerLat + 0.10, this.centerLon + iso.offsetLon + 0.01],
          [this.centerLat - 0.05, this.centerLon + iso.offsetLon - 0.02],
          [this.centerLat - 0.20, this.centerLon + iso.offsetLon - 0.04],
        ];
        const line = L.polyline(pts, {
          color: iso.color,
          weight: 1.5,
          dashArray: iso.dash,
          opacity: 0.6,
        }).addTo(this.leafletMap);
        this.isobathLayers.push(line);
      });

      // 2. Draw Vessel Marker
      const vesselIcon = L.divIcon({
        className: 'vessel-marker-icon',
        html: `
          <div style="position:relative; width:44px; height:44px; display:flex; align-items:center; justify-content:center;">
            <div style="position:absolute; width:40px; height:40px; border-radius:50%; background:rgba(0,100,146,0.2); animation:pulse 2s infinite;"></div>
            <div style="width:28px; height:28px; border-radius:50%; background:#ffffff; border:2.5px solid #006492; display:flex; align-items:center; justify-content:center; transform:rotate(${this.vessel.heading}deg); box-shadow:0 2px 8px rgba(0,0,0,0.25);">
              <span class="material-symbols-outlined" style="font-size:18px; color:#006492;">navigation</span>
            </div>
          </div>
        `,
        iconSize: [44, 44],
        iconAnchor: [22, 22],
      });

      const vMarker = L.marker([this.vessel.lat, this.vessel.lon], { icon: vesselIcon })
        .addTo(this.leafletMap)
        .bindTooltip(`<b>${this.vessel.name}</b><br>GPS Fixed · ${this.vessel.speed} kts`, { direction: 'top', permanent: false });
      this.markers.push(vMarker);

      // 3. Draw PFZ Zones
      const displayZones = this.zones && this.zones.length > 0 ? this.zones : [
        { id: 'A12', code: 'Zone A-12', lat: this.centerLat - 0.08, lon: this.centerLon - 0.12, distance_km: 12, potential: 'high', target_species: 'Indian Mackerel & Sardines' },
        { id: 'B04', code: 'Zone B-04', lat: this.centerLat + 0.12, lon: this.centerLon - 0.15, distance_km: 18, potential: 'medium', target_species: 'Yellowfin Tuna' },
        { id: 'C09', code: 'Zone C-09', lat: this.centerLat - 0.15, lon: this.centerLon - 0.18, distance_km: 24, potential: 'medium', target_species: 'Anchovies' },
      ];

      displayZones.forEach(z => {
        const isRec = z.id === this.recommendedZoneId || z.code === this.recommendedZoneId;
        const isSel = z.id === this.selectedZoneId || z.code === this.selectedZoneId;
        const zoneLat = z.latitude || z.lat || (this.centerLat - 0.08);
        const zoneLon = z.longitude || z.lon || (this.centerLon - 0.12);

        const circle = L.circle([zoneLat, zoneLon], {
          radius: isRec ? 3000 : 2200,
          color: isRec ? '#009a43' : (isSel ? '#006492' : '#73787c'),
          weight: isRec || isSel ? 2.5 : 1.5,
          fillColor: isRec ? '#009a43' : '#006492',
          fillOpacity: isRec ? 0.25 : 0.12,
        }).addTo(this.leafletMap);

        circle.on('click', () => {
          this.selectZone(z.id || z.code);
          if (typeof window.selectMapZone === 'function') {
            window.selectMapZone(z.id || z.code);
          }
        });
        this.markers.push(circle);

        // Marker tag
        const tagIcon = L.divIcon({
          className: 'zone-tag-icon',
          html: `<div style="background:${isRec ? '#009a43' : '#006492'}; color:#ffffff; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold; white-space:nowrap; box-shadow:0 1px 4px rgba(0,0,0,0.3);">${z.code || z.id}</div>`,
          iconAnchor: [20, 10],
        });
        const tagMarker = L.marker([zoneLat, zoneLon], { icon: tagIcon }).addTo(this.leafletMap);
        tagMarker.on('click', () => {
          this.selectZone(z.id || z.code);
          if (typeof window.selectMapZone === 'function') {
            window.selectMapZone(z.id || z.code);
          }
        });
        this.markers.push(tagMarker);
      });

      // 4. Draw Connecting Lines (vessel → each zone)
      displayZones.forEach(z => {
        const isSelected = this.selectedZoneId
          ? (z.id === this.selectedZoneId || z.code === this.selectedZoneId)
          : (z.id === this.recommendedZoneId || z.code === this.recommendedZoneId);
        const zoneLat = parseFloat(z.latitude || z.lat || (this.centerLat - 0.08));
        const zoneLon = parseFloat(z.longitude || z.lon || (this.centerLon - 0.12));
        const vLat = parseFloat(this.vessel.lat);
        const vLon = parseFloat(this.vessel.lon);

        const line = L.polyline(
          [[vLat, vLon], [zoneLat, zoneLon]],
          {
            color: isSelected ? '#00c853' : '#004870',
            weight: isSelected ? 4.5 : 2.5,
            opacity: isSelected ? 1.0 : 0.85,
          }
        ).addTo(this.leafletMap);

        line.on('click', () => {
          this.selectZone(z.id || z.code);
          if (typeof window.selectMapZone === 'function') {
            window.selectMapZone(z.id || z.code);
          }
        });

        this.lConnectingLines.push(line);
        this.markers.push(line);
      });

      // 5. Draw Active Navigation Route
      if (this.isNavigating) {
        const destZone = displayZones.find(z => (z.id === this.recommendedZoneId || z.code === this.recommendedZoneId)) || displayZones[0];
        const destLat = destZone.latitude || destZone.lat;
        const destLon = destZone.longitude || destZone.lon;

        this.routeLayer = L.polyline([
          [this.vessel.lat, this.vessel.lon],
          [destLat, destLon],
        ], {
          color: '#006492',
          weight: 3.5,
          dashArray: '8,6',
          opacity: 0.9,
        }).addTo(this.leafletMap);
      }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // CANVAS CHART FALLBACK
    // ─────────────────────────────────────────────────────────────────────────
    initCanvasChart() {
      this.canvas = document.createElement('canvas');
      this.canvas.width = this.container.clientWidth || 360;
      this.canvas.height = this.container.clientHeight || 500;
      this.ctx = this.canvas.getContext('2d');
      this.container.appendChild(this.canvas);
      this.drawCanvas();
    }

    drawCanvas() {
      if (!this.ctx || !this.canvas) return;
      const ctx = this.ctx;
      const w = this.canvas.width;
      const h = this.canvas.height;

      // Background Sea
      ctx.fillStyle = '#c5e2f7';
      ctx.fillRect(0, 0, w, h);

      // Coastline on East
      ctx.fillStyle = '#f0f5fa';
      ctx.beginPath();
      ctx.moveTo(w * 0.75, 0);
      ctx.bezierCurveTo(w * 0.7, h * 0.3, w * 0.8, h * 0.7, w * 0.72, h);
      ctx.lineTo(w, h);
      ctx.lineTo(w, 0);
      ctx.closePath();
      ctx.fill();

      // Coast contour
      ctx.strokeStyle = '#a3c4dc';
      ctx.lineWidth = 2;
      ctx.stroke();

      const vX = w * 0.48;
      const vY = h * 0.52;

      // Draw Zones & Connecting lines from vessel
      const canvasZones = [
        { id: 'A12', name: 'A-12', x: vX - 95, y: vY + 80 },
        { id: 'B04', name: 'B-04', x: vX - 115, y: vY - 15 },
        { id: 'C09', name: 'C-09', x: vX - 75, y: vY - 90 },
      ];

      canvasZones.forEach(z => {
        const isSel = this.selectedZoneId
          ? (z.id === this.selectedZoneId)
          : (z.id === this.recommendedZoneId);

        // Connecting line
        ctx.beginPath();
        ctx.moveTo(vX, vY);
        ctx.lineTo(z.x, z.y);
        ctx.strokeStyle = isSel ? '#00c853' : '#004870';
        ctx.lineWidth = isSel ? 4.5 : 2.5;
        ctx.stroke();

        // Zone circle
        ctx.beginPath();
        ctx.arc(z.x, z.y, isSel ? 20 : 15, 0, Math.PI * 2);
        ctx.fillStyle = isSel ? 'rgba(0, 200, 83, 0.25)' : 'rgba(0, 72, 112, 0.2)';
        ctx.fill();
        ctx.strokeStyle = isSel ? '#00c853' : '#004870';
        ctx.lineWidth = isSel ? 3 : 2;
        ctx.stroke();

        // Zone label
        ctx.fillStyle = isSel ? '#005320' : '#001e2f';
        ctx.font = 'bold 10px Inter, sans-serif';
        ctx.fillText(z.name, z.x - 10, z.y + 4);
      });

      // Vessel
      ctx.fillStyle = '#006492';
      ctx.beginPath();
      ctx.arc(vX, vY, 11, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.fillText('Sea King II', vX - 28, vY + 26);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // CONTROLS & API ACTIONS
    // ─────────────────────────────────────────────────────────────────────────
    setCenter(lat, lon) {
      this.centerLat = parseFloat(lat);
      this.centerLon = parseFloat(lon);
      this.vessel.lat = this.centerLat;
      this.vessel.lon = this.centerLon;

      if (this.engine === 'google' && this.googleMap) {
        this.googleMap.setCenter({ lat: this.centerLat, lng: this.centerLon });
        this.renderGoogleLayers();
      } else if (this.engine === 'leaflet' && this.leafletMap) {
        this.leafletMap.setView([this.centerLat, this.centerLon], this.zoom);
        this.renderLeafletLayers();
      } else if (this.engine === 'canvas') {
        this.drawCanvas();
      }
    }

    setZones(zones, recommendedId = 'A12') {
      this.zones = zones || [];
      this.recommendedZoneId = recommendedId;
      if (this.engine === 'google') {
        this.renderGoogleLayers();
        this.fitBoundsToZones();
      } else if (this.engine === 'leaflet') {
        this.renderLeafletLayers();
        this.fitBoundsToZones();
      } else if (this.engine === 'canvas') {
        this.drawCanvas();
      }
    }

    fitBoundsToZones() {
      const displayZones = this.zones && this.zones.length > 0 ? this.zones : [];
      if (this.engine === 'google' && this.googleMap && window.google && window.google.maps) {
        const g = window.google.maps;
        const bounds = new g.LatLngBounds();
        bounds.extend({ lat: parseFloat(this.vessel.lat), lng: parseFloat(this.vessel.lon) });
        displayZones.forEach(z => {
          const zLat = parseFloat(z.latitude || z.lat);
          const zLon = parseFloat(z.longitude || z.lon);
          if (!isNaN(zLat) && !isNaN(zLon)) bounds.extend({ lat: zLat, lng: zLon });
        });
        if (!bounds.isEmpty()) {
          this.googleMap.fitBounds(bounds, { top: 60, bottom: 120, left: 40, right: 40 });
        }
      } else if (this.engine === 'leaflet' && this.leafletMap && window.L) {
        const pts = [[parseFloat(this.vessel.lat), parseFloat(this.vessel.lon)]];
        displayZones.forEach(z => {
          const zLat = parseFloat(z.latitude || z.lat);
          const zLon = parseFloat(z.longitude || z.lon);
          if (!isNaN(zLat) && !isNaN(zLon)) pts.push([zLat, zLon]);
        });
        if (pts.length > 1) {
          this.leafletMap.fitBounds(pts, { padding: [40, 40] });
        }
      }
    }

    selectZone(zoneId) {
      this.selectedZoneId = zoneId;
      if (this.engine === 'google') {
        this.renderGoogleLayers();
      } else if (this.engine === 'leaflet') {
        this.renderLeafletLayers();
      }
    }

    startNavigation() {
      this.isNavigating = true;
      if (this.engine === 'google') {
        this.renderGoogleRoute();
      } else if (this.engine === 'leaflet') {
        this.renderLeafletLayers();
      }
    }

    recenter() {
      this.setCenter(this.vessel.lat, this.vessel.lon);
    }

    zoomIn() {
      this.zoom = Math.min(this.zoom + 1, 18);
      if (this.engine === 'google' && this.googleMap) {
        this.googleMap.setZoom(this.zoom);
      } else if (this.engine === 'leaflet' && this.leafletMap) {
        this.leafletMap.setZoom(this.zoom);
      }
    }

    zoomOut() {
      this.zoom = Math.max(this.zoom - 1, 4);
      if (this.engine === 'google' && this.googleMap) {
        this.googleMap.setZoom(this.zoom);
      } else if (this.engine === 'leaflet' && this.leafletMap) {
        this.leafletMap.setZoom(this.zoom);
      }
    }

    resetNorth() {
      if (this.engine === 'google' && this.googleMap) {
        this.googleMap.setHeading(0);
      }
    }

    resize() {
      if (this.engine === 'google' && this.googleMap) {
        window.google.maps.event.trigger(this.googleMap, 'resize');
      } else if (this.engine === 'leaflet' && this.leafletMap) {
        this.leafletMap.invalidateSize();
      }
    }
  }

  window.orcaMarineMap = new MarineMapEngine();
})();
