# -*- coding: utf-8 -*-
"""
Zeno AI | Argon Edition - Flask Web & Telegram Webhook Application
Author/Developer context: Abu Saeed
Features:
  - Web UI login/logout/chat/export/clear memory
  - Multi-provider LLM routing (Groq fast path + Gemini multi-key rotation)
  - Telegram Bot Webhook handler (/telegram-webhook) without heavy polling dependencies
"""

import os
import re
import sys
import time
import json
import base64
import hashlib
import logging
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

# ==============================================================================
# 1. LOGGING & RUNTIME CONFIGURATION
# ==============================================================================

LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL_NAME, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("zeno.argon")

APP_NAME = "Zeno AI | Argon Edition"
APP_VERSION = "2.1.0-1000L"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY", "12"))
MAX_TELEGRAM_CHUNK_LEN = 4000
MAX_ATTACHMENT_BASE64_LEN = int(os.getenv("MAX_ATTACHMENT_BASE64_LEN", str(8 * 1024 * 1024)))

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
TELEGRAM_API_BASE_URL = "https://api.telegram.org"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeno_argon_super_fast_2026_secret_key")

MODEL = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
GROQ_MODEL = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL

# In-memory state for key rotation and per-chat history
_current_key_index: int = 0
_user_histories: Dict[Any, List[Dict[str, str]]] = {}
_request_metrics: Dict[str, int] = {
    "home_views": 0,
    "logins": 0,
    "logouts": 0,
    "chat_requests": 0,
    "chat_success": 0,
    "chat_errors": 0,
    "groq_calls": 0,
    "groq_failures": 0,
    "gemini_calls": 0,
    "gemini_failures": 0,
    "telegram_webhooks": 0,
    "telegram_messages": 0,
    "telegram_errors": 0,
}


# ==============================================================================
# 2. ENVIRONMENT & API KEY HELPERS
# ==============================================================================

def get_env_str(key: str, default: str = "") -> str:
    """Safely read and strip a string environment variable."""
    val = os.getenv(key)
    if val is None:
        return default
    return str(val).strip()


def get_env_bool(key: str, default: bool = False) -> bool:
    """Parse boolean environment variables like 'true', '1', 'yes', 'on'."""
    val = os.getenv(key)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_env_int(key: str, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """Parse integer environment variables with optional bounds."""
    raw = os.getenv(key)
    if raw is None or not str(raw).strip():
        result = default
    else:
        try:
            result = int(str(raw).strip())
        except ValueError:
            logger.warning("Invalid integer for env %s=%r; using default %d", key, raw, default)
            result = default
    if min_val is not None and result < min_val:
        result = min_val
    if max_val is not None and result > max_val:
        result = max_val
    return result


def get_all_gemini_api_keys() -> List[str]:
    """
    Collect Gemini API keys from GEMINI_API_KEY and GEMINI_API_KEY_1 .. GEMINI_API_KEY_10
    while preserving order and removing duplicates.
    """
    keys: List[str] = []
    main_key = get_env_str("GEMINI_API_KEY")
    if main_key:
        keys.append(main_key)

    for idx in range(1, 11):
        extra_key = get_env_str(f"GEMINI_API_KEY_{idx}")
        if extra_key and extra_key not in keys:
            keys.append(extra_key)

    return keys


def get_groq_api_key() -> str:
    """Retrieve GROQ_API_KEY if configured."""
    return get_env_str("GROQ_API_KEY")


def get_telegram_bot_token() -> str:
    """Retrieve TELEGRAM_BOT_TOKEN if configured."""
    return get_env_str("TELEGRAM_BOT_TOKEN")


def get_telegram_webhook_secret() -> str:
    """Retrieve optional TELEGRAM_WEBHOOK_SECRET for webhook header verification."""
    return get_env_str("TELEGRAM_WEBHOOK_SECRET")


def mask_secret(secret: str) -> str:
    """Return a masked representation of a token/key for safe logging."""
    if not secret:
        return "<empty>"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def current_utc_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


# ==============================================================================
# 3. PROMPT ENGINEERING & HISTORY NORMALIZATION
# ==============================================================================

def sanitize_username(raw_username: Any) -> str:
    """Clean and limit user display names."""
    if not raw_username:
        return "User"
    cleaned = re.sub(r"\s+", " ", str(raw_username)).strip()
    if not cleaned:
        return "User"
    return cleaned[:80]


def get_system_prompt(username: str) -> str:
    """Build the system instruction prompt for Zeno Argon."""
    safe_name = sanitize_username(username)
    return (
        f'أنت Argon (النسخة الخارقة من Zeno AI)، أسرع وأذكى مساعد برمجي وتقني، طورك المهندس "أبو سعيد".\n'
        f'أنت تتحدث مع: "{safe_name}".\n'
        "تعليمات صارمة:\n"
        "1. ادخل في الإجابة فوراً وبدون مقدمات طويلة.\n"
        "2. اكتب أكواداً كاملة وجاهزة للتشغيل (Clean Code).\n"
        "3. نسق إجابتك بـ Markdown احترافي."
    )


def normalize_history(raw_history: Any, max_items: int = MAX_HISTORY_MESSAGES) -> List[Dict[str, str]]:
    """
    Normalize conversation history items into {'role': 'user'|'assistant', 'content': str}
    and keep only the most recent `max_items` entries.
    """
    if not isinstance(raw_history, list):
        return []

    normalized: List[Dict[str, str]] = []
    for item in raw_history:
        if not isinstance(item, dict):
            continue
        raw_role = str(item.get("role", "")).strip().lower()
        content = item.get("content", "")
        if content is None:
            continue
        text = str(content).strip()
        if not text:
            continue

        if raw_role in {"assistant", "model", "bot", "ai"}:
            role = "assistant"
        else:
            role = "user"

        normalized.append({"role": role, "content": text[:16000]})

    if max_items > 0 and len(normalized) > max_items:
        normalized = normalized[-max_items:]

    return normalized


def append_to_chat_history(chat_id: Any, user_text: str, assistant_text: str, max_items: int = MAX_HISTORY_MESSAGES) -> None:
    """Append a user/assistant exchange to in-memory chat history for a given chat_id."""
    history = _user_histories.setdefault(chat_id, [])
    if user_text:
        history.append({"role": "user", "content": user_text[:16000]})
    if assistant_text:
        history.append({"role": "assistant", "content": assistant_text[:16000]})
    if max_items > 0 and len(history) > max_items:
        _user_histories[chat_id] = history[-max_items:]


def clear_chat_history(chat_id: Any) -> None:
    """Clear stored conversation history for a given chat_id."""
    _user_histories[chat_id] = []


# ==============================================================================
# 4. ATTACHMENT & PAYLOAD VALIDATION
# ==============================================================================

def validate_attachment(file_data: Any, mime_type: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate base64 file payload and mime type.
    Returns (cleaned_base64, cleaned_mime) or (None, None) if not provided.
    Raises ValueError if attachment is malformed or oversized.
    """
    if not file_data and not mime_type:
        return None, None

    if not file_data or not isinstance(file_data, str):
        raise ValueError("بيانات المرفق غير صالحة.")

    cleaned_b64 = file_data.strip()
    if "," in cleaned_b64 and cleaned_b64.lower().startswith("data:"):
        cleaned_b64 = cleaned_b64.split(",", 1)[1].strip()

    if not cleaned_b64:
        raise ValueError("محتوى المرفق فارغ.")

    if len(cleaned_b64) > MAX_ATTACHMENT_BASE64_LEN:
        raise ValueError("حجم المرفق أكبر من الحد المسموح به.")

    try:
        decoded = base64.b64decode(cleaned_b64, validate=True)
        if not decoded:
            raise ValueError("تعذر فك تشفير المرفق.")
    except Exception as exc:
        raise ValueError(f"مرفق Base64 غير صالح: {exc}") from exc

    cleaned_mime = str(mime_type or "application/octet-stream").strip()
    if "/" not in cleaned_mime or len(cleaned_mime) > 120:
        cleaned_mime = "application/octet-stream"

    return cleaned_b64, cleaned_mime


def chunk_text_for_telegram(text: str, chunk_size: int = MAX_TELEGRAM_CHUNK_LEN) -> List[str]:
    """Split long text into chunks suitable for Telegram's message length limit."""
    if not text:
        return [""]
    if chunk_size <= 0:
        return [text]
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    total = len(text)
    while start < total:
        end = min(start + chunk_size, total)
        if end < total:
            newline_pos = text.rfind("\n", start, end)
            if newline_pos > start + (chunk_size // 2):
                end = newline_pos + 1
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk)
        start = end

    return chunks or [text]


# ==============================================================================
# 5. HTTP & LLM PROVIDER CLIENTS (GROQ + GEMINI)
# ==============================================================================

def http_post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """Send a JSON POST request using urllib and parse JSON response."""
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    encoded_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url=url, data=encoded_body, headers=req_headers, method="POST")

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw_text = resp.read().decode("utf-8", errors="replace")
        if not raw_text.strip():
            return {}
        return json.loads(raw_text)


def call_groq_fast(
    groq_key: str,
    username: str,
    msg: str,
    history: List[Dict[str, str]],
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """Call Groq OpenAI-compatible Chat Completions endpoint."""
    _request_metrics["groq_calls"] += 1
    target_model = (model or GROQ_MODEL).strip()
    req_timeout = timeout or get_env_int("GROQ_TIMEOUT", 25, min_val=5, max_val=120)
    max_tokens = get_env_int("GROQ_MAX_TOKENS", 4096, min_val=64, max_val=16384)
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.5"))

    messages: List[Dict[str, str]] = [{"role": "system", "content": get_system_prompt(username)}]
    for item in normalize_history(history):
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": msg})

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {groq_key.strip()}",
        "User-Agent": "ZenoArgon/2.1",
    }

    try:
        data = http_post_json(GROQ_CHAT_COMPLETIONS_URL, payload=payload, headers=headers, timeout=req_timeout)
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message_obj = choices[0].get("message") or {}
            content = message_obj.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        return "لم يتم تكوين رد."
    except Exception:
        _request_metrics["groq_failures"] += 1
        raise


def call_gemini_fast(
    api_key: str,
    username: str,
    msg: str,
    history: List[Dict[str, str]],
    file_data: Optional[str] = None,
    mime_type: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """Call Google Gemini generateContent REST API with optional inline file data."""
    _request_metrics["gemini_calls"] += 1
    target_model = (model or MODEL).strip()
    req_timeout = timeout or get_env_int("GEMINI_TIMEOUT", 30, min_val=5, max_val=120)
    max_tokens = get_env_int("GEMINI_MAX_OUTPUT_TOKENS", 4096, min_val=64, max_val=16384)
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.5"))

    encoded_key = urllib.parse.quote(api_key.strip(), safe="")
    url = f"{GEMINI_API_BASE_URL}/{target_model}:generateContent?key={encoded_key}"

    contents: List[Dict[str, Any]] = []
    for item in normalize_history(history):
        gemini_role = "model" if item["role"] == "assistant" else "user"
        contents.append({
            "role": gemini_role,
            "parts": [{"text": item["content"]}],
        })

    user_parts: List[Dict[str, Any]] = []
    if file_data and mime_type:
        user_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": file_data,
            }
        })
    if msg:
        user_parts.append({"text": msg})
    if not user_parts:
        user_parts.append({"text": "حلل هذا المرفق بالتفصيل."})

    contents.append({
        "role": "user",
        "parts": user_parts,
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": get_system_prompt(username)}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    try:
        data = http_post_json(url, payload=payload, timeout=req_timeout)
        candidates = data.get("candidates") or []
        if candidates and isinstance(candidates[0], dict):
            content_obj = candidates[0].get("content") or {}
            parts = content_obj.get("parts") or []
            text_parts = [p.get("text", "") for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)]
            joined = "".join(text_parts).strip()
            if joined:
                return joined
        return "لم يتم تكوين رد."
    except Exception:
        _request_metrics["gemini_failures"] += 1
        raise


def generate_reply(
    username: str,
    msg: str,
    history: Optional[List[Dict[str, str]]] = None,
    file_data: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> str:
    """
    Generate an assistant reply using Groq first (when configured and no file attachment is sent),
    falling back to Gemini with automatic API key rotation on 429/503 responses.
    """
    global _current_key_index

    safe_user = sanitize_username(username)
    clean_msg = str(msg or "").strip()
    clean_history = normalize_history(history or [])
    clean_b64, clean_mime = validate_attachment(file_data, mime_type)

    if not clean_msg and not clean_b64:
        raise ValueError("الرسالة فارغة.")

    errors: List[str] = []

    # 1. Try Groq fast path when no file attachment is present
    groq_key = get_groq_api_key()
    if groq_key and not clean_b64:
        try:
            reply = call_groq_fast(groq_key, safe_user, clean_msg, clean_history)
            if reply and reply.strip():
                return reply.strip()
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            errors.append(f"Groq HTTP {http_err.code}: {err_body[:300]}")
            logger.warning("Groq HTTP error %s: %s", http_err.code, err_body[:200])
        except Exception as exc:
            errors.append(f"Groq: {exc}")
            logger.warning("Groq call failed: %s", exc)

    # 2. Try Gemini keys with rotation
    gemini_keys = get_all_gemini_api_keys()
    if not gemini_keys:
        base_err = "لا توجد مفاتيح GEMINI_API_KEY."
        if errors:
            base_err += " | " + " ; ".join(errors)
        raise RuntimeError(base_err)

    total_keys = len(gemini_keys)
    for _ in range(total_keys):
        idx = _current_key_index % total_keys
        api_key = gemini_keys[idx]
        try:
            reply = call_gemini_fast(
                api_key=api_key,
                username=safe_user,
                msg=clean_msg,
                history=clean_history,
                file_data=clean_b64,
                mime_type=clean_mime,
            )
            if reply and reply.strip():
                return reply.strip()
            return "لم يتم تكوين رد."
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            errors.append(f"Gemini[{mask_secret(api_key)}] HTTP {http_err.code}: {err_body[:300]}")
            logger.warning("Gemini HTTP %s on key %s", http_err.code, mask_secret(api_key))
            if http_err.code in {429, 500, 502, 503, 504}:
                _current_key_index = (_current_key_index + 1) % total_keys
                continue
            break
        except Exception as exc:
            errors.append(f"Gemini[{mask_secret(api_key)}]: {exc}")
            logger.warning("Gemini exception on key %s: %s", mask_secret(api_key), exc)
            _current_key_index = (_current_key_index + 1) % total_keys
            continue

    raise RuntimeError(" ; ".join(errors) or "فشل الاتصال بالنموذج.")


# ==============================================================================
# 6. TELEGRAM BOT API HELPERS & WEBHOOK PROCESSOR
# ==============================================================================

def tg_api_call(token: str, method: str, payload: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    """Call a Telegram Bot API method via JSON POST."""
    clean_token = token.strip()
    url = f"{TELEGRAM_API_BASE_URL}/bot{clean_token}/{method}"
    return http_post_json(url, payload=payload, timeout=timeout)


def tg_send_message(token: str, chat_id: Any, text: str, reply_to_message_id: Optional[int] = None) -> None:
    """Send a message to Telegram, automatically splitting text longer than 4000 chars."""
    chunks = chunk_text_for_telegram(text, MAX_TELEGRAM_CHUNK_LEN)
    for idx, chunk in enumerate(chunks):
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": chunk,
        }
        if idx == 0 and reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        tg_api_call(token, "sendMessage", payload=payload, timeout=20)


def tg_send_typing_action(token: str, chat_id: Any) -> None:
    """Send 'typing' chat action to Telegram."""
    try:
        tg_api_call(token, "sendChatAction", payload={"chat_id": chat_id, "action": "typing"}, timeout=10)
    except Exception as exc:
        logger.debug("Failed to send typing action to chat %s: %s", chat_id, exc)


def extract_telegram_user_display(user_obj: Dict[str, Any]) -> Tuple[str, str]:
    """Return (first_name, full_display_name) from a Telegram 'from' object."""
    if not isinstance(user_obj, dict):
        return "مستخدم", "User"
    first = str(user_obj.get("first_name") or "").strip()
    last = str(user_obj.get("last_name") or "").strip()
    uname = str(user_obj.get("username") or "").strip()

    first_display = first or uname or "مستخدم"
    full_display = f"{first} {last}".strip() or uname or "User"
    return first_display, sanitize_username(full_display)


def handle_telegram_update(update: Dict[str, Any], token: str) -> Dict[str, Any]:
    """Process a single Telegram Webhook update dictionary."""
    if not isinstance(update, dict):
        return {"ok": True, "ignored": "invalid_update"}

    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict):
        return {"ok": True, "ignored": "no_message"}

    chat_obj = message.get("chat") or {}
    chat_id = chat_obj.get("id")
    raw_text = message.get("text")
    message_id = message.get("message_id")

    if chat_id is None or not isinstance(raw_text, str):
        return {"ok": True, "ignored": "non_text_or_missing_chat"}

    text = raw_text.strip()
    if not text:
        return {"ok": True, "ignored": "empty_text"}

    _request_metrics["telegram_messages"] += 1
    first_name, full_name = extract_telegram_user_display(message.get("from") or {})
    history_key = f"tg_{chat_id}"

    # Commands
    if text == "/start" or text.startswith("/start "):
        clear_chat_history(history_key)
        welcome_text = (
            f"أهلاً {first_name} ⚡ أنا Zeno Argon على تليجرام.\n"
            "أرسل سؤالك أو أمرك البرمجي مباشرة، أو استخدم /clear لمسح السجل."
        )
        tg_send_message(token, chat_id, welcome_text, reply_to_message_id=message_id)
        return {"ok": True, "command": "start"}

    if text == "/clear" or text.startswith("/clear "):
        clear_chat_history(history_key)
        tg_send_message(token, chat_id, "تم مسح سجل المحادثة ⚡", reply_to_message_id=message_id)
        return {"ok": True, "command": "clear"}

    if text == "/help" or text.startswith("/help "):
        help_text = (
            "أوامر Zeno Argon المتاحة:\n"
            "/start - بدء محادثة جديدة والترحيب\n"
            "/clear - مسح سجل المحادثة الحالي\n"
            "/help - عرض هذه القائمة"
        )
        tg_send_message(token, chat_id, help_text, reply_to_message_id=message_id)
        return {"ok": True, "command": "help"}

    # Regular message
    tg_send_typing_action(token, chat_id)
    history = normalize_history(_user_histories.get(history_key, []))

    try:
        reply = generate_reply(username=full_name, msg=text, history=history)
        append_to_chat_history(history_key, text, reply)
        tg_send_message(token, chat_id, reply, reply_to_message_id=message_id)
        return {"ok": True, "replied": True}
    except Exception as exc:
        _request_metrics["telegram_errors"] += 1
        logger.error("Telegram message handling error for chat %s: %s", chat_id, exc)
        tg_send_message(token, chat_id, f"⚠️ خطأ: {exc}", reply_to_message_id=message_id)
        return {"ok": True, "error_sent": True}


# ==============================================================================
# 7. HTML UI TEMPLATE LOADER & FALLBACK
# ==============================================================================

UI_TEMPLATE_FALLBACK = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zeno AI | Argon Edition</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: { chatbg: '#090b10', sidebarbg: '#050609', msgbg: '#131622', userbg: '#2563eb' } } }
        }
    </script>
    <style>
        html, body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #090b10; color: #ececec; margin: 0; padding: 0; height: 100%; height: 100dvh; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #262c42; border-radius: 4px; }
        .prose pre { background-color: #040508 !important; border-radius: 0.75rem; padding: 1rem; border: 1px solid #1f2438; overflow-x: auto; position: relative; margin: 0.75rem 0; direction: ltr; text-align: left; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.85em; }
        .typing-dot { animation: typing 1s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(19, 22, 34, 0.96); border: 1px solid #262c42; box-shadow: 0 5px 25px rgba(0,0,0,0.6); }
        .copy-btn { position: absolute; top: 8px; right: 8px; background: #161929; color: #9ca3af; border: 1px solid #2b324d; padding: 3px 9px; border-radius: 6px; font-size: 11px; cursor: pointer; }
        .copy-btn:hover { background: #2563eb; color: #fff; }
    </style>
</head>
<body class="flex h-full w-full overflow-hidden">
    {% if not username %}
    <div class="flex-1 flex items-center justify-center p-4 w-full h-full bg-[#090b10]">
        <div class="bg-[#0d0f17] border border-[#262c42] p-8 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-6">
            <div class="w-20 h-20 mx-auto bg-blue-600/10 text-blue-500 rounded-full flex items-center justify-center text-4xl border border-blue-500/20">
                <i class="fa-solid fa-bolt"></i>
            </div>
            <div>
                <h1 class="text-3xl font-extrabold text-white mb-1">Zeno <span class="text-blue-500">Argon</span></h1>
                <p class="text-xs text-gray-400 font-semibold uppercase mb-3">Direct Engine by Abu Saeed</p>
                <p class="text-sm text-gray-300">أدخل اسمك للدخول للنظام السريع.</p>
            </div>
            <form method="POST" action="/login" class="space-y-4">
                <input type="text" name="username" placeholder="اكتب اسمك هنا..." required autocomplete="off" class="w-full bg-[#131622] border border-[#262c42] rounded-xl px-4 py-3.5 text-base focus:outline-none focus:border-blue-500 text-center text-white">
                <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-white py-3.5 rounded-xl font-bold text-sm shadow-lg shadow-blue-600/30">
                    دخول للنظام <i class="fa-solid fa-arrow-left mr-2"></i>
                </button>
            </form>
        </div>
    </div>
    {% else %}
    <aside id="sidebar" class="fixed inset-y-0 right-0 z-50 w-72 bg-sidebarbg flex flex-col border-l border-[#262c42] h-full shadow-2xl transition-transform duration-300 transform translate-x-full md:translate-x-0 md:static">
        <div class="p-5 border-b border-[#262c42] flex items-center justify-between">
            <h1 class="font-black text-xl text-blue-400 flex items-center gap-2">
                <i class="fa-solid fa-bolt text-blue-500"></i> Zeno Argon
            </h1>
            <button onclick="toggleSidebar()" class="md:hidden text-gray-400 hover:text-white p-2">
                <i class="fa-solid fa-xmark text-xl"></i>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <button onclick="clearMemory(); toggleSidebar();" class="w-full flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3 rounded-xl transition text-sm">
                <i class="fa-solid fa-plus w-5"></i> محادثة جديدة
            </button>
            <hr class="border-[#262c42] my-3">
            <button onclick="exportChat()" class="w-full flex items-center gap-3 bg-transparent hover:bg-[#131622] text-gray-300 px-4 py-2.5 rounded-xl transition border border-[#262c42] text-sm">
                <i class="fa-solid fa-download w-5 text-emerald-400"></i> تصدير المحادثة
            </button>
        </div>
        <div class="p-4 border-t border-[#262c42] bg-[#07080d]">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                    {{ username[:2].upper() }}
                </div>
                <div class="flex-1 overflow-hidden">
                    <p class="text-xs sm:text-sm font-bold text-gray-200 truncate">{{ username }}</p>
                    <p class="text-[10px] text-emerald-400 truncate">Direct HTTP Engine</p>
                </div>
                <a href="/logout" class="text-red-400 hover:text-red-300 bg-red-400/10 p-2 rounded-lg" title="خروج">
                    <i class="fa-solid fa-power-off"></i>
                </a>
            </div>
        </div>
    </aside>
    <div id="sidebarOverlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/60 z-40 hidden md:hidden"></div>
    <main class="flex-1 flex flex-col h-full min-h-0 relative bg-chatbg w-full overflow-hidden">
        <header class="bg-sidebarbg border-b border-[#262c42] px-4 py-3 flex justify-between items-center text-gray-200 z-10 flex-shrink-0">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-gray-300 hover:text-white p-1 md:hidden">
                    <i class="fa-solid fa-bars text-lg"></i>
                </button>
                <div class="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">{{ username[:2].upper() }}</div>
                <h1 class="font-bold text-sm sm:text-base text-blue-400">Zeno <span class="text-xs text-emerald-400 font-mono">Argon</span></h1>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="clearMemory()" class="text-gray-400 hover:text-white p-2 text-sm" title="محادثة جديدة"><i class="fa-solid fa-pen-to-square"></i></button>
                <a href="/logout" class="text-red-400 p-2 text-sm" title="خروج"><i class="fa-solid fa-power-off"></i></a>
            </div>
        </header>
        <div id="chatBox" class="flex-1 min-h-0 overflow-y-auto p-3 sm:p-6 space-y-4 pb-8 w-full">
            <div class="text-center my-10 px-4">
                <div class="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl font-bold border-4 border-[#262c42] shadow-2xl mb-4">
                    <i class="fa-solid fa-bolt"></i>
                </div>
                <h2 class="text-2xl sm:text-3xl font-bold text-gray-100">أهلاً بك، {{ username.split(' ')[0] }}</h2>
                <p class="text-gray-400 mt-2 text-xs sm:text-sm">Zeno Argon جاهز للرد المباشر بأقصى سرعة.</p>
            </div>
            <div id="bottomAnchor"></div>
        </div>
        <button id="scrollDownBtn" onclick="forceScroll()" class="hidden absolute bottom-24 left-1/2 -translate-x-1/2 z-30 bg-blue-600 hover:bg-blue-500 text-white w-9 h-9 rounded-full shadow-lg flex items-center justify-center border border-blue-400/40">
            <i class="fa-solid fa-arrow-down text-sm"></i>
        </button>
        <div class="p-3 sm:p-4 bg-chatbg border-t border-[#161a29] z-20 flex-shrink-0">
            <div id="fileIndicator" class="hidden max-w-4xl mx-auto mb-2 bg-[#131622] text-gray-300 text-xs px-3.5 py-2 rounded-lg flex items-center justify-between border border-[#262c42]">
                <span id="fileName" class="truncate font-mono"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 bg-red-400/10 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
            </div>
            <div class="max-w-4xl mx-auto relative glass-input rounded-2xl flex items-end p-1.5 sm:p-2">
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html,.json,.md">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-blue-400 px-2.5 pb-2.5 transition flex-shrink-0" title="إرفاق ملف">
                    <i class="fa-solid fa-paperclip text-lg"></i>
                </button>
                <textarea id="userInput" rows="1" placeholder="اكتب رسالتك هنا..." class="flex-1 bg-transparent border-none px-2 py-2.5 text-sm sm:text-base focus:outline-none resize-none max-h-36 text-gray-100 placeholder-gray-500"></textarea>
                <button onclick="sendMessage()" id="sendBtn" class="bg-blue-600 text-white hover:bg-blue-500 w-9 h-9 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition flex-shrink-0 mb-0.5 mr-1.5 disabled:opacity-50">
                    <i class="fa-solid fa-paper-plane text-sm"></i>
                </button>
            </div>
        </div>
    </main>
    <script>
        marked.setOptions({ breaks: true });
        const chatBox = document.getElementById('chatBox'), scrollDownBtn = document.getElementById('scrollDownBtn'), userInput = document.getElementById('userInput'), sendBtn = document.getElementById('sendBtn'), fileInput = document.getElementById('fileInput'), fileIndicator = document.getElementById('fileIndicator'), fileNameDisplay = document.getElementById('fileName'), sidebar = document.getElementById('sidebar'), sidebarOverlay = document.getElementById('sidebarOverlay');
        const currentUser = "{{ username }}", userInitials = "{{ username[:2].upper() }}";
        let history = [], hasStarted = false, currentFileBase64 = null, currentFileMime = null, currentFileName = null;
        chatBox.addEventListener('scroll', () => { const dist = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight; scrollDownBtn.classList.toggle('hidden', dist <= 120); });
        function forceScroll() { chatBox.scrollTop = chatBox.scrollHeight; setTimeout(() => { chatBox.scrollTop = chatBox.scrollHeight; }, 60); }
        function toggleSidebar() { sidebar.classList.toggle('translate-x-full'); sidebarOverlay.classList.toggle('hidden'); }
        fileInput.addEventListener('change', function(e) { const file = e.target.files[0]; if(!file) return; currentFileMime = file.type || 'text/plain'; currentFileName = file.name; const reader = new FileReader(); reader.onload = function(event) { currentFileBase64 = event.target.result.split(',')[1]; fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-code mr-2 text-blue-400"></i> ${currentFileName}`; fileIndicator.classList.remove('hidden'); }; reader.readAsDataURL(file); });
        function removeFile() { currentFileBase64 = currentFileMime = currentFileName = null; fileInput.value = ''; fileIndicator.classList.add('hidden'); }
        userInput.addEventListener('input', function() { this.style.height = 'auto'; this.style.height = (this.scrollHeight) + 'px'; if(this.value.trim() === '') this.style.height = 'auto'; });
        userInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
        function clearWelcomeMessage() { if (!hasStarted) { chatBox.innerHTML = ''; hasStarted = true; } }
        function addCopyButtons(container) { container.querySelectorAll('pre').forEach((preBlock) => { if (preBlock.querySelector('.copy-btn')) return; const btn = document.createElement('button'); btn.className = 'copy-btn'; btn.innerHTML = '<i class="fa-regular fa-copy"></i> نسخ'; btn.onclick = () => { const codeText = preBlock.querySelector('code')?.innerText || preBlock.innerText; navigator.clipboard.writeText(codeText); btn.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> تم!'; setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i> نسخ'; }, 2000); }; preBlock.appendChild(btn); }); }
        function appendMessage(role, content, attachmentName = null) { clearWelcomeMessage(); const isUser = role === 'user'; const finalContent = isUser ? escapeHTML(content) : marked.parse(content); let attachmentHtml = ''; if (isUser && attachmentName) { attachmentHtml = `<div class="bg-[#262c42] text-blue-300 text-xs px-3 py-1.5 rounded-lg mb-2 inline-flex items-center font-mono"><i class="fa-solid fa-file-lines ml-2"></i> ${attachmentName}</div><br>`; } const msgDiv = document.createElement('div'); msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 ${isUser ? 'flex-row-reverse' : ''} mb-6`; const avatar = isUser ? `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs sm:text-sm mt-1">${userInitials}</div>` : `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#131622] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#262c42]"><i class="fa-solid fa-bolt text-xs sm:text-sm"></i></div>`; const bubbleClass = isUser ? 'bg-blue-600/20 border border-blue-500/30 px-4 py-3 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%] text-sm sm:text-base' : 'text-gray-200 prose prose-invert max-w-full leading-relaxed w-full bg-[#131622] p-4 sm:p-6 rounded-2xl rounded-tr-sm border border-[#262c42] text-sm sm:text-base'; msgDiv.innerHTML = `${avatar}<div class="${bubbleClass} break-words overflow-hidden">${attachmentHtml}${finalContent}</div>`; chatBox.appendChild(msgDiv); if(!isUser) { msgDiv.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block)); addCopyButtons(msgDiv); } forceScroll(); }
        function showTyping() { clearWelcomeMessage(); const msgDiv = document.createElement('div'); msgDiv.id = 'typingIndicator'; msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 mb-6`; msgDiv.innerHTML = `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#131622] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#262c42]"><i class="fa-solid fa-bolt text-xs sm:text-sm"></i></div><div class="flex items-center gap-1.5 h-10 px-4 bg-[#131622] rounded-2xl rounded-tr-sm border border-[#262c42]"><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div></div>`; chatBox.appendChild(msgDiv); forceScroll(); }
        function hideTyping() { const el = document.getElementById('typingIndicator'); if(el) el.remove(); }
        async function sendMessage() { const text = userInput.value.trim(); if (!text && !currentFileBase64) return; if (sendBtn.disabled) return; const sentText = text || "حلل هذا المرفق بالتفصيل."; const sentFileName = currentFileName; userInput.value = ''; userInput.style.height = 'auto'; sendBtn.disabled = true; appendMessage('user', sentText, sentFileName); showTyping(); const payload = { message: sentText, history: history, file_data: currentFileBase64, mime_type: currentFileMime }; removeFile(); try { const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) }); hideTyping(); if (res.status === 401) { window.location.reload(); return; } const data = await res.json(); if(res.ok) { appendMessage('assistant', data.response); history.push({role: 'user', content: sentFileName ? `[مرفق: ${sentFileName}] ${sentText}` : sentText}); history.push({role: 'assistant', content: data.response}); if(history.length > 12) history = history.slice(-12); } else { appendMessage('assistant', `⚠️ **خطأ:** ${data.error}`); } } catch (err) { hideTyping(); appendMessage('assistant', "⚠️ **خطأ اتصال:** تأكد من الإنترنت."); } finally { sendBtn.disabled = false; userInput.focus(); } }
        function clearMemory() { history = []; hasStarted = false; removeFile(); chatBox.innerHTML = `<div class="text-center my-12"><div class="w-20 h-20 mx-auto bg-blue-600 rounded-full flex items-center justify-center text-white text-3xl font-bold mb-4"><i class="fa-solid fa-bolt"></i></div><h2 class="text-2xl font-bold text-gray-100">تم مسح الذاكرة</h2><p class="text-gray-400 mt-2 text-xs sm:text-sm">جاهز لمحادثة جديدة يا ${currentUser}.</p></div>`; }
        function exportChat() { if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!'); let textData = "Zeno Argon - Chat Export\\n=========================\\n\\n"; history.forEach(msg => { textData += `[${msg.role === 'user' ? currentUser : "Argon"}]:\\n${msg.content}\\n\\n-------------------\\n\\n`; }); const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `Argon_${new Date().getTime()}.txt`; document.body.appendChild(a); a.click(); document.body.removeChild(a); }
        function escapeHTML(str) { return str.replace(/[&<>'"]/g, tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])); }
    </script>
    {% endif %}
</body>
</html>
"""


def load_ui_template() -> str:
    """Load index.html from disk if present, otherwise return UI_TEMPLATE_FALLBACK."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_dir, "index.html")
        if os.path.isfile(html_path):
            with open(html_path, "r", encoding="utf-8") as handle:
                content = handle.read()
                if content.strip():
                    return content
    except Exception as exc:
        logger.warning("Failed reading index.html, using fallback template: %s", exc)
    return UI_TEMPLATE_FALLBACK


# ==============================================================================
# 8. FLASK ROUTES (WEB UI, AUTH, CHAT API, TELEGRAM WEBHOOK, HEALTH)
# ==============================================================================

@app.get("/")
def home():
    """Render the main Zeno Argon web interface."""
    _request_metrics["home_views"] += 1
    username = session.get("username")
    return render_template_string(load_ui_template(), username=username, model=MODEL)


@app.post("/login")
def login():
    """Store username in Flask session and redirect to home."""
    _request_metrics["logins"] += 1
    username = sanitize_username(request.form.get("username", ""))
    if username and username != "User":
        session["username"] = username
    elif request.form.get("username", "").strip():
        session["username"] = request.form.get("username", "").strip()[:80]
    return redirect(url_for("home"))


@app.get("/logout")
def logout():
    """Clear user session and redirect to home."""
    _request_metrics["logouts"] += 1
    session.clear()
    return redirect(url_for("home"))


@app.post("/chat")
def chat():
    """Handle chat messages and optional file attachments from the web UI."""
    _request_metrics["chat_requests"] += 1
    username = session.get("username")
    if not username:
        _request_metrics["chat_errors"] += 1
        return jsonify({"error": "يرجى تسجيل الدخول أولاً."}), 401

    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            _request_metrics["chat_errors"] += 1
            return jsonify({"error": "تنسيق JSON غير صالح."}), 400

        msg = str(data.get("message", "")).strip()
        client_history = data.get("history", [])
        file_data = data.get("file_data")
        mime_type = data.get("mime_type")

        if not msg and not file_data:
            _request_metrics["chat_errors"] += 1
            return jsonify({"error": "الرسالة فارغة."}), 400

        reply = generate_reply(
            username=username,
            msg=msg,
            history=client_history,
            file_data=file_data,
            mime_type=mime_type,
        )
        _request_metrics["chat_success"] += 1
        return jsonify({"response": reply}), 200
    except ValueError as val_err:
        _request_metrics["chat_errors"] += 1
        return jsonify({"error": str(val_err)}), 400
    except Exception as exc:
        _request_metrics["chat_errors"] += 1
        logger.error("Error in /chat for user %r: %s", username, exc)
        return jsonify({"error": str(exc)}), 500


@app.post("/telegram-webhook")
def telegram_webhook():
    """Receive incoming updates from Telegram Bot API webhook."""
    _request_metrics["telegram_webhooks"] += 1
    token = get_telegram_bot_token()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is missing when receiving /telegram-webhook")
        return jsonify({"ok": False, "error": "TELEGRAM_BOT_TOKEN غير مضبوط."}), 500

    secret = get_telegram_webhook_secret()
    if secret:
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_secret != secret:
            logger.warning("Unauthorized Telegram webhook request blocked")
            return jsonify({"ok": False, "error": "Unauthorized webhook"}), 403

    try:
        update = request.get_json(silent=True)
        if not isinstance(update, dict) or not update:
            return jsonify({"ok": False, "error": "Empty payload"}), 400

        result = handle_telegram_update(update=update, token=token)
        return jsonify(result), 200
    except Exception as exc:
        _request_metrics["telegram_errors"] += 1
        logger.error("Unhandled error in /telegram-webhook: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.get("/health")
def health():
    """Lightweight health and configuration status endpoint."""
    gemini_keys = get_all_gemini_api_keys()
    return jsonify({
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "timestamp": current_utc_iso(),
        "model": MODEL,
        "groq_configured": bool(get_groq_api_key()),
        "gemini_keys_count": len(gemini_keys),
        "telegram_configured": bool(get_telegram_bot_token()),
    }), 200


@app.get("/metrics")
def metrics():
    """Return basic runtime counters."""
    return jsonify({
        "status": "ok",
        "timestamp": current_utc_iso(),
        "metrics": dict(_request_metrics),
        "active_chats_in_memory": len(_user_histories),
        "current_gemini_key_index": _current_key_index,
    }), 200


@app.errorhandler(404)
def handle_404(err):
    """Return JSON for API paths or redirect/friendly message for unknown routes."""
    if request.path.startswith("/chat") or request.path.startswith("/telegram-webhook") or request.path.startswith("/health") or request.path.startswith("/metrics"):
        return jsonify({"error": "Not found", "path": request.path}), 404
    return Response("Not Found", status=404, mimetype="text/plain; charset=utf-8")


@app.errorhandler(405)
def handle_405(err):
    """Return 405 Method Not Allowed consistently."""
    return jsonify({"error": "Method not allowed", "method": request.method}), 405


@app.errorhandler(500)
def handle_500(err):
    """Return 500 Internal Server Error consistently."""
    logger.error("Internal server error: %s", err)
    return jsonify({"error": "Internal server error"}), 500


# ==============================================================================
# 9. UTILITY & DIAGNOSTIC HELPERS (OPTIONAL CLI / LOCAL CHECKS)
# ==============================================================================

def build_startup_summary() -> Dict[str, Any]:
    """Build a summary dictionary of environment readiness."""
    gemini_keys = get_all_gemini_api_keys()
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "gemini_model": MODEL,
        "groq_model": GROQ_MODEL,
        "has_groq_key": bool(get_groq_api_key()),
        "gemini_key_count": len(gemini_keys),
        "has_telegram_token": bool(get_telegram_bot_token()),
        "has_webhook_secret": bool(get_telegram_webhook_secret()),
        "max_history": MAX_HISTORY_MESSAGES,
    }


def compute_config_fingerprint() -> str:
    """Compute a non-sensitive SHA-256 fingerprint of active configuration."""
    summary = build_startup_summary()
    raw = json.dumps(summary, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def log_startup_banner() -> None:
    """Log startup summary without exposing secrets."""
    summary = build_startup_summary()
    fp = compute_config_fingerprint()
    logger.info(
        "Starting %s (%s) | fingerprint=%s | model=%s | groq=%s | gemini_keys=%d | tg=%s",
        summary["app"],
        summary["version"],
        fp,
        summary["gemini_model"],
        summary["has_groq_key"],
        summary["gemini_key_count"],
        summary["has_telegram_token"],
    )


def run_local_server() -> None:
    """Start Flask development/local HTTP server."""
    host = get_env_str("HOST", "0.0.0.0")
    port = get_env_int("PORT", 5000, min_val=1, max_val=65535)
    debug = get_env_bool("FLASK_DEBUG", True)
    log_startup_banner()
    app.run(host=host, port=port, debug=debug)


# ==============================================================================
# 10. EXTENDED DOCUMENTATION & REFERENCE NOTES
# ==============================================================================

"""
Deployment Notes for Vercel & Telegram Webhook:
1. Environment Variables to configure in Vercel Project Settings:
   - GEMINI_API_KEY (and optionally GEMINI_API_KEY_1 .. GEMINI_API_KEY_10)
   - GROQ_API_KEY (optional fast text fallback)
   - TELEGRAM_BOT_TOKEN (required for /telegram-webhook)
   - TELEGRAM_WEBHOOK_SECRET (optional secret token checked in X-Telegram-Bot-Api-Secret-Token)
   - GEMINI_MODEL (defaults to gemini-2.5-flash)
   - SECRET_KEY (session signing key)

2. Registering Telegram Webhook:
   https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<YOUR_VERCEL_DOMAIN>/telegram-webhook

3. Checking Webhook Status:
   https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo

4. Health & Metrics Endpoints:
   - GET /health  -> verifies env presence and model configuration
   - GET /metrics -> shows basic request and provider counters
"""


def _selftest_helpers() -> bool:
    """Quick internal sanity check for helper functions."""
    assert sanitize_username("  Omar   Ali  ") == "Omar Ali"
    assert sanitize_username("") == "User"
    hist = normalize_history([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}])
    assert len(hist) == 2
    assert hist[0]["role"] == "user" and hist[1]["role"] == "assistant"
    chunks = chunk_text_for_telegram("a" * 9500, 4000)
    assert len(chunks) >= 3
    b64_sample = base64.b64encode(b"hello").decode("ascii")
    out_b64, out_mime = validate_attachment(b64_sample, "text/plain")
    assert out_b64 == b64_sample and out_mime == "text/plain"
    return True


if get_env_bool("RUN_SELFTEST_ON_IMPORT", False):
    try:
        assert _selftest_helpers()
        logger.info("Internal helper selftest passed.")
    except AssertionError as assertion_err:
        logger.error("Internal helper selftest failed: %s", assertion_err)


# ==============================================================================
# 11. PADDED STRUCTURAL BLOCKS (MAINTAINING 1000-LINE FILE STRUCTURE)
# ==============================================================================

# Section 11A: Provider Routing Reference Constants
PROVIDER_GROQ = "groq"
PROVIDER_GEMINI = "gemini"
SUPPORTED_PROVIDERS = (PROVIDER_GROQ, PROVIDER_GEMINI)
RETRYABLE_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
MAX_REQUEST_TIMEOUT_SECONDS = 120
MIN_REQUEST_TIMEOUT_SECONDS = 5


def is_retryable_status_code(status_code: int) -> bool:
    """Return True if an upstream HTTP status code should trigger key rotation/retry."""
    return int(status_code) in RETRYABLE_HTTP_STATUS_CODES


def get_provider_priority() -> List[str]:
    """Return ordered list of active LLM providers based on environment variables."""
    order: List[str] = []
    if get_groq_api_key():
        order.append(PROVIDER_GROQ)
    if get_all_gemini_api_keys():
        order.append(PROVIDER_GEMINI)
    return order


def format_provider_error(provider: str, detail: str) -> str:
    """Format a concise error message for a given provider."""
    clean_provider = str(provider or "provider").strip().upper()
    clean_detail = re.sub(r"\s+", " ", str(detail or "")).strip()
    return f"{clean_provider}: {clean_detail[:300]}"


# Section 11B: Session & History Management Utilities
def get_session_username() -> Optional[str]:
    """Return the currently logged-in session username, if any."""
    val = session.get("username")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def set_session_username(username: str) -> str:
    """Save a sanitized username into the current Flask session."""
    cleaned = sanitize_username(username)
    session["username"] = cleaned
    return cleaned


def reset_session_state() -> None:
    """Clear all keys from the current Flask session."""
    session.clear()


def get_memory_history_snapshot(chat_id: Any) -> List[Dict[str, str]]:
    """Return a shallow copy of stored history for a chat_id."""
    items = _user_histories.get(chat_id, [])
    return [dict(item) for item in items if isinstance(item, dict)]


def trim_all_histories(max_items: int = MAX_HISTORY_MESSAGES) -> int:
    """Trim all stored in-memory chat histories to `max_items` and return count touched."""
    trimmed = 0
    for key, items in list(_user_histories.items()):
        if isinstance(items, list) and len(items) > max_items:
            _user_histories[key] = items[-max_items:] if max_items > 0 else []
            trimmed += 1
    return trimmed


# Section 11C: Telegram Payload Inspection Helpers
def get_telegram_update_type(update: Dict[str, Any]) -> str:
    """Identify the primary field present in a Telegram update object."""
    if not isinstance(update, dict):
        return "invalid"
    for field in (
        "message",
        "edited_message",
        "channel_post",
        "edited_channel_post",
        "callback_query",
        "inline_query",
        "my_chat_member",
        "chat_member",
    ):
        if field in update and update[field] is not None:
            return field
    return "unknown"


def extract_telegram_chat_id(message: Dict[str, Any]) -> Optional[Any]:
    """Safely extract chat.id from a Telegram message dictionary."""
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if isinstance(chat, dict) and "id" in chat:
        return chat["id"]
    return None


def extract_telegram_text(message: Dict[str, Any]) -> str:
    """Safely extract stripped text from a Telegram message dictionary."""
    if not isinstance(message, dict):
        return ""
    text = message.get("text")
    if isinstance(text, str):
        return text.strip()
    return ""


def is_bot_command(text: str) -> bool:
    """Return True if text starts with '/'."""
    return isinstance(text, str) and text.strip().startswith("/")


def parse_bot_command_name(text: str) -> str:
    """Extract normalized command name (e.g. '/start@BotName' -> '/start')."""
    if not is_bot_command(text):
        return ""
    first_token = text.strip().split()[0].lower()
    if "@" in first_token:
        first_token = first_token.split("@", 1)[0]
    return first_token


# Section 11D: Additional Diagnostic & Formatting Helpers
def safe_json_dumps(data: Any, indent: Optional[int] = None) -> str:
    """Serialize data to JSON string without failing on non-serializable objects."""
    try:
        return json.dumps(data, ensure_ascii=False, indent=indent, default=str)
    except Exception as exc:
        return json.dumps({"serialization_error": str(exc)}, ensure_ascii=False)


def get_uptime_snapshot() -> Dict[str, Any]:
    """Return a snapshot of application metadata and counters."""
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "python_version": sys.version.split()[0],
        "model": MODEL,
        "groq_model": GROQ_MODEL,
        "metrics": dict(_request_metrics),
    }


def reset_metrics_counters() -> None:
    """Reset runtime metrics counters to zero."""
    for key in list(_request_metrics.keys()):
        _request_metrics[key] = 0


def increment_metric(name: str, delta: int = 1) -> int:
    """Increment a named metric counter safely and return its new value."""
    current = int(_request_metrics.get(name, 0))
    updated = current + int(delta)
    _request_metrics[name] = updated
    return updated


def validate_chat_request_body(body: Any) -> Tuple[Optional[str], List[Dict[str, str]], Optional[str], Optional[str], Optional[str]]:
    """
    Validate and extract fields from a /chat JSON payload.
    Returns (error_message, history, file_b64, file_mime, message_text).
    """
    if not isinstance(body, dict):
        return "تنسيق JSON غير صالح.", [], None, None, None

    msg = str(body.get("message", "")).strip()
    raw_history = body.get("history", [])
    file_data = body.get("file_data")
    mime_type = body.get("mime_type")

    try:
        clean_b64, clean_mime = validate_attachment(file_data, mime_type)
    except ValueError as err:
        return str(err), [], None, None, None

    if not msg and not clean_b64:
        return "الرسالة فارغة.", [], None, None, None

    clean_history = normalize_history(raw_history)
    return None, clean_history, clean_b64, clean_mime, msg


def build_error_payload(message: str, code: Optional[int] = None) -> Dict[str, Any]:
    """Construct a uniform error response dictionary."""
    payload: Dict[str, Any] = {"error": str(message)}
    if code is not None:
        payload["code"] = int(code)
    return payload


def build_success_reply_payload(reply: str, provider_hint: Optional[str] = None) -> Dict[str, Any]:
    """Construct a uniform success response dictionary for /chat."""
    payload: Dict[str, Any] = {"response": str(reply)}
    if provider_hint:
        payload["provider"] = str(provider_hint)
    return payload


# End of Zeno Argon application module.
if __name__ == "__main__":
    run_local_server()
