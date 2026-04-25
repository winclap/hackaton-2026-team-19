"""Theme extraction using TF-IDF + KMeans clustering.

Runs entirely locally with scikit-learn. No API calls.
Assigns each review to a cluster and extracts top terms per cluster as theme labels.
"""

from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans


def extract_themes(
    df: pd.DataFrame,
    text_column: str = "content",
    n_clusters: int = 8,
    max_features: int = 5000,
) -> pd.DataFrame:
    """Cluster reviews into themes using TF-IDF + KMeans.

    Adds:
        - theme_cluster: int cluster id
        - theme_label: auto-generated label from top TF-IDF terms

    Returns a copy of the DataFrame.
    """
    df = df.copy()
    texts = df[text_column].fillna("").astype(str)

    # Fit TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    # Adjust n_clusters if we have fewer samples
    actual_clusters = min(n_clusters, max(2, len(df) // 5))

    kmeans = MiniBatchKMeans(n_clusters=actual_clusters, random_state=42, n_init=3)
    df["theme_cluster"] = kmeans.fit_predict(tfidf_matrix)

    # Generate labels from top terms per cluster center
    cluster_labels = {}
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    for i in range(actual_clusters):
        top_terms = [feature_names[idx] for idx in order_centroids[i, :3]]
        cluster_labels[i] = "_".join(top_terms)

    df["theme_label"] = df["theme_cluster"].map(cluster_labels)

    return df
