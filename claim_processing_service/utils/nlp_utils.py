from __future__ import annotations

import re
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional

import spacy

DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
]


@lru_cache(maxsize=1)
def get_nlp():
    """Load spaCy model if available; fallback to a blank English pipeline."""
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return spacy.blank("en")


def extract_dates(text: str) -> List[str]:
    found: List[str] = []
    for pattern in DATE_PATTERNS:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    deduped = []
    seen = set()
    for d in found:
        normalized = d.strip()
        if normalized.lower() not in seen:
            seen.add(normalized.lower())
            deduped.append(normalized)
    return deduped


def find_first_match(patterns: List[str], text: str) -> Optional[str]:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return (m.group(1) if m.lastindex else m.group(0)).strip()
    return None


def extract_person_candidates(text: str) -> List[str]:
    nlp = get_nlp()
    doc = nlp(text[:15000])
    people = []
    if "ner" in nlp.pipe_names:
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                people.append(ent.text.strip())
    if not people:
        # Fallback if model is not installed.
        fallback = re.findall(r"\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}", text)
        people.extend(fallback)
    seen = set()
    ordered = []
    for p in people:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(p)
    return ordered


def iso_date_or_raw(date_str: str) -> str:
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
        "%b %d %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ]
    clean = date_str.replace("  ", " ").strip()
    for fmt in formats:
        try:
            return datetime.strptime(clean, fmt).date().isoformat()
        except ValueError:
            continue
    return clean


def key_value_extract(text: str, mapping: Dict[str, List[str]]) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {}
    for key, patterns in mapping.items():
        result[key] = find_first_match(patterns, text)
    return result
