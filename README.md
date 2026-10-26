# LangChain Multi-Agent Research System

A powerful multi-agent research system built with LangChain, Google Gemini, and Tavily that autonomously researches topics, gathers information, scrapes web sources, synthesizes comprehensive reports, evaluates report quality, persists history to SQLite, and streams real-time progress via FastAPI and Server-Sent Events (SSE).

<p align="center">
  <strong>🔬 Research Automation • 🤖 Multi-Agent Orchestration • 📝 Google Gemini LLM • ⚡ FastAPI Backend</strong>
</p>

---

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents for searching, reading, drafting, and critiquing.
- **Google Gemini Integration**: Native tool calling and high-speed generation with `gemini-3.5-flash-lite`.
- **Automated Web Research**: Intelligent web search with Tavily API.
- **Smart Content Extraction**: Multi-strategy web scraping (Trafilatura → Readability + BeautifulSoup → Fallback) with timeout and error handling.
- **AI-Powered Report Generation & Review**: Automatic synthesis of structured reports with built-in critic scoring and actionable feedback.
- **Strict Citation & Source Grounding**: In-text numerical citations `[N]` mapped 1-to-1 to verified sources discovered by Tavily, eliminating fabricated references.
- **SQLite Persistence**: Complete research history stored locally via `aiosqlite` with WAL mode and concurrency safety.
- **FastAPI REST API & SSE**: Real-time progress streaming via Server-Sent Events (`started`, `searching`, `reading`, `writing`, `reviewing`, `completed`, `failed`).
- **Modern React UI**: Polished dashboard built with Vite, TypeScript, and Tailwind CSS.
- **Production-Ready Configuration**: Dynamic CORS origins and port binding for container and static hosting.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           React + Vite Frontend (TypeScript & Tailwind)         │
│           http://localhost:5173 / http://127.0.0.1:5173         │
└────────────────────────────────┬────────────────────────────────┘
                                 │ REST / SSE
┌────────────────────────────────▼────────────────────────────────┐
│               FastAPI Backend (backend/main.py)                 │
│         Endpoints: /api/health, /api/research, /stream          │
└───────────────┬────────────────────────────────┬────────────────┘
                │                                │
┌───────────────▼──────────────┐  ┌──────────────▼────────────────┐
│    In-Memory Event Manager   │  │   SQLite Persistence (aiosqlite)
│     (backend/events.py)      │  │     (src/db/database.py)      │
└───────────────┬──────────────┘  └───────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│              Research Pipeline (src/pipelines/pipeline.py)      │
│            Orchestrates multi-agent research workflow           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
│ Search Agent  │       │ Reader Agent  │       │ Writer Chain  │
│(Gemini + Tool)│       │(Gemini + Tool)│       │(Gemini Prompt)│
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │
        │   ┌───────────────────▼───────────────────┐   │
        └──▶│             Tools Layer               │◀──┘
            │  • web_search (TavilyClient)          │
            │  • scrape_url (Trafilatura/BS4)       │
            └───────────────────┬───────────────────┘
                                │
                        ┌───────▼───────┐
                        │ Critic Chain  │
                        │(Gemini Prompt)│
                        └───────────────┘
```

---

## 🛠️ Technologies Used

| Technology | Purpose |
|-----------|---------|
| **FastAPI & Uvicorn** | High-performance asynchronous backend and SSE streaming server |
| **LangChain Core & Google GenAI** | Multi-agent orchestration with Google Gemini (`gemini-3.5-flash-lite`) |
| **Tavily API** | Web search and information retrieval |
| **aiosqlite** | Asynchronous local SQLite persistence |
| **Trafilatura & BeautifulSoup4** | Resilient web scraping and clean article text extraction |
| **Pydantic v2** | Request validation and response serialization |

---

## 📋 Environment Configuration

### 1. Backend Configuration (`.env`)

Create a `.env` file in the project root for local development, or configure these variables securely in your backend hosting environment (e.g., Render, Railway):

```bash
# Google Gemini API Configuration (Keep secret on backend)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Tavily Search API Configuration (Keep secret on backend)
TAVILY_API_KEY=your_tavily_api_key_here

# Optional Production Deployment Configuration
CORS_ORIGINS=https://your-frontend-domain.vercel.app
PORT=8000
```

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | **Yes** | Google Gemini API key used by the research and critic agents. Keep secret and configure on backend only. |
| `TAVILY_API_KEY` | **Yes** | Tavily API key for web search and source discovery. Keep secret and configure on backend only. |
| `GEMINI_MODEL` | No | Configurable Google Gemini model name. Defaults to `gemini-3.5-flash-lite`. |
| `CORS_ORIGINS` | No | Comma-separated list of additional allowed frontend origins for deployment. Defaults to local Vite development origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://127.0.0.1:3000`). |
| `PORT` | No | Server port supplied dynamically by cloud hosting platforms, defaulting to `8000`. |

> **Security Note**: Never commit or share your `.env` file. It is gitignored by default.

### 2. Frontend Configuration (`frontend/.env`)

The `frontend/.env.example` file serves as a local development template:

```bash
# Frontend API Base URL
VITE_API_BASE_URL=http://127.0.0.1:8000
```

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | **Yes** (Prod) | Base URL pointing to the FastAPI backend API. In local development, defaults to `http://127.0.0.1:8000`. In production frontend hosting (e.g., Vercel, Netlify, Cloudflare Pages), this **must be configured at build time** to your deployed backend URL (e.g. `https://your-backend.onrender.com`). |

### 3. Persistent Storage Notice

> **Storage Notice**: Completed research runs are persisted locally in an SQLite database (`data/research_history.db`) with Write-Ahead Logging (`WAL`) mode enabled for concurrent read/write safety. When deploying the backend to free ephemeral cloud containers (e.g., Render or Railway free tier without an attached persistent disk), local disk files reset on container restart unless a persistent volume or external database is configured.

---

## 🚀 Local Run Instructions (Windows PowerShell)

Run the backend and frontend in two separate PowerShell terminals:

### Terminal 1: FastAPI Backend

```powershell
# 1. (Optional) Install or update backend dependencies
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Start the FastAPI backend with Uvicorn
.\venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API Base**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

You can verify the backend status at any time:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
```

---

### Terminal 2: React Frontend (Vite)

```powershell
# 1. Navigate to the frontend directory
cd frontend

# 2. (Optional) Install npm packages if running for the first time
npm install

# 3. Start the Vite React development server
npm run dev
```

The frontend will be accessible at:
- **Local Web UI**: `http://127.0.0.1:5173` (or `http://localhost:5173`)

---

## 🧪 Automated Testing

### Backend & Pipeline Tests (Python - 50 tests)
Run all 50 automated tests across Phase 2, Phase 3A, Phase 3B, Phase 5 (citations), and regression suites:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Live Backend End-to-End Integration Check
Run the live integration script against the running FastAPI server:

```powershell
.\venv\Scripts\python.exe scripts/verify_integration.py
```

### Frontend Tests (Vitest & TypeScript - 13 tests)
Run component, API client, lint, and production build checks:

```powershell
cd frontend
npm test -- --run
npm run lint
npm run build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Checks API and database connectivity. Never exposes credentials. |
| `POST` | `/api/research` | Starts a research run in the background. Body: `{"topic": "..."}`. Returns 201 with research `id`. |
| `GET` | `/api/research/{id}` | Retrieves full details and report of a saved research run. Returns 404 if not found. |
| `GET` | `/api/research?limit=20` | Lists recent research runs (newest first). Limit validated between 1 and 100. |
| `DELETE` | `/api/research/{id}` | Deletes a research run by ID from database and memory. Returns 404 if not found. |
| `GET` | `/api/research/{id}/stream` | Streams Server-Sent Events (SSE) in real time. Delivers past completed/failed state if connected late. |

### SSE Progress Stages

Events sent over `/api/research/{id}/stream` adhere to standard `text/event-stream` format:
- `started`: Pipeline initialized for topic and run ID.
- `searching`: Search agent is querying Tavily for web sources.
- `reading`: Reader agent is scraping and analyzing key web pages.
- `writing`: Writer agent is synthesizing findings into a comprehensive report.
- `reviewing`: Critic agent is evaluating and scoring the report.
- `completed`: Research run finished successfully with full report and critic feedback.
- `failed`: Emitted on error with safe error message.

---

## 📁 Project Structure

```
.
├── backend/
│   ├── __init__.py
│   ├── events.py               # In-memory pub/sub and SSE stream generator
│   ├── main.py                 # FastAPI application, dynamic CORS/port, and routes
│   └── models.py               # Pydantic request/response models with source schemas
├── data/
│   └── research_history.db     # SQLite research history database (gitignored)
├── frontend/
│   ├── public/                 # Static assets and icons
│   ├── src/
│   │   ├── __tests__/          # Vitest suite (client & component tests)
│   │   ├── api/                # Typed REST & SSE API client
│   │   ├── components/         # React components (Header, ReportViewer, Form, etc.)
│   │   ├── types/              # TypeScript interfaces and types
│   │   ├── App.tsx             # Main dashboard application
│   │   ├── index.css           # Tailwind CSS styles & design tokens
│   │   └── main.tsx            # Vite React entry point
│   ├── .env.example            # Frontend environment variable template
│   ├── package.json            # Frontend dependencies & scripts
│   ├── vite.config.ts          # Vite build & dev server configuration
│   └── vitest.config.ts        # Vitest test configuration
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── agents.py           # Gemini agents (Search, Reader, Writer, Critic)
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py         # SQLite persistence layer with WAL mode via aiosqlite
│   ├── pipelines/
│   │   ├── __init__.py
│   │   └── pipeline.py         # 4-stage pipeline with async progress & citation pipeline
│   └── tools/
│       ├── __init__.py
│       ├── citations.py        # In-text citation validation & source normalization
│       └── tools.py            # Lazy TavilyClient, URL extraction & multi-strategy scraper
├── tests/
│   ├── test_phase2.py          # Phase 2 agent & tool tests
│   ├── test_phase3a.py         # Phase 3A database & pipeline tests
│   ├── test_phase3b.py         # Phase 3B FastAPI & SSE tests
│   ├── test_citations.py       # Citation mapping and normalization tests
│   └── test_phase5.py          # Phase 5 source extraction & regression tests
├── scripts/
│   └── verify_integration.py   # Backend API & SSE integration check script
├── main.py                     # CLI entry point (synchronous)
├── requirements.txt            # Python dependencies
├── .env                        # Local API keys (gitignored)
├── .env.example                # Backend configuration template
└── README.md                   # Project documentation
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.