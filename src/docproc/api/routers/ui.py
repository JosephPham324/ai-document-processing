"""Serving UI router providing an interactive web dashboard for document processing."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["UI"])

UI_HTML = r"""<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-900 text-slate-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document Processing AI Agent</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f0fdf4',
              100: '#dcfce7',
              500: '#22c55e',
              600: '#16a34a',
              700: '#15803d',
            }
          }
        }
      }
    }
  </script>
  <!-- Google Fonts Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <!-- Marked.js for Markdown Rendering -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    body { font-family: 'Inter', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace; }
    .source-highlight {
      animation: pulse-ring 1.5s cubic-bezier(0.4, 0, 0.6, 1) 2;
    }
    @keyframes pulse-ring {
      0%, 100% { outline: 2px solid rgba(34, 197, 94, 0.9); box-shadow: 0 0 15px rgba(34, 197, 94, 0.5); }
      50% { outline: 2px solid rgba(34, 197, 94, 0.3); box-shadow: none; }
    }
    /* Markdown Styles for Agent Summary */
    #res-summary h1, #res-summary h2, #res-summary h3, #res-summary h4 {
      font-weight: 600;
      color: #f1f5f9;
      margin-top: 0.85rem;
      margin-bottom: 0.35rem;
    }
    #res-summary h1 { font-size: 1.05rem; border-bottom: 1px solid #1e293b; padding-bottom: 0.25rem; }
    #res-summary h2 { font-size: 0.95rem; }
    #res-summary h3 { font-size: 0.875rem; color: #34d399; }
    #res-summary ul { list-style-type: disc; margin-left: 1.25rem; margin-top: 0.35rem; margin-bottom: 0.5rem; }
    #res-summary ol { list-style-type: decimal; margin-left: 1.25rem; margin-top: 0.35rem; margin-bottom: 0.5rem; }
    #res-summary li { margin-bottom: 0.25rem; line-height: 1.55; }
    #res-summary p { margin-bottom: 0.5rem; line-height: 1.6; }
    #res-summary strong { color: #f8fafc; font-weight: 600; }
    #res-summary code { background: #020617; padding: 0.1rem 0.35rem; border-radius: 0.25rem; font-family: 'JetBrains Mono', monospace; font-size: 0.85em; border: 1px solid #1e293b; color: #38bdf8; }
    #res-summary blockquote { border-left: 3px solid #10b981; padding-left: 0.75rem; color: #94a3b8; font-style: italic; margin: 0.5rem 0; }
  </style>
</head>
<body class="h-full flex flex-col antialiased">
  <!-- Top Navbar -->
  <header class="border-b border-slate-800 bg-slate-950/70 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="h-9 w-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-lg shadow-sm">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
      </div>
      <div>
        <h1 class="text-base font-semibold text-white tracking-tight flex items-center gap-2">
          Document Intelligence AI Agent
          <span class="text-xs font-normal px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">LangGraph RAG</span>
        </h1>
        <p class="text-xs text-slate-400">Deterministic extraction, policy validation, and 100% source provenance</p>
      </div>
    </div>

    <!-- System Status & Links -->
    <div class="flex items-center space-x-4">
      <div id="status-indicator" class="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
        <span class="w-2 h-2 rounded-full bg-amber-400 animate-ping" id="status-ping"></span>
        <span class="w-2 h-2 rounded-full bg-amber-400" id="status-dot"></span>
        <span id="status-text">Checking backend...</span>
      </div>

      <div class="h-4 w-px bg-slate-800"></div>

      <a href="/docs" target="_blank" class="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition">
        <span>Swagger API</span>
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
      </a>
      <a href="/redoc" target="_blank" class="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition">
        <span>ReDoc</span>
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
      </a>
    </div>
  </header>

  <!-- Main Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-y-auto">

    <!-- Left Column: Document Ingestion & Repository (5 cols) -->
    <section class="lg:col-span-5 flex flex-col space-y-5">

      <!-- Upload Card -->
      <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-white flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            Upload & Ingest Document
          </h2>
          <span class="text-[11px] text-slate-400">PDF, TXT, MD (Max 20MB)</span>
        </div>

        <div id="drop-zone" class="border-2 border-dashed border-slate-700/80 hover:border-emerald-500/50 rounded-lg p-5 text-center transition cursor-pointer bg-slate-900/50 group">
          <input type="file" id="file-input" class="hidden" accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown">
          <div class="flex flex-col items-center justify-center space-y-2">
            <div class="p-3 bg-slate-800 rounded-full group-hover:scale-110 transition text-slate-300">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
            </div>
            <p class="text-xs text-slate-300"><span class="font-medium text-emerald-400">Click to browse</span> or drag & drop files here</p>
            <p id="selected-file-label" class="text-[11px] text-slate-400 font-mono italic">No file selected</p>
          </div>
        </div>

        <div class="mt-3 flex items-center justify-between gap-3">
          <button id="upload-btn" disabled class="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium text-xs py-2 px-4 rounded-lg transition flex items-center justify-center gap-2 shadow-sm">
            <svg id="upload-spinner" class="hidden animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
            <span id="upload-btn-text">Ingest & Vectorize</span>
          </button>
        </div>
        <div id="upload-message" class="hidden mt-2 text-xs p-2 rounded"></div>
      </div>

      <!-- Ingested Documents List Card -->
      <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 shadow-sm flex-1 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h2 class="text-sm font-semibold text-white flex items-center gap-2">
              <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
              Indexed Documents
            </h2>
            <p class="text-[11px] text-slate-400">Select documents to scope your query, or leave all checked.</p>
          </div>
          <button id="refresh-docs-btn" title="Refresh list" class="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          </button>
        </div>

        <!-- Filter bar -->
        <div class="flex items-center justify-between text-xs py-1 border-b border-slate-800 mb-2">
          <div class="flex items-center gap-2">
            <input type="checkbox" id="select-all-checkbox" checked class="rounded bg-slate-900 border-slate-700 text-emerald-600 focus:ring-emerald-500">
            <label for="select-all-checkbox" class="text-slate-400 text-xs cursor-pointer select-none">Select All</label>
          </div>
          <span id="doc-count-badge" class="text-[11px] font-mono text-slate-500">0 documents</span>
        </div>

        <!-- Document List Container -->
        <div id="documents-container" class="space-y-2 overflow-y-auto max-h-[380px] pr-1">
          <div class="text-center py-8 text-xs text-slate-500">
            Loading indexed documents...
          </div>
        </div>
      </div>

    </section>

    <!-- Right Column: Query & Analysis Console (7 cols) -->
    <section class="lg:col-span-7 flex flex-col space-y-5">

      <!-- Query Input Card -->
      <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 shadow-sm">
        <h2 class="text-sm font-semibold text-white mb-2 flex items-center gap-2">
          <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
          Ask Document Agent
        </h2>

        <!-- Example Chips -->
        <div class="mb-3 flex flex-wrap gap-1.5">
          <span class="text-[11px] text-slate-500 self-center mr-1">Examples:</span>
          <button class="example-chip text-[11px] bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-full transition cursor-pointer"
                  data-prompt="What is the document about?">
            What is it about?
          </button>
          <button class="example-chip text-[11px] bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-full transition cursor-pointer"
                  data-prompt="Extract the vendor name and amount, then compare the payment terms against the policy.">
            Quote vs. Policy Comparison
          </button>
          <button class="example-chip text-[11px] bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-full transition cursor-pointer"
                  data-prompt="Extract vendor name, total quote amount, and payment terms from the vendor quotation.">
            Extract Quote Fields
          </button>
          <button class="example-chip text-[11px] bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-full transition cursor-pointer"
                  data-prompt="Verify if the payment terms comply with the corporate procurement requirement of payment within 30 days.">
            Validate Compliance
          </button>
        </div>

        <textarea id="query-input" rows="3" class="w-full bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition resize-none" placeholder="Enter your question or task (e.g. Extract key terms, compare values, or validate policies)..."></textarea>

        <div class="mt-3 flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-800/80">
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-1.5">
              <label for="top-k-slider" class="text-xs text-slate-400">Top-K:</label>
              <input type="range" id="top-k-slider" min="1" max="15" value="5" class="w-16 accent-emerald-500 cursor-pointer">
              <span id="top-k-val" class="text-xs font-mono text-emerald-400">5</span>
            </div>
            <div class="flex items-center gap-1.5">
              <label for="threshold-slider" class="text-xs text-slate-400">Cutoff:</label>
              <input type="range" id="threshold-slider" min="0.05" max="0.60" step="0.05" value="0.20" class="w-16 accent-emerald-500 cursor-pointer">
              <span id="threshold-val" class="text-xs font-mono text-emerald-400">0.20</span>
            </div>
            <span id="query-scope-indicator" class="text-[11px] text-slate-500 font-mono">Scope: All Documents</span>
          </div>

          <button id="run-query-btn" class="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium text-xs py-2 px-5 rounded-lg transition flex items-center gap-2 shadow-sm">
            <svg id="query-spinner" class="hidden animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
            <span id="query-btn-text">Execute Agent Workflow</span>
          </button>
        </div>
      </div>

      <!-- Agent Results & Visual Inspection -->
      <div id="results-card" class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 shadow-sm flex-1 space-y-4">

        <!-- Placeholder before first query -->
        <div id="results-placeholder" class="text-center py-16 flex flex-col items-center justify-center space-y-3">
          <div class="p-3 bg-slate-900 rounded-full border border-slate-800 text-slate-600">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
          </div>
          <p class="text-xs text-slate-400 font-medium">Ready for Document Analysis</p>
          <p class="text-[11px] text-slate-500 max-w-sm">Type a query or pick an example prompt above to run LangGraph stateful analysis with citation provenance.</p>
        </div>

        <!-- Populated Results Container (hidden by default) -->
        <div id="results-content" class="hidden space-y-4">

          <!-- Summary Header -->
          <div class="p-4 rounded-lg bg-slate-900/90 border border-slate-800">
            <div class="flex items-center justify-between mb-2">
              <span id="res-status-badge" class="px-2 py-0.5 rounded text-[11px] font-mono font-semibold uppercase tracking-wider"></span>
              <div class="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                <span id="res-request-id"></span>
                <span>•</span>
                <span id="res-duration"></span>
              </div>
            </div>
            <div id="res-summary" class="text-xs text-slate-200 leading-relaxed font-normal"></div>
          </div>

          <!-- Structured Extracted Data -->
          <div id="section-extracted" class="space-y-2">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
              Extracted Structured Entities
            </h3>
            <div id="extracted-fields-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-2"></div>
          </div>

          <!-- Rule Validations -->
          <div id="section-validation" class="space-y-2">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              Compliance & Policy Validation
            </h3>
            <div id="validation-rules-list" class="space-y-1.5"></div>
          </div>

          <!-- Grounded Sources / Citations -->
          <div id="section-sources" class="space-y-2">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              Grounded Source Citations (100% Provenance)
            </h3>
            <div id="sources-list" class="space-y-2"></div>
          </div>

          <!-- Execution Trace & Tool Timeline -->
          <div id="section-trace" class="border-t border-slate-800 pt-3">
            <details class="group">
              <summary class="text-xs text-slate-400 hover:text-slate-200 cursor-pointer select-none flex items-center justify-between">
                <span class="flex items-center gap-1.5 font-medium">
                  <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                  LangGraph Execution Trace & Tool Pipeline
                </span>
                <span class="text-[11px] text-slate-500 group-open:rotate-180 transition transform">▼</span>
              </summary>
              <div class="mt-3 space-y-3 text-xs bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                <div>
                  <div class="text-[11px] text-slate-500 uppercase tracking-wider mb-1.5">Completed Graph Steps</div>
                  <div id="workflow-steps" class="flex flex-wrap gap-1.5"></div>
                </div>
                <div>
                  <div class="text-[11px] text-slate-500 uppercase tracking-wider mb-1.5">Tool Invocations</div>
                  <div id="workflow-tools" class="space-y-1"></div>
                </div>
                <div>
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-[11px] text-slate-500 uppercase tracking-wider">Raw JSON Response</span>
                    <button id="copy-json-btn" class="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 transition">Copy</button>
                  </div>
                  <pre id="raw-json" class="p-2.5 bg-slate-950 rounded text-[11px] text-slate-300 max-h-48 overflow-y-auto"></pre>
                </div>
              </div>
            </details>
          </div>

        </div>
      </div>

    </section>

  </main>

  <!-- Client-side Logic -->
  <script>
    let activeDocuments = [];
    let selectedDocIds = new Set();
    let currentRawResponse = null;

    // Element References
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');
    const statusPing = document.getElementById('status-ping');

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const selectedFileLabel = document.getElementById('selected-file-label');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadSpinner = document.getElementById('upload-spinner');
    const uploadBtnText = document.getElementById('upload-btn-text');
    const uploadMessage = document.getElementById('upload-message');

    const documentsContainer = document.getElementById('documents-container');
    const docCountBadge = document.getElementById('doc-count-badge');
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const refreshDocsBtn = document.getElementById('refresh-docs-btn');

    const queryInput = document.getElementById('query-input');
    const topKSlider = document.getElementById('top-k-slider');
    const topKVal = document.getElementById('top-k-val');
    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdVal = document.getElementById('threshold-val');
    const queryScopeIndicator = document.getElementById('query-scope-indicator');
    const runQueryBtn = document.getElementById('run-query-btn');
    const querySpinner = document.getElementById('query-spinner');
    const queryBtnText = document.getElementById('query-btn-text');

    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsContent = document.getElementById('results-content');
    const resStatusBadge = document.getElementById('res-status-badge');
    const resRequestId = document.getElementById('res-request-id');
    const resDuration = document.getElementById('res-duration');
    const resSummary = document.getElementById('res-summary');
    const extractedFieldsGrid = document.getElementById('extracted-fields-grid');
    const validationRulesList = document.getElementById('validation-rules-list');
    const sourcesList = document.getElementById('sources-list');
    const workflowSteps = document.getElementById('workflow-steps');
    const workflowTools = document.getElementById('workflow-tools');
    const rawJson = document.getElementById('raw-json');
    const copyJsonBtn = document.getElementById('copy-json-btn');

    // 1. Health & Readiness Check
    async function checkHealth() {
      try {
        const res = await fetch('/ready');
        if (res.ok) {
          const data = await res.json();
          statusDot.className = 'w-2 h-2 rounded-full bg-emerald-400';
          statusPing.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-ping';
          statusText.textContent = `Online (${data.dependencies?.embedding_provider || 'ready'})`;
        } else {
          statusDot.className = 'w-2 h-2 rounded-full bg-amber-400';
          statusPing.className = 'hidden';
          statusText.textContent = 'Degraded (DB check)';
        }
      } catch (err) {
        statusDot.className = 'w-2 h-2 rounded-full bg-red-400';
        statusPing.className = 'hidden';
        statusText.textContent = 'Offline';
      }
    }

    // 2. Fetch & Render Documents
    async function loadDocuments() {
      try {
        const res = await fetch('/documents?limit=100');
        if (!res.ok) throw new Error('Failed to load documents');
        const data = await res.json();
        activeDocuments = data.items || [];
        docCountBadge.textContent = `${activeDocuments.length} document${activeDocuments.length === 1 ? '' : 's'}`;

        // Reset selected doc IDs to include all loaded docs
        selectedDocIds = new Set(activeDocuments.map(d => d.document_id));
        selectAllCheckbox.checked = true;
        renderDocumentList();
        updateScopeIndicator();
      } catch (err) {
        documentsContainer.innerHTML = `<div class="p-3 text-xs text-red-400 bg-red-950/20 border border-red-900/40 rounded">Error loading documents: ${err.message}</div>`;
      }
    }

    function renderDocumentList() {
      if (activeDocuments.length === 0) {
        documentsContainer.innerHTML = `
          <div class="text-center py-8 text-xs text-slate-500">
            No documents indexed yet. Upload a PDF, TXT, or MD file above!
          </div>`;
        return;
      }

      documentsContainer.innerHTML = activeDocuments.map(doc => {
        const isChecked = selectedDocIds.has(doc.document_id);
        const statusColors = {
          completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
          processing: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
          failed: 'bg-red-500/10 text-red-400 border-red-500/20'
        };
        const badgeColor = statusColors[doc.status] || 'bg-slate-800 text-slate-400 border-slate-700';

        return `
          <div class="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 rounded-lg transition flex items-center justify-between gap-3 group">
            <div class="flex items-center gap-3 overflow-hidden">
              <input type="checkbox" data-id="${doc.document_id}" ${isChecked ? 'checked' : ''} class="doc-checkbox rounded bg-slate-950 border-slate-700 text-emerald-600 focus:ring-emerald-500">
              <div class="overflow-hidden">
                <div class="text-xs font-medium text-slate-200 truncate flex items-center gap-1.5" title="${doc.filename}">
                  <span>${doc.filename}</span>
                </div>
                <div class="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                  <span>${doc.page_count} page${doc.page_count === 1 ? '' : 's'}</span>
                  <span>•</span>
                  <span>${doc.chunk_count} chunk${doc.chunk_count === 1 ? '' : 's'}</span>
                  <span>•</span>
                  <span class="px-1.5 py-0.2 rounded border text-[10px] ${badgeColor}">${doc.status}</span>
                </div>
              </div>
            </div>

            <button data-delete-id="${doc.document_id}" title="Delete document" class="delete-doc-btn opacity-0 group-hover:opacity-100 p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/30 rounded transition">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        `;
      }).join('');

      // Wire checkboxes
      document.querySelectorAll('.doc-checkbox').forEach(cb => {
        cb.addEventListener('change', (e) => {
          const id = e.target.getAttribute('data-id');
          if (e.target.checked) selectedDocIds.add(id);
          else selectedDocIds.delete(id);
          selectAllCheckbox.checked = selectedDocIds.size === activeDocuments.length;
          updateScopeIndicator();
        });
      });

      // Wire delete buttons
      document.querySelectorAll('.delete-doc-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          const id = btn.getAttribute('data-delete-id');
          if (confirm('Delete this document and all its indexed chunks?')) {
            try {
              const res = await fetch(`/documents/${id}`, { method: 'DELETE' });
              if (res.ok) {
                await loadDocuments();
              } else {
                alert('Failed to delete document');
              }
            } catch (err) {
              alert('Delete error: ' + err.message);
            }
          }
        });
      });
    }

    function updateScopeIndicator() {
      if (selectedDocIds.size === activeDocuments.length || activeDocuments.length === 0) {
        queryScopeIndicator.textContent = 'Scope: All Documents';
      } else if (selectedDocIds.size === 0) {
        queryScopeIndicator.textContent = 'Scope: None (Select ≥1 doc)';
      } else {
        queryScopeIndicator.textContent = `Scope: ${selectedDocIds.size} Selected`;
      }
    }

    selectAllCheckbox.addEventListener('change', (e) => {
      if (e.target.checked) {
        selectedDocIds = new Set(activeDocuments.map(d => d.document_id));
      } else {
        selectedDocIds.clear();
      }
      renderDocumentList();
      updateScopeIndicator();
    });

    refreshDocsBtn.addEventListener('click', loadDocuments);

    // 3. Upload File Handlers
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('border-emerald-500', 'bg-slate-900/80');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-emerald-500', 'bg-slate-900/80');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-emerald-500', 'bg-slate-900/80');
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
      }
    });

    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect() {
      if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        selectedFileLabel.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        uploadBtn.disabled = false;
        uploadMessage.classList.add('hidden');
      } else {
        selectedFileLabel.textContent = 'No file selected';
        uploadBtn.disabled = true;
      }
    }

    uploadBtn.addEventListener('click', async () => {
      if (!fileInput.files.length) return;
      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append('file', file);

      uploadBtn.disabled = true;
      uploadSpinner.classList.remove('hidden');
      uploadBtnText.textContent = 'Processing...';
      uploadMessage.classList.add('hidden');

      try {
        const res = await fetch('/documents', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (res.ok) {
          uploadMessage.className = 'mt-2 text-xs p-2.5 rounded bg-emerald-950/40 border border-emerald-800 text-emerald-300';
          uploadMessage.textContent = `✓ Ingested "${data.filename}" (${data.page_count} pages, ${data.chunk_count} chunks indexed).`;
          uploadMessage.classList.remove('hidden');
          fileInput.value = '';
          selectedFileLabel.textContent = 'No file selected';
          await loadDocuments();
        } else {
          throw new Error(data.error?.message || 'Failed to ingest file');
        }
      } catch (err) {
        uploadMessage.className = 'mt-2 text-xs p-2.5 rounded bg-red-950/40 border border-red-800 text-red-300';
        uploadMessage.textContent = `✗ Upload failed: ${err.message}`;
        uploadMessage.classList.remove('hidden');
      } finally {
        uploadBtn.disabled = false;
        uploadSpinner.classList.add('hidden');
        uploadBtnText.textContent = 'Ingest & Vectorize';
      }
    });

    // 4. Query Controls & Execution
    topKSlider.addEventListener('input', (e) => {
      topKVal.textContent = e.target.value;
    });

    thresholdSlider.addEventListener('input', (e) => {
      thresholdVal.textContent = parseFloat(e.target.value).toFixed(2);
    });

    document.querySelectorAll('.example-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        queryInput.value = chip.getAttribute('data-prompt');
        queryInput.focus();
      });
    });

    runQueryBtn.addEventListener('click', executeQuery);

    async function executeQuery() {
      const query = queryInput.value.trim();
      if (!query) {
        alert('Please enter a query or prompt.');
        return;
      }

      const top_k = parseInt(topKSlider.value, 10) || 5;
      const cutoff = parseFloat(thresholdSlider.value) || 0.20;
      const payload = {
        query: query,
        top_k: top_k,
        relevance_threshold: cutoff
      };

      // If subset of documents selected, pass document_ids
      if (selectedDocIds.size > 0 && selectedDocIds.size < activeDocuments.length) {
        payload.document_ids = Array.from(selectedDocIds);
      }

      runQueryBtn.disabled = true;
      querySpinner.classList.remove('hidden');
      queryBtnText.textContent = 'Analyzing...';

      try {
        const res = await fetch('/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
          renderQueryResults(data);
        } else {
          throw new Error(data.error?.message || 'Query execution failed');
        }
      } catch (err) {
        alert('Query Error: ' + err.message);
      } finally {
        runQueryBtn.disabled = false;
        querySpinner.classList.add('hidden');
        queryBtnText.textContent = 'Execute Agent Workflow';
      }
    }

    // 5. Render Agent Results
    function renderQueryResults(data) {
      currentRawResponse = data;
      resultsPlaceholder.classList.add('hidden');
      resultsContent.classList.remove('hidden');

      // Status Badge
      const statusMap = {
        completed: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
        completed_with_warnings: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
        no_evidence: { bg: 'bg-slate-800', text: 'text-slate-400', border: 'border-slate-700' },
        failed: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' }
      };
      const sc = statusMap[data.status] || { bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };
      resStatusBadge.className = `px-2 py-0.5 rounded text-[11px] font-mono font-semibold uppercase tracking-wider border ${sc.bg} ${sc.text} ${sc.border}`;
      resStatusBadge.textContent = data.status.replace(/_/g, ' ');

      resRequestId.textContent = data.request_id || '';
      resDuration.textContent = data.workflow?.duration_ms ? `${data.workflow.duration_ms} ms` : '';

      // Format summary with Markdown rendering and clickable citation pills
      const rawText = data.summary || 'No summary generated.';
      let htmlContent = rawText;
      if (typeof marked !== 'undefined') {
        try {
          marked.setOptions({ breaks: true, gfm: true });
          htmlContent = marked.parse(rawText);
        } catch (e) {
          console.error('Markdown parse error:', e);
          htmlContent = rawText;
        }
      }
      const formattedSummary = htmlContent.replace(/\[(src_[a-zA-Z0-9_\-]+)\]/g, (match, srcId) => {
        return `<button onclick="scrollToSource('${srcId}')" class="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded hover:bg-emerald-500/20 transition mx-0.5 inline-block cursor-pointer">[${srcId}]</button>`;
      });
      resSummary.innerHTML = formattedSummary;

      // Render Extracted Fields
      const extractedEntries = Object.entries(data.extracted_data || {});
      const extractedSection = document.getElementById('section-extracted');
      if (extractedEntries.length === 0) {
        extractedSection.classList.add('hidden');
      } else {
        extractedSection.classList.remove('hidden');
        extractedFieldsGrid.innerHTML = extractedEntries.map(([key, item]) => {
          const valDisplay = item.value !== null ? item.value : '<span class="text-slate-500 italic">None</span>';
          const unitDisplay = item.unit ? `<span class="text-slate-400 text-[10px] ml-1">(${item.unit})</span>` : '';
          const sources = (item.sources || []).map(src =>
            `<button onclick="scrollToSource('${src}')" class="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded hover:bg-emerald-500/20 transition">[${src}]</button>`
          ).join(' ');

          return `
            <div class="p-3 bg-slate-900 border border-slate-800 rounded-lg">
              <div class="text-[11px] font-mono text-slate-400 capitalize mb-1">${key.replace(/_/g, ' ')}</div>
              <div class="text-sm font-semibold text-slate-100 flex items-center">
                <span>${valDisplay}</span>
                ${unitDisplay}
              </div>
              <div class="mt-2 flex items-center justify-between text-[10px] pt-1.5 border-t border-slate-800/80">
                <span class="text-slate-500">Status: <span class="text-slate-300">${item.status}</span></span>
                <div class="flex items-center gap-1">${sources}</div>
              </div>
            </div>
          `;
        }).join('');
      }

      // Render Validation Results
      const valResults = data.validation_results || [];
      const valSection = document.getElementById('section-validation');
      if (valResults.length === 0) {
        valSection.classList.add('hidden');
      } else {
        valSection.classList.remove('hidden');
        validationRulesList.innerHTML = valResults.map(vr => {
          const isPass = vr.status === 'passed';
          const badgeClass = isPass
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : 'bg-red-500/10 text-red-400 border-red-500/30';
          const sources = (vr.sources || []).map(src =>
            `<button onclick="scrollToSource('${src}')" class="text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700 px-1.5 py-0.2 rounded hover:text-white transition">[${src}]</button>`
          ).join(' ');

          return `
            <div class="p-3 bg-slate-900 border border-slate-800 rounded-lg flex flex-col gap-1.5">
              <div class="flex items-center justify-between">
                <span class="text-xs font-mono font-medium text-slate-300">${vr.rule_id}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${badgeClass}">
                  ${vr.status}
                </span>
              </div>
              <p class="text-xs text-slate-300 font-normal leading-relaxed">${vr.message}</p>
              ${sources ? `<div class="mt-1 flex items-center gap-1 text-[11px] text-slate-500">Sources: ${sources}</div>` : ''}
            </div>
          `;
        }).join('');
      }

      // Render Grounded Sources / Citations
      const sources = data.sources || [];
      const sourcesSection = document.getElementById('section-sources');
      if (sources.length === 0) {
        sourcesSection.classList.add('hidden');
      } else {
        sourcesSection.classList.remove('hidden');
        sourcesList.innerHTML = sources.map(src => {
          const pct = Math.round((src.similarity_score || 0) * 100);
          return `
            <div id="source-${src.source_id}" class="p-3.5 bg-slate-900/90 border border-slate-800 rounded-lg space-y-2 transition">
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  <span class="font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-[11px]">
                    ${src.source_id}
                  </span>
                  <span class="text-slate-200 font-medium">${src.document_name}</span>
                  <span class="text-slate-400 text-[11px]">• Page ${src.page}</span>
                </div>
                <div class="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono">
                  <span>Score:</span>
                  <span class="text-emerald-400 font-bold">${src.similarity_score?.toFixed(4) || 'N/A'}</span>
                </div>
              </div>
              <div class="p-2.5 bg-slate-950/80 rounded border border-slate-800/80 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
"${src.excerpt}"
              </div>
            </div>
          `;
        }).join('');
      }

      // Render Workflow Steps
      const steps = data.workflow?.steps_completed || [];
      workflowSteps.innerHTML = steps.map((s, idx) => `
        <span class="px-2 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px] font-mono flex items-center gap-1.5">
          <span class="text-emerald-400 font-bold">${idx + 1}.</span> ${s}
        </span>
      `).join('');

      // Render Tool Calls
      const tools = data.workflow?.tool_calls || [];
      if (tools.length === 0) {
        workflowTools.innerHTML = '<span class="text-slate-500 text-[11px]">No tools called.</span>';
      } else {
        workflowTools.innerHTML = tools.map(t => `
          <div class="flex items-center justify-between p-1.5 rounded bg-slate-950/60 border border-slate-800 text-[11px] font-mono">
            <span class="text-slate-300">${t.tool_name}</span>
            <div class="flex items-center gap-2 text-slate-400">
              <span class="text-emerald-400">${t.status}</span>
              <span>•</span>
              <span>${t.duration_ms} ms</span>
            </div>
          </div>
        `).join('');
      }

      // Raw JSON
      rawJson.textContent = JSON.stringify(data, null, 2);
    }

    // Scroll to source card & flash outline
    function scrollToSource(sourceId) {
      const el = document.getElementById(`source-${sourceId}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('source-highlight');
        setTimeout(() => el.classList.remove('source-highlight'), 3000);
      }
    }

    copyJsonBtn.addEventListener('click', () => {
      if (currentRawResponse) {
        navigator.clipboard.writeText(JSON.stringify(currentRawResponse, null, 2));
        copyJsonBtn.textContent = 'Copied!';
        setTimeout(() => copyJsonBtn.textContent = 'Copy', 1500);
      }
    });

    // Initial Load
    checkHealth();
    loadDocuments();
    setInterval(checkHealth, 15000);
  </script>
</body>
</html>
"""


@router.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
    summary="Document Processing Web Dashboard",
)
async def serve_ui() -> HTMLResponse:
    """Serves the interactive single-page application dashboard."""
    return HTMLResponse(content=UI_HTML)


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
    summary="Document Processing Web Dashboard Alias",
)
async def serve_ui_alias() -> HTMLResponse:
    """Alias for root dashboard UI."""
    return HTMLResponse(content=UI_HTML)
