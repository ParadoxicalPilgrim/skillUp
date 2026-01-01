# Skill Up — AI-Powered Skill Gap Analyzer

**Bridging the gap between your current skills and your dream job.**

Skill Up is an AI-powered career guidance platform that analyzes your resume against a target job role and provides **personalized, actionable recommendations** to help you upskill effectively.

---

## 🚀 Features

- **Resume Upload & AI Analysis** — Upload a PDF resume and specify a target job role
- **Skill Gap Detection** — Identifies 8–10 critical missing skills
- **Personalized Project Ideas** — 5 hands-on projects to build real-world experience
- **Alternative Job Recommendations** — 3–4 roles aligned with your current skill set
- **Course & Video Suggestions** — Curated Coursera, Udemy, and YouTube resources

---

## 🛠 Tech Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI**: Google Gemini 1.5 Flash
- **PDF Processing**: PyMuPDF (fitz)
- **APIs**: Google Custom Search, YouTube Data API

---

## 🚀 Quick Start (Local Development)
  - Prerequisites
  - Python 3.10+
  - Node.js 18+
  - Git
## Backend Setup
```bash
cd backend
```
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

```bash
# Create environment file
cp .env.example .env
# Add keys: GEMINI_API_KEY, GOOGLE_API_KEY, YOUTUBE_API_KEY, SEARCH_ENGINE_ID
```
```bash
uvicorn main:app --reload
```
---
## Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open 👉 [http://localhost:5173](http://localhost:5173)
---
## 🌟 Contributing

We welcome contributions!
This project is part of ACM Winter of Code (WoC) 2.0 — Anokha 2026.

Please read CONTRIBUTING.md for:
  - How to pick issues
  - PR guidelines
  - Event rules & scoring
⚠️ Only issues labeled AMSOC-ACCEPTED are eligible for WoC points.

## 📜 License
MIT License — free to use, modify, and distribute.
