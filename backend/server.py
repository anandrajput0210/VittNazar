import re
import hashlib
import json
import mimetypes
import tempfile
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from engine import extract_claims
from pressure import detect_pressure_signals
from pdf_reader import extract_pdf_text
from receipt import (
    create_promise_receipt,
    save_promise_receipt,
    load_promise_receipt,
)
from verifier import verify_claims
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
PORT = 8000

def calculate_document_fingerprint(file_bytes):
    """
    Calculate a SHA-256 fingerprint for the exact uploaded document.
    """

    return hashlib.sha256(
        file_bytes
    ).hexdigest()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def parse_multipart_form(body, content_type):
    """
    Parse multipart/form-data using Python's standard library.
    """
    headers = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n"
        "\r\n"
    ).encode("utf-8")

    message = BytesParser(
        policy=policy.default
    ).parsebytes(headers + body)

    form = {}

    for part in message.iter_parts():
        field_name = part.get_param(
            "name",
            header="content-disposition"
        )

        if not field_name:
            continue

        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""

        if filename:
            form[field_name] = {
                "filename": filename,
                "content": payload
            }
        else:
            charset = (
                part.get_content_charset()
                or "utf-8"
            )

            form[field_name] = payload.decode(
                charset,
                errors="replace"
            )

    return form

def generate_receipt_pdf(receipt):
    """
    Generate a simple standalone Promise Receipt PDF
    using only Python's standard library.
    """

    def clean_text(value):
        value = str(value)
        value = value.replace("\r", " ")
        value = value.replace("\n", " ")
        return value.encode(
            "latin-1",
            errors="replace"
        ).decode("latin-1")

    def escape_pdf_text(value):
        return (
            clean_text(value)
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

    def wrap_text(text, width=92):
        words = clean_text(text).split()
        lines = []
        current = ""

        for word in words:
            candidate = (
                word
                if not current
                else current + " " + word
            )

            if len(candidate) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines or [""]

    lines = []

    lines.append("VittNazar")
    lines.append("Promise-to-Term Verification")
    lines.append("")
    lines.append(
    f"Receipt ID: {receipt.get('receipt_id', '')}"
)
    lines.append(
    f"Created: {receipt.get('created_at', '')}"
)

    document_info = receipt.get(
    "document",
    {}
)

    if (
        document_info.get("filename")
        and document_info.get("fingerprint")
):
        lines.append("")
    lines.append("VERIFIED DOCUMENT")
    lines.append(
        f"Filename: {document_info.get('filename')}"
    )
    lines.append(
        f"SHA-256: {document_info.get('fingerprint')}"
    )

    lines.append("")
    summary = receipt.get("summary", {})

    lines.append(
        f"Total claims: {summary.get('total_claims', 0)}"
    )
    lines.append(
        f"Supported: {summary.get('supported', 0)}"
    )
    lines.append(
        f"Partially supported: "
        f"{summary.get('partially_supported', 0)}"
    )
    lines.append(
        f"Conflicts with document: "
        f"{summary.get('contradicted', 0)}"
    )
    lines.append(
        f"Needs verification: "
        f"{summary.get('not_found', 0)}"
    )
    lines.append("")

    pressure_signals = receipt.get(
        "pressure_signals",
        []
    )

    if pressure_signals:
        lines.append("PRESSURE SIGNALS")
        lines.append(
            "These are persuasion patterns detected in the "
            "sales message. They are not proof of wrongdoing."
        )
        lines.append("")

        for signal in pressure_signals:
            lines.append(
                f"- {signal.get('label', '')}: "
                f"\"{signal.get('matched_text', '')}\""
            )

            lines.extend(
                wrap_text(
                    signal.get("explanation", ""),
                    88
                )
            )

            lines.append("")

    lines.append("PROMISE RECEIPT")
    lines.append("")

    items = receipt.get("items", [])

    for index, item in enumerate(items, start=1):
        lines.append(
            f"{index}. {item.get('claim', '')}"
        )
        status_labels = {
    "supported": "Supported by document",
    "contradicted": "Conflicts with document",
    "partially_supported": "Partially supported",
    "not_found": "Needs verification",
}

        status = status_labels.get(
    item.get("status", ""),
    item.get("status", "")
)

        lines.append(
    f"Status: {status}"
)

        lines.extend(
            wrap_text(
                item.get("reason", ""),
                88
            )
        )

        evidence_page = item.get(
            "evidence_page"
        )

        if evidence_page:
            lines.append(
                f"Document evidence - Page "
                f"{evidence_page}:"
            )
        else:
            lines.append(
                "Document evidence:"
            )

        lines.extend(
            wrap_text(
                item.get("evidence", ""),
                88
            )
        )

        lines.append("Clarification question:")

        lines.extend(
            wrap_text(
                item.get(
                    "clarification_question",
                    ""
                ),
                88
            )
        )

        lines.append("")

    lines.append(
        "VittNazar does not determine whether a seller is "
        "fraudulent or whether an investment is suitable."
    )

    lines.extend(
        wrap_text(
            "It compares supplied claims with supplied "
            "documentation and highlights information that "
            "requires independent verification.",
            88
        )
    )

    # PDF layout.
    page_width = 595
    page_height = 842
    left_margin = 48
    top_margin = 800
    bottom_margin = 48

    font_size = 9
    leading = 13

    # Split content across PDF pages.
    pages = []
    current_page = []
    y = top_margin

    for line in lines:
        extra_space = leading

        if line == "":
            extra_space = leading

        if y - extra_space < bottom_margin:
            pages.append(current_page)
            current_page = []
            y = top_margin

        current_page.append(
            (
                line,
                y
            )
        )

        y -= extra_space

    if current_page:
        pages.append(current_page)

    def make_page_content(page_lines):
        commands = [
            "BT",
            "/F1 9 Tf",
        ]

        first_line = True

        for text, y_position in page_lines:
            escaped = escape_pdf_text(text)

            if first_line:
                commands.append(
                    f"1 0 0 1 {left_margin} "
                    f"{y_position} Tm"
                )
                first_line = False
            else:
                commands.append(
                    f"1 0 0 1 {left_margin} "
                    f"{y_position} Tm"
                )

            commands.append(
                f"({escaped}) Tj"
            )

        commands.append("ET")

        return "\n".join(commands).encode(
            "latin-1",
            errors="replace"
        )

    page_contents = [
        make_page_content(page)
        for page in pages
    ]

    objects = []

    # Object 1: Catalog.
    objects.append(
        b"<< /Type /Catalog /Pages 2 0 R >>"
    )

    # Object 2: Pages placeholder.
    page_object_numbers = []

    # Object 3: Font.
    objects.append(
        b"<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica >>"
    )

    for content in page_contents:
        page_object_number = len(objects) + 1
        stream_object_number = page_object_number + 1

        page_object_numbers.append(
            page_object_number
        )

        page_dict = (
            f"<< /Type /Page "
            f"/Parent 2 0 R "
            f"/MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {stream_object_number} 0 R >>"
        ).encode("latin-1")

        stream_dict = (
            f"<< /Length {len(content)} >>\n"
        ).encode("latin-1") + (
            b"stream\n"
            + content
            + b"\nendstream"
        )

        objects.append(page_dict)
        objects.append(stream_dict)

    kids = " ".join(
        f"{number} 0 R"
        for number in page_object_numbers
    )

    objects[1] = (
        f"<< /Type /Pages "
        f"/Count {len(page_object_numbers)} "
        f"/Kids [{kids}] >>"
    ).encode("latin-1")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    pdf.extend(b"%\xe2\xe3\xcf\xd3\n")

    offsets = [0]

    for object_number, obj in enumerate(
        objects,
        start=1
    ):
        offsets.append(len(pdf))

        pdf.extend(
            f"{object_number} 0 obj\n".encode(
                "latin-1"
            )
        )

        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)

    pdf.extend(
        f"xref\n0 {len(objects) + 1}\n".encode(
            "latin-1"
        )
    )

    pdf.extend(
        b"0000000000 65535 f \n"
    )

    for offset in offsets[1:]:
        pdf.extend(
            f"{offset:010d} 00000 n \n".encode(
                "latin-1"
            )
        )

    pdf.extend(
        (
            f"trailer\n"
            f"<< /Size {len(objects) + 1} "
            f"/Root 1 0 R >>\n"
            f"startxref\n"
            f"{xref_offset}\n"
            f"%%EOF"
        ).encode("latin-1")
    )

    return bytes(pdf)

class VittNazarHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):
        response = json.dumps(
            data,
            indent=2
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()

        self.wfile.write(response)

    def serve_file(self, file_path):
        try:
            file_path = file_path.resolve()
            frontend_root = FRONTEND_DIR.resolve()

            if frontend_root not in file_path.parents:
                self.send_json(
                    403,
                    {"error": "Forbidden"}
                )
                return

            if not file_path.exists() or not file_path.is_file():
                self.send_json(
                    404,
                    {"error": "File not found"}
                )
                return

            content = file_path.read_bytes()

            content_type = (
                mimetypes.guess_type(
                    file_path.name
                )[0]
                or "application/octet-stream"
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                content_type
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            self.end_headers()

            self.wfile.write(content)

        except Exception as error:
            self.send_json(
                500,
                {
                    "error": str(error)
                }
            )

    def do_GET(self):
        if self.path == "/":
            self.serve_file(
                FRONTEND_DIR / "index.html"
            )
            return

        if self.path == "/style.css":
            self.serve_file(
                FRONTEND_DIR / "style.css"
            )
            return

        if self.path == "/app.js":
            self.serve_file(
                FRONTEND_DIR / "app.js"
            )
            return

                # --------------------------------------------------
        # PROMISE RECEIPT RETRIEVAL
        # --------------------------------------------------

        parsed_url = urlparse(self.path)

        if parsed_url.path == "/api/receipt":
            query = parse_qs(parsed_url.query)

            receipt_id = query.get(
                "id",
                [""]
            )[0].strip()

            if not receipt_id:
                self.send_json(
                    400,
                    {
                        "error": "Receipt ID is required."
                    }
                )
                return

            # Receipt IDs are generated by VittNazar in the form:
            # VN-YYYYMMDD-HHMMSS
            if not re.fullmatch(
    r"VN-\d{8}-\d{6}-[A-F0-9]{6}",
    receipt_id
):
                self.send_json(
                    400,
                    {
                        "error": "Invalid receipt ID."
                    }
                )
                return

            receipt = load_promise_receipt(
                receipt_id
            )

            if receipt is None:
                self.send_json(
                    404,
                    {
                        "error": "Receipt not found."
                    }
                )
                return

            self.send_json(
                200,
                {
                    "status": "success",
                    "receipt": receipt
                }
            )

            return
        
        if self.path == "/api/health":
            self.send_json(
                200,
                {
                    "status": "ok",
                    "service": "VittNazar"
                }
            )
            return

        self.send_json(
            404,
            {
                "error": "Not Found"
            }
        )

            
    def do_POST(self):
                # --------------------------------------------------
        # PROMISE RECEIPT PDF DOWNLOAD
        # --------------------------------------------------

        if self.path == "/api/download-receipt":
            try:
                content_length = int(
                    self.headers.get(
                        "Content-Length",
                        "0"
                    )
                )

                body = self.rfile.read(
                    content_length
                )

                data = json.loads(
                    body.decode("utf-8")
                )

                receipt = data.get("receipt")

                if not isinstance(receipt, dict):
                    self.send_json(
                        400,
                        {
                            "error": "Receipt data is required."
                        }
                    )
                    return

                pdf_bytes = generate_receipt_pdf(
                    receipt
                )

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "application/pdf"
                )

                self.send_header(
                    "Content-Disposition",
                    (
                        "attachment; "
                        "filename="
                        f"VittNazar-"
                        f"{receipt.get('receipt_id', 'receipt')}.pdf"
                    )
                )

                self.send_header(
                    "Content-Length",
                    str(len(pdf_bytes))
                )

                self.end_headers()

                self.wfile.write(pdf_bytes)

            except json.JSONDecodeError:
                self.send_json(
                    400,
                    {
                        "error": "Invalid JSON."
                    }
                )

            except Exception as error:
                self.send_json(
                    500,
                    {
                        "error": str(error)
                    }
                )

            return
        # --------------------------------------------------
        # PDF DOCUMENT EXTRACTION
        # --------------------------------------------------

        if self.path == "/api/extract-document":
            try:
                content_type = self.headers.get(
                    "Content-Type",
                    ""
                )

                if not content_type.startswith(
                    "multipart/form-data"
                ):
                    self.send_json(
                        400,
                        {
                            "error": (
                                "Multipart form data is required."
                            )
                        }
                    )
                    return

                content_length = int(
                    self.headers.get(
                        "Content-Length",
                        "0"
                    )
                )

                body = self.rfile.read(
                    content_length
                )

                form = parse_multipart_form(
                    body,
                    content_type
                )

                uploaded_file = form.get("file")

                if not uploaded_file:
                    self.send_json(
                        400,
                        {
                            "error": "PDF file is required."
                        }
                    )
                    return

                filename = uploaded_file["filename"]

                if not filename.lower().endswith(".pdf"):
                    self.send_json(
                        400,
                        {
                            "error": (
                                "Only PDF files are supported."
                            )
                        }
                    )
                    return

                pdf_bytes = uploaded_file["content"]

                max_pdf_size = 10 * 1024 * 1024

                if len(pdf_bytes) > max_pdf_size:
                    self.send_json(
                        413,
                        {
                            "error": (
                                "PDF file is too large. "
                                "Maximum allowed size is 10 MB."
                            )
                        }
                    )
                    return

                if not pdf_bytes:
                    self.send_json(
                        400,
                        {
                            "error": "Uploaded PDF is empty."
                        }
                    )
                    return

                if not pdf_bytes.startswith(b"%PDF-"):
                    self.send_json(
                        400,
                        {
                            "error": (
                                "The uploaded file is not a valid PDF."
                            )
                        }
                    )
                    return

                temporary_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        suffix=".pdf",
                        delete=False
                    ) as temporary_file:
                        temporary_file.write(pdf_bytes)
                        temporary_path = temporary_file.name

                    extracted_text = extract_pdf_text(
                        temporary_path
                    )

                finally:
                    if temporary_path:
                        Path(
                            temporary_path
                        ).unlink(
                            missing_ok=True
                        )

                if not extracted_text:
                    self.send_json(
                        422,
                        {
                            "error": (
                                "No extractable text was found "
                                "in the PDF."
                            )
                        }
                    )
                    return

                document_fingerprint = calculate_document_fingerprint(
    pdf_bytes
)

                self.send_json(
    200,
    {
        "status": "success",
        "filename": filename,
        "characters": len(extracted_text),
        "text": extracted_text,
        "document_fingerprint": document_fingerprint
    }
)
            except ValueError as error:
                self.send_json(
                    400,
                    {
                        "error": str(error)
                    }
                )

            except Exception as error:
                self.send_json(
                    500,
                    {
                        "error": str(error)
                    }
                )

            return

        # --------------------------------------------------
        # MAIN ANALYSIS
        # --------------------------------------------------

        if self.path != "/api/analyze":
            self.send_json(
                404,
                {
                    "error": "Not Found"
                }
            )
            return

        try:
            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            body = self.rfile.read(
                content_length
            )

            data = json.loads(
                body.decode("utf-8")
            )

            pitch = data.get(
                "pitch",
                ""
            )

            official_document = data.get(
                "official_document",
                ""
            )

            if (
                not isinstance(pitch, str)
                or not pitch.strip()
            ):
                self.send_json(
                    400,
                    {
                        "error": (
                            "Sales pitch is required."
                        )
                    }
                )
                return

            if (
                not isinstance(
                    official_document,
                    str
                )
                or not official_document.strip()
            ):
                self.send_json(
                    400,
                    {
                        "error": (
                            "Official document text "
                            "is required."
                        )
                    }
                )
                return

            claims = extract_claims(
                pitch
            )

            results = verify_claims(
                claims,
                official_document
            )

            pressure_signals = (
                detect_pressure_signals(
                    pitch
                )
            )

            receipt = create_promise_receipt(
    results,
    pressure_signals,
    {
        "filename": data.get(
            "document_filename"
        ),
        "fingerprint": data.get(
            "document_fingerprint"
        ),
    }
)

            save_promise_receipt(
    receipt
)

            self.send_json(
    200,
    {
        "status": "success",
        "receipt": receipt
    }
)

        except json.JSONDecodeError:
            self.send_json(
                400,
                {
                    "error": "Invalid JSON."
                }
            )

        except Exception as error:
            self.send_json(
                500,
                {
                    "error": str(error)
                }
            )


def run_server():
    server = HTTPServer(
        (HOST, PORT),
        VittNazarHandler
    )

    print(
        f"VittNazar running at "
        f"http://{HOST}:{PORT}"
    )

    print(
        f"Frontend directory: "
        f"{FRONTEND_DIR}"
    )

    print(
        "API endpoint: POST /api/analyze"
    )

    print(
        "PDF endpoint: POST /api/extract-document"
    )

    print(
    "Receipt PDF endpoint: POST /api/download-receipt"
)

    print(
        "Press Ctrl+C to stop."
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nStopping VittNazar..."
        )

    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()