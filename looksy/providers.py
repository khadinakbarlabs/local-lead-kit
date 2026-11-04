"""Single-turn text requests, made only after the caller obtains per-request approval."""

from contextlib import closing
import http.client
import json
import os
from pathlib import Path
import re
import ssl


_MAX_PROMPT_BYTES = 32 * 1024
_MAX_RESPONSE_BYTES = 256 * 1024
_MAX_TEXT_BYTES = 16 * 1024
_MAX_TOKENS = 1024
_TIMEOUT_SECONDS = 30
_MODEL_SEGMENT = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_HOSTS = {
    "anthropic": "api.anthropic.com",
    "openrouter": "openrouter.ai",
    "openai": "api.openai.com",
    "gemini": "generativelanguage.googleapis.com",
}


class ProviderError(ValueError):
    """A displayable error that contains no request or provider response data."""


def _request_fields(provider, key, model, prompt):
    messages = [{"role": "user", "content": prompt}]
    headers = {"Content-Type": "application/json"}
    if provider == "gemini":
        headers["x-goog-api-key"] = key
        path = f"/v1beta/models/{model}:generateContent"
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": _MAX_TOKENS}}
    else:
        headers["Authorization"] = "Bearer " + key
        if provider == "openai":
            path = "/v1/responses"
            body = {"model": model, "input": prompt, "max_output_tokens": _MAX_TOKENS, "store": False}
        else:
            body = {"model": model, "messages": messages, "max_tokens": _MAX_TOKENS}
            if provider == "anthropic":
                path = "/v1/messages"
                headers["anthropic-version"] = "2026-10-21"
            else:
                path = "/api/v1/chat/completions"
                body["provider"] = {"allow_fallbacks": False, "require_parameters": True}
    return path, body, headers


def _reply_text(provider, data):
    """Collect final assistant text, excluding thinking, tools and incomplete replies."""
    if data.get("error"):
        raise ProviderError("The provider reported an error.")
    if provider == "anthropic":
        if data["stop_reason"] not in ("end_turn", "stop_sequence"):
            return ""
        parts = [part["text"] for part in data["content"] if part["type"] == "text"]
    elif provider == "openai":
        if data["status"] != "completed":
            return ""
        parts = [
            part["text"]
            for item in data["output"] if item["type"] == "message" and item["role"] == "assistant"
            for part in item["content"] if part["type"] == "output_text"
        ]
    elif provider == "openrouter":
        choice = data["choices"][0]
        message = choice["message"]
        if choice["finish_reason"] != "stop" or message["role"] != "assistant":
            return ""
        parts = [message["content"]]
    else:
        choice = data["candidates"][0]
        if choice["finishReason"] != "STOP":
            return ""
        parts = [part["text"] for part in choice["content"]["parts"]
                 if "text" in part and not part.get("thought")]
    return "\n".join(parts).strip()


def _tls_context():
    # Framework Python on macOS can lack a default CA file; use the OS trust bundle.
    cafile = os.environ.get("SSL_CERT_FILE")
    if not cafile and not ssl.get_default_verify_paths().cafile and Path("/etc/ssl/cert.pem").is_file():
        cafile = "/etc/ssl/cert.pem"
    return ssl.create_default_context(cafile=cafile)


def ask(provider: str, key: str, model: str, prompt: str) -> str:
    """Send exactly one text prompt to the specified provider and model."""
    if not isinstance(provider, str) or provider not in _HOSTS:
        raise ProviderError("Choose a supported AI provider.")
    if not isinstance(key, str) or not re.fullmatch(r"[!-~]{1,4096}", key):
        raise ProviderError("Connect a valid API key for this provider.")
    pattern = _MODEL_SEGMENT
    if provider == "openrouter":
        pattern = rf"{_MODEL_SEGMENT}/{_MODEL_SEGMENT}(?::free)?"
    if not isinstance(model, str) or len(model) > 200 or ".." in model or not re.fullmatch(pattern, model):
        raise ProviderError("Use a valid model ID for this provider.")
    if not isinstance(prompt, str) or len(prompt) > _MAX_PROMPT_BYTES or not prompt.strip():
        raise ProviderError("Provide a text prompt of up to 32 KiB.")
    try:
        prompt_size = len(prompt.encode("utf-8"))
    except UnicodeError:
        raise ProviderError("The prompt must be valid UTF-8 text.") from None
    if prompt_size > _MAX_PROMPT_BYTES:
        raise ProviderError("Provide a text prompt of up to 32 KiB.")

    path, body, headers = _request_fields(provider, key, model, prompt)
    try:
        # HTTPSConnection uses verified TLS and never follows a redirect.
        with closing(http.client.HTTPSConnection(
            _HOSTS[provider], timeout=_TIMEOUT_SECONDS, context=_tls_context()
        )) as connection:
            connection.request("POST", path, body=json.dumps(body).encode("ascii"), headers=headers)
            with closing(connection.getresponse()) as response:
                if response.status != 200:
                    raise ProviderError(f"The provider returned HTTP {response.status}.")
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except (http.client.HTTPException, OSError):
        raise ProviderError("The provider connection ended without a confirmed reply.") from None
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise ProviderError("The provider response exceeded the size limit.")
    try:
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ProviderError("The provider returned an unreadable response.")
        answer = _reply_text(provider, data)
        size = len(answer.encode("utf-8"))
    except ProviderError:
        raise
    except (ValueError, KeyError, IndexError, AttributeError, TypeError, RecursionError):
        raise ProviderError("The provider returned an unreadable response.") from None
    if not answer or size > _MAX_TEXT_BYTES or key in answer:
        raise ProviderError("The provider did not return usable, complete text within the output limit.")
    return answer
