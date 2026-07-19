"""
prefetch_model.py
Optional: downloads and caches the pretrained emotion model ahead of time,
so the first `python app.py` start isn't slowed down by the download.

Run once, whenever you like:
    python prefetch_model.py

(You do NOT need to run this before app.py - app.py will download the
model itself on first startup if it isn't cached yet. This script just
lets you do that step separately/in advance.)
"""

from transformers import pipeline

MODEL_NAME = "bhadresh-savani/distilbert-base-uncased-emotion"

if __name__ == "__main__":
    print(f"Downloading and caching '{MODEL_NAME}'...")
    pipeline("text-classification", model=MODEL_NAME, top_k=None)
    print("Done. Model is cached - app.py will now start instantly.")
