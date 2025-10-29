# Electronic Components Inventory (Local-first, Agent-powered)

A lightweight stock tracking app for electronic components with a built‑in local AI assistant. The UI is a simple web app served by Flask. AI is powered by LangChain + llama.cpp (GGUF models) running entirely on your machine. An optional native, chrome‑less window is provided via PyWebview (Qt or Chromium app‑mode fallback) for a desktop‑app feel.

## Highlights
- Local LLM via `llama-cpp-python` (no cloud required)
- LangChain Agent with tools:
  - `inventory`: read-only inventory search from SQLite
  - `search`: quick web snippets via DuckDuckGo Instant Answer
  - `electronics_calc`: Ohm's law, RC cutoff, divider, simple arithmetic
  - `add_to_memory`, `list_memory`, `remove_from_memory`: small JSON memory
- Auto-renders inventory results as tables in the chat
- Native frameless window (PyWebview) or fallback to your browser

---

## Quick Start

Prerequisites:
- Python 3.11+ (tested with 3.12)
- Linux desktop (Qt/GTK optional for native window)

Optional system packages (recommended for faster build):
```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential
```

Install:
```bash
cd /home/aykut/Dropbox/Developments/Git/stock_tracking
chmod +x install.sh run.sh stop.sh
./install.sh
```
- Creates virtualenv and installs Python deps (including Qt libs for PyWebview)
- Initializes SQLite DB (`inventory.db`)
- Ensures `models/` exists; downloads TinyLlama if empty

Run:
```bash
./run.sh
```
- Opens the app at `http://localhost:5000`
- If PyWebview backends are present, a native chrome‑less window opens; otherwise the default browser is used

Stop:
```bash
./stop.sh
```

Models:
- Place a `.gguf` model under `models/` or set an absolute path:
```bash
export LLM_MODEL=/absolute/path/to/YourModel.gguf
./run.sh
```
- Defaults to the smallest available model; `install.sh` fetches TinyLlama for convenience

---

## Setup script (alternative to install.sh)

Use when you want a one-shot environment prep (and optional system deps):

```bash
./setup.sh                      # create venv, install requirements, init DB
./setup.sh --install-system-deps # also apt-get cmake/GTK/Chromium if available
```

## Packaging

Create a zip in `dist/` for sharing or archiving:

```bash
./pack.sh                 # excludes large model files and venv/uploads by default
./pack.sh --include-models # include models/*.gguf in the archive
```

The archive is named like `stock_tracking_YYYYMMDD_HHMMSS.zip`.

---

## Architecture

```
┌───────────────┐     HTTP (Flask)       ┌──────────────────────────┐
│  Web UI       │  /api/* endpoints      │  Flask Server (app.py)   │
│  (index.html, │ <─────────────────────>│  - Stocks/Categories API │
│  script.js)   │                        │  - Conversations API     │
└──────┬────────┘                        │  - /api/ai/ask           │
       │                                 └───────────┬──────────────┘
       │                                             │
       │                                  LangChain AgentExecutor
       │                                   ┌────────────────────┐
       └──────────────────────────────────▶│  LlamaCpp (GGUF)   │
                                           │  Tools:            │
                                           │   - inventory      │
                                           │   - search         │
                                           │   - electronics…   │
                                           │   - memory (JSON)  │
                                           └────────────────────┘
```

- Database: SQLite (`inventory.db`)
- LLM: `llama-cpp-python` (CPU by default). Configure with `LLM_MODEL` or drop `.gguf` in `models/`.
- Agent: LangChain ZERO_SHOT_REACT_DESCRIPTION with ConversationBufferMemory
- Tools:
  - `inventory(query: str)` — returns JSON rows `[ { name, category, quantity, unit } ]`
  - `search(query: str)` — short web snippets (DuckDuckGo Instant Answer)
  - `electronics_calc(cmd: str)` — `ohms V=5,R=2k` | `rc_cutoff R=10k,C=100nF` | `divider Vin=5,R1=10k,R2=5k` | arithmetic
  - `add_to_memory(text)`, `list_memory()`, `remove_from_memory(substr)` — JSON stored in `memory/agent_memory.json`

The UI auto-renders inventory arrays as categorized tables.

---

## Environment variables

- `LLM_MODEL` — Absolute path to a `.gguf` model (overrides `models/` discovery)
- `MODEL_DIR` — Directory to scan for `.gguf` (default: `models`)

Native window:
- Requires either Qt or GTK backends. The repo includes Qt wheels:
  - `PyQt5`, `PyQtWebEngine`, `qtpy`
- If backends are missing, `run.sh` falls back to your default browser. It will also try Chromium app mode (`--app`), if installed.

---

## Usage (UI)

- Sidebar lets you manage categories/stocks
- AI Assistant tab: ask questions like:
  - “what i have” → lists inventory table by category (Resistor, Capacitor, …)
  - “do we have 10k resistors?” → filtered results
  - “ohms V=12, R=220” → current calculation
  - “rc_cutoff R=10k, C=100nF” → cutoff frequency
  - “add ‘Prefer blue LEDs for status’ to memory” → stores a memory note

Each answer shows the model file name used.

---

## Usage (API)

List categories:
```bash
curl -s http://localhost:5000/api/categories | jq
```

Ask AI:
```bash
curl -s -X POST http://localhost:5000/api/ai/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"what i have"}' | jq
```
- Response includes `data.answer` (text), `data.model` (GGUF filename) and, when available, `data.inventory` (array rendered as table in UI).

---

## Troubleshooting

- `llama-cpp-python` build failures
  - Install toolchain: `sudo apt-get install -y cmake build-essential`
  - Reinstall: `source venv/bin/activate && pip install -r requirements.txt`

- No model found / slow first run
  - Ensure a `.gguf` is in `models/` or set `LLM_MODEL=/abs/path/model.gguf`

- PyWebview cannot load Qt/GTK
  - Qt: `pip install -U PyQt5 PyQtWebEngine qtpy`
  - GTK (system): `sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0`
  - Fallback: Chromium app mode is used automatically if present; otherwise your default browser opens

- Inventory table not showing
  - The agent is instructed to include JSON arrays. If it fails, the backend falls back to returning inventory rows for queries like “what i have”, ensuring the UI can render a table.

---

## Project Layout (key files)

- `app.py` — Flask app, endpoints, LangChain agent & tools
- `script.js` — Frontend logic; chat rendering and table view
- `style.css`, `index.html` — UI
- `database.py` — DB schema + lightweight migrations (timestamps)
- `models/` — put `.gguf` here (or use `LLM_MODEL`)
- `native_view.py` — PyWebview / Chromium app‑mode launcher
- `run.sh` — starts Flask and opens native window or browser
- `stop.sh` — stops Flask
- `requirements.txt` — Python dependencies

---

## License & Credits

- Built with Flask, LangChain, llama.cpp
- Thanks to the open‑source communities of LangChain and ggml/llama.cpp

This repository is for local evaluation and personal productivity use.
