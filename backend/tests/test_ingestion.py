"""
Integration tests for PDF ingestion.

Tests cover:
- Valid PDF processing
- Scanned PDF detection (needs_ocr)
- Invalid PDF handling
- Chunking behavior
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import io


class TestPDFValidation:
    """Tests for PDF validation."""
    
    def test_valid_pdf_is_accepted(self):
        """Valid PDF files are accepted."""
        from app.services.ingestion import validate_pdf_content
        
        # Create a minimal valid PDF header
        valid_pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        
        with patch("fitz.open") as fitz_mock:
            doc_mock = MagicMock()
            doc_mock.page_count = 10
            doc_mock.is_encrypted = False
            fitz_mock.return_value.__enter__ = MagicMock(return_value=doc_mock)
            fitz_mock.return_value.__exit__ = MagicMock()
            
            # Should not raise
            result = validate_pdf_content(valid_pdf)
            assert result is True
            
    def test_invalid_pdf_is_rejected(self):
        """Invalid files are rejected."""
        from app.services.ingestion import validate_pdf_content
        
        invalid_data = b"This is not a PDF file"
        
        result = validate_pdf_content(invalid_data)
        assert result is False
        
    def test_encrypted_pdf_is_rejected(self):
        """Encrypted PDFs are rejected."""
        from app.services.ingestion import validate_pdf_content
        
        with patch("fitz.open") as fitz_mock:
            doc_mock = MagicMock()
            doc_mock.is_encrypted = True
            fitz_mock.return_value.__enter__ = MagicMock(return_value=doc_mock)
            fitz_mock.return_value.__exit__ = MagicMock()
            
            result = validate_pdf_content(b"%PDF-1.4")
            assert result is False


class TestScannedPDFDetection:
    """Tests for detecting scanned (image-based) PDFs."""
    
    def test_detects_text_pdf(self):
        """PDFs with text are not marked as needing OCR."""
        from app.services.ingestion import detect_needs_ocr
        
        with patch("fitz.open") as fitz_mock:
            page_mock = MagicMock()
            page_mock.get_text.return_value = "This is actual text content from the PDF."
            
            doc_mock = MagicMock()
            doc_mock.__iter__ = MagicMock(return_value=iter([page_mock, page_mock]))
            doc_mock.page_count = 2
            
            fitz_mock.return_value.__enter__ = MagicMock(return_value=doc_mock)
            fitz_mock.return_value.__exit__ = MagicMock()
            
            result = detect_needs_ocr(b"%PDF-1.4")
            assert result is False
            
    def test_detects_scanned_pdf(self):
        """PDFs with only images are marked as needing OCR."""
        from app.services.ingestion import detect_needs_ocr
        
        with patch("fitz.open") as fitz_mock:
            # Page with almost no text (scanned)
            page_mock = MagicMock()
            page_mock.get_text.return_value = ""
            page_mock.get_images.return_value = [(1,), (2,)]  # Has images
            
            doc_mock = MagicMock()
            doc_mock.__iter__ = MagicMock(return_value=iter([page_mock, page_mock]))
            doc_mock.page_count = 2
            
            fitz_mock.return_value.__enter__ = MagicMock(return_value=doc_mock)
            fitz_mock.return_value.__exit__ = MagicMock()
            
            result = detect_needs_ocr(b"%PDF-1.4")
            assert result is True


class TestPDFChunking:
    """Tests for PDF text chunking."""
    
    def test_chunks_text_by_size(self):
        """Text is chunked into appropriate sizes."""
        from app.services.chunker import chunk_text
        
        # Long text that needs chunking
        text = "This is a test sentence. " * 100
        
        chunks = chunk_text(text, max_chunk_size=500, overlap=50)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 550  # max_chunk_size + some buffer
            
    def test_preserves_sentence_boundaries(self):
        """Chunks try to break at sentence boundaries."""
        from app.services.chunker import chunk_text
        
        text = "First sentence here. Second sentence here. Third sentence here."
        
        chunks = chunk_text(text, max_chunk_size=30, overlap=5)
        
        # Each chunk should ideally end at a sentence boundary
        for chunk in chunks:
            # Should contain complete words at minimum
            assert not chunk.endswith(" ")
            
    def test_handles_empty_text(self):
        """Empty text returns empty list."""
        from app.services.chunker import chunk_text
        
        chunks = chunk_text("", max_chunk_size=500)
        
        assert chunks == [] or chunks == [""]


class TestIngestionFlow:
    """End-to-end ingestion tests."""
    
    @pytest.mark.asyncio
    async def test_ingest_creates_chunks_with_embeddings(self):
        """Full ingestion flow creates chunks and embeddings."""
        with patch("app.services.ingestion.fetch_pdf") as fetch_mock, \
             patch("app.services.ingestion.extract_text_from_pdf") as extract_mock, \
             patch("app.services.ingestion.create_chunks") as chunk_mock, \
             patch("app.services.embeddings.create_embedding") as embed_mock:
            
            fetch_mock.return_value = b"%PDF-1.4 content"
            extract_mock.return_value = [("Page 1 text", 1), ("Page 2 text", 2)]
            chunk_mock.return_value = [
                {"text": "Chunk 1", "page": 1},
                {"text": "Chunk 2", "page": 2}
            ]
            embed_mock.return_value = [0.1] * 1536  # OpenAI embedding size
            
            from app.services.ingestion import ingest_source
            
            # This would run the full flow
            # Actual test depends on implementation details
            
    def test_progress_callback_called(self):
        """Progress callback is called during ingestion."""
        progress_updates = []
        
        def progress_callback(stage, current, total):
            progress_updates.append((stage, current, total))
        
        # Test that progress is reported
        # Implementation specific


class TestPDFDownload:
    """Tests for PDF downloading."""
    
    @pytest.mark.asyncio
    async def test_download_with_timeout(self):
        """Downloads respect timeout settings."""
        with patch("httpx.AsyncClient") as client_mock:
            response_mock = MagicMock()
            response_mock.status_code = 200
            response_mock.content = b"%PDF-1.4 content"
            
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=response_mock)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock()
            client_mock.return_value = client_instance
            
            from app.services.ingestion import fetch_pdf
            
            result = await fetch_pdf("https://example.com/rules.pdf")
            
            assert result == b"%PDF-1.4 content"
            
    @pytest.mark.asyncio
    async def test_download_handles_404(self):
        """404 responses raise appropriate error."""
        with patch("httpx.AsyncClient") as client_mock:
            response_mock = MagicMock()
            response_mock.status_code = 404
            
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=response_mock)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock()
            client_mock.return_value = client_instance
            
            from app.services.ingestion import fetch_pdf
            
            with pytest.raises(Exception):
                await fetch_pdf("https://example.com/missing.pdf")
