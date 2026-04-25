"""Fast sentiment analysis using VADER (NLTK) + scikit-learn fallback.

VADER is rule-based and works well for social-media/review text.
No API calls needed — runs locally in milliseconds.
"""

from __future__ import annotations

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd

# Ensure VADER lexicon is available
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

_sia = SentimentIntensityAnalyzer()


def _classify_compound(score: float) -> str:
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"


def analyze_sentiment(df: pd.DataFrame, text_column: str = "content") -> pd.DataFrame:
    """Add sentiment columns to a DataFrame using VADER.

    Adds:
        - sentiment_compound: float [-1, 1]
        - sentiment_pos / sentiment_neg / sentiment_neu: float [0, 1]
        - sentiment: "positive" | "negative" | "neutral"

    Returns a copy of the DataFrame with new columns.
    """
    df = df.copy()
    texts = df[text_column].fillna("").astype(str)

    scores = texts.apply(lambda t: _sia.polarity_scores(t))
    df["sentiment_compound"] = scores.apply(lambda s: s["compound"])
    df["sentiment_pos"] = scores.apply(lambda s: s["pos"])
    df["sentiment_neg"] = scores.apply(lambda s: s["neg"])
    df["sentiment_neu"] = scores.apply(lambda s: s["neu"])
    df["sentiment"] = df["sentiment_compound"].apply(_classify_compound)

    return df
