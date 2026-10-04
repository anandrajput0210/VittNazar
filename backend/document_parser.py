import re


def parse_document_sections(document):
    """
    Convert extracted PDF text into structured sections.

    Expected PDF format:

    [PAGE 1]
    1. Return
    Some text...

    2. Charges
    Some text...

    Returns a list like:

    [
        {
            "page": 1,
            "title": "Return",
            "text": "Some text..."
        }
    ]
    """

    page_pattern = re.compile(
        r"\[PAGE\s+(\d+)\]\s*\n(.*?)(?=\n\[PAGE\s+\d+\]|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    section_pattern = re.compile(
        r"(?m)^\s*(\d+)\.\s+([^\n]+?)\s*$"
    )

    sections = []

    for page_number, page_text in page_pattern.findall(document):

        matches = list(
            section_pattern.finditer(page_text)
        )

        # If the page has no numbered sections,
        # keep the entire page as one section.
        if not matches:
            cleaned = page_text.strip()

            if cleaned:
                sections.append(
                    {
                        "page": int(page_number),
                        "title": f"Page {page_number}",
                        "text": cleaned,
                    }
                )

            continue

        for index, match in enumerate(matches):

            section_number = match.group(1)
            section_title = match.group(2).strip()

            start = match.end()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(page_text)

            section_text = page_text[start:end].strip()

            sections.append(
                {
                    "page": int(page_number),
                    "number": int(section_number),
                    "title": section_title,
                    "text": section_text,
                }
            )

    return sections