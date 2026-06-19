"""Gregg-shorthand-inspired field-note compressor.

Turns a verbose spoken field note into a compact, structured, low-bandwidth
field-log line that is fast to read back over a phone and cheap to sync when
connectivity returns. Fully deterministic — no LLM, works offline.

Principles borrowed from Gregg's Light-Line Phonography:
  * brief forms        — frequent terms -> fixed short codes
  * phrasing           — common multi-word phrases blend into one token
  * vowel omission     — unknown long words drop interior vowels
  * prefix/suffix      — standard affixes get fixed marks
  * filler removal     — obscure/neutral filler words dropped
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from .config import CONTENT_DIR

_LEXICON_PATH = CONTENT_DIR / "shorthand" / "lexicon.json"

# number (optionally signed/decimal) + optional unit token
_MEASURE_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*"
    r"(mm|cm|m|km|kg|g|mg|deg|degrees|c|f|hpa|mbar|ml|l|min|sec|s|%|n)?",
    re.IGNORECASE,
)
_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]*")


@lru_cache(maxsize=1)
def _lexicon() -> dict:
    with open(_LEXICON_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _omit_vowels(word: str) -> str:
    """Keep first letter, drop interior non-essential vowels (Gregg-style)."""
    if len(word) <= 4:
        return word
    head, tail = word[0], word[1:]
    reduced = re.sub(r"[aeiou]", "", tail)
    out = head + reduced
    return out if len(out) >= 2 else word


def _apply_affixes(word: str, lex: dict) -> str:
    for pre, code in lex.get("prefixes", {}).items():
        if word.startswith(pre) and len(word) > len(pre) + 2:
            return code + _omit_vowels(word[len(pre):])
    for suf, code in lex.get("suffixes", {}).items():
        if word.endswith(suf) and len(word) > len(suf) + 2:
            return _omit_vowels(word[: -len(suf)]) + code
    return _omit_vowels(word)


def extract_measurements(text: str) -> list[dict]:
    """Pull out number+unit measurements as structured rows."""
    out = []
    for m in _MEASURE_RE.finditer(text):
        value, unit = m.group(1), m.group(2)
        if unit is None:
            continue  # require a unit to avoid catching stray digits
        out.append({"value": float(value), "unit": unit.lower()})
    return out


def compress(text: str) -> dict:
    """Compress a spoken field note.

    Returns a dict with the compact field line, the token mapping, extracted
    measurements, and the original text for the custody record.
    """
    lex = _lexicon()
    brief = {k.lower(): v for k, v in lex.get("brief_forms", {}).items()}
    phrases = {k.lower(): v for k, v in lex.get("phrases", {}).items()}
    stop = set(w.lower() for w in lex.get("stopwords_droppable", []))

    work = text.lower()
    # 1) phrase blending first (longest phrases first)
    for phrase in sorted(phrases, key=len, reverse=True):
        work = re.sub(rf"\b{re.escape(phrase)}\b", phrases[phrase], work)

    tokens_out: list[str] = []
    mapping: list[dict] = []
    for raw in work.split():
        # carry trailing punctuation through to keep readability minimal
        word = _WORD_RE.match(raw)
        token = word.group(0) if word else raw
        if not token:
            continue
        low = token.lower()
        if low in stop:
            continue
        if low in brief:
            code = brief[low]
        elif low in phrases.values():
            code = low  # already a blended phrase code
        else:
            code = _apply_affixes(low, lex)
        tokens_out.append(code)
        if code != low:
            mapping.append({"from": token, "to": code})

    measurements = extract_measurements(text)
    field_line = " ".join(tokens_out)
    ratio = round(len(field_line) / max(len(text), 1), 3)

    return {
        "field_line": field_line,
        "measurements": measurements,
        "token_map": mapping,
        "original": text,
        "compression_ratio": ratio,
    }
