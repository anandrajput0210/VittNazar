from pathlib import Path


def extract_pdf_text(file_path):
    """
    Extract text from a text-based PDF while preserving page numbers.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("PDF file was not found.")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError(
            "pypdf is not installed. Install it with: pip install pypdf"
        )

    reader = PdfReader(str(path))

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        text = page.extract_text() or ""

        pages.append(
            f"[PAGE {page_number}]\n{text.strip()}"
        )

    return "\n\n".join(pages).strip()