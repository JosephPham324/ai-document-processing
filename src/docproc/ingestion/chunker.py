"""Page-aware recursive text chunker."""

from dataclasses import dataclass

from docproc.ingestion.parsers import ParsedDocument


@dataclass
class TextChunk:
    """A single chunk of text with page number and indexing."""

    chunk_index: int
    page_number: int | None
    text: str
    token_count: int


def estimate_token_count(text: str) -> int:
    """Estimates token count using character heuristic (approx. 4 chars per token)."""
    return max(1, len(text) // 4)


def split_text_recursive(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Recursively splits text into chunks of maximum size with specified overlap."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Hierarchy of split separators
    separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]

    def _split_into_pieces(input_text: str, sep_idx: int) -> list[str]:
        if sep_idx >= len(separators):
            # Hard character slice when no separator works
            return [
                input_text[i : i + chunk_size]
                for i in range(0, len(input_text), chunk_size - chunk_overlap)
            ]

        sep = separators[sep_idx]
        parts = input_text.split(sep)
        if len(parts) <= 1:
            return _split_into_pieces(input_text, sep_idx + 1)

        result_chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for part in parts:
            part_len = len(part) + (len(sep) if current_chunk else 0)
            if current_length + part_len <= chunk_size:
                current_chunk.append(part)
                current_length += part_len
            else:
                if current_chunk:
                    joined = sep.join(current_chunk).strip()
                    if joined:
                        result_chunks.append(joined)
                    # Handle overlap from previous chunk
                    overlap_chars = 0
                    overlap_parts: list[str] = []
                    for p in reversed(current_chunk):
                        if overlap_chars + len(p) <= chunk_overlap:
                            overlap_parts.insert(0, p)
                            overlap_chars += len(p) + len(sep)
                        else:
                            break
                    current_chunk = overlap_parts
                    current_length = sum(len(p) for p in current_chunk) + (
                        len(sep) * max(0, len(current_chunk) - 1)
                    )

                # If the part itself is too long, recursively split it
                if len(part) > chunk_size:
                    sub_chunks = _split_into_pieces(part, sep_idx + 1)
                    result_chunks.extend(sub_chunks)
                    current_chunk = []
                    current_length = 0
                else:
                    current_chunk.append(part)
                    current_length += len(part) + (len(sep) if len(current_chunk) > 1 else 0)

        if current_chunk:
            final_joined = sep.join(current_chunk).strip()
            if final_joined:
                result_chunks.append(final_joined)

        return result_chunks

    raw_chunks = _split_into_pieces(text, 0)
    # Deduplicate empty or whitespace-only chunks
    return [c.strip() for c in raw_chunks if c.strip()]


def chunk_document(
    parsed_doc: ParsedDocument,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[TextChunk]:
    """Chunks a parsed document page by page, preserving page attribution."""
    chunks: list[TextChunk] = []
    global_index = 0

    for page in parsed_doc.pages:
        page_text = page.text.strip()
        if not page_text:
            continue

        page_chunks = split_text_recursive(
            page_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        for piece in page_chunks:
            chunks.append(
                TextChunk(
                    chunk_index=global_index,
                    page_number=page.page_number,
                    text=piece,
                    token_count=estimate_token_count(piece),
                )
            )
            global_index += 1

    return chunks
