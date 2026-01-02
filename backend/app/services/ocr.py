"""
OCR service for extracting text from scanned PDFs.
Uses pytesseract with pdf2image for high-quality OCR.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import OCR libraries
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OCR libraries not available: {e}")
    OCR_AVAILABLE = False


def is_ocr_available() -> bool:
    """Check if OCR is available."""
    return OCR_AVAILABLE


def ocr_pdf_bytes(pdf_bytes: bytes, dpi: int = 200) -> list[tuple[int, str]]:
    """
    Extract text from a scanned PDF using OCR.
    
    Args:
        pdf_bytes: Raw PDF file content
        dpi: Resolution for PDF to image conversion (higher = better quality but slower)
        
    Returns:
        List of (page_number, text) tuples (1-indexed)
    """
    if not OCR_AVAILABLE:
        logger.error("OCR not available - pytesseract or pdf2image not installed")
        return []
    
    pages = []
    
    try:
        logger.info(f"Starting OCR on PDF ({len(pdf_bytes)} bytes) at {dpi} DPI...")
        
        # Convert PDF to images
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        total_pages = len(images)
        logger.info(f"Converted PDF to {total_pages} images")
        
        for page_num, image in enumerate(images, start=1):
            try:
                # Run OCR on this page
                text = pytesseract.image_to_string(image, lang='eng')
                text = text.strip()
                
                if text:
                    pages.append((page_num, text))
                    logger.debug(f"Page {page_num}/{total_pages}: {len(text)} chars")
                else:
                    logger.debug(f"Page {page_num}/{total_pages}: No text extracted")
                    
            except Exception as e:
                logger.error(f"OCR failed for page {page_num}: {e}")
                continue
        
        total_chars = sum(len(text) for _, text in pages)
        logger.info(f"OCR complete: {len(pages)} pages with text, {total_chars} total chars")
        
        return pages
        
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return []


def ocr_image(image: "Image.Image") -> str:
    """
    Extract text from a single image using OCR.
    
    Args:
        image: PIL Image object
        
    Returns:
        Extracted text
    """
    if not OCR_AVAILABLE:
        return ""
    
    try:
        return pytesseract.image_to_string(image, lang='eng').strip()
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return ""


def check_tesseract_installation() -> dict:
    """
    Check if Tesseract is properly installed.
    
    Returns:
        Dict with installation status and version info
    """
    result = {
        "installed": False,
        "version": None,
        "languages": [],
        "error": None,
    }
    
    if not OCR_AVAILABLE:
        result["error"] = "pytesseract or pdf2image not installed"
        return result
    
    try:
        version = pytesseract.get_tesseract_version()
        result["installed"] = True
        result["version"] = str(version)
        
        # Get available languages
        try:
            langs = pytesseract.get_languages()
            result["languages"] = langs
        except Exception:
            result["languages"] = ["eng"]  # Assume English is available
            
    except Exception as e:
        result["error"] = str(e)
    
    return result
