"""
utils.py
Shared emotion-detection logic for Lexicon.

v2: uses a pretrained transformer (bhadresh-savani/distilbert-base-uncased-emotion,
trained on the dair-ai/emotion dataset: sadness, joy, love, anger, fear, surprise)
instead of a hand-trained TF-IDF + XGBoost pipeline. This removes the dependency
on the old (now-dead) CrowdFlower dataset URL and gives much better generalization
on real, conversational sentences instead of short 2016 tweets.
"""

# Emotions shown in the UI (unchanged - frontend/app.js expects exactly these keys)
EMOTIONS = ["anger", "happiness", "sadness", "love", "hate", "surprise"]

# The pretrained model's native labels -> Lexicon's display labels.
# The model has no "hate" class (most emotion datasets don't separate it from
# anger), so hate is detected via an explicit keyword override in app.py instead.
MODEL_LABEL_MAP = {
    "joy": "happiness",
    "sadness": "sadness",
    "anger": "anger",
    "love": "love",
    "surprise": "surprise",
    "fear": "sadness",  # closest available bucket; no separate "fear" UI state
}

HATE_KEYWORDS = ["hate", "despise", "loathe", "detest"]

# Words that are unambiguously negative in context but that the transformer
# (trained on short, clean tweets) sometimes gets outvoted on by a stray
# positive-sounding word or an odd tokenization. If one of these appears and
# the model's top pick is happiness/love/surprise, we don't trust that pick.
NEGATIVE_OVERRIDE_KEYWORDS = [
    "headache", "pain", "hurts", "hurting", "sick", "exhausted", "tired",
    "annoying", "sucks", "terrible", "awful", "miserable", "broken",
    "heartbroken", "sorry", "fail", "failed", "worst", "bored", "boring",
]


def squeeze_repeated_chars(text: str) -> str:
    """Collapse runs of 3+ repeated letters down to 2 (e.g. 'loooong' ->
    'loong', 'sooooo' -> 'soo'). Improves tokenization for informal/elongated
    spelling the model wasn't trained on, without destroying real words."""
    import re
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def contains_negative_override(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in NEGATIVE_OVERRIDE_KEYWORDS)

# Front-end display metadata for each emotion (color, gradient, emoji, copy)
# Unchanged from v1.
EMOTION_META = {
    "happiness": {"color": "#F5A524", "gradient": ["#F5A524", "#FFD166"],
                  "emoji": "😊", "label": "Happiness", "message": "Spread the joy!"},
    "sadness":   {"color": "#3B82F6", "gradient": ["#3B82F6", "#60A5FA"],
                  "emoji": "😢", "label": "Sadness", "message": "Tomorrow will be better."},
    "anger":     {"color": "#EF4444", "gradient": ["#EF4444", "#F97316"],
                  "emoji": "😠", "label": "Anger", "message": "Take a deep breath."},
    "love":      {"color": "#EC4899", "gradient": ["#EC4899", "#F472B6"],
                  "emoji": "❤️", "label": "Love", "message": "Love is all around."},
    "hate":      {"color": "#78716C", "gradient": ["#78716C", "#A8A29E"],
                  "emoji": "🤬", "label": "Hate", "message": "Let it go."},
    "surprise":  {"color": "#8B5CF6", "gradient": ["#8B5CF6", "#C084FC"],
                  "emoji": "😲", "label": "Surprise", "message": "Life is full of surprises!"},
}


def contains_hate_keyword(text: str) -> bool:
    """Cheap, explicit override signal for the one emotion the pretrained
    model can't distinguish from anger on its own."""
    lowered = text.lower()
    return any(word in lowered for word in HATE_KEYWORDS)


def remap_scores(raw_scores: dict) -> dict:
    """Collapse the model's native label set onto Lexicon's 6 display emotions,
    summing probability mass where more than one native label maps to one bucket
    (e.g. fear + sadness both feed the 'sadness' bucket)."""
    merged = {e: 0.0 for e in EMOTIONS}
    for label, score in raw_scores.items():
        bucket = MODEL_LABEL_MAP.get(label)
        if bucket:
            merged[bucket] += score
    return merged
