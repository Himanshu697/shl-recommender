import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.config import CATALOG_PATH, TOP_K_RETRIEVAL

_catalog = None
_vectorizer = None
_tfidf_matrix = None
_documents = None


def _load_catalog():
    global _catalog, _vectorizer, _tfidf_matrix, _documents
    if _catalog is not None:
        return

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        _catalog = json.load(f)

    _documents = []
    for item in _catalog:
        keys_str = " ".join(item.get("keys", []))
        levels_str = " ".join(item.get("job_levels", []))
        langs_str = " ".join(item.get("languages", []))
        doc = f"{item['name']} {item.get('description', '')} {keys_str} {levels_str} {langs_str}"
        _documents.append(doc)

    _vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, stop_words="english")
    _tfidf_matrix = _vectorizer.fit_transform(_documents)


def _keys_to_test_type(keys: list) -> str:
    mapping = {
        "Knowledge & Skills": "K",
        "Personality & Behavior": "P",
        "Ability & Aptitude": "A",
        "Competencies": "C",
        "Simulations": "S",
        "Biodata & Situational Judgment": "B",
        "Assessment Exercises": "E",
        "Development & 360": "D",
    }
    codes = []
    for k in keys:
        code = mapping.get(k)
        if code and code not in codes:
            codes.append(code)
    return ", ".join(codes) if codes else "K"


def search(query: str, top_k: int = TOP_K_RETRIEVAL) -> list:
    _load_catalog()

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            item = _catalog[idx]
            results.append({
                "name": item["name"],
                "url": item["link"],
                "test_type": _keys_to_test_type(item.get("keys", [])),
                "keys": item.get("keys", []),
                "description": item.get("description", ""),
                "duration": item.get("duration", ""),
                "languages": item.get("languages", []),
                "job_levels": item.get("job_levels", []),
            })
    return results


def get_by_name(name: str) -> dict | None:
    _load_catalog()
    name_lower = name.lower()
    for item in _catalog:
        if name_lower in item["name"].lower():
            return {
                "name": item["name"],
                "url": item["link"],
                "test_type": _keys_to_test_type(item.get("keys", [])),
                "keys": item.get("keys", []),
                "description": item.get("description", ""),
                "duration": item.get("duration", ""),
                "languages": item.get("languages", []),
                "job_levels": item.get("job_levels", []),
            }
    return None


def get_all() -> list:
    _load_catalog()
    results = []
    for item in _catalog:
        results.append({
            "name": item["name"],
            "url": item["link"],
            "test_type": _keys_to_test_type(item.get("keys", [])),
            "keys": item.get("keys", []),
            "description": item.get("description", ""),
            "duration": item.get("duration", ""),
            "languages": item.get("languages", []),
            "job_levels": item.get("job_levels", []),
        })
    return results
