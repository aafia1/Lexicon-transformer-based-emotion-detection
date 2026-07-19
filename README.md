<div align="center">

# 🎭 Lexicon — AI Emotion Detection System

**A Flask REST API + responsive web UI that detects emotion from text in real time.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.4-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/🤗%20Transformers-4.44-FFD21E?style=flat-square)](https://huggingface.co/transformers)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](#-license)

</div>

---

## 📖 Overview

Lexicon detects **6 emotions** behind any piece of text — anger, happiness,
sadness, love, hate, and surprise — through a clean REST API and an animated,
dark/light-mode web UI.

v2 runs on a pretrained transformer
(**[`bhadresh-savani/distilbert-base-uncased-emotion`](https://huggingface.co/bhadresh-savani/distilbert-base-uncased-emotion)**)
instead of a hand-trained TF-IDF + XGBoost pipeline — no training step, no
dataset dependency, and noticeably better accuracy on real, conversational
sentences rather than short 2016 tweets.

| ❤️ Love | 😊 Happiness | 😢 Sadness | 😠 Anger | 🤬 Hate | 😲 Surprise |
|:---:|:---:|:---:|:---:|:---:|:---:|

---

## ✨ Features

- 🧠 **Transformer-based classification** — pretrained DistilBERT, no training required
- ⚡ **REST API** — single and batch prediction endpoints
- 🎨 **Animated web UI** — confidence gauge, per-emotion color theming, dark/light mode
- 🕘 **Session history** — saved locally in the browser
- 🛡️ **Guardrail overrides** — keyword-based sanity checks layered on top of model output
- 📦 **Single-process deploy** — Flask serves the API and the frontend together

---

## 📁 Project structure

```
emotion-detection-pro/
├── backend/
│   ├── app.py                 # Flask API + serves the frontend
│   ├── utils.py                # Emotion label mapping + guardrail overrides
│   ├── prefetch_model.py       # Optional: pre-download the model
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── Dockerfile                  # Optional: for container-based hosts
├── Procfile                    # Optional: for buildpack-based hosts
└── README.md
```

---

## 🚀 Getting started

```bash
git clone https://github.com/aafia1/emotion-detection-pro.git
cd emotion-detection-pro/backend

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
python app.py
```

First run downloads the model (~260MB, cached after). Open **http://localhost:5000** 🎉

---

## 📡 API reference

### `POST /api/predict`
```json
{ "text": "I adore everything about you" }
```
**Response**
```json
{
  "emotion": "love",
  "confidence": 91.4,
  "distribution": { "anger": 1.2, "happiness": 5.6, "...": "..." },
  "meta": { "emoji": "❤️", "label": "Love", "color": "#EC4899" },
  "word_count": 5,
  "latency_ms": 42.1
}
```

### `POST /api/predict/batch`
```json
{ "texts": ["I love this!", "This makes me furious."] }
```

### `GET /api/health`
```json
{ "status": "ok", "model_loaded": true }
```

---

## 🛠️ Tech stack

| Layer | Tools |
|---|---|
| Backend | Flask, Flask-CORS, Gunicorn |
| ML | PyTorch, 🤗 Transformers (DistilBERT) |
| Frontend | HTML, CSS, vanilla JS |

---


## 📜 License

This project is licensed under the MIT License — see [`LICENSE`](LICENSE) for details.

---

## 🙌 Credits

Built on top of the original *AI Emotion Detection System* project, developed
as part of the Machine Learning Internship at Ezitech Institute. v2 pipeline
uses `bhadresh-savani/distilbert-base-uncased-emotion` (dair-ai/emotion dataset).
