"""
RAG OCR Pipeline Module

Provides OCR capabilities for document processing:
- PDF text extraction
- Image OCR (using pytesseract or cloud APIs)
- Multi-page document handling
- Layout analysis
- Table extraction
"""
from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    IMAGE = "image"
    SCAN = "scan"  # Scanned PDF
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """Represents a bounding box for text regions."""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


@dataclass
class TextBlock:
    """Represents an extracted text block."""
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    page_num: int = 1
    block_type: str = "text"  # text, table, heading, etc.
    metadata: Dict = field(default_factory=dict)


@dataclass
class PageContent:
    """Content extracted from a single page."""
    page_num: int
    text: str
    blocks: List[TextBlock] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    images: List[bytes] = field(default_factory=list)
    width: int = 0
    height: int = 0
    
    @property
    def avg_confidence(self) -> float:
        if not self.blocks:
            return 0.0
        return sum(b.confidence for b in self.blocks) / len(self.blocks)


@dataclass
class DocumentContent:
    """Complete document extraction result."""
    source: str
    doc_type: DocumentType
    pages: List[PageContent]
    metadata: Dict = field(default_factory=dict)
    
    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)
    
    @property
    def num_pages(self) -> int:
        return len(self.pages)
    
    @property
    def avg_confidence(self) -> float:
        if not self.pages:
            return 0.0
        return sum(p.avg_confidence for p in self.pages) / len(self.pages)
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "doc_type": self.doc_type.value,
            "num_pages": self.num_pages,
            "full_text": self.full_text,
            "avg_confidence": self.avg_confidence,
            "metadata": self.metadata,
        }


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    @abstractmethod
    def extract_text(self, image: bytes) -> Tuple[str, float]:
        """Extract text from an image. Returns (text, confidence)."""
        pass
    
    @abstractmethod
    def extract_blocks(self, image: bytes) -> List[TextBlock]:
        """Extract text blocks with positions from an image."""
        pass


class TesseractOCREngine(BaseOCREngine):
    """OCR engine using pytesseract."""
    
    def __init__(self, lang: str = "eng", config: str = ""):
        self.lang = lang
        self.config = config
        self._tesseract_available = False
        
        try:
            import pytesseract
            self._pytesseract = pytesseract
            self._tesseract_available = True
        except ImportError:
            logger.warning("pytesseract not available. OCR will be limited.")
    
    def extract_text(self, image: bytes) -> Tuple[str, float]:
        """Extract text using Tesseract."""
        if not self._tesseract_available:
            return "", 0.0
        
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image))
            text = self._pytesseract.image_to_string(
                img, lang=self.lang, config=self.config
            )
            # Estimate confidence (Tesseract provides per-word confidence)
            data = self._pytesseract.image_to_data(img, output_type=self._pytesseract.Output.DICT)
            confidences = [int(c) for c in data["conf"] if c != "-1"]
            avg_conf = sum(confidences) / len(confidences) / 100 if confidences else 0.5
            return text.strip(), avg_conf
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return "", 0.0
    
    def extract_blocks(self, image: bytes) -> List[TextBlock]:
        """Extract text blocks with bounding boxes."""
        if not self._tesseract_available:
            return []
        
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image))
            data = self._pytesseract.image_to_data(img, output_type=self._pytesseract.Output.DICT)
            
            blocks: List[TextBlock] = []
            n_boxes = len(data["level"])
            
            for i in range(n_boxes):
                text = data["text"][i].strip()
                if not text:
                    continue
                
                conf = int(data["conf"][i]) if data["conf"][i] != "-1" else 0
                
                blocks.append(TextBlock(
                    text=text,
                    confidence=conf / 100,
                    bbox=BoundingBox(
                        x=data["left"][i],
                        y=data["top"][i],
                        width=data["width"][i],
                        height=data["height"][i],
                    ),
                    block_type="word",
                ))
            
            return blocks
        except Exception as e:
            logger.error(f"Tesseract block extraction failed: {e}")
            return []


class MockOCREngine(BaseOCREngine):
    """Mock OCR engine for testing."""
    
    def extract_text(self, image: bytes) -> Tuple[str, float]:
        return "[OCR text would appear here]", 0.95
    
    def extract_blocks(self, image: bytes) -> List[TextBlock]:
        return [TextBlock(
            text="[Mock OCR block]",
            confidence=0.95,
            bbox=BoundingBox(0, 0, 100, 20),
        )]


class PDFExtractor:
    """Extracts content from PDF documents."""
    
    def __init__(self, ocr_engine: Optional[BaseOCREngine] = None):
        self.ocr_engine = ocr_engine or TesseractOCREngine()
        self._pymupdf_available = False
        self._pdfplumber_available = False
        
        try:
            import fitz  # PyMuPDF
            self._fitz = fitz
            self._pymupdf_available = True
        except ImportError:
            logger.warning("PyMuPDF not available")
        
        try:
            import pdfplumber
            self._pdfplumber = pdfplumber
            self._pdfplumber_available = True
        except ImportError:
            logger.warning("pdfplumber not available")
    
    def is_scanned_pdf(self, pdf_path: Union[str, Path]) -> bool:
        """Detect if PDF is scanned (image-based) or native."""
        if not self._pymupdf_available:
            return False
        
        try:
            doc = self._fitz.open(str(pdf_path))
            text_chars = 0
            total_pages = min(3, len(doc))  # Check first 3 pages
            
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                text_chars += len(text.strip())
            
            doc.close()
            
            # If very little text, likely scanned
            return text_chars < 100 * total_pages
        except Exception as e:
            logger.error(f"Error detecting scanned PDF: {e}")
            return False
    
    def extract_native(self, pdf_path: Union[str, Path]) -> DocumentContent:
        """Extract text from native (searchable) PDF."""
        pages: List[PageContent] = []
        
        if self._pymupdf_available:
            try:
                doc = self._fitz.open(str(pdf_path))
                
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    rect = page.rect
                    
                    # Extract text blocks
                    blocks = []
                    for block in page.get_text("dict")["blocks"]:
                        if "lines" in block:
                            block_text = ""
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    block_text += span["text"] + " "
                            
                            if block_text.strip():
                                bbox = block.get("bbox", (0, 0, 0, 0))
                                blocks.append(TextBlock(
                                    text=block_text.strip(),
                                    confidence=1.0,  # Native text has high confidence
                                    bbox=BoundingBox(
                                        int(bbox[0]), int(bbox[1]),
                                        int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
                                    ),
                                    page_num=page_num + 1,
                                    block_type="text",
                                ))
                    
                    pages.append(PageContent(
                        page_num=page_num + 1,
                        text=text.strip(),
                        blocks=blocks,
                        width=int(rect.width),
                        height=int(rect.height),
                    ))
                
                doc.close()
            except Exception as e:
                logger.error(f"PyMuPDF extraction failed: {e}")
        
        elif self._pdfplumber_available:
            try:
                with self._pdfplumber.open(str(pdf_path)) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text = page.extract_text() or ""
                        pages.append(PageContent(
                            page_num=page_num + 1,
                            text=text.strip(),
                            width=int(page.width),
                            height=int(page.height),
                        ))
            except Exception as e:
                logger.error(f"pdfplumber extraction failed: {e}")
        
        return DocumentContent(
            source=str(pdf_path),
            doc_type=DocumentType.PDF,
            pages=pages,
            metadata={"extraction_method": "native"},
        )
    
    def extract_scanned(self, pdf_path: Union[str, Path]) -> DocumentContent:
        """Extract text from scanned PDF using OCR."""
        pages: List[PageContent] = []
        
        if not self._pymupdf_available:
            logger.error("PyMuPDF required for scanned PDF extraction")
            return DocumentContent(
                source=str(pdf_path),
                doc_type=DocumentType.SCAN,
                pages=[],
            )
        
        try:
            doc = self._fitz.open(str(pdf_path))
            
            for page_num, page in enumerate(doc):
                # Render page to image
                mat = self._fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                
                # OCR the image
                text, confidence = self.ocr_engine.extract_text(img_bytes)
                blocks = self.ocr_engine.extract_blocks(img_bytes)
                
                # Update block page numbers
                for block in blocks:
                    block.page_num = page_num + 1
                
                pages.append(PageContent(
                    page_num=page_num + 1,
                    text=text,
                    blocks=blocks,
                    width=pix.width,
                    height=pix.height,
                ))
            
            doc.close()
        except Exception as e:
            logger.error(f"Scanned PDF extraction failed: {e}")
        
        return DocumentContent(
            source=str(pdf_path),
            doc_type=DocumentType.SCAN,
            pages=pages,
            metadata={"extraction_method": "ocr"},
        )
    
    def extract(self, pdf_path: Union[str, Path]) -> DocumentContent:
        """Auto-detect and extract content from PDF."""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        if self.is_scanned_pdf(pdf_path):
            logger.info(f"Detected scanned PDF: {pdf_path}")
            return self.extract_scanned(pdf_path)
        else:
            logger.info(f"Detected native PDF: {pdf_path}")
            return self.extract_native(pdf_path)
    
    def extract_tables(self, pdf_path: Union[str, Path]) -> List[List[List[str]]]:
        """Extract tables from PDF."""
        tables: List[List[List[str]]] = []
        
        if not self._pdfplumber_available:
            logger.warning("pdfplumber required for table extraction")
            return tables
        
        try:
            with self._pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        # Clean up table cells
                        cleaned = [
                            [cell.strip() if cell else "" for cell in row]
                            for row in table
                        ]
                        tables.append(cleaned)
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
        
        return tables


class ImageOCR:
    """OCR for image files."""
    
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"}
    
    def __init__(self, ocr_engine: Optional[BaseOCREngine] = None):
        self.ocr_engine = ocr_engine or TesseractOCREngine()
    
    def extract(
        self,
        image_source: Union[str, Path, bytes, BinaryIO],
    ) -> DocumentContent:
        """Extract text from an image."""
        # Get image bytes
        if isinstance(image_source, bytes):
            img_bytes = image_source
            source_name = "bytes"
        elif isinstance(image_source, (str, Path)):
            path = Path(image_source)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {path}")
            img_bytes = path.read_bytes()
            source_name = str(path)
        else:
            img_bytes = image_source.read()
            source_name = getattr(image_source, "name", "stream")
        
        # Extract text
        text, confidence = self.ocr_engine.extract_text(img_bytes)
        blocks = self.ocr_engine.extract_blocks(img_bytes)
        
        # Get image dimensions
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(img_bytes))
            width, height = img.size
        except Exception:
            width, height = 0, 0
        
        page = PageContent(
            page_num=1,
            text=text,
            blocks=blocks,
            width=width,
            height=height,
        )
        
        return DocumentContent(
            source=source_name,
            doc_type=DocumentType.IMAGE,
            pages=[page],
            metadata={"avg_confidence": confidence},
        )


class DocumentProcessor:
    """
    High-level document processor for RAG ingestion.
    
    Automatically handles PDFs and images.
    """
    
    def __init__(self, ocr_engine: Optional[BaseOCREngine] = None):
        self.ocr_engine = ocr_engine or TesseractOCREngine()
        self.pdf_extractor = PDFExtractor(self.ocr_engine)
        self.image_ocr = ImageOCR(self.ocr_engine)
    
    def process(
        self,
        file_path: Union[str, Path],
    ) -> DocumentContent:
        """
        Process a document and extract content.
        
        Args:
            file_path: Path to PDF or image file
        
        Returns:
            DocumentContent with extracted text and metadata
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == ".pdf":
            return self.pdf_extractor.extract(path)
        elif suffix in ImageOCR.SUPPORTED_FORMATS:
            return self.image_ocr.extract(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def process_batch(
        self,
        file_paths: List[Union[str, Path]],
    ) -> List[DocumentContent]:
        """Process multiple documents."""
        results = []
        for path in file_paths:
            try:
                result = self.process(path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {path}: {e}")
        return results
    
    def process_to_text(
        self,
        file_path: Union[str, Path],
    ) -> str:
        """Process document and return just the text."""
        content = self.process(file_path)
        return content.full_text


# ============================================================================
# Convenience Functions
# ============================================================================

def extract_pdf_text(pdf_path: Union[str, Path]) -> str:
    """Extract all text from a PDF file."""
    extractor = PDFExtractor()
    content = extractor.extract(pdf_path)
    return content.full_text


def extract_image_text(image_path: Union[str, Path]) -> str:
    """Extract text from an image file."""
    ocr = ImageOCR()
    content = ocr.extract(image_path)
    return content.full_text


def process_document(file_path: Union[str, Path]) -> DocumentContent:
    """Process any supported document type."""
    processor = DocumentProcessor()
    return processor.process(file_path)


def is_scanned_pdf(pdf_path: Union[str, Path]) -> bool:
    """Check if a PDF is scanned (image-based)."""
    extractor = PDFExtractor()
    return extractor.is_scanned_pdf(pdf_path)
