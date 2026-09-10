/**
 * ORCA 2D Marine Companion Animation Controller
 * Maps sea state (SAFE, CAUTION, DANGER) to wave speed and shark movement
 * without altering the approved 2D SVG visuals.
 */

class OrcaCompanion {
  constructor() {
    this.container = document.getElementById('orca-marine-companion');
    this.shark = document.getElementById('companion-shark-actor');
    this.currentStatus = 'safe';
  }

  setSeaCondition(status) {
    this.currentStatus = (status || 'safe').toLowerCase();
    const wavesBack = document.querySelectorAll('.wave-back');
    const wavesMid = document.querySelectorAll('.wave-mid');
    const wavesFore = document.querySelectorAll('.wave-fore');

    if (this.currentStatus === 'danger') {
      // Fast rough surge
      wavesBack.forEach(w => w.style.animationDuration = '6s');
      wavesMid.forEach(w => w.style.animationDuration = '5s');
      wavesFore.forEach(w => w.style.animationDuration = '3.5s');
    } else if (this.currentStatus === 'caution') {
      // Moderate active swell
      wavesBack.forEach(w => w.style.animationDuration = '12s');
      wavesMid.forEach(w => w.style.animationDuration = '9s');
      wavesFore.forEach(w => w.style.animationDuration = '7s');
    } else {
      // Calm, gentle oceanic glide (default)
      wavesBack.forEach(w => w.style.animationDuration = '18s');
      wavesMid.forEach(w => w.style.animationDuration = '14s');
      wavesFore.forEach(w => w.style.animationDuration = '10s');
    }
  }

  pingShark() {
    if (this.shark) {
      this.shark.classList.add('scale-110');
      setTimeout(() => this.shark.classList.remove('scale-110'), 600);
    }
  }
}

window.orcaCompanion = new OrcaCompanion();
