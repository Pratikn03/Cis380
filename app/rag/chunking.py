"""
RAG Chunking Strategies Module

Provides multiple chunking strategies for document processing:
- Character-based chunking (basic)
- Sentence-based chunking (semantic boundaries)
- Recursive chunking (hierarchical splitting)
- Semantic chunking (embedding-based similarity)
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""
    CHARACTER = "character"
    SENTENCE = "sentence"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    source: str
    chunk_id: str
    index: int
    start_char: int = 0
    end_char: int = 0
    strategy: str = "character"
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "index": self.index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "strategy": self.strategy,
            "metadata": self.metadata,
        }


class BaseChunker(ABC):
    """Abstract base class for chunking strategies."""
    
    def __init__(
        self,
        chunk_size: int = 900,
        overlap: int = 150,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    @abstractmethod
    def chunk(self, text: str, source: str = "unknown") -> List[Chunk]:
        """Split text into chunks."""
        pass
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        return " ".join(text.replace("\n", " ").split())


class CharacterChunker(BaseChunker):
    """Simple character-based chunking with overlap."""
    
    def chunk(self, text: str, source: str = "unknown") -> List[Chunk]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []
        
        chunks: List[Chunk] = []
        start = 0
        index = 0
        
        while start < len(cleaned):
            end = min(len(cleaned), start + self.chunk_size)
            chunk_text = cleaned[start:end].strip()
            
            if chunk_text and len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:char:{index}",
                    index=index,
                    start_char=start,
                    end_char=end,
                    strategy="character",
                ))
                index += 1
            
            if end == len(cleaned):
                break
            start = max(end - self.overlap, 0)
        
        return chunks


class SentenceChunker(BaseChunker):
    """Sentence-based chunking that respects sentence boundaries."""
    
    SENTENCE_ENDINGS = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = self.SENTENCE_ENDINGS.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, text: str, source: str = "unknown") -> List[Chunk]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []
        
        sentences = self._split_sentences(cleaned)
        chunks: List[Chunk] = []
        current_chunk: List[str] = []
        current_length = 0
        index = 0
        char_pos = 0
        chunk_start = 0
        
        for sentence in sentences:
            sentence_len = len(sentence) + 1  # +1 for space
            
            if current_length + sentence_len > self.chunk_size and current_chunk:
                # Finalize current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:sent:{index}",
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    strategy="sentence",
                ))
                index += 1
                
                # Keep overlap sentences
                overlap_text = ""
                overlap_sentences = []
                for s in reversed(current_chunk):
                    if len(overlap_text) + len(s) < self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_text = " ".join(overlap_sentences)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = len(overlap_text)
                chunk_start = char_pos - current_length
            
            current_chunk.append(sentence)
            current_length += sentence_len
            char_pos += sentence_len
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:sent:{index}",
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    strategy="sentence",
                ))
        
        return chunks


class RecursiveChunker(BaseChunker):
    """
    Recursive chunking that tries multiple separators hierarchically.
    
    Splits on larger semantic boundaries first, then progressively
    smaller ones until chunk size is met.
    """
    
    DEFAULT_SEPARATORS = [
        "\n\n",      # Paragraphs
        "\n",        # Lines
        ". ",        # Sentences
        ", ",        # Clauses
        " ",         # Words
        "",          # Characters
    ]
    
    def __init__(
        self,
        chunk_size: int = 900,
        overlap: int = 150,
        min_chunk_size: int = 100,
        separators: Optional[List[str]] = None,
    ):
        super().__init__(chunk_size, overlap, min_chunk_size)
        self.separators = separators or self.DEFAULT_SEPARATORS
    
    def _split_text(
        self,
        text: str,
        separators: List[str],
    ) -> List[str]:
        """Recursively split text using separators."""
        if not separators:
            return [text] if text else []
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator == "":
            # Character-level split as last resort
            return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.overlap)]
        
        splits = text.split(separator)
        result: List[str] = []
        current = ""
        
        for split in splits:
            piece = split + separator if separator else split
            
            if len(current) + len(piece) <= self.chunk_size:
                current += piece
            else:
                if current:
                    if len(current) <= self.chunk_size:
                        result.append(current.strip())
                    else:
                        # Recursively split oversized chunks
                        result.extend(self._split_text(current, remaining_separators))
                current = piece
        
        if current:
            if len(current) <= self.chunk_size:
                result.append(current.strip())
            else:
                result.extend(self._split_text(current, remaining_separators))
        
        return [r for r in result if r.strip()]
    
    def chunk(self, text: str, source: str = "unknown") -> List[Chunk]:
        if not text.strip():
            return []
        
        raw_chunks = self._split_text(text, self.separators)
        chunks: List[Chunk] = []
        char_pos = 0
        
        for index, chunk_text in enumerate(raw_chunks):
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:rec:{index}",
                    index=index,
                    start_char=char_pos,
                    end_char=char_pos + len(chunk_text),
                    strategy="recursive",
                ))
            char_pos += len(chunk_text)
        
        return chunks


class ParagraphChunker(BaseChunker):
    """Paragraph-based chunking that respects document structure."""
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def chunk(self, text: str, source: str = "unknown") -> List[Chunk]:
        paragraphs = self._split_paragraphs(text)
        if not paragraphs:
            return []
        
        chunks: List[Chunk] = []
        current_chunk: List[str] = []
        current_length = 0
        index = 0
        char_pos = 0
        chunk_start = 0
        
        for para in paragraphs:
            para_len = len(para) + 2  # +2 for paragraph break
            
            if current_length + para_len > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:para:{index}",
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    strategy="paragraph",
                ))
                index += 1
                current_chunk = []
                current_length = 0
                chunk_start = char_pos
            
            current_chunk.append(para)
            current_length += para_len
            char_pos += para_len
        
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:para:{index}",
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    strategy="paragraph",
                ))
        
        return chunks


class SemanticChunker(BaseChunker):
    """
    Semantic chunking using embedding similarity.
    
    Groups sentences that are semantically similar together,
    creating more coherent chunks for retrieval.
    """
    
    def __init__(
        self,
        chunk_size: int = 900,
        overlap: int = 150,
        min_chunk_size: int = 100,
        similarity_threshold: float = 0.5,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        super().__init__(chunk_size, overlap, min_chunk_size)
        self.similarity_threshold = similarity_threshold
        self.embed_fn = embed_fn
    
    def _compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, text: str, source: str = "unknown") -> List[Chunk]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []
        
        sentences = self._split_sentences(cleaned)
        if not sentences:
            return []
        
        # If no embedding function, fall back to sentence chunking
        if not self.embed_fn:
            logger.warning("No embedding function provided, falling back to sentence chunking")
            fallback = SentenceChunker(self.chunk_size, self.overlap, self.min_chunk_size)
            return fallback.chunk(text, source)
        
        # Compute embeddings for all sentences
        try:
            embeddings = [self.embed_fn(s) for s in sentences]
        except Exception as e:
            logger.error(f"Embedding failed: {e}, falling back to sentence chunking")
            fallback = SentenceChunker(self.chunk_size, self.overlap, self.min_chunk_size)
            return fallback.chunk(text, source)
        
        # Group sentences by semantic similarity
        chunks: List[Chunk] = []
        current_group: List[str] = [sentences[0]]
        current_embedding = embeddings[0]
        current_length = len(sentences[0])
        index = 0
        char_pos = 0
        chunk_start = 0
        
        for i in range(1, len(sentences)):
            sentence = sentences[i]
            embedding = embeddings[i]
            similarity = self._compute_similarity(current_embedding, embedding)
            
            should_split = (
                similarity < self.similarity_threshold or
                current_length + len(sentence) > self.chunk_size
            )
            
            if should_split and current_group:
                chunk_text = " ".join(current_group)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        text=chunk_text,
                        source=source,
                        chunk_id=f"{source}:sem:{index}",
                        index=index,
                        start_char=chunk_start,
                        end_char=chunk_start + len(chunk_text),
                        strategy="semantic",
                        metadata={"similarity_threshold": self.similarity_threshold},
                    ))
                    index += 1
                
                char_pos += len(chunk_text) + 1
                chunk_start = char_pos
                current_group = []
                current_length = 0
            
            current_group.append(sentence)
            current_embedding = embedding
            current_length += len(sentence) + 1
        
        # Add final chunk
        if current_group:
            chunk_text = " ".join(current_group)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    chunk_id=f"{source}:sem:{index}",
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    strategy="semantic",
                    metadata={"similarity_threshold": self.similarity_threshold},
                ))
        
        return chunks


class ChunkerFactory:
    """Factory for creating chunker instances."""
    
    _chunkers = {
        ChunkingStrategy.CHARACTER: CharacterChunker,
        ChunkingStrategy.SENTENCE: SentenceChunker,
        ChunkingStrategy.RECURSIVE: RecursiveChunker,
        ChunkingStrategy.PARAGRAPH: ParagraphChunker,
        ChunkingStrategy.SEMANTIC: SemanticChunker,
    }
    
    @classmethod
    def create(
        cls,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        **kwargs,
    ) -> BaseChunker:
        """Create a chunker instance."""
        chunker_class = cls._chunkers.get(strategy)
        if not chunker_class:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        return chunker_class(**kwargs)
    
    @classmethod
    def register(cls, strategy: ChunkingStrategy, chunker_class: type):
        """Register a custom chunker."""
        cls._chunkers[strategy] = chunker_class


# ============================================================================
# Legacy API (backwards compatibility)
# ============================================================================

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    """
    Legacy function for basic character-based chunking.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunker = CharacterChunker(chunk_size=chunk_size, overlap=overlap, min_chunk_size=1)
    return [c.text for c in chunker.chunk(text)]


def chunk_with_metadata(
    text: str, source: str, chunk_size: int = 900, overlap: int = 150
) -> Iterable[dict]:
    """
    Legacy function for chunking with basic metadata.
    
    Args:
        text: Text to chunk
        source: Source identifier
        chunk_size: Maximum chunk size
        overlap: Overlap between chunks
    
    Yields:
        Dictionaries with chunk text and metadata
    """
    chunker = CharacterChunker(chunk_size=chunk_size, overlap=overlap, min_chunk_size=1)
    for chunk in chunker.chunk(text, source):
        yield {
            "source": chunk.source,
            "text": chunk.text,
            "chunk_id": f"{source}:{chunk.index}",  # Legacy format
        }


# ============================================================================
# Convenience functions
# ============================================================================

def chunk_document(
    text: str,
    source: str = "unknown",
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    chunk_size: int = 900,
    overlap: int = 150,
    **kwargs,
) -> List[Chunk]:
    """
    Chunk a document using the specified strategy.
    
    Args:
        text: Document text to chunk
        source: Source identifier for the document
        strategy: Chunking strategy to use
        chunk_size: Maximum chunk size
        overlap: Overlap between chunks
        **kwargs: Additional arguments for the chunker
    
    Returns:
        List of Chunk objects
    """
    chunker = ChunkerFactory.create(
        strategy=strategy,
        chunk_size=chunk_size,
        overlap=overlap,
        **kwargs,
    )
    return chunker.chunk(text, source)


def auto_chunk(
    text: str,
    source: str = "unknown",
    chunk_size: int = 900,
) -> List[Chunk]:
    """
    Automatically select the best chunking strategy based on content.
    
    Uses paragraph chunking for structured documents,
    sentence chunking for prose, and character chunking for code.
    """
    # Detect document type
    paragraph_count = len(re.split(r'\n\s*\n', text))
    code_indicators = text.count('{') + text.count('}') + text.count('def ') + text.count('class ')
    
    if code_indicators > 10:
        # Likely code - use recursive chunking
        strategy = ChunkingStrategy.RECURSIVE
    elif paragraph_count > 5:
        # Structured document - use paragraph chunking
        strategy = ChunkingStrategy.PARAGRAPH
    else:
        # Prose - use sentence chunking
        strategy = ChunkingStrategy.SENTENCE
    
    logger.info(f"Auto-selected chunking strategy: {strategy}")
    return chunk_document(text, source, strategy, chunk_size)
