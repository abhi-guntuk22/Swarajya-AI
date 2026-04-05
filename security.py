"""
security.py — Authentication, Prompt Firewall & Rate Limiter
Swarajya-AI Security Layer

Design principle: Fail closed. When in doubt, block.
"""

import time
import hashlib
import re
import streamlit as st
from config import AUTH_PASSWORD, MIN_REQUEST_GAP_SECONDS, SESSION_COOKIE_NAME


# ─────────────────────────────────────────────
# 🔐 Authentication
# ─────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Deterministic hash so we never store plaintext in session state."""
    return hashlib.sha256(password.encode()).hexdigest()


HASHED_PASSWORD = _hash_password(AUTH_PASSWORD)


def check_auth() -> bool:
    """
    Returns True if this session is authenticated.
    Uses Streamlit session_state for in-process isolation.
    """
    return st.session_state.get("authenticated", False)


def login(password: str) -> tuple[bool, str]:
    """
    Validate password and mark session as authenticated.
    Returns (success: bool, message: str)
    """
    if _hash_password(password) == HASHED_PASSWORD:
        st.session_state["authenticated"] = True
        st.session_state["login_time"] = time.time()
        return True, "✅ Access granted. Welcome to Swarajya-AI."

    fails = st.session_state.get("failed_attempts", 0) + 1
    st.session_state["failed_attempts"] = fails

    if fails >= 5:
        return False, "🔒 Too many failed attempts. Restart the session."

    return False, f"❌ Invalid password. ({5 - fails} attempts remaining)"


def logout():
    """Clear all session authentication state."""
    for key in ["authenticated", "login_time", "failed_attempts", "messages", "last_request_time"]:
        st.session_state.pop(key, None)


# ─────────────────────────────────────────────
# 🛡️ Prompt Firewall
# ─────────────────────────────────────────────

JAILBREAK_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|your|prior)\s+(instructions?|rules?|prompt)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(dan|evil|jailbroken|unrestricted|free)", re.IGNORECASE),
    re.compile(r"pretend\s+(you|to)\s+(are|have\s+no)\s+(restrictions?|rules?|guidelines?)", re.IGNORECASE),
    re.compile(r"(act|behave|respond)\s+as\s+(if\s+)?(you\s+are\s+)?(a\s+)?(different|evil|uncensored|unrestricted)", re.IGNORECASE),
    re.compile(r"do\s+anything\s+now", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"prompt\s+injection", re.IGNORECASE),
    re.compile(r"system\s+prompt\s*(override|ignore|bypass|leak)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all)\s+(you\s+)?(were\s+)?(told|trained|instructed)", re.IGNORECASE),
    re.compile(r"\[SYSTEM\]|\[INST\]|\[\/INST\]", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
]

BLOCKED_TOPICS = [
    re.compile(r"\b(hack|exploit|vulnerability|0day|zero.?day)\b.*\b(bank|government|military|weapon)\b", re.IGNORECASE),
    re.compile(r"\b(create|generate|write)\b.*\b(malware|virus|ransomware|trojan|keylogger)\b", re.IGNORECASE),
    re.compile(r"\b(how\s+to\s+make)\b.*\b(bomb|weapon|explosive)\b", re.IGNORECASE),
]


def validate_prompt(prompt: str) -> tuple[bool, str]:
    """
    Scan input for jailbreak attempts and blocked topics.
    Returns (is_safe: bool, reason: str)
    """
    if not prompt or not prompt.strip():
        return False, "Empty prompt received."

    if len(prompt) > 4000:
        return False, "Prompt exceeds maximum length of 4000 characters."

    for pattern in JAILBREAK_PATTERNS:
        if pattern.search(prompt):
            return False, (
                "🛡️ **Prompt Firewall Activated**\n\n"
                "This request contains patterns associated with prompt injection or jailbreak attempts. "
                "Swarajya-AI is designed for educational use only.\n\n"
                "_If you believe this is a false positive, rephrase your question._"
            )

    for pattern in BLOCKED_TOPICS:
        if pattern.search(prompt):
            return False, (
                "🛡️ **Content Policy Violation**\n\n"
                "This request touches topics outside Swarajya-AI's educational scope. "
                "Please ask about IT engineering, computer science, or SPPU academics."
            )

    return True, ""


# ─────────────────────────────────────────────
# ⏱️ Rate Limiter
# ─────────────────────────────────────────────

def check_rate_limit() -> tuple[bool, float]:
    """
    Enforce minimum gap between requests per session.
    Returns (is_allowed: bool, wait_seconds: float)
    """
    last_time = st.session_state.get("last_request_time", 0)
    elapsed = time.time() - last_time

    if elapsed < MIN_REQUEST_GAP_SECONDS:
        wait = MIN_REQUEST_GAP_SECONDS - elapsed
        return False, round(wait, 1)

    return True, 0.0


def record_request_time():
    """Mark the current time as the last request time for this session."""
    st.session_state["last_request_time"] = time.time()
