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
- **SQLite Persistence**: Complete research history stored locally via `aiosqlite` with indexing and concurrency safety.
- **FastAPI REST API & SSE**: Real-time progress streaming via Server-Sent Events (`started`, `searching`, `reading`, `writing`, `reviewing`, `completed`, `failed`).
- **CORS Configured**: Ready for local React / Vite frontend development (`http://localhost:5173` and `http://127.0.0.1:5173`).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               React / Vite Frontend (Future Phase)              │
│               http://localhost:5173 / http://127.0.0.1:5173     │
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

Create a `.env` file in the project root:

```bash
# Google Gemini API Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Tavily Search API Configuration
TAVILY_API_KEY=your_tavily_api_key_here
```

> **Note**: Never commit or share your `.env` file. It is gitignored by default.

---

## 🚀 Local Run Instructions (Windows PowerShell)

Run all commands from the repository root:

### 1. Install or update dependencies in the existing virtual environment

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Start the FastAPI backend with Uvicorn

```powershell
.\venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be accessible at:
- **API Base**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

### 3. Check API health

In a separate PowerShell terminal:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected",
  "version": "1.0.0"
}
```

### 4. Run the automated test suite

Execute all 32 automated tests across Phase 2, Phase 3A, and Phase 3B:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
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
│   ├── main.py                 # FastAPI application, CORS, and route handlers
│   └── models.py               # Pydantic request/response models
├── data/
│   └── research_history.db     # SQLite research history database (gitignored)
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── agents.py           # Gemini agents (Search, Reader, Writer, Critic)
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py         # SQLite persistence layer via aiosqlite
│   ├── pipelines/
│   │   ├── __init__.py
│   │   └── pipeline.py         # 4-stage pipeline with async progress callbacks
│   └── tools/
│       ├── __init__.py
│       └── tools.py            # Lazy TavilyClient & resilient multi-strategy scraper
├── tests/
│   ├── test_phase2.py          # Phase 2 agent & tool tests
│   ├── test_phase3a.py         # Phase 3A database & pipeline tests
│   └── test_phase3b.py         # Phase 3B FastAPI & SSE tests
├── main.py                     # CLI entry point (synchronous)
├── requirements.txt            # Python dependencies
├── .env                        # Local API keys (gitignored)
├── .env.example                # Example configuration template
└── README.md                   # Project documentation
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.