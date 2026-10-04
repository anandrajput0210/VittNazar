import re


PRESSURE_PATTERNS = [
    {
        "category": "urgency",
        "patterns": [
            r"\bact\s+now\b",
            r"\blimited\s+time\b",
            r"\blast\s+chance\b",
            r"\bonly\s+(?:available|valid)\s+(?:today|now)\b",
            r"\boffer\s+ends\s+today\b",
            r"\bsubscribe\s+today\b",
            r"\bdecide\s+today\b",
        ],
        "label": "Urgency / time pressure",
        "explanation": (
            "The message uses time pressure that may encourage "
            "a rushed financial decision."
        ),
    },
    {
        "category": "fear_of_missing_out",
        "patterns": [
            r"\bmiss\s+out\b",
            r"\bdon'?t\s+miss\b",
            r"\bexclusive\s+opportunity\b",
            r"\bonly\s+a\s+few\s+spots?\b",
            r"\bvip\s+opportunity\b",
        ],
        "label": "Fear-of-missing-out language",
        "explanation": (
            "The message suggests that failing to act may cause "
            "the investor to miss a special opportunity."
        ),
    },
]


def normalize_text(text):
    """Normalize whitespace and convert text to lowercase."""
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_pressure_signals(text):
    """
    Detect persuasion/pressure signals separately from financial claims.

    Returns one result per detected signal category.
    """
    text = normalize_text(text)

    signals = []
    seen_categories = set()

    for group in PRESSURE_PATTERNS:
        for pattern in group["patterns"]:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if not match:
                continue

            category = group["category"]

            if category in seen_categories:
                break

            signals.append(
                {
                    "category": category,
                    "label": group["label"],
                    "matched_text": match.group(0),
                    "explanation": group["explanation"],
                }
            )

            seen_categories.add(category)
            break

    return signals