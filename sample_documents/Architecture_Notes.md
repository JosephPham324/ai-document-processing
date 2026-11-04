# System Architecture Specifications

## Overview
This document outlines the architectural conventions and operational limits for the Document Processing platform.

### Ingestion Specifications
- Supported formats: PDF, TXT, Markdown.
- Maximum payload limit: 20 MB per file.
- Chunking strategy: Recursive page-aware splitting with 500-character windows and 50-character overlap.
- Deduplication: SHA-256 content hashing to ensure idempotent ingestion.

### Retrieval & Orchestration
- Vector similarity threshold: 0.5 minimum cosine similarity score.
- Workflow orchestration: LangGraph with explicit state transitions and typed contracts.
- Guardrails: Maximum 10 workflow steps and 6 tool executions per request.
