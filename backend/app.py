"""
app.py
Flask REST API for the Lexicon emotion detection system.

v2: loads a pretrained HuggingFace transformer at startup instead of joblib
artifacts trained by train_model.py. No training step needed - the model
downloads once (cached by HuggingFace under ~/.cache/huggingface) the first
time you run this file.

    GET  /api/health          -> {"status": "ok", "model_loaded": true}
    POST /api/predict         -> {"text": "..."}  single prediction
    POST /api/predict/batch   -> {"texts": ["...", "..."]}  batch prediction

Also serves the static frontend (frontend/) so the whole app runs from
a single process at http://localhost:5000
"""

import os
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from utils import (
    EMOTIONS, EMOTION_META, contains_hate_keyword, contains_negative_override,
    remap_scores, squeeze_repeated_chars,
)

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ---------------------------------------------------------------------
# Load the pretrained model once at startup
# ---------------------------------------------------------------------
MODEL_NAME = "bhadresh-savani/distilbert-base-uncased-emotion"
classifier = None

try:
    print(f"Loading emotion model '{MODEL_NAME}'...")
    print("(first run downloads ~260MB and caches it - can take a minute)")
    from transformers import pipeline
    classifier = pipeline("text-classification", model=MODEL_NAME, top_k=None)
    print("Model loaded successfully.")
except Exception as exc:  # noqa: BLE001 - want to keep serving with a clear error
    print("=" * 70)
    print("WARNING: could not load the emotion model:", exc)
    print("Check your internet connection (first run needs to download it)")
    print("and that 'transformers' and 'torch' are installed.")
    print("=" * 70)


def predict_single(text: str) -> dict:
    normalized = squeeze_repeated_chars(text)
    raw = classifier(normalized)[0]  # [{"label": "joy", "score": 0.87}, ...] for all classes
    raw_scores = {item["label"]: item["score"] for item in raw}

    merged = remap_scores(raw_scores)

    if contains_hate_keyword(text):
        # The model has no "hate" class - when the keyword is explicit,
        # reclassify most of anger's probability mass as hate.
        merged["hate"] = max(merged["anger"], 0.6)
        merged["anger"] *= 0.3

    top_emotion = max(merged, key=merged.get)
    if top_emotion in ("happiness", "love", "surprise") and contains_negative_override(text):
        # A clearly negative word (headache, sucks, exhausted, ...) shouldn't
        # lose to a shaky positive read from the model. Dampen the positive
        # bucket and boost sadness instead.
        merged[top_emotion] *= 0.3
        merged["sadness"] = max(merged["sadness"], 0.55)

    total = sum(merged.values()) or 1.0
    distribution = {k: round((v / total) * 100, 1) for k, v in merged.items()}
    final_emotion = max(merged, key=merged.get)
    confidence = distribution[final_emotion]

    meta = EMOTION_META.get(final_emotion, {})
    return {
        "emotion": final_emotion,
        "confidence": confidence,
        "distribution": distribution,
        "meta": meta,
        "word_count": len(text.split()),
    }


# ---------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "model_loaded": classifier is not None})


@app.route("/api/predict", methods=["POST"])
def predict():
    if classifier is None:
        return jsonify({"error": "Model not loaded. Check server logs for details."}), 503

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Field 'text' is required and cannot be empty."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text too long (max 2000 characters)."}), 400

    start = time.time()
    result = predict_single(text)
    result["latency_ms"] = round((time.time() - start) * 1000, 1)
    return jsonify(result)


@app.route("/api/predict/batch", methods=["POST"])
def predict_batch():
    if classifier is None:
        return jsonify({"error": "Model not loaded. Check server logs for details."}), 503

    data = request.get_json(silent=True) or {}
    texts = data.get("texts") or []
    if not isinstance(texts, list) or not texts:
        return jsonify({"error": "Field 'texts' must be a non-empty list."}), 400
    if len(texts) > 50:
        return jsonify({"error": "Max 50 items per batch."}), 400

    results = []
    for t in texts:
        t = (t or "").strip()
        if not t:
            continue
        results.append({"text": t, **predict_single(t)})
    return jsonify({"results": results, "count": len(results)})


@app.route("/api/emotions")
def emotions_meta():
    return jsonify(EMOTION_META)


# ---------------------------------------------------------------------
# Serve the frontend
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
