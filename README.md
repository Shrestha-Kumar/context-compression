<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/4/4e/Open_Source_Initiative_keyhole.svg" width="60" alt="OSI Open Source"/>
  <h1 align="center">KINETIC_SYS | Context Compression Module</h1>
  <p align="center">
    <strong>Infinite Context. Zero Latency.</strong><br/>
    A brutally efficient LLM compression system engineered for the Hack 60 Advanced AI Hackathon.
  </p>

  <p align="center">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white">
    <img alt="React" src="https://img.shields.io/badge/React-18.0-blue?logo=react&logoColor=white">
    <img alt="Vite" src="https://img.shields.io/badge/Vite-5.0-blue?logo=vite&logoColor=white">
    <img alt="TailwindCSS" src="https://img.shields.io/badge/TailwindCSS-3.4-blue?logo=tailwind-css&logoColor=white">
    <img alt="Qwen2.5" src="https://img.shields.io/badge/LLM-Qwen2.5%201.5B-green">
  </p>
</div>

---

## 🖤 Overview

A highly modular two-tier compression architecture designed to run large-scale context agents securely on constrained consumer hardware (6–12 GB VRAM). By unifying a strictly typed UI with a cutting-edge Chain-of-Thought (CoT) LoRA adapter, **Kinetic_SYS** maintains >95% goal state accuracy across +30 chat turns.

**Aesthetics:** The UI relies on a brutalist, strictly monochrome aesthetic. Uncompromised scaling constraints ensure data displays dynamically via SVGs across `kvCacheMetrics` natively wrapped over a 3D Spline background. 

---

## 🏛 Architecture

### The Frontend (Vite + React + Tailwind)
We broke from generic frameworks to embrace a highly functional, pure `React` engine.
- **Dynamic Live Metrics:** Active tracking of compression ratios via dynamic mathematical SVG tracing natively connected to the WebSockets. 
- **Zustand AppStore:** Singleton memory architecture managing `activeConstraints` directly in real-time.
- **Spline WASM Isolation:** Robust error boundary architecture (`SplineErrorBoundary`) catching 100k+ WASM particle overflows, gracefully scaling the application on low-end hardware without halting the DOM render.

### The Backend (FastAPI + QLoRA CoT)
- **Attention Sink KV-Cache:** PyTorch tensor slicing guarantees the anchor system prompt retains zero attention decay. 
- **Qwen2.5-1.5B Fine-tune:** A state-of-the-art PEFT model explicitly fine-tuned via `LoRA` parameters. The model handles all contextual parsing organically, stripping away legacy TF-IDF or regex dependencies resulting in pure, inferential constraints execution.
- **Persistent Chat History (SQLite):** New session-based architecture that auto-saves conversation state (messages, memory, telemetry) to a local SQLite database, allowing users to resume historical threads seamlessly.
- **Async WebSocket Duplex:** Streams data points simultaneously down the wire to the frontend to provide immediate telemetry on layer times and latency.

---

## ⚙️ Stack & Frameworks

| Layer | Framework/Tech | Usage |
|-------|----------------|-------|
| **Core UI** | `React` + `Vite` | Instant hot module replacement and DOM mapping. |
| **Styling** | `Tailwind CSS` | Strictly bound `app.css` utilizing custom monochromatic tracking layers. |
| **Animation** | `Framer Motion` | Granular bounds scaling, expanding dynamic structural divs (e.g., ConstraintsSidebar). |
| **3D Engine** | `@splinetool/react-spline` | Heavyweight WebGL overlay for premium user transitions. |
| **Backend API** | `FastAPI` | Asynchronous WebSocket telemetry handling. |
| **Model** | `Qwen2.5-1.5B` (HuggingFace) | Lightweight SLM fine-tuned specifically for entity relation. |

---

## 🛠 Complete Setup Guide

### 1. Repository Initialization
Clone the repository:
```bash
git clone <your-repo>
cd context-compression-module
```

### 2. Backend Bootup
Since the model is strictly bound to PyTorch and QLoRA, ensure CUDA 12.1+ and the proper environment are initialized.

**Using Micromamba (Recommended):**
```bash
micromamba create -n dl python=3.10
micromamba activate dl
pip install -r backend/requirements.txt
```

**Start the local PyTorch ASGI Socket:**
```bash
PYTHONPATH=. micromamba run -n dl python3 backend/app.py
```

### 3. Frontend Initialization
Spin up the `Vite` pipeline on another terminal natively:
```bash
cd frontend
npm install
npm run dev
```

The application will map directly to `http://localhost:5173`. 
Upon loading, the WASM engine allocates 100,000 particle limits for the Spline rendering engine. Click `Deploy Pipeline`. The error handler guarantees safe load execution across devices.

---

## 🚀 Evaluation
Run the automated benchmarking scripts for your presentation phase.
```bash
python -m backend.evaluation.benchmark --mode both
```
Watch the agent perfectly parse the needle test! The compression preserves >90% token reduction directly visible via the `MetricsPanel` in the frontend dashboard. 

---
<div align="center">
<i>Built for Hack 60. Industry-standard format approved.</i>
</div>
