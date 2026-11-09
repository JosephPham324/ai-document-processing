"""Ingestion service orchestrating parsing, chunking, embedding, and storage."""

import hashlib
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docproc.api.error_handlers import (
    FileTooLargeException,
    UnsupportedMediaTypeException,
)
from docproc.config import get_settings
from docproc.db.models import Document, DocumentChunk
from docproc.ingestion.chunker import chunk_document
from docproc.ingestion.parsers import ParsingError, parse_document
from docproc.providers.factory import get_embedding_provider
from docproc.schemas.document import DocumentResponse

logger = logging.getLogger(__name__)


def compute_sha256(data: bytes) -> str:
    """Computes SHA-256 hex digest of file bytes."""
    return hashlib.sha256(data).hexdigest()


class IngestionService:
    """Handles end-to-end ingestion lifecycle for uploaded documents."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: str | None = None,
        embedding_api_key: str | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.embedder = get_embedding_provider(
            self.settings,
            provider_name=embedding_provider,
            api_key=embedding_api_key,
        )

    async def ingest_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> DocumentResponse:
        """Parses, chunks, embeds, and stores document in PostgreSQL."""
        # 1. Validate file size
        file_size = len(file_bytes)
        if file_size > self.settings.MAX_FILE_SIZE_BYTES:
            raise FileTooLargeException(file_size, self.settings.MAX_FILE_SIZE_BYTES)

        # 2. Validate MIME type
        norm_content_type = content_type.lower()
        if (
            norm_content_type not in self.settings.ALLOWED_CONTENT_TYPES
            and not filename.lower().endswith((".pdf", ".txt", ".md", ".markdown"))
        ):
            raise UnsupportedMediaTypeException(content_type, self.settings.ALLOWED_CONTENT_TYPES)

        # 3. Check duplicate upload via SHA-256 checksum
        checksum = compute_sha256(file_bytes)
        existing_doc_stmt = select(Document).where(Document.checksum_sha256 == checksum)
        result = await self.session.execute(existing_doc_stmt)
        existing_doc = result.scalar_one_or_none()

        if existing_doc:
            if existing_doc.status == "completed":
                logger.info(
                    f"Duplicate document detected (id={existing_doc.id}); returning existing record."
                )
                return DocumentResponse(
                    document_id=str(existing_doc.id),
                    filename=existing_doc.filename,
                    content_type=existing_doc.content_type,
                    status=existing_doc.status,
                    page_count=existing_doc.page_count,
                    chunk_count=existing_doc.chunk_count,
                    created_at=existing_doc.created_at,
                    error=None,
                )
            else:
                # Re-use existing document record if previous ingestion failed
                doc_record = existing_doc
                doc_record.status = "processing"
                doc_record.error_code = None
                doc_record.error_message = None
        else:
            doc_record = Document(
                id=uuid.uuid4(),
                filename=filename,
                content_type=norm_content_type,
                file_size=file_size,
                checksum_sha256=checksum,
                status="processing",
            )
            self.session.add(doc_record)
            await self.session.flush()

        # 4. Parse document
        try:
            parsed = parse_document(file_bytes, filename, norm_content_type)
            doc_record.page_count = parsed.page_count
        except ParsingError as p_err:
            logger.error(f"Failed parsing document {filename}: {p_err}")
            doc_record.status = "failed"
            doc_record.error_code = p_err.code
            doc_record.error_message = p_err.message
            await self.session.commit()
            return DocumentResponse(
                document_id=str(doc_record.id),
                filename=doc_record.filename,
                content_type=doc_record.content_type,
                status="failed",
                page_count=None,
                chunk_count=0,
                created_at=doc_record.created_at,
                error={"code": p_err.code, "message": p_err.message},
            )

        # 5. Chunk document
        chunks = chunk_document(
            parsed,
            chunk_size=self.settings.DEFAULT_CHUNK_SIZE,
            chunk_overlap=self.settings.DEFAULT_CHUNK_OVERLAP,
        )
        if not chunks:
            doc_record.status = "failed"
            doc_record.error_code = "NO_CHUNKS_GENERATED"
            doc_record.error_message = "Document yielded zero text chunks."
            await self.session.commit()
            return DocumentResponse(
                document_id=str(doc_record.id),
                filename=doc_record.filename,
                content_type=doc_record.content_type,
                status="failed",
                page_count=parsed.page_count,
                chunk_count=0,
                created_at=doc_record.created_at,
                error={
                    "code": "NO_CHUNKS_GENERATED",
                    "message": "Document yielded zero text chunks.",
                },
            )

        # 6. Generate embeddings
        chunk_texts = [c.text for c in chunks]
        try:
            embeddings = await self.embedder.embed_documents(chunk_texts)
        except Exception as emb_err:
            logger.error(f"Embedding generation failed: {emb_err}")
            doc_record.status = "failed"
            doc_record.error_code = "EMBEDDING_PROVIDER_ERROR"
            doc_record.error_message = str(emb_err)
            await self.session.commit()
            return DocumentResponse(
                document_id=str(doc_record.id),
                filename=doc_record.filename,
                content_type=doc_record.content_type,
                status="failed",
                page_count=parsed.page_count,
                chunk_count=0,
                created_at=doc_record.created_at,
                error={"code": "EMBEDDING_PROVIDER_ERROR", "message": str(emb_err)},
            )

        # 7. Store chunks
        for text_chunk, emb in zip(chunks, embeddings, strict=True):
            chunk_db = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc_record.id,
                chunk_index=text_chunk.chunk_index,
                page_number=text_chunk.page_number,
                text=text_chunk.text,
                embedding=emb,
                token_count=text_chunk.token_count,
                metadata_={
                    "filename": filename,
                    "page": text_chunk.page_number,
                    "chunk_index": text_chunk.chunk_index,
                },
            )
            self.session.add(chunk_db)

        # 8. Finalize document record
        doc_record.chunk_count = len(chunks)
        doc_record.status = "completed"
        await self.session.commit()
        await self.session.refresh(doc_record)

        return DocumentResponse(
            document_id=str(doc_record.id),
            filename=doc_record.filename,
            content_type=doc_record.content_type,
            status="completed",
            page_count=doc_record.page_count,
            chunk_count=doc_record.chunk_count,
            created_at=doc_record.created_at,
            error=None,
        )
