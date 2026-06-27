# KrishiMitra 🌾 - AI-Powered Farming Assistant

## Overview
KrishiMitra is a multi-agent AI farming assistant built for Indian farmers using Google ADK. It provides real-time weather advisories, live mandi prices, crop disease diagnosis, government scheme recommendations, and profit calculations — all in English, Hindi, and Kannada.

## ADK Concepts Demonstrated
1. **Multi-Agent Orchestration** — 7 specialized agents (Mausam, Mandi, Nidan, Sarkari, Profit, Memory, Orchestrator) working together
2. **RAG (Retrieval Augmented Generation)** — farming knowledge base retrieved for crop and scheme queries
3. **Agent Memory/State** — farmer profile persisted across sessions in JSON
4. **Tool Use** — OpenWeatherMap API, data.gov.in mandi API integrated as ADK tools
5. **Parallel Agent Execution** — multiple agents called simultaneously for complex queries

## Features
- 🌤️ Real-time weather + irrigation advice for any Indian city
- 🏪 Live mandi prices from Karnataka, Maharashtra, Punjab
- 🌿 Crop disease diagnosis from text description
- 📋 Government scheme finder (PM-KISAN, crop insurance, subsidies)
- 💰 Profit calculator based on yield and market prices
- 🗣️ Voice input in English, Hindi, Kannada
- 🌐 Full multilingual UI — English, हिंदी, ಕನ್ನಡ
- 💾 Conversation history with save and reload
- 👤 Farmer profile memory across sessions

## Multi-Agent Architecture
User Query → Orchestrator Agent → Routes to:
- Mausam (Weather Agent) → OpenWeatherMap API
- Mandi (Market Agent) → data.gov.in API + RAG
- Nidan (Pest & Disease Agent) → RAG + Mistral
- Sarkari (Scheme Agent) → RAG + Mistral
- Profit (Calculator Agent) → Mistral
- Memory (Profile Agent) → Local JSON storage

## Tech Stack
- Backend: Python, Google ADK, FastAPI, Mistral AI
- Frontend: HTML, CSS, JavaScript (single file)
- APIs: OpenWeatherMap, data.gov.in
- RAG: TF-IDF retrieval on farming knowledge base
- Storage: Local JSON for farmer profiles and chat history

## Installation
```bash
git clone https://github.com/dishaprabhakar2006-blip/KrishiMitra
cd KrishiMitra
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
uvicorn main:app --reload --port 8000
```

## API Keys Required
- MISTRAL_API_KEY — from mistral.ai
- OPENWEATHER_API_KEY — from openweathermap.org
- GEMINI_API_KEY — from aistudio.google.com (optional, for vision)

## Future Scope
- 📸 Image and video upload for visual crop disease detection
- 🔥 Firebase integration for cloud-based farmer profiles
- 📱 Mobile app with offline support
- 🛰️ Satellite imagery integration for field monitoring
- 🌍 Support for 10+ Indian regional languages
- 📊 Crop yield prediction using ML models
- 🤝 Farmer community forum with peer advice

## Track
Agents for Good — Agriculture & Rural Development

## Author
Disha Prabhakar — B.E. AIML, BMS College of Engineering, Bangalore
