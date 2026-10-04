import re

try:
    from .document_parser import parse_document_sections
except ImportError:
    from document_parser import parse_document_sections

def normalize_text(text):
    """Normalize whitespace and lowercase text."""
    return re.sub(r"\s+", " ", text.strip().lower())


def find_evidence(document, category, claim_text=""):
    """
    Find the most relevant evidence by first selecting
    the document section associated with the claim.
    """

    section_map = {
        "guaranteed_return": [
            "Return",
            "Guarantee Conditions",
            "Important Information",
        ],
        "no_charges": [
            "Charges",
        ],
        "easy_withdrawal": [
            "Withdrawal",
        ],
        "low_risk": [
            "Risk",
        ],
    }

    evidence_terms = {
        "guaranteed_return": [
            "does not guarantee",
            "not guaranteed",
            "no guarantee",
            "guaranteed return",
            "guaranteed",
            "assured return",
        ],
        "no_charges": [
            "no charges",
            "zero charges",
            "charges",
            "fees",
            "expenses",
            "costs",
        ],
        "easy_withdrawal": [
            "lock-in",
            "exit load",
            "withdrawal penalty",
            "withdrawal restriction",
            "withdrawal",
            "withdraw",
            "redemption",
            "surrender",
        ],
        "low_risk": [
            "risk-free",
            "risk free",
            "no risk",
            "low risk",
            "market risk",
            "investment risk",
            "risk",
        ],
    }

    sections = parse_document_sections(document)

    preferred_titles = section_map.get(category, [])
    terms = evidence_terms.get(category, [])

    relevant_sections = [
        section
        for section in sections
        if section["title"].strip().lower()
        in {title.lower() for title in preferred_titles}
    ]

    # If no matching section exists, fall back to all sections.
    if not relevant_sections:
        relevant_sections = sections

    for section in relevant_sections:
        section_text = section["text"].strip()

        # Normalize wrapped PDF lines.
        section_text = re.sub(r"\s+", " ", section_text)

        sentences = [
            sentence.strip()
            for sentence in re.split(
                r"(?<=[.!?])\s+",
                section_text
            )
            if sentence.strip()
        ]

        if category == "guaranteed_return":
            priority_terms = [
                "does not guarantee",
                "not guaranteed",
                "no guarantee",
                "guaranteed return",
                "guaranteed",
                "assured return",
            ]
        elif category == "easy_withdrawal":
            priority_terms = [
                "lock-in",
                "exit load",
                "withdrawal penalty",
                "withdrawal restriction",
                "withdrawal",
                "redemption",
                "surrender",
            ]
        else:
            priority_terms = terms

        relevant = []

        for term in priority_terms:
            for sentence in sentences:
                if (
                    term.lower() in sentence.lower()
                    and sentence not in relevant
                ):
                    relevant.append(sentence)

        if relevant:
            # Guaranteed-return claims need enough context
            # to distinguish a general guarantee from a
            # specific percentage/condition.
            if category == "guaranteed_return":
                evidence = " ".join(relevant[:2])
            else:
                evidence = relevant[0]

            return (
                evidence,
                section["page"],
            )

    return (
        "No matching evidence sentence was found.",
        None,
    )
def verify_guaranteed_return(
    document,
    claim_text,
    evidence_text,
):
    """
    Verify guaranteed-return claims using only the
    relevant evidence.
    """

    evidence = normalize_text(evidence_text)

    # Extract percentages from the seller claim and official evidence.
    claim_percentage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*%",
        claim_text,
    )

    evidence_percentage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*%",
        evidence,
    )

    # Detect whether the official document contains
    # clear guarantee-related language.
    guarantee_match = re.search(
        r"(?:guaranteed|assured)\s+"
        r"(?:(?:\d+(?:\.\d+)?)\s*%\s+)?"
        r"(?:annual\s+|monthly\s+|yearly\s+)?"
        r"(?:return|returns|income)",
        evidence,
    )

    # Detect wording where the document specifically says
    # that a stated annual percentage is NOT guaranteed.
    specific_percentage_not_guaranteed = re.search(
        r"(?:does\s+not\s+guarantee|not\s+guaranteed|"
        r"does\s+not\s+assure|not\s+assured)"
        r"(?:\s+(?:a\s+)?)"
        r"(?:specific\s+)?annual\s+percentage",
        evidence,
    )

    # Detect a broad statement that the return itself is not guaranteed.
    broad_not_guaranteed = re.search(
        r"(?:return|returns|income)"
        r"\s+(?:is|are)\s+not\s+(?:guaranteed|assured)",
        evidence,
    )

    # No clear guarantee language in the relevant evidence.
    if not guarantee_match:
        if broad_not_guaranteed:
            return (
                "contradicted",
                "The relevant official document evidence states "
                "that the return is not guaranteed."
            )

        return (
            "not_found",
            "The relevant official document evidence does not "
            "contain clear guarantee-related language."
        )

    # Seller claimed a specific percentage.
    if claim_percentage_match:
        claim_percentage = float(
            claim_percentage_match.group(1)
        )

        # The official document gives a percentage.
        if evidence_percentage_match:
            evidence_percentage = float(
                evidence_percentage_match.group(1)
            )

            if claim_percentage == evidence_percentage:
                return (
                    "supported",
                    "The relevant official evidence contains "
                    "guarantee language and the stated percentage matches."
                )

            return (
                "contradicted",
                "The relevant official evidence contains a "
                "different percentage from the sales claim."
            )

        # The document supports a guarantee but explicitly
        # does not confirm the specific annual percentage.
        if specific_percentage_not_guaranteed:
            return (
                "partially_supported",
                "The relevant official evidence supports the existence "
                "of a guarantee, but it does not confirm the specific "
                "annual percentage stated in the sales claim."
            )

        # A guarantee exists, but its exact percentage is absent.
        return (
            "partially_supported",
            "The relevant official evidence supports the existence "
            "of a guarantee, but it does not confirm the specific "
            "percentage stated in the sales claim."
        )

    # No percentage was claimed by the seller.
    if broad_not_guaranteed:
        return (
            "contradicted",
            "The relevant official document evidence states "
            "that the return is not guaranteed."
        )

    return (
        "supported",
        "The relevant official evidence contains guarantee-related "
        "language. The exact conditions still need review."
    )


def verify_no_charges(
    document,
    claim_text,
    evidence_text,
):
    """
    Verify claims that say there are no charges or fees.
    """

    evidence = normalize_text(evidence_text)

    no_charge_patterns = [
        r"no\s+charges?",
        r"zero\s+charges?",
        r"no\s+fees?",
        r"zero\s+fees?",
        r"without\s+charges?",
        r"without\s+fees?",
    ]

    charge_patterns = [
        r"\bcharges?\b",
        r"\bfees?\b",
        r"\bexpenses?\b",
        r"\bcosts?\b",
    ]

    # Explicitly states there are no charges.
    if any(
        re.search(pattern, evidence)
        for pattern in no_charge_patterns
    ):
        return (
            "supported",
            "The relevant official evidence indicates that "
            "no charges or fees apply."
        )

    # Relevant evidence states that charges exist/apply.
    if any(
        re.search(pattern, evidence)
        for pattern in charge_patterns
    ):
        return (
            "contradicted",
            "The sales claim says there are no charges, but the "
            "relevant official evidence refers to charges, fees, "
            "expenses, or costs."
        )

    return (
        "not_found",
        "The relevant official document evidence does not provide "
        "enough information about charges or fees."
    )


def verify_easy_withdrawal(
    document,
    claim_text,
    evidence_text,
):
    """
    Verify claims about easy or immediate withdrawal.
    """

    evidence = normalize_text(evidence_text)

    restriction_patterns = [
        r"lock[-\s]?in",
        r"exit\s+load",
        r"withdrawal\s+penalty",
        r"withdrawal\s+restriction",
        r"surrender\s+charge",
    ]

    unrestricted_patterns = [
        r"withdraw\s+anytime",
        r"withdraw\s+at\s+any\s+time",
        r"redemption\s+is\s+available\s+anytime",
    ]

    conditional_patterns = [
        r"withdrawal.*subject\s+to",
        r"redemption.*subject\s+to",
        r"withdrawal.*conditions?",
        r"redemption.*conditions?",
    ]

    # Explicit restriction.
    if any(
        re.search(pattern, evidence)
        for pattern in restriction_patterns
    ):
        return (
            "contradicted",
            "The relevant official document evidence contains "
            "a withdrawal restriction or exit-related condition."
        )

    # Explicitly unrestricted.
    if any(
        re.search(pattern, evidence)
        for pattern in unrestricted_patterns
    ):
        return (
            "supported",
            "The relevant official evidence supports the "
            "withdrawal claim."
        )

    # Withdrawal is possible, but conditions are mentioned.
    if any(
        re.search(pattern, evidence)
        for pattern in conditional_patterns
    ):
        return (
            "partially_supported",
            "The relevant official evidence indicates that "
            "withdrawal is available subject to conditions."
        )

    if (
        "withdrawal" in evidence
        or "redemption" in evidence
        or "withdraw" in evidence
    ):
        return (
            "not_found",
            "The relevant official evidence discusses withdrawal "
            "or redemption but does not establish that it is "
            "available anytime."
        )

    return (
        "not_found",
        "The relevant official evidence does not provide enough "
        "information to verify the withdrawal claim."
    )


def verify_low_risk(
    document,
    claim_text,
    evidence_text,
):
    """
    Verify claims describing a product as risk-free or very safe.
    """

    evidence = normalize_text(evidence_text)
    claim = normalize_text(claim_text)

    strong_no_risk_claim = any(
        phrase in claim
        for phrase in [
            "no risk",
            "zero risk",
            "risk-free",
            "risk free",
            "completely safe",
        ]
    )

    # Check explicit negation FIRST.
    # This prevents phrases such as:
    # "should not be described as completely risk-free"
    # from being incorrectly treated as positive evidence.
    explicit_risk_warning = any(
        phrase in evidence
        for phrase in [
            "not risk-free",
            "not risk free",
            "not be described as risk-free",
            "not be described as risk free",
            "not be described as completely risk-free",
            "not be described as completely risk free",
            "should not be described as risk-free",
            "should not be described as risk free",
            "should not be described as completely risk-free",
            "should not be described as completely risk free",
            "does not describe as risk-free",
            "does not describe as risk free",
            "does not guarantee that there is no risk",
            "not guaranteed to be risk-free",
            "involves risks",
            "involve risks",
            "involves risk",
            "involve risk",
            "market risk",
            "investment risk",
            "risk factors",
            "risk of loss",
            "loss of capital",
        ]
    )

    if explicit_risk_warning:
        return (
            "contradicted",
            "The relevant official evidence contains a risk "
            "disclosure that conflicts with the risk-free or "
            "completely-safe claim."
        )

    # Only treat positive no-risk language as supporting evidence
    # when it is not part of an explicit negation.
    explicit_no_risk_in_document = any(
        phrase in evidence
        for phrase in [
            "risk-free",
            "risk free",
            "no risk",
            "zero risk",
        ]
    )

    if explicit_no_risk_in_document and strong_no_risk_claim:
        return (
            "supported",
            "The relevant official evidence contains "
            "corresponding low/no-risk language."
        )

    if (
        "low risk" in claim
        and "low risk" in evidence
    ):
        return (
            "supported",
            "The relevant official evidence contains "
            "corresponding low-risk language."
        )

    if "risk" in evidence:
        return (
            "not_found",
            "The relevant official evidence discusses risk, "
            "but does not provide enough evidence to confirm "
            "the exact claim."
        )

    return (
        "not_found",
        "The relevant official evidence does not provide enough "
        "information to verify the risk claim."
    )


def verify_claims(claims, official_document):
    """
    Evidence-first verification for all supported claim categories.
    """

    original_document = official_document.strip()

    results = []

    for claim in claims:
        category = claim["category"]
        matched_text = claim["matched_text"]

        # First find evidence specifically related to this claim.
        evidence, evidence_page = find_evidence(
            original_document,
            category,
            matched_text,
        )

        if category == "guaranteed_return":
            status, reason = verify_guaranteed_return(
                original_document,
                matched_text,
                evidence,
            )

        elif category == "no_charges":
            status, reason = verify_no_charges(
                original_document,
                matched_text,
                evidence,
            )

        elif category == "easy_withdrawal":
            status, reason = verify_easy_withdrawal(
                original_document,
                matched_text,
                evidence,
            )

        elif category == "low_risk":
            status, reason = verify_low_risk(
                original_document,
                matched_text,
                evidence,
            )

        else:
            status = "not_found"
            reason = (
                "No verification rule is available "
                "for this claim."
            )

        results.append(
            {
                "claim": matched_text,
                "category": category,
                "status": status,
                "reason": reason,
                "evidence": evidence,
                "evidence_page": evidence_page,
            }
        )

    return results