"""In-memory database mock session for high-speed isolated tests."""

import uuid
from datetime import UTC, datetime
from typing import Any

from docproc.db.models import Document, DocumentChunk


class MockAsyncResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None

    def scalar_one(self) -> Any:
        return self._items[0]

    def scalars(self) -> "MockAsyncResult":
        return self

    def all(self) -> list[Any]:
        return self._items


class InMemoryAsyncSession:
    """Simulates an AsyncSession holding Document and DocumentChunk records in-memory."""

    def __init__(self) -> None:
        self.documents: dict[uuid.UUID, Document] = {}
        self.chunks: dict[uuid.UUID, DocumentChunk] = {}
        self.pending_adds: list[Any] = []
        self.pending_deletes: list[Any] = []

    def add(self, obj: Any) -> None:
        self.pending_adds.append(obj)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for obj in self.pending_adds:
            if isinstance(obj, Document):
                if not hasattr(obj, "id") or not obj.id:
                    obj.id = uuid.uuid4()
                if not hasattr(obj, "created_at") or not obj.created_at:
                    obj.created_at = now
                self.documents[obj.id] = obj
            elif isinstance(obj, DocumentChunk):
                if not hasattr(obj, "id") or not obj.id:
                    obj.id = uuid.uuid4()
                if not hasattr(obj, "created_at") or not obj.created_at:
                    obj.created_at = now
                self.chunks[obj.id] = obj
        self.pending_adds.clear()

    async def commit(self) -> None:
        await self.flush()
        for obj in self.pending_deletes:
            if isinstance(obj, Document):
                self.documents.pop(obj.id, None)
                # Cascade chunks
                chunk_ids_to_del = [
                    cid for cid, c in self.chunks.items() if c.document_id == obj.id
                ]
                for cid in chunk_ids_to_del:
                    self.chunks.pop(cid, None)
        self.pending_deletes.clear()

    async def rollback(self) -> None:
        self.pending_adds.clear()
        self.pending_deletes.clear()

    async def refresh(self, obj: Any) -> None:
        pass

    async def delete(self, obj: Any) -> None:
        self.pending_deletes.append(obj)

    async def close(self) -> None:
        pass

    async def execute(self, statement: Any) -> MockAsyncResult:
        # Simple inspection of SQLAlchemy statements
        sql_str = str(statement).lower()
        params = {}
        try:
            params = dict(statement.compile().params)
        except Exception:
            pass

        if "count(" in sql_str or "count_1" in sql_str:
            return MockAsyncResult([len(self.documents)])

        if "from documents" in sql_str:
            docs = list(self.documents.values())

            # Check checksum filter
            for pval in params.values():
                if isinstance(pval, str) and len(pval) == 64:  # sha256
                    matched = [d for d in docs if d.checksum_sha256 == pval]
                    return MockAsyncResult(matched)

            # Check ID filter
            for pval in params.values():
                if isinstance(pval, uuid.UUID):
                    matched = [d for d in docs if d.id == pval]
                    return MockAsyncResult(matched)

            # Order by created_at desc
            docs.sort(key=lambda d: d.created_at, reverse=True)
            return MockAsyncResult(docs)

        if "from document_chunks" in sql_str:
            chunks = list(self.chunks.values())
            target_doc_ids = [pval for pval in params.values() if isinstance(pval, uuid.UUID)]
            if target_doc_ids:
                chunks = [c for c in chunks if c.document_id in target_doc_ids]

            rows = []
            for c in chunks:
                doc = self.documents.get(c.document_id)
                fn = doc.filename if doc else "doc"
                dist = 0.2 if c.text.strip() else 0.9
                rows.append((c, dist, fn))
            return MockAsyncResult(rows)

        return MockAsyncResult([])
