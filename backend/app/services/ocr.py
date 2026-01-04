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


def ocr_pdf_bytes(pdf_bytes: bytes, dpi: int = 150, progress_callback=None) -> list[tuple[int, str]]:
    """
    Extract text from a scanned PDF using OCR.
    
    MEMORY-OPTIMIZED: Processes pages one at a time to avoid OOM on limited containers.
    
    Args:
        pdf_bytes: Raw PDF file content
        dpi: Resolution for PDF to image conversion (lower = less memory, 150 is good balance)
        progress_callback: Optional callback(page, total_pages, text_so_far) for progress updates
        
    Returns:
        List of (page_number, text) tuples (1-indexed)
    """
    if not OCR_AVAILABLE:
        logger.error("OCR not available - pytesseract or pdf2image not installed")
        return []
    
    pages = []
    
    try:
        import gc
        import fitz  # PyMuPDF for page counting
        
        logger.info(f"Starting OCR on PDF ({len(pdf_bytes)} bytes) at {dpi} DPI...")
        
        # First, get total page count using PyMuPDF (low memory)
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            total_pages = len(doc)
        
        logger.info(f"PDF has {total_pages} pages - processing one at a time...")
        
        # Process each page individually to minimize memory usage
        for page_num in range(1, total_pages + 1):
            try:
                logger.info(f"OCR page {page_num}/{total_pages}...")
                
                # Convert only THIS page to image
                page_images = convert_from_bytes(
                    pdf_bytes, 
                    dpi=dpi,
                    first_page=page_num,
                    last_page=page_num,
                    grayscale=True,  # Reduce memory by ~66%
                    thread_count=1,  # Reduce memory spikes
                )
                
                if not page_images:
                    logger.warning(f"No image generated for page {page_num}")
                    continue
                
                image = page_images[0]
                
                # Run OCR on this single page
                text = pytesseract.image_to_string(image, lang='eng')
                text = text.strip()
                
                if text:
                    pages.append((page_num, text))
                    logger.debug(f"Page {page_num}/{total_pages}: {len(text)} chars")
                else:
                    logger.debug(f"Page {page_num}/{total_pages}: No text extracted")
                
                # CRITICAL: Free memory immediately
                del image
                del page_images
                gc.collect()
                
                # Progress callback
                if progress_callback:
                    progress_callback(page_num, total_pages, sum(len(t) for _, t in pages))
                    
            except Exception as e:
                logger.error(f"OCR failed for page {page_num}: {e}")
                gc.collect()  # Still try to free memory
                continue
        
        total_chars = sum(len(text) for _, text in pages)
        logger.info(f"OCR complete: {len(pages)} pages with text, {total_chars} total chars")
        
        return pages
        
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
