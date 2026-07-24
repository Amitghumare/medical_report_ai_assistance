"""
Step 2: Extract Report Text
Handles text extraction from uploaded medical reports.
Supports: JPG/PNG (OCR via pytesseract) and PDF (native text via pdfplumber,
falling back to OCR for scanned/image-based PDFs).
"""

import io
from PIL import Image

import pytesseract
import pdfplumber
from pdf2image import convert_from_bytes

# Fast, general-purpose OCR config: OEM 3 (default LSTM engine), PSM 6
# (assume a uniform block of text) — noticeably faster than the default
# auto page-segmentation mode on typical medical report scans.
OCR_CONFIG = "--oem 3 --psm 6"

# Phone camera / high-res scans can be 3000px+ wide, which slows Tesseract
# down a lot for no accuracy benefit. Cap the longest side.
MAX_IMAGE_DIMENSION = 2000

# Lower DPI = faster page rendering for the scanned-PDF OCR fallback,
# with minimal accuracy loss for typical lab report text.
PDF_OCR_DPI = 150


def _downscale_if_needed(image: Image.Image) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= MAX_IMAGE_DIMENSION:
        return image
    scale = MAX_IMAGE_DIMENSION / longest
    new_size = (int(width * scale), int(height * scale))
    return image.resize(new_size, Image.LANCZOS)


def extract_text_from_image(file_bytes: bytes) -> str:
    """Run OCR on an image file (jpg/png) and return extracted text."""
    image = Image.open(io.BytesIO(file_bytes))
    image = _downscale_if_needed(image)
    text = pytesseract.image_to_string(image, config=OCR_CONFIG)
    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF. First tries native text extraction
    (fast, accurate for digital PDFs). If little/no text is found,
    falls back to rendering pages as images and running OCR
    (for scanned reports).
    """
    text_parts = []

    # Attempt 1: native text extraction
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except Exception:
        text_parts = []

    combined = "\n".join(text_parts).strip()

    # If native extraction produced very little text, the PDF is likely
    # scanned/image-based -> fall back to OCR.
    if len(combined) < 30:
        try:
            pages = convert_from_bytes(file_bytes, dpi=PDF_OCR_DPI)
            ocr_parts = [
                pytesseract.image_to_string(_downscale_if_needed(page), config=OCR_CONFIG)
                for page in pages
            ]
            ocr_combined = "\n".join(ocr_parts).strip()
            if len(ocr_combined) > len(combined):
                return ocr_combined
        except Exception as e:
            if not combined:
                raise RuntimeError(
                    f"Could not extract text from PDF (native or OCR failed): {e}"
                )

    return combined


def _extract_by_type(file_bytes: bytes, filename: str) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def extract_text(uploaded_file) -> str:
    """
    Main entry point. Takes a Streamlit UploadedFile and routes it
    to the correct extraction method based on file type. Cached by
    file content so re-processing the same upload is instant.
    """
    file_bytes = uploaded_file.getvalue()
    return _extract_cached(file_bytes, uploaded_file.name)


try:
    import streamlit as st

    _extract_cached = st.cache_data(show_spinner=False)(_extract_by_type)
except ImportError:  # allows running extractor logic outside streamlit (tests)
    _extract_cached = _extract_by_type
