import json
import os

import httpx

from app.bank import (
    balance_enquiry,
    change_of_address,
    cheque_book_request,
    kyc_update,
    statement_request,
    transaction_details,
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
MODEL = "qwen2.5:7b"
TIMEOUT_SECONDS = 60
MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = (
    "You are a bank customer-service assistant for the signed-in demo customer. "
    "Use the tools for a balance, transactions, a statement, an address change, "
    "a cheque book, or a KYC update. Report only what the tools return. "
    "Do not invent balances, dates, account refs, or addresses. "
    "If a tool returns an error, explain that error and stop."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "balance_enquiry",
            "description": "List the signed-in customer's accounts and balances.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transaction_details",
            "description": "List transactions. Optionally filter by account_ref or a word in the description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_ref": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "statement_request",
            "description": "Return the statement lines for one account, or every account if account_ref is omitted.",
            "parameters": {
                "type": "object",
                "properties": {"account_ref": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_of_address",
            "description": "Save a new registered address for the signed-in customer.",
            "parameters": {
                "type": "object",
                "properties": {"new_address": {"type": "string"}},
                "required": ["new_address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cheque_book_request",
            "description": "Request a cheque book for 25 or 50 leaves. It is sent to the registered address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_ref": {"type": "string"},
                    "leaves": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kyc_update",
            "description": "Set KYC status to pending or verified.",
            "parameters": {
                "type": "object",
                "properties": {"kyc_status": {"type": "string"}},
                "required": ["kyc_status"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "balance_enquiry": balance_enquiry,
    "transaction_details": transaction_details,
    "statement_request": statement_request,
    "change_of_address": change_of_address,
    "cheque_book_request": cheque_book_request,
    "kyc_update": kyc_update,
}


class ModelUnvavailable(Exception):
    """Raised when Ollama cannot return assistant text."""


def reply(messages: list[dict], customer_id: str) -> str:
    """Call the model, run any tool it requests, and return the final text.

    customer_id comes from the API, never from the model's tool arguments.
    """
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
    for _ in range(MAX_TOOL_ROUNDS):
        message = _call_model(conversation)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ModelUnvavailable("The model returned an empty response.")
            return content
        conversation.append(message)
        for call in tool_calls:
            conversation.append(_run_tool(call, customer_id))
    raise ModelUnvavailable("The model asked for too many tools.")


def _call_model(conversation: list[dict]) -> dict:
    payload = {
        "model": MODEL,
        "messages": conversation,
        "tools": TOOLS,
        "stream": False,
    }
    try:
        response = httpx.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        message = response.json()["message"]
    except (httpx.HTTPError, KeyError, TypeError) as exception:
        raise ModelUnvavailable("The model is not available.") from exception
    if not isinstance(message, dict):
        raise ModelUnvavailable("The model is not available.")
    return message


def _run_tool(call: dict, customer_id: str) -> dict:
    function = call.get("function") or {}
    name = function.get("name")
    try:
        arguments = _arguments(function.get("arguments"))
        # The model must not choose whose data is read. Drop any customer id it invented.
        arguments.pop("customer_id", None)
        tool = TOOL_FUNCTIONS[name]
        result = tool(customer_id=customer_id, **arguments)
        content = json.dumps(result)
    except (KeyError, TypeError, ValueError) as exception:
        content = json.dumps({"error": str(exception) or "The tool could not run."})
    tool_message = {"role": "tool", "name": name, "content": content}
    if call.get("id"):
        tool_message["tool_call_id"] = call["id"]
    return tool_message


def _arguments(raw) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, str):
        parsed = json.loads(raw) if raw.strip() else {}
    else:
        parsed = raw
    if not isinstance(parsed, dict):
        raise ValueError("Tool arguments must be an object.")
    return parsed
