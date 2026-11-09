"""Document ingestion, retrieval, and management API endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docproc.api.error_handlers import DocumentNotFoundException
from docproc.db.models import Document
from docproc.db.session import get_db
from docproc.ingestion.service import IngestionService
from docproc.schemas.document import DocumentListResponse, DocumentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
    description="Accepts PDF, TXT, or Markdown documents (up to 20MB), parses text, generates embeddings, and stores chunks.",
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    filename = file.filename or "unknown_file"
    content_type = file.content_type or "application/octet-stream"

    client_emb_prov = request.headers.get("X-Embedding-Provider")
    client_emb_key = (
        request.headers.get("X-OpenAI-API-Key")
        or request.headers.get("X-Gemini-API-Key")
        or request.headers.get("X-API-Key")
    )

    # Read bytes
    file_bytes = await file.read()

    ingestion_service = IngestionService(
        session,
        embedding_provider=client_emb_prov,
        embedding_api_key=client_emb_key,
    )
    response = await ingestion_service.ingest_document(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )
    return response


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
    description="Returns metadata, page counts, chunk counts, and ingestion statuses for stored documents.",
)
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    # Total count
    count_stmt = select(func.count(Document.id))
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Query items
    stmt = select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    docs = result.scalars().all()

    items = [
        DocumentResponse(
            document_id=str(d.id),
            filename=d.filename,
            content_type=d.content_type,
            status=d.status,
            page_count=d.page_count,
            chunk_count=d.chunk_count,
            created_at=d.created_at,
            error=(
                {"code": d.error_code, "message": d.error_message}
                if d.status == "failed" and d.error_code
                else None
            ),
        )
        for d in docs
    ]
    return DocumentListResponse(items=items, total=total)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details by ID",
    description="Returns metadata and ingestion status for a single document.",
)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id) from None

    stmt = select(Document).where(Document.id == doc_uuid)
    result = await session.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise DocumentNotFoundException(document_id)

    return DocumentResponse(
        document_id=str(doc.id),
        filename=doc.filename,
        content_type=doc.content_type,
        status=doc.status,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        error=(
            {"code": doc.error_code, "message": doc.error_message}
            if doc.status == "failed" and doc.error_code
            else None
        ),
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its chunks",
    description="Cascades deletion to all text chunks and vector embeddings associated with the document.",
)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id) from None

    stmt = select(Document).where(Document.id == doc_uuid)
    result = await session.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise DocumentNotFoundException(document_id)

    await session.delete(doc)
    await session.commit()
