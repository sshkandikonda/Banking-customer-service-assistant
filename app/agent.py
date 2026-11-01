import os

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
MODEL = "qwen2.5:7b"
# The first call loads the model into memory.
TIMEOUT_SECONDS = 60

# Fixed instruction sent on every call. The browser cannot replace it.
SYSTEM_PROMPT = (
    "You are a bank customer-service assistant in a demo. "
    "You can only chat. You cannot look up balances, transactions, statements, "
    "addresses, cheque books, or KYC. If the customer asks for account data or "
    "a service request, say clearly that you cannot look that up yet. "
    "Do not invent balances, account numbers or transactions."
)

class ModelUnvavailable(Exception):
    #Raised when Ollama cannot return assistant text.

    pass


def reply(messages: list[dict]) -> str:
    # Send the conversation to Ollama once and return the assistant's text.

    # messages is the browser's list of {"role", "content"} dicts.
    # This function does not store them and does not call a tool.
    # System message first, then the conversation copied in the same order.
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "stream": False,  # One JSON response, not a stream of chunks.
    }
    try:
        # Send the payload as JSON. This waits until Ollama finishes the whole reply.
        # If nothing accepts the connection, or the wait exceeds TIMEOUT_SECONDS,
        # httpx raises an HTTPError here.
        response = httpx.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)

        # A connection can succeed and still be a failure, such as 404 when the
        # model is not pulled. raise_for_status turns any 4xx or 5xx into an HTTPError.
        response.raise_for_status()

        # response.json() parses the body into a dict. Ollama's shape is
        # {"message": {"role": "assistant", "content": "..."}}.
        # ["message"]["content"] reads that text.
        # A missing "message" or "content" key raises KeyError.
        # A body that is not a dict, or a null "message", raises TypeError.
        content = response.json()["message"]["content"]
    except (httpx.HTTPError, KeyError, TypeError) as exception:
        # Replace those different failures with one error main.py can catch.
        # "from exception" keeps the original cause attached for debugging.
        raise ModelUnvavailable("The model is not available.") from exception

    # Ollama answered, but the text is missing or only whitespace.
    # That is still a failure: an empty string is not a reply to show in the chat.
    if not isinstance(content, str) or not content.strip():
        raise ModelUnvavailable("The model returned an empty response.")

    # Hand the assistant text back to the caller. Nothing here is saved.
    return content
