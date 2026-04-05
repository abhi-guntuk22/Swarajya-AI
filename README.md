# ⚡ Swarajya-AI — Sovereign Intelligence Hub

> **AMD Slingshot 2026 Hackathon Entry**
> *GPU-Powered · 100% Offline · Made in India 🇮🇳*

---

## 🎯 The Problem

Every time a student or engineer uses ChatGPT or Claude:

- Their **questions leave India's borders** — sent to US-based cloud servers
- They need **a stable internet connection** — impossible in rural/tier-3 cities
- Their **academic work, code, and ideas** are stored on foreign infrastructure
- They are **dependent on foreign companies' uptime, pricing, and policies**

For a nation of 1.4 billion people trying to build a knowledge economy, this is a **sovereignty problem**.

---

## 💡 The Solution: Swarajya-AI

Swarajya-AI turns any GPU-enabled laptop into a **Local AI Server** — a complete, self-contained intelligence hub that:

| Feature | Swarajya-AI | ChatGPT / Claude |
|---------|-------------|-----------------|
| Internet Required | ❌ Never | ✅ Always |
| Data Leaves Device | ❌ Never | ✅ Every query |
| Works in Rural India | ✅ Yes | ❌ No |
| Cost per query | ₹0 | $0.01–0.06 |
| Data Sovereignty | ✅ 100% | ❌ 0% |
| Offline-first | ✅ Yes | ❌ No |

---

## ✨ Features

### 🔐 Gatekeeper Authentication
- Password-protected access (session-isolated per user)
- Brute-force protection (lockout after 5 failed attempts)

### 🛡️ Prompt Firewall
- Regex-based jailbreak detection (12+ attack patterns)
- Blocked topic classification (malware, weapons, etc.)
- Input length validation and sanitization

### ⏱️ Rate Limiter
- Minimum 10-second gap between requests per session
- Prevents abuse and GPU overload in multi-user scenarios

### 🎓 AI Modes (SPPU IT Engineering Focus)
1. **Concept Explanation** — Deep explanations with Indian analogies
2. **Code Debugger** — Bug detection, correction, and best practices
3. **Syllabus Finder** — SPPU curriculum mapping and study guidance

### 🇮🇳 Hinglish Mode
Natural Hindi-English mixed responses for better comprehension

### 📊 Hardware Monitor (Real-time)
- GPU name + VRAM usage
- CPU utilization
- RAM consumption
- Disk space

### 🌐 LAN Access
- Auto-detected local IP
- Any device on the same WiFi can connect (phones, tablets, other laptops)

---

## 🏗️ Architecture

```
Swarajya-AI/
├── app.py          # Streamlit frontend (UI, routing, CSS)
├── brain.py        # Ollama inference engine (LLM communication)
├── security.py     # Auth, Prompt Firewall, Rate Limiter
├── utils.py        # Hardware monitoring, network detection
├── config.py       # Centralized configuration (single source of truth)
├── requirements.txt
├── .gitignore
└── README.md
```

### Request Flow

```
User Input
    │
    ▼
[Rate Limiter] ──too fast──► ⏱️ Wait message
    │
    ▼
[Prompt Firewall] ──blocked──► 🛡️ Rejection message
    │
    ▼
[brain.py: build_system_prompt()]
    │
    ▼
[Ollama API: POST /api/generate] ──error──► 🔌 Error message
    │
    ▼
[Response rendered in chat]
```

---

## ⚙️ Setup Guide

### Prerequisites

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull the Llama 3 model (~4.7 GB)
ollama pull llama3

# 3. Start Ollama
ollama serve
```

### Installation

```bash
# Clone the repository
git clone https://github.com/abhi-guntuk22/Swarajya-AI.git
cd Swarajya-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) AMD ROCm GPU support
pip install torch --index-url https://download.pytorch.org/whl/rocm5.7
```

### Run

```bash
# Multi-user LAN server (recommended)
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Access the app:
- **Local:** http://localhost:8501
- **LAN:** http://[your-ip]:8501 (shown in sidebar)

**Default Password:** `Bharat2026`

> ⚠️ Change the password before deployment:
> ```python
> # In config.py
> AUTH_PASSWORD = "YourSecurePassword"
> ```
> Or via environment variable: `export SWARAJYA_PASSWORD=YourPassword`

---

## 🎮 AMD GPU Optimization

Swarajya-AI is optimized for AMD GPUs via ROCm:

```bash
pip install torch --index-url https://download.pytorch.org/whl/rocm5.7
```

Ollama automatically uses AMD GPU if ROCm is installed.

**Tested AMD GPUs:** RX 6600, RX 6700 XT, RX 7900 XTX, Radeon Pro series

---

## 🌍 Why Offline Matters for India

- **45%** of Indian internet users face connectivity issues regularly
- Rural internet speeds average **5-10 Mbps** — insufficient for real-time AI
- Under India's **DPDPA 2023**, local data handling is the future
- Swarajya-AI is **DPDPA-by-design** — no data ever leaves the device
- SPPU has **500,000+ enrolled students** — most lack reliable AI access
- A single Swarajya-AI laptop can serve **an entire classroom** over WiFi

---

## 🔮 Future Roadmap

### Phase 2 — RAG Integration
- Upload SPPU PDFs → ChromaDB vector store → Context-aware answers
- Question papers, textbooks, lab manuals

### Phase 3 — Voice Interface
- Speak in Hindi/Marathi → Whisper transcription → AI → TTS
- Powered by OpenAI Whisper (local, offline)

### Phase 4 — Mobile App
- React Native app connecting to Swarajya-AI over LAN
- Works on any Android/iOS device on the same WiFi

---

## 🛡️ Security Model

| Threat | Mitigation |
|--------|-----------|
| Unauthorized access | Password auth + session isolation |
| Jailbreak attacks | 12-pattern regex firewall |
| Prompt injection | Template injection detection |
| Brute force | 5-attempt lockout |
| Request flooding | 10s rate limiter per session |
| Data exfiltration | Zero network calls (air-gapped design) |

---

## 📄 License

MIT License — Built for Bharat, open to the world.

---

<div align="center">

**Built with ❤️ for AMD Slingshot 2026**

*"Swarajya — Self-Rule through Sovereign AI"* 🇮🇳

</div>
