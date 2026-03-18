# Filesystem Organization Application — Specification

Copyright 2026 by GuidoGerb Publishing, LLC

## 1. Overview

A NAS-scale filesystem cataloging application that indexes every file, classifies
content by type and purpose, generates SHA-256 checksums, builds a hierarchical
tag system, tracks file versions, detects duplicates, and exposes all operations
through a suite of MCP (Model Context Protocol) servers. AI inference runs locally
on an NVIDIA RTX 4090 (24 GB VRAM).

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Client (AI Agent)                       │
│   Claude Desktop / VS Code Copilot / Custom Agent               │
└─────────┬───────────┬───────────┬───────────┬───────────┬───────┘
          │           │           │           │           │
     stdio/http  stdio/http  stdio/http  stdio/http  stdio/http
          │           │           │           │           │
┌─────────▼──┐ ┌──────▼─────┐ ┌──▼────────┐ ┌▼─────────┐ ┌▼──────────┐
│ fs-scanner │ │ fs-tagger  │ │ fs-catalog │ │ fs-search │ │ fs-ai     │
│   Server   │ │   Server   │ │   Server   │ │  Server   │ │  Server   │
└─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └────┬─────┘ └─────┬─────┘
      │              │              │              │             │
      │              │              ▼              │             ▼
      │              │     ┌────────────────┐     │    ┌─────────────────┐
      └──────────────┴────►│  PostgreSQL DB  │◄───┘    │ Local Inference │
                           │  (file_catalog) │         │  NVIDIA 4090    │
                           └────────────────┘          │  (Ollama/vLLM)  │
                                                       └─────────────────┘
```

### Deployment Targets

| Mode       | Transport | PostgreSQL        | Inference        |
|------------|-----------|-------------------|------------------|
| Local dev  | stdio     | Docker :5433      | Ollama localhost |
| Home NAS   | HTTP      | Docker/native PG  | 4090 local       |
| AWS prod   | Lambda    | RDS PostgreSQL    | —                |

---

## 3. Database Schema

Database: `file_catalog` (PostgreSQL 16)

### 3.1 `file_entry` — Every file on the filesystem

```sql
CREATE TABLE file_entry (
    id              BIGSERIAL       PRIMARY KEY,
    path            TEXT            NOT NULL,
    filename        TEXT            NOT NULL,
    extension       VARCHAR(32)     NOT NULL DEFAULT '',
    mime_type       VARCHAR(128)    NOT NULL DEFAULT 'application/octet-stream',
    size_bytes      BIGINT          NOT NULL,
    sha256          VARCHAR(64)     NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    modified_at     TIMESTAMPTZ     NOT NULL,
    indexed_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    is_duplicate    BOOLEAN         NOT NULL DEFAULT FALSE,
    duplicate_of    BIGINT          REFERENCES file_entry(id),
    UNIQUE (path)
);

CREATE INDEX idx_file_entry_sha256 ON file_entry (sha256);
CREATE INDEX idx_file_entry_extension ON file_entry (extension);
CREATE INDEX idx_file_entry_mime_type ON file_entry (mime_type);
CREATE INDEX idx_file_entry_path_trgm ON file_entry USING gin (path gin_trgm_ops);
```

### 3.2 `file_version` — Version tracking per file

```sql
CREATE TABLE file_version (
    id              BIGSERIAL       PRIMARY KEY,
    file_id         BIGINT          NOT NULL REFERENCES file_entry(id) ON DELETE CASCADE,
    version_number  INTEGER         NOT NULL,
    sha256          VARCHAR(64)     NOT NULL,
    size_bytes      BIGINT          NOT NULL,
    snapshot_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    change_type     VARCHAR(16)     NOT NULL DEFAULT 'modified',
        -- 'created', 'modified', 'renamed', 'deleted'
    previous_path   TEXT,
    UNIQUE (file_id, version_number)
);

CREATE INDEX idx_file_version_file_id ON file_version (file_id);
```

### 3.3 `tag_group` — Categories of tags

```sql
CREATE TABLE tag_group (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(256)    NOT NULL UNIQUE,
    description     TEXT            NOT NULL DEFAULT '',
    source          VARCHAR(64)     NOT NULL DEFAULT 'system',
        -- 'system' (auto-generated), 'ai' (model-inferred), 'user' (manual)
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
```

### 3.4 `tag` — Individual tags within groups

```sql
CREATE TABLE tag (
    id              SERIAL          PRIMARY KEY,
    tag_group_id    INTEGER         NOT NULL REFERENCES tag_group(id) ON DELETE CASCADE,
    name            VARCHAR(256)    NOT NULL,
    description     TEXT            NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (tag_group_id, name)
);

CREATE INDEX idx_tag_group ON tag (tag_group_id);
```

### 3.5 `file_tag` — Many-to-many: files ↔ tags

```sql
CREATE TABLE file_tag (
    file_id         BIGINT          NOT NULL REFERENCES file_entry(id) ON DELETE CASCADE,
    tag_id          INTEGER         NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    confidence      REAL            NOT NULL DEFAULT 1.0,
        -- 1.0 = deterministic, <1.0 = AI-inferred probability
    source          VARCHAR(64)     NOT NULL DEFAULT 'system',
        -- 'system', 'ai:<model_name>', 'user'
    assigned_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (file_id, tag_id)
);

CREATE INDEX idx_file_tag_tag ON file_tag (tag_id);
```

### 3.6 `mime_type_registry` — Known MIME types with tag group mappings

```sql
CREATE TABLE mime_type_registry (
    id              SERIAL          PRIMARY KEY,
    mime_type       VARCHAR(128)    NOT NULL UNIQUE,
    extension       VARCHAR(32)     NOT NULL,
    category        VARCHAR(64)     NOT NULL,
        -- 'document', 'image', 'video', 'audio', 'code', 'archive',
        -- 'data', 'executable', 'font', 'model-weight', '3d-model', 'other'
    tag_group_id    INTEGER         REFERENCES tag_group(id),
    description     TEXT            NOT NULL DEFAULT '',
    is_binary       BOOLEAN         NOT NULL DEFAULT TRUE
);
```

### 3.7 `scan_job` — Audit trail for scan operations

```sql
CREATE TABLE scan_job (
    id              BIGSERIAL       PRIMARY KEY,
    root_path       TEXT            NOT NULL,
    status          VARCHAR(16)     NOT NULL DEFAULT 'running',
        -- 'running', 'completed', 'failed', 'cancelled'
    files_found     BIGINT          NOT NULL DEFAULT 0,
    files_new       BIGINT          NOT NULL DEFAULT 0,
    files_modified  BIGINT          NOT NULL DEFAULT 0,
    files_deleted   BIGINT          NOT NULL DEFAULT 0,
    duplicates_found BIGINT         NOT NULL DEFAULT 0,
    errors          INTEGER         NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
```

### 3.8 `ai_analysis` — AI model inference results cached per file

```sql
CREATE TABLE ai_analysis (
    id              BIGSERIAL       PRIMARY KEY,
    file_id         BIGINT          NOT NULL REFERENCES file_entry(id) ON DELETE CASCADE,
    model_name      VARCHAR(256)    NOT NULL,
    analysis_type   VARCHAR(64)     NOT NULL,
        -- 'classification', 'description', 'ocr', 'transcription',
        -- 'code-summary', 'embedding', 'content-tags'
    result_json     JSONB           NOT NULL,
    confidence      REAL,
    analyzed_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (file_id, model_name, analysis_type)
);

CREATE INDEX idx_ai_analysis_file ON ai_analysis (file_id);
CREATE INDEX idx_ai_analysis_type ON ai_analysis (analysis_type);
```

### 3.9 `file_embedding` — Vector embeddings for semantic search

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE file_embedding (
    id              BIGSERIAL       PRIMARY KEY,
    file_id         BIGINT          NOT NULL REFERENCES file_entry(id) ON DELETE CASCADE,
    model_name      VARCHAR(256)    NOT NULL,
    embedding       vector(768)     NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (file_id, model_name)
);

CREATE INDEX idx_file_embedding_vector ON file_embedding
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 4. MCP Servers

### 4.1 `fs-scanner` — Filesystem Scanning & Indexing

**Purpose:** Walk directory trees, compute SHA-256 hashes, detect MIME types,
identify duplicates, track file modifications, and record scan jobs.

#### Tools

| Tool                    | Parameters                                        | Description                                           |
|-------------------------|---------------------------------------------------|-------------------------------------------------------|
| `scan_directory`        | `path`, `recursive=true`, `follow_symlinks=false` | Full scan of a directory tree; creates a `scan_job`   |
| `scan_file`             | `path`                                            | Index a single file (hash, MIME, size, timestamps)    |
| `compute_sha256`        | `path`                                            | Return SHA-256 of a single file                       |
| `detect_mime_type`      | `path`                                            | Return MIME type using magic bytes + extension        |
| `find_duplicates`       | `path=null`, `sha256=null`                        | Find files with identical hashes (optional scope)     |
| `diff_snapshot`         | `path`, `since=null`                              | Compare current FS state vs last indexed snapshot     |
| `get_scan_status`       | `job_id`                                          | Get progress/status of a running scan job             |
| `cancel_scan`           | `job_id`                                          | Cancel a running scan                                 |

#### Resources

| URI                         | Description                              |
|-----------------------------|------------------------------------------|
| `scan://jobs`               | List of all scan jobs                    |
| `scan://jobs/{id}`          | Details of a specific scan job           |
| `scan://stats`              | Global stats (total files, size, dupes) |

---

### 4.2 `fs-tagger` — Tag Management & Auto-Tagging

**Purpose:** Manage the tag taxonomy — create/merge/rename tag groups and tags,
auto-tag files by extension/MIME type, and apply AI-inferred tags.

#### Tools

| Tool                      | Parameters                                 | Description                                          |
|---------------------------|--------------------------------------------|------------------------------------------------------|
| `create_tag_group`        | `name`, `description=''`                   | Create a new tag group                               |
| `create_tag`              | `tag_group`, `name`, `description=''`      | Create a tag within a group                          |
| `rename_tag`              | `tag_id`, `new_name`                       | Rename an existing tag                               |
| `merge_tags`              | `source_tag_id`, `target_tag_id`           | Merge source into target, reassign all files         |
| `delete_tag`              | `tag_id`                                   | Remove a tag and all file associations               |
| `tag_file`                | `file_id`, `tag_id`, `confidence=1.0`      | Apply a tag to a file                                |
| `untag_file`              | `file_id`, `tag_id`                        | Remove a tag from a file                             |
| `auto_tag_by_mime`        | `path=null`                                | Auto-tag all files by MIME type category             |
| `auto_tag_by_extension`   | `path=null`                                | Auto-tag all files by extension → tag group mapping  |
| `bulk_tag`                | `file_ids[]`, `tag_ids[]`                  | Batch tag multiple files                             |

#### Resources

| URI                         | Description                              |
|-----------------------------|------------------------------------------|
| `tags://groups`             | List all tag groups                      |
| `tags://groups/{id}`        | Tags within a group                      |
| `tags://file/{file_id}`     | All tags applied to a file               |
| `tags://stats`              | Tag distribution statistics              |

#### Prompts

| Prompt                    | Arguments                  | Description                                        |
|---------------------------|----------------------------|----------------------------------------------------|
| `suggest_tags`            | `file_id`                  | Suggest tags for a file based on its properties     |
| `suggest_tag_taxonomy`    | `root_path`                | Suggest a tag taxonomy for a directory tree          |

---

### 4.3 `fs-catalog` — File Catalog & Version Registry

**Purpose:** CRUD operations on the file catalog, version history, MIME type registry,
and reporting.

#### Tools

| Tool                       | Parameters                                  | Description                                        |
|----------------------------|---------------------------------------------|----------------------------------------------------|
| `get_file`                 | `file_id` or `path`                         | Get full file record with tags and versions        |
| `list_files`               | `path=null`, `mime=null`, `ext=null`, `limit=100`, `offset=0` | Query files with filters    |
| `get_versions`             | `file_id`                                   | List all versions of a file                        |
| `register_mime_type`       | `mime_type`, `extension`, `category`        | Add a MIME type to the registry                    |
| `list_mime_types`          | `category=null`                             | List registered MIME types                         |
| `get_file_stats`           | `path=null`                                 | Aggregate stats: count by type, size, duplicates   |
| `export_catalog`           | `path`, `format='json'`                     | Export catalog for a subtree as JSON or CSV        |
| `get_duplicates_report`    | `min_size=0`                                | Report all duplicate sets sorted by wasted space   |

#### Resources

| URI                          | Description                              |
|------------------------------|------------------------------------------|
| `catalog://summary`          | Global catalog summary                   |
| `catalog://mime-registry`    | Full MIME type registry                  |
| `catalog://tree/{path}`      | Hierarchical file tree with tag counts   |

---

### 4.4 `fs-search` — Search & Query Engine

**Purpose:** Full-text, semantic, and faceted search across the catalog.

#### Tools

| Tool                      | Parameters                                          | Description                                      |
|---------------------------|-----------------------------------------------------|--------------------------------------------------|
| `search_files`            | `query`, `scope='all'`, `limit=50`                  | Full-text search on path, filename, tags         |
| `search_by_tag`           | `tag_ids[]`, `op='AND'`, `limit=100`                | Find files matching tag combinations             |
| `search_by_sha256`        | `sha256`                                            | Find all files with a given hash                 |
| `search_by_size`          | `min_bytes=0`, `max_bytes=null`                     | Find files in a size range                       |
| `search_by_date`          | `after=null`, `before=null`, `date_field='modified'`| Find files by date range                         |
| `semantic_search`         | `query`, `limit=20`                                 | Vector similarity search using embeddings        |
| `find_similar`            | `file_id`, `limit=10`                               | Find files with similar embeddings               |
| `search_duplicates`       | `path=null`, `min_size=0`                           | Find duplicate files, optionally scoped          |

#### Resources

| URI                        | Description                              |
|----------------------------|------------------------------------------|
| `search://recent`          | Recently indexed files                   |
| `search://largest`         | Largest files in the catalog             |
| `search://orphan-tags`     | Tags not assigned to any file            |

---

### 4.5 `fs-ai` — AI Analysis & Classification

**Purpose:** Run local AI models (on NVIDIA 4090) to classify, describe,
tag, OCR, transcribe, and embed files.

#### Tools

| Tool                       | Parameters                               | Description                                         |
|----------------------------|------------------------------------------|-----------------------------------------------------|
| `classify_file`            | `file_id`, `model='auto'`               | Classify file content and suggest tags              |
| `describe_image`           | `file_id`, `model='auto'`               | Generate text description of an image               |
| `ocr_document`             | `file_id`, `model='auto'`               | Extract text from document/image via OCR            |
| `transcribe_audio`         | `file_id`, `model='auto'`               | Transcribe audio/video to text                      |
| `summarize_document`       | `file_id`, `model='auto'`, `max_tokens=512` | Generate summary of a text/PDF document        |
| `summarize_code`           | `file_id`, `model='auto'`               | Summarize purpose/structure of a code file          |
| `generate_embedding`       | `file_id`, `model='auto'`               | Generate vector embedding for semantic search       |
| `batch_analyze`            | `file_ids[]`, `analysis_type`           | Queue batch AI analysis on multiple files           |
| `auto_classify_directory`  | `path`, `recursive=true`                | AI-classify all un-analyzed files under a path      |
| `list_models`              |                                          | List available local models and their status        |

#### Resources

| URI                          | Description                              |
|------------------------------|------------------------------------------|
| `ai://models`               | Available models and GPU memory usage    |
| `ai://queue`                | Pending analysis jobs                    |
| `ai://analysis/{file_id}`   | Cached AI analysis results for a file    |

#### Prompts

| Prompt                      | Arguments                  | Description                                             |
|-----------------------------|----------------------------|---------------------------------------------------------|
| `analyze_directory`         | `path`, `depth='full'`     | Plan an AI analysis strategy for a directory            |
| `explain_file`              | `file_id`                  | Explain what a file is and how it should be categorized |
| `recommend_organization`    | `path`                     | Suggest a reorganization plan for a directory           |

---

## 5. AI Models for NVIDIA RTX 4090 (24 GB VRAM)

All models run locally via Ollama or vLLM. Selected to fit within 24 GB VRAM
with room for concurrent inference on smaller models.

### 5.1 File Classification & General Intelligence

| Model                              | VRAM   | Quantization | Purpose                                    |
|------------------------------------|--------|-------------|---------------------------------------------|
| `Qwen/Qwen3-8B`                   | ~6 GB  | Q4_K_M      | General file classification, tag suggestion |
| `huihui-ai/Huihui-Qwen3.5-4B-Claude-4.6-Opus-abliterated` | ~3 GB | Q4_K_M | Fast classification, second opinion |
| `LiquidAI/LFM2.5-1.2B-Instruct`  | ~1 GB  | FP16        | Ultra-fast triage for simple decisions      |

### 5.2 Vision & OCR (Image/Document Understanding)

| Model                              | VRAM   | Quantization | Purpose                                    |
|------------------------------------|--------|-------------|---------------------------------------------|
| `deepseek-ai/DeepSeek-OCR-2`      | ~8 GB  | Q4_K_M      | OCR on documents, scans, receipts, PDFs     |
| `zai-org/GLM-OCR`                 | ~8 GB  | Q4_K_M      | Secondary OCR, CJK document specialist      |
| `Qwen/Qwen2.5-VL-7B-Instruct`    | ~6 GB  | Q4_K_M      | Image description, visual classification    |

### 5.3 Code Understanding

| Model                              | VRAM   | Quantization | Purpose                                    |
|------------------------------------|--------|-------------|---------------------------------------------|
| `Qwen/Qwen3-Coder-8B`            | ~6 GB  | Q4_K_M      | Code file summarization, language detection |
| `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | ~3 GB | Q4_K_M | Fast code classification          |

### 5.4 Audio Transcription

| Model                              | VRAM   | Quantization | Purpose                                    |
|------------------------------------|--------|-------------|---------------------------------------------|
| `openai/whisper-large-v3-turbo`   | ~3 GB  | FP16        | Audio/video transcription                   |
| `openai/whisper-medium`           | ~1.5 GB| FP16        | Faster transcription for large batches      |

### 5.5 Embedding Models (for Semantic Search)

| Model                              | VRAM    | Dims | Purpose                                    |
|------------------------------------|---------|------|--------------------------------------------|
| `nomic-ai/nomic-embed-multimodal-3b` | ~2 GB | 768  | Multimodal embedding (images + text)       |
| `nomic-ai/nomic-embed-code`       | ~0.5 GB | 768  | Code file embedding                        |
| `nomic-ai/CodeRankEmbed`          | ~0.5 GB | 768  | Code ranking/retrieval embedding           |
| `sentence-transformers/all-MiniLM-L6-v2` | ~0.3 GB | 384 | Lightweight text embedding fallback  |

### 5.6 Multi-Model Orchestration Strategy

The fs-ai server uses a model selection strategy based on file type:

```
File detected → MIME category
  ├─ image/*          → Qwen2.5-VL-7B (describe) + nomic-embed-multimodal (embed)
  ├─ application/pdf  → DeepSeek-OCR-2 (OCR) + Qwen3-8B (summarize)
  ├─ text/plain       → Qwen3-8B (classify) + nomic-embed-multimodal (embed)
  ├─ text/x-*         → Qwen3-Coder-8B (summarize) + nomic-embed-code (embed)
  ├─ audio/*          → whisper-large-v3-turbo (transcribe) + Qwen3-8B (summarize)
  ├─ video/*          → whisper (audio track) + Qwen2.5-VL (keyframes)
  ├─ application/zip  → scan contents → recursively classify
  └─ other            → Qwen3-8B (classify from filename/extension)
```

**VRAM budget:** Peak usage ≤ 18 GB (largest model + embedding model concurrent),
leaving ~6 GB headroom for OS, CUDA context, and batch queuing.

---

## 6. System Tag Groups (Auto-Created)

The following tag groups are automatically created during initial setup:

| Tag Group               | Source  | Example Tags                                            |
|-------------------------|---------|--------------------------------------------------------|
| `file-type`             | system  | document, image, video, audio, code, archive, data     |
| `extension`             | system  | .py, .jpg, .pdf, .mp4, .zip, .csv, ...                |
| `mime-category`         | system  | text, image, audio, video, application, font, model    |
| `language`              | ai      | python, javascript, rust, html, css, sql, markdown     |
| `document-type`         | ai      | invoice, receipt, letter, report, manual, contract     |
| `image-content`         | ai      | photo, screenshot, diagram, chart, logo, icon, art     |
| `audio-type`            | ai      | speech, music, podcast, ambient, sound-effect          |
| `project`               | user    | (user-defined project associations)                     |
| `status`                | user    | reviewed, needs-review, archive, important, delete     |
| `content-rating`        | ai      | safe, sensitive, confidential, public                  |
| `quality`               | ai      | high-res, low-res, corrupted, incomplete               |
| `duplicate-status`      | system  | original, duplicate, near-duplicate                     |

---

## 7. Scan & Indexing Pipeline

### 7.1 Initial Full Scan

```
1. CREATE scan_job (root_path, status='running')
2. os.walk() → for each file:
   a. stat() → size, mtime, ctime
   b. SHA-256 (streaming, 8 MB chunks)
   c. MIME detection (python-magic + fallback to extension)
   d. INSERT file_entry (or UPDATE if path exists)
   e. INSERT file_version (version 1 or increment)
   f. Check sha256 duplicates → SET is_duplicate, duplicate_of
   g. Auto-tag by extension + MIME category
3. UPDATE scan_job (status='completed', counts)
```

### 7.2 Incremental Rescan

```
1. SELECT indexed_at, sha256 FROM file_entry WHERE path LIKE '{root}%'
2. os.walk() → compare mtime vs indexed_at
   - New files → full index
   - Modified (mtime > indexed_at) → re-hash, new version
   - Missing from FS → mark version as 'deleted'
3. Report diff summary
```

### 7.3 AI Analysis Pass (Post-Scan)

```
1. SELECT file_entry WHERE id NOT IN (SELECT file_id FROM ai_analysis)
2. Group by MIME category → select model chain
3. Queue → process files through appropriate models
4. Store results in ai_analysis + apply inferred tags to file_tag
5. Generate embeddings → store in file_embedding
```

---

## 8. MCP Server Implementation Map

Each server maps to a Python module under `mcp/servers/filesystem_org/`:

```
mcp/servers/filesystem_org/
├── __init__.py
├── fs_scanner.py          # fs-scanner MCP server
├── fs_tagger.py           # fs-tagger MCP server
├── fs_catalog.py          # fs-catalog MCP server
├── fs_search.py           # fs-search MCP server
├── fs_ai.py               # fs-ai MCP server
├── db.py                  # Shared PostgreSQL connection (mirrors blockchain/db.py pattern)
├── models.py              # Local model management (Ollama API client)
└── mime_registry.py       # MIME type detection and registry
```

### Server Registration in `run.py`

```
python run.py fsorg-scan      # Launch fs-scanner (stdio or --http)
python run.py fsorg-tag       # Launch fs-tagger
python run.py fsorg-catalog   # Launch fs-catalog
python run.py fsorg-search    # Launch fs-search
python run.py fsorg-ai        # Launch fs-ai
python run.py fsorg-all       # Launch all 5 servers on sequential HTTP ports
```

---

## 9. Docker Compose Extension

```yaml
services:
  file-catalog-db:
    image: pgvector/pgvector:pg16
    container_name: ggp-file-catalog
    environment:
      POSTGRES_USER: catalog
      POSTGRES_PASSWORD: ${FILE_CATALOG_DB_PASSWORD}
      POSTGRES_DB: file_catalog
    ports:
      - "5434:5432"
    volumes:
      - file_catalog_data:/var/lib/postgresql/data
      - ./resources/postgres-init/file-catalog:/docker-entrypoint-initdb.d:ro

  ollama:
    image: ollama/ollama:latest
    container_name: ggp-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  file_catalog_data:
  ollama_models:
```

---

## 10. Terraform (AWS Production)

For AWS deployment, the fs-scanner and fs-ai servers are not needed (no local
filesystem), but fs-catalog, fs-tagger, and fs-search deploy as Lambda functions
behind API Gateway:

```
infra/filesystem-org/
├── main.tf               # Provider, backend, tags
├── variables.tf          # Environment, DB, CORS
├── rds.tf                # RDS PostgreSQL + pgvector
├── lambda-catalog.tf     # fs-catalog Lambda
├── lambda-tagger.tf      # fs-tagger Lambda
├── lambda-search.tf      # fs-search Lambda
├── api-gateway.tf        # HTTP API with /catalog, /tags, /search routes
└── outputs.tf            # Endpoints, ARNs
```

---

## 11. Testing Strategy

```
tests/filesystem_org/
├── conftest.py                # Fixtures: in-memory DB, mock Ollama, temp FS trees
├── test_fs_scanner.py         # Scan tools, SHA-256, MIME detection, duplicates
├── test_fs_tagger.py          # Tag CRUD, auto-tagging, merge/rename
├── test_fs_catalog.py         # File queries, version history, MIME registry
├── test_fs_search.py          # Full-text, tag-based, semantic search
├── test_fs_ai.py              # Model selection, classify, OCR, embed (mocked)
├── test_db_schema.py          # Schema creation, constraints, indexes
└── test_mime_registry.py      # MIME detection accuracy, registry lookups
```

All tests use pytest with mocked PostgreSQL (or ephemeral Docker container)
and mocked Ollama API — no real GPU or filesystem access needed.

---

## 12. Security Considerations

- **Path traversal:** All file paths are resolved with `Path.resolve()` and validated
  against the configured NAS mount root. Symlinks outside root are rejected.
- **SQL injection:** All queries use parameterized statements via psycopg2 `%s` placeholders.
- **Large file DoS:** SHA-256 computed in 8 MB streaming chunks; scan jobs have
  configurable timeouts and file-count limits.
- **AI prompt injection:** File contents sent to models are sandboxed in system prompts
  that instruct classification only — no code execution or tool calls.
- **CORS:** HTTP transport uses strict origin whitelisting (no `*`).
- **Credentials:** Database passwords from environment variables, never in source.

---

## 13. Non-Goals (Explicitly Out of Scope)

- **File modification/deletion** — This is a read-only catalog. Moving/deleting
  files requires a separate application with explicit user confirmation.
- **Real-time FS monitoring** — Initial implementation uses poll-based rescans.
  inotify/fswatch integration is a future enhancement.
- **Cloud storage scanning** — S3/GCS/Azure Blob scanning is not included;
  this targets local NAS filesystems.
- **Training or fine-tuning** — AI models are used as-is for inference only.
