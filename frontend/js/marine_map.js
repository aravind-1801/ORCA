/**
 * ORCA Marine Navigation Map Engine
 * Interactive, high-fidelity marine chart with Kerala coastline, bathymetry isobaths,
 * vessel tracking, PFZ fishing zones, navigation route vectors, and responsive controls.
 * Works seamlessly with Leaflet or offline Canvas/SVG nautical chart fallback.
 */

(function () {
  'use strict';

  class MarineMapEngine {
    constructor() {
      this.container = null;
      this.leafletMap = null;
      this.canvas = null;
      this.ctx = null;

      // Coordinate center (default: Kollam Coast)
      this.centerLat = 8.88;
      this.centerLon = 76.59;
      this.zoom = 11;

      // Pan offset for canvas mode
      this.panX = 0;
      this.panY = 0;
      this.isDragging = false;
      this.dragStartX = 0;
      this.dragStartY = 0;

      // State data
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
      this.headingDeg = 218;

      // Marine markers & layers
      this.markers = [];
      this.routeLayer = null;
      this.isobathLayers = [];

      this.isInitialized = false;
    }

    init(containerId) {
      this.container = document.getElementById(containerId);
      if (!this.container) return;

      this.container.innerHTML = '';
      this.container.style.position = 'relative';
      this.container.style.overflow = 'hidden';

      // Try Leaflet if available
      if (window.L && typeof window.L.map === 'function') {
        try {
          this.initLeaflet();
          this.isInitialized = true;
          return;
        } catch (e) {
          console.warn('Leaflet init fallback to Canvas Marine Chart:', e.message);
        }
      }

      // High-Fidelity Canvas / SVG Interactive Nautical Chart
      this.initCanvasChart();
      this.isInitialized = true;

      window.addEventListener('orca:languageChanged', () => {
        if (this.leafletMap) {
          this.renderLeafletLayers();
        } else {
          this.drawCanvas();
        }
      });
    }

    initLeaflet() {
      const L = window.L;
      this.leafletMap = L.map(this.container, {
        center: [this.centerLat, this.centerLon],
        zoom: this.zoom,
        zoomControl: false,
        attributionControl: false,
      });

      // Bright Basemap — OpenStreetMap (Google Maps-style light)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors',
      }).addTo(this.leafletMap);

      // Handle map clicks
      this.leafletMap.on('click', () => {
        // deselect or close tooltip
      });

      this.renderLeafletLayers();
    }

    renderLeafletLayers() {
      if (!this.leafletMap || !window.L) return;
      const L = window.L;

      // Clear existing
      this.markers.forEach(m => m.remove());
      this.markers = [];
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
            <div style="position:absolute; width:40px; height:40px; border-radius:50%; background:rgba(26,111,168,0.2); animation:pulse 2s infinite;"></div>
            <div style="width:28px; height:28px; border-radius:50%; background:#ffffff; border:2.5px solid #1a6fa8; display:flex; align-items:center; justify-content:center; transform:rotate(${this.vessel.heading}deg); box-shadow:0 2px 8px rgba(0,0,0,0.25);">
              <span class="material-symbols-outlined" style="font-size:18px; color:#1a6fa8;">navigation</span>
            </div>
            <div style="position:absolute; bottom:-16px; left:50%; transform:translateX(-50%); background:#ffffff; color:#1a6fa8; font-size:9px; font-weight:700; padding:1px 6px; border-radius:3px; white-space:nowrap; border:1px solid #1a6fa8; box-shadow:0 1px 4px rgba(0,0,0,0.15);">
              🚢 ${this.vessel.name}
            </div>
          </div>
        `,
        iconSize: [44, 44],
        iconAnchor: [22, 22],
      });

      const vesselMarker = L.marker([this.vessel.lat, this.vessel.lon], { icon: vesselIcon })
        .addTo(this.leafletMap)
        .on('click', () => {
          if (window.selectZone) window.selectZone('vessel');
        });
      this.markers.push(vesselMarker);

      // 3. Draw PFZ Fishing Zones
      const targetZone = this.zones.find(z => (z.id || z.code) === this.selectedZoneId) || this.zones[0];

      this.zones.forEach(zone => {
        const isRec = (zone.id || zone.code) === this.recommendedZoneId;
        const isSel = (zone.id || zone.code) === this.selectedZoneId;
        const potential = (zone.potential || 'low').toLowerCase();

        const color = potential === 'high' ? '#009a43' : (potential === 'moderate' ? '#f59e0b' : '#73787c');
        const zCode = zone.code || zone.name || zone.id;

        const zoneIcon = L.divIcon({
          className: 'zone-marker-icon',
          html: `
            <div style="position:relative; width:48px; height:48px; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer;">
              ${isRec ? `<div style="position:absolute; width:44px; height:44px; border-radius:50%; background:rgba(0,154,67,0.25); animation:pulse 1.5s infinite;"></div>` : ''}
              <div style="width:${isRec ? '32px' : '26px'}; height:${isRec ? '32px' : '26px'}; border-radius:50%; background:${isSel ? '#ffffff' : color}; border:2px solid ${isSel ? color : '#ffffff'}; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(0,0,0,0.35);">
                <span class="material-symbols-outlined" style="font-size:${isRec ? '18px' : '15px'}; color:${isSel ? color : '#ffffff'};">phishing</span>
              </div>
              <div style="margin-top:2px; background:#ffffff; color:#1a1a1a; font-size:9px; font-weight:700; padding:1px 5px; border-radius:3px; white-space:nowrap; border:1px solid ${color}; box-shadow:0 1px 4px rgba(0,0,0,0.15);">
                ${zCode} ${isRec ? '★' : ''}
              </div>
            </div>
          `,
          iconSize: [48, 48],
          iconAnchor: [24, 24],
        });

        const zMarker = L.marker([zone.latitude, zone.longitude], { icon: zoneIcon })
          .addTo(this.leafletMap)
          .on('click', () => {
            if (window.selectZone) window.selectZone(zone.id || zone.code);
          });
        this.markers.push(zMarker);
      });

      // 4. Draw Route from Vessel to Selected Zone
      if (targetZone && targetZone.latitude && targetZone.longitude) {
        this.routeLayer = L.polyline(
          [
            [this.vessel.lat, this.vessel.lon],
            [targetZone.latitude, targetZone.longitude],
          ],
          {
            color: '#009a43',
            weight: 3,
            dashArray: '8,6',
            opacity: 0.9,
          }
        ).addTo(this.leafletMap);
      }
    }

    initCanvasChart() {
      this.container.innerHTML = '';
      this.canvas = document.createElement('canvas');
      this.canvas.className = 'w-full h-full cursor-grab active:cursor-grabbing select-none';
      this.canvas.style.display = 'block';
      this.canvas.style.width = '100%';
      this.canvas.style.height = '100%';
      this.container.appendChild(this.canvas);
      this.ctx = this.canvas.getContext('2d');

      // Resize listener
      this.resizeCanvas();
      window.addEventListener('resize', () => {
        this.resizeCanvas();
        this.drawCanvas();
      });

      // Interactive drag & pan
      this.canvas.addEventListener('mousedown', (e) => {
        this.isDragging = true;
        this.dragStartX = e.clientX - this.panX;
        this.dragStartY = e.clientY - this.panY;
      });

      window.addEventListener('mousemove', (e) => {
        if (!this.isDragging) return;
        this.panX = e.clientX - this.dragStartX;
        this.panY = e.clientY - this.dragStartY;
        this.drawCanvas();
      });

      window.addEventListener('mouseup', () => {
        this.isDragging = false;
      });

      // Touch drag
      this.canvas.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
          this.isDragging = true;
          this.dragStartX = e.touches[0].clientX - this.panX;
          this.dragStartY = e.touches[0].clientY - this.panY;
        }
      }, { passive: true });

      this.canvas.addEventListener('touchmove', (e) => {
        if (!this.isDragging || e.touches.length !== 1) return;
        this.panX = e.touches[0].clientX - this.dragStartX;
        this.panY = e.touches[0].clientY - this.dragStartY;
        this.drawCanvas();
      }, { passive: true });

      this.canvas.addEventListener('touchend', () => {
        this.isDragging = false;
      });

      // Click zone hit testing
      this.canvas.addEventListener('click', (e) => {
        const rect = this.canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;
        this.handleCanvasClick(clickX, clickY);
      });

      this.drawCanvas();
    }

    resizeCanvas() {
      if (!this.canvas) return;
      const rect = this.container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      this.canvas.width = (rect.width || 400) * dpr;
      this.canvas.height = (rect.height || 450) * dpr;
      if (this.ctx) {
        this.ctx.scale(dpr, dpr);
      }
    }

    // Convert lat/lon to canvas X, Y relative to center and zoom
    coordToPoint(lat, lon, width, height) {
      const scale = (width / 0.6) * (this.zoom / 10);
      const x = (width / 2) + ((lon - this.centerLon) * scale) + this.panX;
      const y = (height / 2) - ((lat - this.centerLat) * scale) + this.panY;
      return { x, y };
    }

    drawCanvas() {
      if (!this.ctx || !this.canvas) return;
      const dpr = window.devicePixelRatio || 1;
      const w = this.canvas.width / dpr;
      const h = this.canvas.height / dpr;
      const ctx = this.ctx;

      ctx.clearRect(0, 0, w, h);

      // 1. Ocean Background Gradient (Deep Marine Blue)
      const oceanGrad = ctx.createLinearGradient(0, 0, w, h);
      oceanGrad.addColorStop(0, '#093548');
      oceanGrad.addColorStop(0.5, '#072b3b');
      oceanGrad.addColorStop(1, '#051d28');
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, 0, w, h);

      // 2. Marine Graticule / Latitude & Longitude Grid
      ctx.strokeStyle = 'rgba(125, 201, 255, 0.08)';
      ctx.lineWidth = 1;
      const gridSize = 40 * (this.zoom / 10);
      const startX = (this.panX % gridSize);
      const startY = (this.panY % gridSize);

      ctx.beginPath();
      for (let x = startX; x < w; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
      }
      for (let y = startY; y < h; y += gridSize) {
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
      }
      ctx.stroke();

      // 3. Kerala Coastal Landmass (Runs NW to SE on eastern side of chart)
      ctx.save();
      const coastPts = [
        this.coordToPoint(this.centerLat + 0.35, this.centerLon + 0.08, w, h),
        this.coordToPoint(this.centerLat + 0.20, this.centerLon + 0.05, w, h),
        this.coordToPoint(this.centerLat + 0.08, this.centerLon + 0.02, w, h), // Neendakara harbor inlet
        this.coordToPoint(this.centerLat + 0.04, this.centerLon + 0.01, w, h),
        this.coordToPoint(this.centerLat - 0.05, this.centerLon - 0.01, w, h), // Kollam port
        this.coordToPoint(this.centerLat - 0.20, this.centerLon - 0.03, w, h),
        this.coordToPoint(this.centerLat - 0.35, this.centerLon - 0.06, w, h),
      ];

      ctx.beginPath();
      ctx.moveTo(w + 50, -50);
      ctx.lineTo(coastPts[0].x, coastPts[0].y);
      for (let i = 1; i < coastPts.length; i++) {
        const xc = (coastPts[i - 1].x + coastPts[i].x) / 2;
        const yc = (coastPts[i - 1].y + coastPts[i].y) / 2;
        ctx.quadraticCurveTo(coastPts[i - 1].x, coastPts[i - 1].y, xc, yc);
      }
      ctx.lineTo(coastPts[coastPts.length - 1].x, coastPts[coastPts.length - 1].y);
      ctx.lineTo(w + 50, h + 50);
      ctx.closePath();

      // Coastal land gradient (dark coastal terrain)
      const landGrad = ctx.createLinearGradient(w / 2, 0, w, 0);
      landGrad.addColorStop(0, '#0f2f3d');
      landGrad.addColorStop(1, '#081c25');
      ctx.fillStyle = landGrad;
      ctx.fill();

      // Coastline Shore Accent
      ctx.strokeStyle = '#275268';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Ashtamudi Lake / Estuary Inlet
      const inlet = this.coordToPoint(this.centerLat + 0.06, this.centerLon + 0.04, w, h);
      ctx.fillStyle = '#082533';
      ctx.beginPath();
      ctx.ellipse(inlet.x, inlet.y, 16, 8, -Math.PI / 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.restore();

      // 4. Bathymetric Depth Lines & Labels
      const curLang = window.orcaI18n ? window.orcaI18n.currentLang : 'en-IN';
      const isobaths = [
        { label: curLang.startsWith('ta') ? '10 மீ ஆழக்கோடு' : (curLang.startsWith('ml') ? '10 മീ ആഴരേഖ' : '10M DEPTH LINE'), offsetLon: -0.04, dash: [4, 4], color: 'rgba(0, 100, 146, 0.45)' },
        { label: curLang.startsWith('ta') ? '20 மீ ஆழக்கோடு' : (curLang.startsWith('ml') ? '20 മീ ആഴരേഖ' : '20M DEPTH LINE'), offsetLon: -0.09, dash: [6, 6], color: 'rgba(0, 100, 146, 0.55)' },
        { label: curLang.startsWith('ta') ? '50 மீ ஆழக்கோடு' : (curLang.startsWith('ml') ? '50 മീ ആഴരേഖ' : '50M ISOBATH'), offsetLon: -0.17, dash: [8, 6], color: 'rgba(0, 84, 123, 0.5)' },
        { label: curLang.startsWith('ta') ? '100 மீ கண்டத்திட்டு' : (curLang.startsWith('ml') ? '100 മീ വൻകരത്തട്ട്' : '100M SHELF BREAK'), offsetLon: -0.28, dash: [10, 8], color: 'rgba(0, 62, 92, 0.45)' },
      ];

      isobaths.forEach(iso => {
        ctx.save();
        ctx.strokeStyle = iso.color;
        ctx.lineWidth = 1.5;
        ctx.setLineDash(iso.dash);

        const p1 = this.coordToPoint(this.centerLat + 0.35, this.centerLon + iso.offsetLon + 0.06, w, h);
        const p2 = this.coordToPoint(this.centerLat, this.centerLon + iso.offsetLon, w, h);
        const p3 = this.coordToPoint(this.centerLat - 0.35, this.centerLon + iso.offsetLon - 0.05, w, h);

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.quadraticCurveTo(p2.x, p2.y, p3.x, p3.y);
        ctx.stroke();

        // Label along the curve
        ctx.fillStyle = 'rgba(125, 201, 255, 0.65)';
        ctx.font = 'bold 9px Space Grotesk, sans-serif';
        ctx.fillText(iso.label, p2.x + 8, p2.y - 4);
        ctx.restore();
      });

      // 5. Land Labels (Dynamic per location preset & language)
      const harborPt = this.coordToPoint(this.centerLat + 0.05, this.centerLon + 0.015, w, h);
      ctx.fillStyle = '#b5c9d8';
      ctx.font = '600 10px Inter, sans-serif';

      let harborText = '⚓ Neendakara Harbor';
      let portText = '🏛 Kollam Port';

      if (this.centerLat > 12.0) { // Chennai
        harborText = curLang.startsWith('ta') ? '⚓ காசிமேடு துறைமுகம்' : (curLang.startsWith('ml') ? '⚓ കാശിമേട് ഹാർബർ' : '⚓ Kasimedu Fishing Harbor');
        portText = curLang.startsWith('ta') ? '🏛 சென்னை துறைமுகம்' : (curLang.startsWith('ml') ? '🏛 ചെന്നൈ പോർട്ട്' : '🏛 Chennai Port');
      } else if (this.centerLat > 9.7) { // Kochi
        harborText = curLang.startsWith('ta') ? '⚓ கொச்சி துறைமுகம்' : (curLang.startsWith('ml') ? '⚓ കൊച്ചി ഹാർബർ' : '⚓ Kochi Harbor');
        portText = curLang.startsWith('ta') ? '🏛 போர்ட் கொச்சி' : (curLang.startsWith('ml') ? '🏛 ഫോർട്ട് കൊച്ചി' : '🏛 Fort Kochi Port');
      } else if (this.centerLat > 9.2) { // Alappuzha
        harborText = curLang.startsWith('ta') ? '⚓ ஆலப்புழை துறைமுகம்' : (curLang.startsWith('ml') ? '⚓ ആലപ്പുഴ ഹാർബർ' : '⚓ Alappuzha Port');
        portText = curLang.startsWith('ta') ? '🏛 ஆலப்புழை கடலோரம்' : (curLang.startsWith('ml') ? '🏛 ആലപ്പുഴ പോർട്ട്' : '🏛 Alappuzha Coast');
      } else if (this.centerLat < 8.7) { // Vizhinjam / TVM
        harborText = curLang.startsWith('ta') ? '⚓ விழிஞ்சம் துறைமுகம்' : (curLang.startsWith('ml') ? '⚓ വിഴിഞ്ഞം ഹാർബർ' : '⚓ Vizhinjam Seaport');
        portText = curLang.startsWith('ta') ? '🏛 திருவனந்தபுரம்' : (curLang.startsWith('ml') ? '🏛 തിരുവനന്തപുരം' : '🏛 Thiruvananthapuram');
      } else { // Kollam
        harborText = curLang.startsWith('ta') ? '⚓ நீண்டகரை துறைமுகம்' : (curLang.startsWith('ml') ? '⚓ നീണ്ടകര ഹാർബർ' : '⚓ Neendakara Harbor');
        portText = curLang.startsWith('ta') ? '🏛 கொல்லம் துறைமுகம்' : (curLang.startsWith('ml') ? '🏛 കൊല്ലം പോർട്ട്' : '🏛 Kollam Port');
      }

      ctx.fillText(harborText, harborPt.x + 8, harborPt.y);
      const portPt = this.coordToPoint(this.centerLat - 0.03, this.centerLon - 0.005, w, h);
      ctx.fillText(portText, portPt.x + 8, portPt.y);


      // 6. Navigation Course Vector (from Vessel to Selected Zone)
      const targetZone = this.zones.find(z => (z.id || z.code) === this.selectedZoneId) || this.zones[0];
      const vPt = this.coordToPoint(this.vessel.lat, this.vessel.lon, w, h);

      if (targetZone) {
        const zPt = this.coordToPoint(targetZone.latitude, targetZone.longitude, w, h);

        ctx.save();
        ctx.strokeStyle = '#009a43';
        ctx.lineWidth = 3;
        ctx.setLineDash([8, 6]);
        ctx.beginPath();
        ctx.moveTo(vPt.x, vPt.y);
        ctx.lineTo(zPt.x, zPt.y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Course annotation pill along vector
        const midX = (vPt.x + zPt.x) / 2;
        const midY = (vPt.y + zPt.y) / 2;
        ctx.fillStyle = 'rgba(11, 31, 42, 0.9)';
        ctx.strokeStyle = '#009a43';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(midX - 38, midY - 10, 76, 20, 4);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#7ffc97';
        ctx.font = 'bold 9px Space Grotesk, sans-serif';
        ctx.textAlign = 'center';
        const distStr = curLang.startsWith('ta') ? `218° · 12 கி.மீ` : (curLang.startsWith('ml') ? `218° · 12 കി.മീ` : `218° · 12 km`);
        ctx.fillText(distStr, midX, midY + 3);
        ctx.textAlign = 'left';
        ctx.restore();
      }

      // 7. Render Zones
      this.zones.forEach(zone => {
        const pt = this.coordToPoint(zone.latitude, zone.longitude, w, h);
        const isRec = (zone.id || zone.code) === this.recommendedZoneId;
        const isSel = (zone.id || zone.code) === this.selectedZoneId;
        const potential = (zone.potential || 'low').toLowerCase();

        const color = potential === 'high' ? '#009a43' : (potential === 'moderate' ? '#f59e0b' : '#73787c');
        const radius = isRec ? 16 : 13;

        // Pulsing radar ring for recommended zone
        if (isRec) {
          ctx.save();
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, radius + 8, 0, 2 * Math.PI);
          ctx.fillStyle = 'rgba(0, 154, 67, 0.25)';
          ctx.fill();
          ctx.restore();
        }

        // Zone circle
        ctx.save();
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = isSel ? '#ffffff' : color;
        ctx.fill();
        ctx.strokeStyle = isSel ? color : '#ffffff';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Zone text code
        ctx.fillStyle = isSel ? color : '#ffffff';
        ctx.font = 'bold 9px Space Grotesk, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const codeShort = (zone.code || zone.id || 'A12').replace('Zone ', '');
        ctx.fillText(codeShort, pt.x, pt.y);

        // Badge label below
        ctx.font = 'bold 8px Inter, sans-serif';
        const badgeTxt = isRec ? 'HIGH POTENTIAL' : (potential === 'moderate' ? 'MODERATE' : 'NORMAL');
        const badgeW = ctx.measureText(badgeTxt).width + 8;

        ctx.fillStyle = 'rgba(11, 28, 48, 0.9)';
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(pt.x - (badgeW / 2), pt.y + radius + 3, badgeW, 14, 3);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.fillText(badgeTxt, pt.x, pt.y + radius + 10);
        ctx.restore();
      });

      // 8. Render Vessel (Own Boat)
      ctx.save();
      // Animated pulse ring
      ctx.beginPath();
      ctx.arc(vPt.x, vPt.y, 22, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(125, 201, 255, 0.2)';
      ctx.fill();

      // Vessel body
      ctx.beginPath();
      ctx.arc(vPt.x, vPt.y, 14, 0, 2 * Math.PI);
      ctx.fillStyle = '#0b1f2a';
      ctx.fill();
      ctx.strokeStyle = '#7dc9ff';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Direction vector arrow
      const headingRad = (this.vessel.heading - 90) * (Math.PI / 180);
      const tipX = vPt.x + Math.cos(headingRad) * 12;
      const tipY = vPt.y + Math.sin(headingRad) * 12;

      ctx.beginPath();
      ctx.moveTo(tipX, tipY);
      ctx.lineTo(vPt.x + Math.cos(headingRad + 2.5) * 8, vPt.y + Math.sin(headingRad + 2.5) * 8);
      ctx.lineTo(vPt.x, vPt.y);
      ctx.lineTo(vPt.x + Math.cos(headingRad - 2.5) * 8, vPt.y + Math.sin(headingRad - 2.5) * 8);
      ctx.closePath();
      ctx.fillStyle = '#7dc9ff';
      ctx.fill();

      // Vessel Label Pill
      ctx.fillStyle = '#0b1f2a';
      ctx.strokeStyle = '#7dc9ff';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(vPt.x - 38, vPt.y + 18, 76, 16, 3);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 8px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`🚤 ${this.vessel.name}`, vPt.x, vPt.y + 26);
      ctx.restore();
    }

    handleCanvasClick(x, y) {
      if (!this.canvas) return;
      const dpr = window.devicePixelRatio || 1;
      const w = this.canvas.width / dpr;
      const h = this.canvas.height / dpr;

      // Check vessel click
      const vPt = this.coordToPoint(this.vessel.lat, this.vessel.lon, w, h);
      const vDist = Math.hypot(x - vPt.x, y - vPt.y);
      if (vDist <= 24) {
        if (window.selectZone) window.selectZone('vessel');
        return;
      }

      // Check zone clicks
      for (const zone of this.zones) {
        const zPt = this.coordToPoint(zone.latitude, zone.longitude, w, h);
        const zDist = Math.hypot(x - zPt.x, y - zPt.y);
        if (zDist <= 24) {
          if (window.selectZone) window.selectZone(zone.id || zone.code);
          return;
        }
      }
    }

    setCenter(lat, lon) {
      this.centerLat = lat;
      this.centerLon = lon;
      this.vessel.lat = lat;
      this.vessel.lon = lon;
      this.panX = 0;
      this.panY = 0;

      if (this.leafletMap) {
        this.leafletMap.setView([lat, lon], this.zoom);
        this.renderLeafletLayers();
      } else {
        this.drawCanvas();
      }
    }

    setZones(zones, recommendedZoneId) {
      this.zones = zones || [];
      if (recommendedZoneId) this.recommendedZoneId = recommendedZoneId;
      if (this.leafletMap) {
        this.renderLeafletLayers();
      } else {
        this.drawCanvas();
      }
    }

    selectZone(zoneId) {
      this.selectedZoneId = zoneId;
      if (this.leafletMap) {
        this.renderLeafletLayers();
      } else {
        this.drawCanvas();
      }
    }

    zoomIn() {
      if (this.leafletMap) {
        this.leafletMap.zoomIn();
      } else {
        this.zoom = Math.min(this.zoom + 1.2, 18);
        this.drawCanvas();
      }
    }

    zoomOut() {
      if (this.leafletMap) {
        this.leafletMap.zoomOut();
      } else {
        this.zoom = Math.max(this.zoom - 1.2, 6);
        this.drawCanvas();
      }
    }

    recenter() {
      this.panX = 0;
      this.panY = 0;
      this.zoom = 11;
      if (this.leafletMap) {
        this.leafletMap.setView([this.vessel.lat, this.vessel.lon], 11);
      } else {
        this.drawCanvas();
      }
    }

    orientNorth() {
      if (this.leafletMap) {
        this.leafletMap.setBearing ? this.leafletMap.setBearing(0) : this.recenter();
      } else {
        this.panX = 0;
        this.panY = 0;
        this.drawCanvas();
      }
    }

    resize() {
      if (this.leafletMap) {
        this.leafletMap.invalidateSize();
      } else if (this.canvas) {
        this.resizeCanvas();
        this.drawCanvas();
      }
    }
  }

  window.orcaMarineMap = new MarineMapEngine();
})();

