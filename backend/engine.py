import re


CLAIM_PATTERNS = [
    {
        "category": "guaranteed_return",
        "patterns": [
            r"guaranteed\s+\d+(?:\.\d+)?\s*%",
            r"guaranteed\s+(?:returns?|income)",
            r"assured\s+\d+(?:\.\d+)?\s*%",
            r"fixed\s+\d+(?:\.\d+)?\s*%\s*(?:return|returns|income)",
        ],
    },
    {
        "category": "no_charges",
        "patterns": [
            r"no\s+charges?",
            r"zero\s+charges?",
            r"no\s+fees?",
            r"zero\s+fees?",
        ],
    },
    {
    "category": "easy_withdrawal",
    "patterns": [
        r"withdraw\s+anytime",
        r"withdraw\s+at\s+any\s+time",
        r"withdrawal\s+anytime",
        r"withdrawal\s+at\s+any\s+time",
        r"flexible\s+withdrawal",
        r"easy\s+withdrawal",
        r"withdraw\s+flexibly",
        r"easy\s+to\s+withdraw",
    ],
},
    {
        "category": "low_risk",
        "patterns": [
            r"no\s+risk",
            r"zero\s+risk",
            r"risk[-\s]?free",
            r"completely\s+safe",
            r"very\s+safe",
        ],
    },
    
]


def normalize_text(text):
    """Convert repeated whitespace into a consistent format."""
    return re.sub(r"\s+", " ", text.strip())


def extract_claims(text):
    """
    Extract unique financial claims from a sales pitch.

    Claims are returned in the same order in which they
    appear in the sales pitch.

    Each claim contains:
    - category
    - matched_text
    """

    text = normalize_text(text)

    claims = []
    seen_claims = set()

    for group in CLAIM_PATTERNS:
        category = group["category"]

        for pattern in group["patterns"]:
            matches = re.finditer(
                pattern,
                text,
                re.IGNORECASE
            )

            for match in matches:
                start = match.start()
                end = match.end()

                left_boundary = max(
                    text.rfind(".", 0, start),
                    text.rfind(",", 0, start),
                    text.rfind(";", 0, start),
                    text.rfind(" and ", 0, start),
                    text.rfind(" with ", 0, start),
                ) + 1

                right_boundaries = [
                    position
                    for position in [
                        text.find(".", end),
                        text.find(",", end),
                        text.find(";", end),
                        text.find(" and ", end),
                        text.find(" with ", end),
                    ]
                    if position != -1
                ]

                right_boundary = (
                    min(right_boundaries)
                    if right_boundaries
                    else len(text)
                )

                claim_text = text[
                    left_boundary:right_boundary
                ].strip()

                if not claim_text:
                    claim_text = match.group(0).strip()

                claim_text = re.sub(
                    r"^(and|with)\s+",
                    "",
                    claim_text,
                    flags=re.IGNORECASE
                )

                claim_text = re.sub(
                    r"\s+(and|with)$",
                    "",
                    claim_text,
                    flags=re.IGNORECASE
                ).strip()

                claim_key = (
                    category,
                    claim_text.lower()
                )

                if claim_key not in seen_claims:
                    claims.append(
                        {
                            "category": category,
                            "matched_text": claim_text,
                            "_position": start,
                        }
                    )

                    seen_claims.add(claim_key)

    # Restore the order in which claims appeared in the pitch.
    claims.sort(
        key=lambda claim: claim["_position"]
    )

    # Remove the internal position field before returning.
    for claim in claims:
        del claim["_position"]

    return claims

def extract_claim_details(matched_text, category):
    """
    Extract structured details from an individual financial claim.
    """

    details = {
        "percentage": None,
        "duration_value": None,
        "duration_unit": None,
        "guaranteed": None,
        "charges_free": None,
        "withdrawal_anytime": None,
        "risk_free": None,
    }

    # Extract percentage
    percentage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*%",
        matched_text
    )

    if percentage_match:
        details["percentage"] = float(
            percentage_match.group(1)
        )

    # Extract duration
    duration_match = re.search(
        r"(\d+(?:\.\d+)?)\s*"
        r"(years?|months?|days?)",
        matched_text,
        re.IGNORECASE
    )

    if duration_match:
        details["duration_value"] = float(
            duration_match.group(1)
        )

        details["duration_unit"] = (
            duration_match.group(2).lower()
        )

    if category == "guaranteed_return":
        details["guaranteed"] = True

    elif category == "no_charges":
        details["charges_free"] = True

    elif category == "easy_withdrawal":
        details["withdrawal_anytime"] = True

    elif category == "low_risk":
        details["risk_free"] = True

    return details