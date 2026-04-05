"""
brain.py — Ollama Inference Engine
Swarajya-AI's AI core. All model communication happens here.

Design: Stateless functions. No side effects. Caller handles state.
"""

import json
import requests
from typing import Generator
from config import (
    OLLAMA_API_ENDPOINT,
    OLLAMA_TAGS_ENDPOINT,
    DEFAULT_MODEL,
    REQUEST_TIMEOUT_SECONDS,
    SYSTEM_PROMPT_BASE,
    HINGLISH_ADDENDUM,
    MODE_PROMPTS,
)


# ─────────────────────────────────────────────
# 🔌 Connectivity Check
# ─────────────────────────────────────────────

class OllamaConnectionError(Exception):
    """Raised when Ollama server is unreachable."""
    pass

class ModelNotFoundError(Exception):
    """Raised when the requested model is not installed."""
    pass

class VRAMOverflowError(Exception):
    """Raised on GPU/VRAM-related inference failures."""
    pass


def check_ollama_health() -> dict:
    """
    Ping Ollama and verify the target model is available.
    Returns a status dict.
    Raises OllamaConnectionError if unreachable.
    """
    try:
        response = requests.get(OLLAMA_TAGS_ENDPOINT, timeout=5)
        response.raise_for_status()

        tags_data = response.json()
        installed_models = [m["name"].split(":")[0] for m in tags_data.get("models", [])]
        model_available = DEFAULT_MODEL in installed_models or any(
            DEFAULT_MODEL in m for m in installed_models
        )

        return {
            "online": True,
            "model_available": model_available,
            "installed_models": installed_models,
        }

    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError(
            "Cannot connect to Ollama. Ensure it is running:\n"
            "`ollama serve` in a terminal, then `ollama pull llama3`"
        )
    except requests.exceptions.Timeout:
        raise OllamaConnectionError("Ollama is running but not responding (timeout).")
    except Exception as e:
        raise OllamaConnectionError(f"Unexpected error checking Ollama health: {e}")


# ─────────────────────────────────────────────
# 🧠 Prompt Builder
# ─────────────────────────────────────────────

def build_system_prompt(mode: str, hinglish: bool = False) -> str:
    """Construct a full system prompt from base + mode-specific instructions."""
    prompt = SYSTEM_PROMPT_BASE.strip()

    if hinglish:
        prompt += "\n\n" + HINGLISH_ADDENDUM.strip()

    mode_instruction = MODE_PROMPTS.get(mode, "")
    if mode_instruction:
        prompt += f"\n\n--- CURRENT MODE ---\n{mode_instruction}"

    return prompt


def build_conversation_context(history: list[dict], new_message: str) -> str:
    """
    Flatten conversation history into a single context string.
    Ollama's /api/generate doesn't natively support multi-turn,
    so we manually construct the conversational context.
    """
    context_parts = []

    for turn in history[-6:]:
        role = turn.get("role", "")
        content = turn.get("content", "").strip()
        if role == "user":
            context_parts.append(f"Student: {content}")
        elif role == "assistant":
            context_parts.append(f"SwarajyaBot: {content}")

    context_parts.append(f"Student: {new_message}")
    return "\n\n".join(context_parts)


# ─────────────────────────────────────────────
# 🚀 Core Inference
# ─────────────────────────────────────────────

def query_model(
    user_message: str,
    conversation_history: list[dict],
    mode: str = "Concept Explanation",
    hinglish: bool = False,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Send a prompt to Ollama and return the model's full response.

    Args:
        user_message: The current user input
        conversation_history: List of {"role": str, "content": str} dicts
        mode: One of the keys in MODE_PROMPTS
        hinglish: Whether to request Hinglish output
        model: Ollama model name to use

    Returns:
        The model's response as a string

    Raises:
        OllamaConnectionError: If Ollama is unreachable
        ModelNotFoundError: If the model isn't installed
        VRAMOverflowError: If GPU runs out of memory
        RuntimeError: For other inference failures
    """
    system_prompt = build_system_prompt(mode, hinglish)
    full_prompt = build_conversation_context(conversation_history, user_message)

    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 1024,
            "num_ctx": 4096,
            "repeat_penalty": 1.1,
        }
    }

    try:
        response = requests.post(
            OLLAMA_API_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Model `{model}` is not installed.\n"
                f"Run: `ollama pull {model}` in your terminal."
            )

        if response.status_code == 500:
            error_body = response.text.lower()
            if "out of memory" in error_body or "vram" in error_body or "cuda" in error_body:
                raise VRAMOverflowError(
                    "GPU ran out of VRAM. Try:\n"
                    "1. Closing other GPU-heavy applications\n"
                    "2. Using a smaller model variant (llama3:8b)\n"
                    "3. Reducing context window in config.py"
                )
            raise RuntimeError(f"Ollama returned HTTP 500: {response.text[:200]}")

        response.raise_for_status()

        data = response.json()
        reply = data.get("response", "").strip()

        if not reply:
            raise RuntimeError("Model returned an empty response. Please retry.")

        return reply

    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError(
            "Lost connection to Ollama mid-request.\n"
            "Ensure `ollama serve` is still running."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Request timed out after {REQUEST_TIMEOUT_SECONDS}s.\n"
            "The model may be overloaded. Please wait and retry."
        )
    except (OllamaConnectionError, ModelNotFoundError, VRAMOverflowError, RuntimeError):
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected inference error: {e}")


def format_error_for_ui(error: Exception) -> str:
    """Convert exception types into user-friendly Markdown messages."""
    if isinstance(error, OllamaConnectionError):
        return (
            "### 🔌 Ollama Not Running\n\n"
            f"{error}\n\n"
            "**Quick Fix:**\n"
            "```bash\n# Terminal 1\nollama serve\n\n# Terminal 2\nollama pull llama3\n```"
        )
    if isinstance(error, ModelNotFoundError):
        return (
            "### 📦 Model Not Installed\n\n"
            f"{error}\n\n"
            "**This will take 3-5 minutes on first run.** (~4.7 GB download)"
        )
    if isinstance(error, VRAMOverflowError):
        return (
            "### ⚡ GPU Memory Full\n\n"
            f"{error}"
        )
    return f"### ⚠️ Inference Error\n\n{error}"
