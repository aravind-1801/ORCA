# ORCA — Marine EcOsystem Reasoning with Collaborative Agents

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Gemini-AI-4285F4?style=for-the-badge&logo=google" />
  <img src="https://img.shields.io/badge/Google%20Maps-API-34A853?style=for-the-badge&logo=google-maps" />
  <img src="https://img.shields.io/badge/Demo%20Mode-Active-orange?style=for-the-badge" />
</p>

> **ORCA** is an AI-powered marine navigation and fishing intelligence system designed for small-scale coastal fishermen. It provides real-time Potential Fishing Zone (PFZ) advisories, ocean condition telemetry, safety alerts, and multilingual voice assistance — all in a mobile-first Progressive Web App (PWA).

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running Locally](#running-locally)
- [API Reference](#api-reference)
- [Multi-Agent System](#multi-agent-system)
- [Frontend Map Engine](#frontend-map-engine)
- [Contributing](#contributing)

---

## Overview

ORCA bridges the gap between satellite ocean data and real-world fishing decisions. Using satellite sources (INCOIS PFZ-7, ISRO Oceansat-3, IMD Coastal Radar), a multi-agent AI backbone (Google Gemini), and an interactive marine chart, ORCA delivers:

- **Where to fish** — ranked PFZ zones with confidence, target species, and ETA.
- **Is it safe?** — live weather, wave height, and safety classification.
- **How to get there** — bearing, course, and navigation route on an interactive map.
- **Voice assistance** — multilingual voice queries in English and Malayalam.

---

## Features

| Feature | Description |
|---|---|
| 🗺️ **Interactive Marine Chart** | Google Maps + Leaflet dual-engine with depth isobaths, vessel tracking, and zone circles |
| 🔗 **Connecting Lines** | Visual lines from vessel to all PFZ zones; highlighted line for selected zone |
| 🤖 **Multi-Agent AI** | Orchestrator delegates to Weather, Ocean, Safety, Fishing Zone, and Response agents |
| 📡 **Real Satellite Data** | INCOIS PFZ-7, Oceansat-3, IMD Coastal Radar, MOSDAC integration with demo fallback |
| 🔊 **Voice I/O** | Speech-to-Text via Groq Whisper, Text-to-Speech via Fish Audio |
| 🌐 **Multilingual** | English & Malayalam (extensible to 8+ Indian coastal languages) |
| 🧠 **RAG Pipeline** | TF-IDF / BGE-M3 retrieval-augmented generation for domain-specific query answering |
| 🔐 **Safety-First** | Deterministic safety overrides — AI cannot contradict danger classifications |
| 📱 **Mobile-First PWA** | Responsive UI designed for Android in low-connectivity coastal environments |
| 🏗️ **Demo Mode** | Fully functional offline demo with realistic INCOIS zone data |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│               ORCA Frontend (PWA)               │
│   HTML · Vanilla CSS · JavaScript               │
│   Google Maps API  /  Leaflet (fallback)        │
└────────────────────┬────────────────────────────┘
                     │ REST API + SSE
┌────────────────────▼────────────────────────────┐
│           FastAPI Backend (Python)              │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │         Multi-Agent Orchestrator         │  │
│  │  Weather · Ocean · Safety · FishZone    │  │
│  │  Response Agent (Gemini 3.6 Flash)      │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │  INCOIS     │  │  ISRO    │  │  IMD     │  │
│  │  PFZ-7 API  │  │Oceansat-3│  │  Radar   │  │
│  └─────────────┘  └──────────┘  └──────────┘  │
│                                                 │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐ │
│  │ RAG      │  │ Groq STT   │  │ Fish Audio │ │
│  │ Pipeline │  │ (Whisper)  │  │ TTS        │ │
│  └──────────┘  └────────────┘  └────────────┘ │
│                                                 │
│  SQLite  ·  In-Memory Cache  ·  Async SQLAlchemy│
└─────────────────────────────────────────────────┘
```

---

## Project Structure

```
ORCA/
├── backend/
│   ├── app/
│   │   ├── agents/           # Multi-agent system
│   │   │   ├── orchestrator.py
│   │   │   ├── fishing_zone_agent.py
│   │   │   ├── weather_agent.py
│   │   │   ├── ocean_agent.py
│   │   │   ├── safety_agent.py
│   │   │   └── response_agent.py
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── data_sources/     # INCOIS, ISRO, MOSDAC adapters
│   │   ├── llm/              # Gemini provider, LLM factory
│   │   ├── rag/              # RAG pipeline, vector store, reranker
│   │   ├── services/         # Business logic services
│   │   ├── schemas/          # Pydantic models
│   │   ├── models/           # SQLAlchemy DB models
│   │   └── main.py           # FastAPI app entry point
│   ├── tests/                # Pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── index.html            # Single-page PWA shell
│   └── js/
│       ├── app.js            # Application controller
│       ├── marine_map.js     # Dual-engine map (Google Maps + Leaflet)
│       ├── api.js            # REST API client
│       └── voice.js          # Voice STT/TTS integration
├── .env.example              # Environment variable template
├── backend/.env.example
├── start.sh                  # Linux/macOS launcher
├── start.bat                 # Windows launcher
└── docker-compose.yml        # Docker setup (optional)
```

---

## Tech Stack

**Backend**
- **Python 3.10+** — FastAPI, Uvicorn, SQLAlchemy (async), Pydantic v2
- **AI/ML** — Google Gemini 3.6 Flash, scikit-learn, FAISS, XGBoost, BGE-M3 embeddings
- **Voice** — Groq Whisper (STT), Fish Audio (TTS)
- **Data Sources** — INCOIS PFZ-7, ISRO Oceansat-3, IMD Coastal Radar, MOSDAC
- **Database** — SQLite (dev) / PostgreSQL-compatible (prod)

**Frontend**
- **HTML5 + Vanilla CSS + JavaScript** (no framework)
- **Google Maps JavaScript API** (primary map engine)
- **Leaflet + OpenStreetMap** (fallback map engine)
- **Material Symbols** — icon set

---

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip` package manager
- A Google Gemini API key (`GEMINI_API_KEY`)
- *(Optional)* Google Maps Browser Key for live satellite map
- *(Optional)* Groq API key (voice STT), Fish Audio API key (voice TTS)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/aravind-1801/ORCA.git
cd ORCA

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt
```

### Configuration

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Open `.env` and set at minimum:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_KEY=your_google_maps_browser_key_here  # Optional — Leaflet/OSM works without it
STT_API_KEY=your_groq_api_key_here                 # Optional — voice input
FISH_AUDIO_API_KEY=your_fish_audio_key_here        # Optional — voice output
DEMO_MODE=true                                      # Use realistic demo data (no live API calls)
```

> **Tip:** With `DEMO_MODE=true`, the app runs fully offline using pre-loaded INCOIS zone data and simulated telemetry — no API keys are required to explore the application.

### Running Locally

**Windows (double-click or CMD):**
```bat
start.bat
```

**Linux / macOS / Git Bash:**
```bash
./start.sh
```

**Or manually with Uvicorn:**
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:

| URL | Purpose |
|---|---|
| [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | 📱 ORCA Web App |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | 📖 Swagger API Docs |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | 🩺 Backend Health |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health and mode status |
| `GET` | `/api/fishing-zones` | List ranked PFZ zones near coordinates |
| `GET` | `/api/fishing-zones/{zone_id}` | Zone detail with diagnostics |
| `GET` | `/api/marine/status` | Full ocean + weather telemetry snapshot |
| `GET` | `/api/recommendation` | AI-generated fishing recommendation |
| `POST` | `/api/recommendation/query` | Natural language query to multi-agent AI |
| `GET` | `/api/alerts` | Active safety and weather alerts |
| `POST` | `/api/voice/transcribe` | STT — transcribe audio file |
| `GET` | `/api/profile` | Vessel and user profile |
| `GET` | `/api/location` | Current vessel location |
| `GET` | `/api/config` | Frontend runtime configuration |

Full interactive docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## Multi-Agent System

ORCA uses a **collaborative multi-agent architecture** built on Google Gemini:

```
User Query
    │
    ▼
Orchestrator Agent
    ├─► Weather Agent       — wind, wave, rain, swell data
    ├─► Ocean Agent         — SST, chlorophyll, currents
    ├─► Safety Agent        — danger classification (deterministic override)
    ├─► Fishing Zone Agent  — ranked PFZ zones, species, confidence
    └─► Response Agent      — synthesizes and localises final answer
                              (English / Malayalam)
```

**Key Safety Design:** The Safety Agent applies **deterministic rules** — if conditions are dangerous, the response always warns the fisherman regardless of what the LLM generates.

---

## Frontend Map Engine

The map uses a **dual-engine architecture** with automatic fallback:

1. **Google Maps** (primary) — satellite imagery, terrain, real coastal geography
2. **Leaflet + OSM** (fallback) — works without a Maps API key
3. **Canvas Vector Chart** (final fallback) — pure offline diagram

**Features:**
- Vessel position marker with heading arrow
- PFZ zone circles (green = high potential, grey = low)
- **Connecting lines** from vessel to all zones — selected zone highlighted in bright green
- Depth isobath contour lines (10m, 20m, 50m, 100m)
- Navigation route overlay
- Auto-fit bounds to show vessel + all zones on load

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and commit: `git commit -m "feat: add my feature"`
4. Push to your fork: `git push origin feature/my-feature`
5. Open a Pull Request against `main`

**Please ensure:**
- No `.env` files or API keys are committed
- New backend routes have corresponding tests in `backend/tests/`
- All safety-critical logic includes deterministic guards

---

## License

This project is part of the ORCA research initiative for coastal fisherman welfare. Please contact the maintainers before commercial use.

---

<p align="center">
  Built with ❤️ for the coastal fishing communities of Kerala, India.
</p>
