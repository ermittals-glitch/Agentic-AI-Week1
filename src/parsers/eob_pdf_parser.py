"""PDF/JPEG text extraction for EOB documents."""

from __future__ import annotations

from io import BytesIO

from src.parsers.extraction_rules import extract_eob_fields


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    text_chunks: list[str] = []
    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text_chunks.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(text_chunks).strip()


def _extract_text_from_image(file_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(BytesIO(file_bytes))
        return pytesseract.image_to_string(image) or ""
    except Exception:
        return ""


def parse_eob_document(file_name: str, file_bytes: bytes) -> dict:
    lower = file_name.lower()
    text = ""

    if lower.endswith(".pdf"):
        text = _extract_text_from_pdf(file_bytes)
    elif lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png"):
        text = _extract_text_from_image(file_bytes)

    parsed = extract_eob_fields(raw_text=text, filename=file_name)
    parsed["parse_status"] = "Parsed" if text else "Text extraction not available"
    return parsed
