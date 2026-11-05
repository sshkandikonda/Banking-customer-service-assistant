from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import ModelUnvavailable, reply
from app.bank import list_customer_ids

app = FastAPI()

MAX_MESSAGES = 10
MAX_CONTENT_LENGTH = 2000

class ChatMessage(BaseModel):
    # One item from the browser: {"role": "user", "content": "Hello"}.
    role: str
    content: str

class ChatRequest(BaseModel):
    # The POST /chat body. FastAPI turns the JSON into this object.
    messages: list[ChatMessage]
    customer_id: str


class ChatResponse(BaseModel):
    # The JSON the page receives: {"reply": "..."}
    reply: str

def validate_messages(messages: list[ChatMessage]) -> None:
    # Reject a bad conversation before Ollama is called.
    if not 1 <= len(messages) <= MAX_MESSAGES:
        raise HTTPException(status_code=400, detail="Send between 1 and 20 messages.")
    for message in messages:
        if message.role not in {"user", "assistant"}:
            raise HTTPException(status_code=400, detail="Each role must be user or assistant.")
        if not message.content.strip() or len(message.content) > MAX_CONTENT_LENGTH:
            raise HTTPException(status_code=400, detail="Each message must be a non-empty string of at most 2000 characters.")
    if messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must be from the user.")


def validate_customer(customer_id: str) -> None:
    if customer_id not in list_customer_ids():
        raise HTTPException(status_code=400, detail="Choose a demo customer.")

@app.post("/chat")
def chat(body: ChatRequest) -> ChatResponse:
    # body is the parsed JSON. Validation failures become HTTP 400.
    validate_messages(body.messages)
    validate_customer(body.customer_id)
    # reply expects plain dicts, not ChatMessage objects.
    messages = [{"role": message.role, "content": message.content} for message in body.messages]
    try:
        reply_text = reply(messages, body.customer_id)
    except ModelUnvavailable as exception:
        # Ollama is down, the model is missing, or the reply was empty.
        raise HTTPException(status_code=503, detail=str(exception))
    return ChatResponse(reply=reply_text)


# Serve app/static at /. This must stay below /chat so the page does not swallow that route.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")