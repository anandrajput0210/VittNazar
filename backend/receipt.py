from datetime import datetime
import json
from pathlib import Path
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = PROJECT_ROOT / "data" / "receipts"

RECEIPTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


CLARIFICATION_QUESTIONS = {
    "guaranteed_return": (
        "Please show the exact section of the official document "
        "that supports the stated guaranteed return."
    ),
    "no_charges": (
        "Please provide the complete list of applicable charges, "
        "fees, and other costs."
    ),
    "easy_withdrawal": (
        "Please explain the withdrawal, lock-in, exit-load, "
        "and surrender conditions."
    ),
    "low_risk": (
        "Please explain the risks described in the official "
        "product documentation."
    ),
}


def create_promise_receipt(
    claim_results,
    pressure_signals=None,
    document_metadata=None,
):
    """
    Create a structured Promise Receipt.

    claim_results:
        Results from claim-to-document verification.

    pressure_signals:
        Separate persuasion/pressure signals detected
        in the sales pitch.
    """

    if pressure_signals is None:
        pressure_signals = []

    if document_metadata is None:
        document_metadata = {}

    receipt_items = []

    for result in claim_results:
        category = result["category"]

        receipt_items.append(
    {
        "claim": result["claim"],
        "status": result["status"],
        "reason": result["reason"],
        "evidence": result["evidence"],
        "evidence_page": result.get("evidence_page"),
        "clarification_question": CLARIFICATION_QUESTIONS.get(
            category,
            "Please provide official documentation supporting this claim."
        ),
    }
)

    summary = {
        "total_claims": len(claim_results),
        "supported": sum(
            1
            for item in claim_results
            if item["status"] == "supported"
        ),
        "contradicted": sum(
            1
            for item in claim_results
            if item["status"] == "contradicted"
        ),
        "not_found": sum(
            1
            for item in claim_results
            if item["status"] == "not_found"
        ),
        "partially_supported": sum(
            1
            for item in claim_results
            if item["status"] == "partially_supported"
),
        "pressure_signals": len(pressure_signals),
    }

    return {
    "receipt_id": (
    datetime.now().strftime(
        "VN-%Y%m%d-%H%M%S"
    )
    + "-"
    + uuid.uuid4().hex[:6].upper()
),
    "created_at": datetime.now().isoformat(
        timespec="seconds"
    ),
    "document": {
        "filename": document_metadata.get(
            "filename"
        ),
        "fingerprint": document_metadata.get(
            "fingerprint"
        ),
    },
    "summary": summary,
    "items": receipt_items,
    "pressure_signals": pressure_signals,
}

def save_promise_receipt(receipt):
    """
    Save a Promise Receipt as a JSON file using its receipt ID.
    """

    receipt_id = receipt["receipt_id"]

    receipt_path = (
        RECEIPTS_DIR
        / f"{receipt_id}.json"
    )

    receipt_path.write_text(
        json.dumps(
            receipt,
            indent=2
        ),
        encoding="utf-8"
    )

    return receipt_path


def load_promise_receipt(receipt_id):
    """
    Load a saved Promise Receipt by receipt ID.
    """

    receipt_path = (
        RECEIPTS_DIR
        / f"{receipt_id}.json"
    )

    if not receipt_path.exists():
        return None

    return json.loads(
        receipt_path.read_text(
            encoding="utf-8"
        )
    )
