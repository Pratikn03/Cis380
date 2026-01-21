from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.rag.ocr import DocumentProcessor


SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".md", ".html", ".htm", ".json", ".csv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}


@dataclass
class DocumentPage:
    page_num: int
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class DocumentContent:
    doc_id: str
    source: str
    doc_type: str
    pages: List[DocumentPage]
    metadata: dict = field(default_factory=dict)


def _hash_doc(path: Path) -> str:
    payload = f"{path.resolve()}|{path.stat().st_mtime}|{path.stat().st_size}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(path: Path) -> List[DocumentPage]:
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        pages: List[DocumentPage] = []
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(DocumentPage(page_num=idx, text=text))
        return pages
    except Exception:
        return []


def _load_docx(path: Path) -> List[DocumentPage]:
    try:
        import docx

        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        return [DocumentPage(page_num=1, text=text)]
    except Exception:
        return []


def _load_html(path: Path) -> List[DocumentPage]:
    raw = _load_text(path)
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(separator=" ")
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text)
    return [DocumentPage(page_num=1, text=text)]


def _load_structured(path: Path) -> List[DocumentPage]:
    raw = _load_text(path)
    if path.suffix.lower() == ".json":
        try:
            obj = json.loads(raw)
            raw = json.dumps(obj, indent=2)
        except Exception:
            pass
    return [DocumentPage(page_num=1, text=raw)]


def load_document(path: Path) -> Optional[DocumentContent]:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTS and ext not in IMAGE_EXTS:
        return None
    doc_id = _hash_doc(path)
    pages: List[DocumentPage] = []
    if ext in {".txt", ".md"}:
        pages = [DocumentPage(page_num=1, text=_load_text(path))]
    elif ext in {".json", ".csv"}:
        pages = _load_structured(path)
    elif ext in {".html", ".htm"}:
        pages = _load_html(path)
    elif ext == ".docx":
        pages = _load_docx(path)
    elif ext == ".pdf":
        pages = _load_pdf(path)
        if not any(p.text.strip() for p in pages):
            try:
                processor = DocumentProcessor()
                content = processor.process(path)
                pages = [
                    DocumentPage(page_num=page.page_num, text=page.text)
                    for page in content.pages
                ]
            except Exception:
                pages = []
    elif ext in IMAGE_EXTS:
        try:
            processor = DocumentProcessor()
            content = processor.process(path)
            pages = [
                DocumentPage(page_num=page.page_num, text=page.text)
                for page in content.pages
            ]
        except Exception:
            pages = []
    if not pages:
        return None
    return DocumentContent(
        doc_id=doc_id,
        source=str(path),
        doc_type=ext.lstrip("."),
        pages=pages,
        metadata={"filename": path.name},
    )


def scan_documents(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and (path.suffix.lower() in SUPPORTED_EXTS or path.suffix.lower() in IMAGE_EXTS)
    ]
