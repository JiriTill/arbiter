"""
Google Cloud Vision OCR service for extracting text from scanned PDFs.

This is the production OCR solution that:
1. Uses Google Cloud Vision API (cloud-based, no memory limits)
2. Handles any PDF regardless of size
3. Provides excellent OCR accuracy
4. Supports multiple languages

Requires:
- GOOGLE_APPLICATION_CREDENTIALS_JSON env var with service account JSON
- Or GOOGLE_APPLICATION_CREDENTIALS file path
"""

import base64
import json
import logging
import os
import tempfile
from typing import Callable

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Try to import Google Cloud Vision
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    VISION_AVAILABLE = True
except ImportError:
    logger.warning("Google Cloud Vision not installed. Run: pip install google-cloud-vision")
    VISION_AVAILABLE = False


def is_cloud_vision_available() -> bool:
    """Check if Google Cloud Vision is available and configured."""
    if not VISION_AVAILABLE:
        return False
    
    # Check for credentials
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        return True
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    
    return False


def get_vision_client() -> "vision.ImageAnnotatorClient":
    """Create authenticated Vision API client."""
    if not VISION_AVAILABLE:
        raise ImportError("google-cloud-vision not installed")
    
    # Option 1: JSON credentials from environment variable
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return vision.ImageAnnotatorClient(credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
            raise
    
    # Option 2: File path (default Google Cloud SDK behavior)
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        return vision.ImageAnnotatorClient(credentials=credentials)
    
    # Option 3: Try default credentials (works in GCP environments)
    try:
        return vision.ImageAnnotatorClient()
    except Exception as e:
        logger.error(f"No Google Cloud credentials found: {e}")
        raise ValueError(
            "Google Cloud Vision credentials not configured. "
            "Set GOOGLE_APPLICATION_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS"
        )


def ocr_pdf_with_vision(
    pdf_bytes: bytes,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> list[tuple[int, str]]:
    """
    Extract text from a PDF using Google Cloud Vision API.
    
    This is the production OCR method - cloud-based, no memory limits,
    excellent accuracy.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        progress_callback: Optional callback(page, total_pages, total_chars)
        
    Returns:
        List of (page_number, text) tuples (1-indexed)
    """
    if not is_cloud_vision_available():
        raise ValueError("Google Cloud Vision not available")
    
    logger.info(f"Starting Google Cloud Vision OCR on PDF ({len(pdf_bytes):,} bytes)...")
    
    client = get_vision_client()
    pages = []
    
    try:
        # Open PDF and iterate pages
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            total_pages = len(doc)
            logger.info(f"PDF has {total_pages} pages")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_number = page_num + 1  # 1-indexed
                
                logger.debug(f"Processing page {page_number}/{total_pages}...")
                
                # Render page to image (150 DPI for good OCR quality)
                # This is memory-efficient because we process one page at a time
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                
                # Send to Google Cloud Vision
                image = vision.Image(content=img_bytes)
                response = client.document_text_detection(image=image)
                
                if response.error.message:
                    logger.error(f"Vision API error on page {page_number}: {response.error.message}")
                    continue
                
                # Extract text
                text = response.full_text_annotation.text if response.full_text_annotation else ""
                text = text.strip()
                
                if text:
                    pages.append((page_number, text))
                    logger.debug(f"Page {page_number}: {len(text)} chars")
                else:
                    logger.debug(f"Page {page_number}: No text extracted")
                
                # Progress callback
                if progress_callback:
                    total_chars = sum(len(t) for _, t in pages)
                    progress_callback(page_number, total_pages, total_chars)
                
                # Clean up pixmap memory
                del pix
                del img_bytes
        
        total_chars = sum(len(text) for _, text in pages)
        logger.info(f"Vision OCR complete: {len(pages)} pages, {total_chars:,} chars")
        
        return pages
        
    except Exception as e:
        logger.error(f"Google Cloud Vision OCR failed: {e}")
        raise


def ocr_image_with_vision(image_bytes: bytes) -> str:
    """
    Extract text from a single image using Google Cloud Vision.
    
    Args:
        image_bytes: Image as bytes (PNG, JPEG, etc.)
        
    Returns:
        Extracted text
    """
    if not is_cloud_vision_available():
        return ""
    
    try:
        client = get_vision_client()
        image = vision.Image(content=image_bytes)
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            logger.error(f"Vision API error: {response.error.message}")
            return ""
        
        return response.full_text_annotation.text if response.full_text_annotation else ""
        
    except Exception as e:
        logger.error(f"Vision OCR failed: {e}")
        return ""


def check_vision_status() -> dict:
    """
    Check Google Cloud Vision API status and configuration.
    
    Returns:
        Dict with status information
    """
    result = {
        "available": False,
        "library_installed": VISION_AVAILABLE,
        "credentials_configured": False,
        "credentials_source": None,
        "error": None,
    }
    
    if not VISION_AVAILABLE:
        result["error"] = "google-cloud-vision library not installed"
        return result
    
    # Check credentials
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        result["credentials_configured"] = True
        result["credentials_source"] = "GOOGLE_APPLICATION_CREDENTIALS_JSON"
    elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if os.path.exists(creds_path):
            result["credentials_configured"] = True
            result["credentials_source"] = f"GOOGLE_APPLICATION_CREDENTIALS (file: {creds_path})"
        else:
            result["error"] = f"Credentials file not found: {creds_path}"
            return result
    else:
        result["error"] = "No credentials configured"
        return result
    
    # Try to create client to verify credentials
    try:
        client = get_vision_client()
        result["available"] = True
    except Exception as e:
        result["error"] = str(e)
    
    return result
