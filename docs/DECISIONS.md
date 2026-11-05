# Decisions for the learning build

These four choices are fixed. Everything here is free to install and free to run. No API keys, no paid model, no cloud account.

## 1. Language and agent style

Python 3.11 or newer.

The agent loop is our own code: a list of messages, a tool schema, and a loop that calls the model, runs a tool, and appends the result. FastAPI is the API. The chat UI is a React app. `app/static/index.html` is the Step 1 lab that shows the browser primitives React is built on. It stays until the React app replaces it.

The loop stays hand-written so routing, tool calls, and state stay visible. The official MCP Python SDK is added at Step 5, when the tools move behind MCP servers. LangGraph and other agent frameworks stay out of this project.

## 2. The LLM and how it runs

The API and Ollama run as two containers, started with Docker Compose from Docker Desktop. The API container is built from the project `Dockerfile`. The Ollama container uses the `ollama/ollama` image. The model files live in the Compose volume `ollama-models`.

`app/agent.py` reads `OLLAMA_URL` from the environment. Compose sets it to `http://ollama:11434/api/chat`. A run without Docker still falls back to `http://127.0.0.1:11434/api/chat`.

`qwen2.5:7b` (about 4.7 GB) is pulled inside the running Ollama container with `docker compose exec ollama ollama pull qwen2.5:7b`. Until that pull finishes, the container has no model. The Homebrew Ollama service stays stopped so it does not hold port 11434.

| Role | Model | When |
|---|---|---|
| In-bank model | `qwen2.5:7b` | From Milestone 1. It is the only model until Step 10. |
| Stand-in for a third-party model | `llama3.2:3b` | Step 10 only, and only after PII redaction. |

Both weights are free. Both stay on the laptop. `qwen2.5:7b` is the choice because it follows tool calls well enough for these intents. If that model is too slow, both roles move to `llama3.2:3b`.

## 3. The fake bank

One JSON file, `data/bank.json`. Three customers, no real people, no real account numbers.

| Customer | Id | Accounts | Used to practise |
|---|---|---|---|
| Priya Shah | `cust_101` | Savings `acc_1` | Balance, and a follow-up that needs the session |
| Rohan Iyer | `cust_102` | Savings `acc_2` and current `acc_3` | "Which account?" plus balance and last five transactions together |
| Meera Nair | `cust_103` | Savings `acc_4` | "What was this debit?" and a cheque-book request to her registered address |

Each account has a balance, five transactions, and a registered address. Cheque-book requests are appended to the same file.

Login is a name on the fake login screen. That name selects the customer id. There is no real identity provider.

## 4. Tools in Step 2

One agent can call all six tools from the Step 2 diagram: balance enquiry, transaction details, statement request, change of address, cheque book request, and KYC update. The practice questions are still balance, a debit explanation, and a cheque book. There is no login yet. The page selects one of the three demo customers, and the API passes that id into every tool.

## What this build uses

| Piece | Tool |
|---|---|
| Language | Python 3.11+ |
| API | FastAPI, Uvicorn |
| Chat UI | React. `app/static/index.html` is the current Step 1 lab only. |
| Model runtime | Ollama container (`ollama/ollama`), reached at `http://ollama:11434` |
| App runtime | Docker Compose: `api` container and `ollama` container |
| Models | `qwen2.5:7b`, later `llama3.2:3b` |
| Tools-as-servers | MCP Python SDK, from Step 5 |
| Bank, session, queue | JSON file, then an in-memory dict, then a Python list |

## What this build does not use

Paid LLM APIs, hosted agent platforms, LangGraph, a database, Redis, Kafka, Kubernetes, and a real bank login. Docker Compose is how this lab runs. Kubernetes can wait.
