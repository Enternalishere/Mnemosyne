# Mnemosyne – Personal Knowledge Operating System

Mnemosyne is a time‑aware reasoning engine over your own memories.

It turns raw text (notes, chats, tweets, voice transcripts, PDFs) into
structured memory objects and then answers questions strictly based on
those memories, tracking how your beliefs evolve over time.

Core ideas:
- Memories are immutable and time‑stamped.
- Time is a first‑class dimension for reasoning.
- Belief evolution is explicit via revision chains.
- No hallucinated facts – answers come only from stored memories.

---

## Features

- **Memory ingestion pipeline**
  - Splits raw text into atomic beliefs/thoughts.
  - Assigns `memory_type`, `confidence`, `topic` keywords.
  - Links new memories to older ones via `revision_of`.
  - Detects contradictions between memories.

- **Time‑aware reasoning engine**
  - Answers questions using only provided memory objects.
  - Supports present, past (“as of YYYY‑MM‑DD”), and date ranges.
  - Surfaces belief evolution using `revision_of` chains.
  - Returns answers in a strict, structured format.

- **Persistent local store**
  - JSON‑backed memory store.
  - Topic and time‑range filters.
  - Snapshot support for versioned backups.

- **Higher‑level workflows**
  - Topic‑centric “thinking sessions” that summarize how your beliefs
    on a topic have changed.
  - Belief graph (nodes + edges) for visualization.
  - Time‑ordered timelines of memories per topic.

- **Interfaces**
  - Python API.
  - CLI for ingesting text and asking questions.
  - HTTP API (ideal for deploying to Hugging Face Spaces).
  - Minimal frontend dashboard (HTML/JS/CSS) suitable for Vercel.

---

## Project structure

- `mnemosyne_engine.py` – core time‑aware reasoning engine
- `memory_pipeline.py` – ingestion, belief extraction, revisions, contradictions
- `memory_store.py` – JSON memory store, filters, snapshots
- `mnemosyne_app.py` – CLI + high‑level orchestration helpers
- `api_server.py` – HTTP API server (ingest, answer, sessions, graph, timeline)
- `thinking_sessions.py` – topic‑centric thinking sessions
- `analytics.py` – belief graph and timeline builders
- `frontend/` – static UI (index.html, styles.css, app.js)
- `tests/run_tests.py` – simple test runner for core functionality

---

## Memory object schema

The core unit is a memory object:

```json
{
  "memory_id": "string",
  "content": "string",
  "created_at": "ISO timestamp",
  "memory_type": "belief | fact | reflection | decision",
  "confidence": 0.0,
  "source": "note | pdf | tweet | chat | voice | session",
  "topic": ["string"],
  "revision_of": "memory_id or null"
}
```

Mnemosyne treats older memories as valid for their time and never deletes
or overwrites them – only adds new ones that can point back via
`revision_of`.

---

## Local setup

Requirements:
- Python 3.10+ (tested with 3.11+)

Install dependencies (none beyond the standard library are required).

Run tests:

```bash
cd Mnemosyne
python tests/run_tests.py
```

You should see:

```text
All tests passed.
```

---

## CLI usage

The CLI is defined in `mnemosyne_app.py`.

### Ingest text

```bash
python mnemosyne_app.py ingest \
  --store data/memories.json \
  --text "I believe RAG is the future of personal AI." \
  --source note \
  --profile journal
```

Options:
- `--store` – path to the JSON store file.
- `--text` – raw text to ingest.
- `--source` – one of `note|pdf|tweet|chat|voice`.
- `--timestamp` – optional ISO timestamp (defaults to current UTC).
- `--profile` – `default|journal|research` (journal filters out plain facts).

### Ask a question

```bash
python mnemosyne_app.py answer \
  --store data/memories.json \
  --question "What do I currently believe about RAG?"
```

This returns a structured answer summarizing the relevant memories and
belief evolution.

### Thinking session

```bash
python mnemosyne_app.py session \
  --store data/memories.json \
  --topic rag \
  --start 2026-01-01T00:00:00 \
  --end 2026-02-01T00:00:00
```

This runs a topic‑centric reasoning pass and writes a new reflection
memory summarizing the session.

---

## HTTP API

The HTTP API is implemented in `api_server.py`.

Start the server:

```bash
python api_server.py
```

By default it listens on `http://127.0.0.1:8000`.

### Endpoints

All requests are `POST` with JSON bodies.

#### `POST /ingest`

Body:

```json
{
  "text": "I believe RAG is the future of personal AI.",
  "source": "note",
  "timestamp": "2026-01-14T10:30:00",
  "store": "data/memories.json",
  "profile": "journal"
}
```

Response:

```json
{
  "new_memories": [...],
  "revisions": [...],
  "contradictions": [...],
  "total_memories": 1
}
```

#### `POST /answer`

Body:

```json
{
  "question": "What do I currently believe about RAG?",
  "store": "data/memories.json"
}
```

Response:

```json
{
  "has_memories": true,
  "answer": "<Mnemosyne formatted answer string>"
}
```

#### `POST /session`

Body:

```json
{
  "topic": "rag",
  "store": "data/memories.json",
  "start": "2026-01-01T00:00:00",
  "end": "2026-02-01T00:00:00"
}
```

Response:

```json
{
  "answer": "<session reasoning answer>",
  "summary_memory": { ... }
}
```

#### `POST /graph`

Body:

```json
{
  "store": "data/memories.json"
}
```

Response:

```json
{
  "nodes": [...],
  "edges": [...]
}
```

#### `POST /timeline`

Body:

```json
{
  "store": "data/memories.json",
  "topic": "rag"
}
```

Response:

```json
{
  "items": [...]
}
```

---

## Frontend (Vercel‑ready)

The `frontend/` folder contains a minimal static UI:

- `index.html`
- `styles.css`
- `app.js`

You can serve it locally:

```bash
cd frontend
python -m http.server 4173
```

Then open `http://127.0.0.1:4173/` in a browser and set the API base URL
to your running backend (e.g. `http://127.0.0.1:8000` or your Hugging
Face Space URL).

To deploy to Vercel:
- Create a new project with `frontend/` as the root.
- Use “Other” / static site with no build step.
- Set output directory to `.`.

---

## Deployment notes

- **Backend (Hugging Face Spaces)**  
  Use `api_server.py` as the entrypoint. The Space should expose the HTTP
  API endpoints described above.

- **Frontend (Vercel)**  
  Deploy `frontend/` as a static site and point the “API base URL” input
  to your Hugging Face backend.

---

## License

Choose and add a license (for example, MIT) depending on how you want
others to use this project.

