# Banking customer-service assistant

This file is the setup and run process. It stays limited to what you install and how you start the app.

The chat page in Chrome talks to an API container. That container asks an Ollama container for the reply. Both run in Docker Desktop on this Mac. No API key and no cloud account.

## Setup required

| Tool | What it does | Check |
|---|---|---|
| Docker Desktop | Runs the API container and the Ollama container | Docker Desktop is open |
| Google Chrome | The browser for the chat page | Open Chrome |

Python, a virtual environment, and the Homebrew Ollama service are not used to start the app. Stop the Homebrew service so it does not keep port 11434:

```bash
brew services stop ollama
```

The page is `app/static/index.html`. React is the planned UI and is not part of these run steps yet.

## What Docker starts

| Container | Image | Role |
|---|---|---|
| `api` | Built from `Dockerfile` | FastAPI on port 8000, published to the Mac |
| `ollama` | `ollama/ollama` | The model server, reachable by the API as `http://ollama:11434` |

The model files live in the Compose volume `ollama-models`. `qwen2.5:7b` is about 4.7 GB and is pulled into that volume once.

`app/agent.py` reads `OLLAMA_URL`. Compose sets it to `http://ollama:11434/api/chat`.

## Run

From the project folder, with Docker Desktop open:

```bash
docker compose up --build
```

Leave that terminal open. The log is ready when you see `Uvicorn running on http://0.0.0.0:8000` and Ollama `Listening on [::]:11434`.

In a second terminal, from the same folder, pull the model. This works only while the first terminal is still running:

```bash
docker compose exec ollama ollama pull qwen2.5:7b
```

If that command says `service "ollama" is not running`, the first terminal is not up. Start `docker compose up --build` and wait for the listening lines, then pull again.

In Chrome, open:

```text
http://127.0.0.1:8000/
```

## Stop

`Ctrl+C` in the Compose terminal stops the containers.

```bash
docker compose down
```

`down` removes the containers and keeps the model volume. The model is deleted only if you add `-v`.

## If the page will not load

| What you see | What to do |
|---|---|
| Chrome says the connection was refused | Compose is not running. Repeat [Run](#run) and leave that terminal open |
| `service "ollama" is not running` | The pull was started before Compose. Start Compose first, then pull |
| The page says the model is not available | The model is not in the volume yet, or it is still loading. Run the `docker compose exec` pull and wait until it finishes |
| `GET /favicon.ico` 404 in the log | Harmless. The page has no icon |

The first reply after a start can be slow. Ollama is loading the model into the container's memory.
