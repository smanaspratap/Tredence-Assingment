# Workflow Engine

A lightweight, LangGraph-style workflow engine built with FastAPI. It includes a small code-review agent, support for nodes and edges, shared mutable state, looping, background execution, WebSockets for streaming logs, and structured JSON logging.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Testing the Workflow](#testing-the-workflow)
- [What the Engine Supports](#what-the-engine-supports)
- [API Endpoints](#api-endpoints)
- [Future Improvements](#future-improvements)

---

## Features

- **Workflow Graph Engine** — async nodes, edge mapping, and shared state handled in a simple, extensible way  
- **Mini Code-Review Agent** — extracts functions → checks complexity → detects issues → suggests improvements (with looping)  
- **FastAPI Endpoints** — REST + WebSocket streaming  
- **Background Task Execution** — workflows run without blocking  
- **Real-time WebSocket Logs** — view run events via `ws://localhost:8000/ws/run/{run_id}`  
- **Structured Logging** — JSON logs stored in `logs.json`  
- **Tool Registry** — plug in new tools easily

---

## Project Structure

```
workflow-engine/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + route definitions
│   ├── config.py            # Pydantic settings
│   ├── logging_config.py    # Loguru setup
│   ├── models.py            # Pydantic models
│   ├── graph_engine.py      # Core workflow engine
│   └── tools/
│       ├── __init__.py      # Tool registry
│       └── code_review.py   # Node implementations for code review agent
├── requirements.txt
└── README.md
```

---

## How to Run

### 1. Create a virtual environment

```
python -m venv venv
```

**Windows**
```
venv\Scripts\activate
```

**macOS/Linux**
```
source venv/bin/activate
```

### 2. Install dependencies

```
pip install "uvicorn[standard]"
pip install -r requirements.txt
```

### 3. Start the server

```
uvicorn app.main:app --reload
```

You can now access:

- API root → `http://127.0.0.1:8000`  
- API docs → `http://127.0.0.1:8000/docs`

A default `code_review` graph loads automatically on startup.

---

## Testing the Workflow

### **Option 1: Swagger UI (Easy & Recommended)**

1. Open `http://127.0.0.1:8000/docs`
2. Find **POST** → `/graph/{graph_id}/run`
3. Click **Try it out**
4. Set: `graph_id = code_review`
5. In the request body, enter something like:

```
{
  "code": "def foo():\n print('debug')\n # TODO: fix this"
}
```

6. Hit **Execute**, copy the `run_id`
7. Go to **GET** `/graph/run/{run_id}/state`
8. Paste the `run_id` → **Execute**

### **Option 2: curl**

Start a workflow:

```
curl -X POST "http://localhost:8000/graph/code_review/run" \
-H "Content-Type: application/json" \
-d "{\"code\": \"def foo():\n print('debug')\n # TODO: fix\"}"
```

Check the final result:

```
curl "http://localhost:8000/graph/run/<RUN_ID>/state"
```

**Typical Output**

```
{
  "status": "completed",
  "state": {
    "functions": ["foo"],
    "issues": ["Debug prints present", "Contains TODO comments"],
    "quality_score": 0.8,
    "improvements": ["Consider addressing: Debug prints present"]
  }
}
```

---

## What the Engine Supports

### Core Capabilities

**1. Nodes**  
Each node is an async Python function that can read/modify shared state. Nodes are registered as tools.

**2. Edges**  
A simple mapping determines execution flow:  
`"extract_functions": "check_complexity"`

**3. Shared State**  
A mutable dictionary passed between nodes, carrying items like `functions`, `issues`, or `quality_score`.

**4. Looping**  
Nodes repeat until a condition is met — in this case, when `quality_score >= 0.9` or after `max_iterations` (default 5).

**5. Basic Branching**  
Handled implicitly via loop conditions.

### Code Review Agent Flow

```
extract_functions → check_complexity → detect_issues → suggest_improvements
                           ↑                                    |
                           └────────────────────────────────────┘
                 (loop until quality_score ≥ 0.9)
```

**Node responsibilities:**

- `extract_functions`: regex-based function extraction  
- `check_complexity`: evaluates structure and length  
- `detect_issues`: flags debug prints, TODOs, long code  
- `suggest_improvements`: rule-based suggestions + adjusts quality score  

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/graph/create` | Create a new workflow graph |
| **POST** | `/graph/{graph_id}/run` | Start a workflow run (returns `run_id`) |
| **GET** | `/graph/run/{run_id}/state` | Fetch state, logs, and run status |
| **WS** | `/ws/run/{run_id}` | Stream live run events |

### Example: Creating a Custom Graph

```
{
  "nodes": {
    "extract_functions": "extract_functions",
    "check_complexity": "check_complexity",
    "detect_issues": "detect_issues",
    "suggest_improvements": "suggest_improvements"
  },
  "edges": {
    "extract_functions": "check_complexity",
    "check_complexity": "detect_issues",
    "detect_issues": "suggest_improvements",
    "suggest_improvements": "suggest_improvements"
  },
  "max_iterations": 5
}
```

---

## Future Improvements

With more time, the following enhancements would make the engine production-ready:

### 1. Persistent Storage  
Move graphs/runs from in-memory storage to SQLite/Postgres.

### 2. Smarter Branching  
Dynamic routing based on state values.

### 3. Tool Registration API  
Allow uploading new tools at runtime.

### 4. State Validation  
Per-graph schema enforcement using Pydantic.

### 5. Observability  
- Prometheus metrics  
- OpenTelemetry traces  
- Better error handling & retries  

### 6. Production Extras  
- Dockerized builds  
- Authentication & rate limiting  
- Horizontal scaling with Redis  
