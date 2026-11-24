# -*- coding: utf-8 -*-
"""Zeno AI | Argon Edition

تدفق /chat:
  1) Groq (إن وُجد GROQ_API_KEY ولا يوجد ملف مرفق) مع قائمة موديلات احتياطية.
  2) Gemini مع تدوير المفاتيح (GEMINI_API_KEY, GEMINI_API_KEY_1..10) وقائمة موديلات احتياطية.
  3) إذا فشل الاثنان: رسالة خطأ مفصّلة (بدون كشف أي مفتاح).
"""
import base64
import binascii
import logging
import os
import re
import threading
import time

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

try:  # اختياري: قراءة ملف .env محلياً
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("zeno")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# index.html بجانب app.py هو واجهة المستخدم الفعلية (قالب Jinja)
app = Flask(__name__, template_folder=BASE_DIR)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # حد Vercel ~4.5MB
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

_secret = os.getenv("SECRET_KEY")
if not _secret:
    log.warning("SECRET_KEY غير مضبوط؛ يتم استخدام مفتاح افتراضي. اضبطه في متغيرات البيئة.")
    _secret = "zeno_argon_super_fast_2026"
app.secret_key = _secret


def _unique(items):
    out = []
    for i in items:
        i = (i or "").strip()
        if i and i not in out:
            out.append(i)
    return out


# ملاحظة: llama-3.3-70b-versatile أوقفته Groq (16/08/2026). غيّر الموديل عبر GROQ_MODEL عند الحاجة.
GROQ_MODELS = _unique([os.getenv("GROQ_MODEL"), "openai/gpt-oss-120b", "qwen/qwen3.6-27b"])
GEMINI_MODELS = _unique([os.getenv("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-2.5-flash"])

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

MAX_HISTORY = 12
# ميزانية زمنية إجمالية لكل طلب /chat (ثوانٍ) كي لا تتراكم المحاولات الفاشلة
TIME_BUDGET = float(os.getenv("TIME_BUDGET", "40"))
# مستوى التفكير في Gemini 3.x: minimal/low/medium/high (الافتراضي في Google هو high وهو بطيء جداً)
GEMINI_THINKING = (os.getenv("GEMINI_THINKING") or "low").strip().lower()
MAX_TEXT_FILE_CHARS = 200_000

_key_lock = threading.Lock()
_key_index = 0


# ---------------------------------------------------------------- أخطاء
class ProviderError(Exception):
    """kind: model | key | transient | other"""

    def __init__(self, message, kind="other", status=None):
        super().__init__(message)
        self.kind = kind
        self.status = status


class ProviderFailed(Exception):
    def __init__(self, provider, errors):
        super().__init__(provider)
        self.provider = provider
        self.errors = errors


def _short(text, n=300):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[:n] + "…"


def _error_message(resp):
    try:
        err = resp.json().get("error", {})
        if isinstance(err, dict):
            return err.get("message") or str(err)
        return str(err)
    except Exception:
        return resp.text


# ---------------------------------------------------------------- أدوات
_GEMINI_KEY_RE = re.compile(r"^gemini_api_key_?(\d*)$", re.I)
_GROQ_KEY_RE = re.compile(r"^groq_api_key$", re.I)


def _env_matches(regex):
    """يرجع [(الاسم, القيمة)] لكل متغير بيئة يطابق النمط، بغض النظر عن حالة الأحرف."""
    out = []
    for name, val in os.environ.items():
        m = regex.match(name)
        if m and (val or "").strip():
            idx = int(m.group(1)) if m.groups() and m.group(1) else 0
            out.append((idx, name, val.strip()))
    out.sort()
    return [(n, v) for _, n, v in out]


def get_gemini_keys():
    """يقبل GEMINI_API_KEY و GEMINI_API_KEY_1.. وأيضاً Gemini_api_key1 (أي حالة أحرف)."""
    return _unique([v for _, v in _env_matches(_GEMINI_KEY_RE)])


def get_groq_key():
    found = _env_matches(_GROQ_KEY_RE)
    return found[0][1] if found else ""


def clean_username(name):
    name = re.sub(r"[\x00-\x1f\x7f]", " ", str(name or ""))
    return re.sub(r"\s+", " ", name).strip()[:40]


def get_system_prompt(username):
    return f"""أنت Argon (النسخة الخارقة من Zeno AI)، أسرع وأذكى مساعد برمجي وتقني، طورك المهندس "أبو سعيد".
أنت تتحدث مع: "{username}".
تعليمات صارمة:
1. ادخل في الإجابة فوراً وبدون مقدمات طويلة.
2. اكتب أكواداً كاملة وجاهزة للتشغيل (Clean Code).
3. نسق إجابتك بـ Markdown احترافي."""


def clean_history(raw):
    """يضمن شكل [{role: user|assistant, content: str}] يبدأ بـ user ويتناوب الأدوار."""
    if not isinstance(raw, list):
        return []
    out = []
    for h in raw[-MAX_HISTORY:]:
        if not isinstance(h, dict):
            continue
        role = "assistant" if h.get("role") == "assistant" else "user"
        text = str(h.get("content", "")).strip()
        if not text:
            continue
        if out and out[-1]["role"] == role:
            out[-1]["content"] += "\n\n" + text
        else:
            out.append({"role": role, "content": text[:20000]})
    while out and out[0]["role"] == "assistant":
        out.pop(0)
    return out


def build_user_parts(msg, file_data, mime_type, file_name):
    """صور وPDF تُرسل كما هي؛ الملفات النصية تُفك وتُرسل كنص (أضمن مع Gemini)."""
    parts = []
    if file_data:
        mime = (mime_type or "").strip().lower() or "text/plain"
        if mime.startswith("image/") or mime == "application/pdf":
            parts.append({"inline_data": {"mime_type": mime, "data": file_data}})
        else:
            try:
                text = base64.b64decode(file_data, validate=True).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError, ValueError):
                raise ValueError("تعذّر قراءة الملف المرفق كنص. المدعوم: صور، PDF، وملفات نصية UTF-8.")
            name = clean_username(file_name) or "attachment"
            parts.append({"text": f"--- بداية الملف المرفق: {name} ---\n{text[:MAX_TEXT_FILE_CHARS]}\n--- نهاية الملف ---"})
    if msg:
        parts.append({"text": msg})
    return parts


# ---------------------------------------------------------------- Groq
def _classify_groq(status, message):
    low = (message or "").lower()
    if status == 404 or "model_not_found" in low or "decommissioned" in low or "does not exist" in low:
        return "model"
    if status in (401, 403):
        return "key"
    if status == 429 or status >= 500:
        return "transient"
    return "other"


def _groq_request(api_key, model, messages, timeout):
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, "temperature": 0.5, "max_completion_tokens": 2048},
            timeout=(5, timeout),
        )
    except requests.RequestException as e:
        raise ProviderError(f"{type(e).__name__}: {_short(e, 150)}", "transient")

    if r.status_code != 200:
        msg = _error_message(r)
        raise ProviderError(f"HTTP {r.status_code} - {_short(msg)}", _classify_groq(r.status_code, msg), r.status_code)

    try:
        text = r.json()["choices"][0]["message"].get("content") or ""
    except Exception:
        raise ProviderError(f"رد غير متوقع: {_short(r.text)}", "other")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    if not text:
        raise ProviderError("رد فارغ من الموديل", "transient")
    return text


def call_groq(api_key, username, msg, history, deadline):
    messages = [{"role": "system", "content": get_system_prompt(username)}]
    messages += history
    messages.append({"role": "user", "content": msg})
    errors = []
    for model in GROQ_MODELS:
        remaining = deadline - time.monotonic()
        if remaining < 3:
            errors.append("Groq: انتهت الميزانية الزمنية للطلب")
            break
        try:
            text = _groq_request(api_key, model, messages, min(15, remaining))
            return text, model
        except ProviderError as e:
            errors.append(f"Groq · {model}: {e}")
            log.warning("Groq فشل (%s): %s", model, e)
            if e.kind in ("model", "transient"):
                continue  # جرّب الموديل التالي
            break  # مفتاح خاطئ أو طلب غير صالح: لا فائدة من المتابعة
    raise ProviderFailed("groq", errors)


# ---------------------------------------------------------------- Gemini
def _classify_gemini(status, message):
    low = (message or "").lower()
    if "api key" in low and ("invalid" in low or "expired" in low or "not valid" in low):
        return "key"
    if status == 404 or "is not found" in low or "not supported for generatecontent" in low:
        return "model"
    if status in (401, 403, 429):
        return "key"  # مفتاح غير صالح/محظور/تجاوز الحصة -> دوّر المفتاح
    if status >= 500:
        return "transient"
    return "other"


def _gen_config(model, with_thinking=True):
    cfg = {"maxOutputTokens": 4096}
    if model.startswith("gemini-3"):
        # Gemini 3 يفكّر بمستوى high افتراضياً (بطيء) والموصى به تركه temperature افتراضياً
        if with_thinking and GEMINI_THINKING:
            cfg["thinkingConfig"] = {"thinkingLevel": GEMINI_THINKING}
    else:
        cfg["temperature"] = 0.5
        if with_thinking and model.startswith("gemini-2.5-flash"):
            cfg["thinkingConfig"] = {"thinkingBudget": 0}
    return cfg


def _gemini_post(api_key, model, system_prompt, contents, timeout, with_thinking):
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": _gen_config(model, with_thinking),
    }
    try:
        return requests.post(
            f"{GEMINI_BASE}/{model}:generateContent",
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},  # المفتاح في الهيدر لا في الرابط
            json=payload,
            timeout=(5, timeout),
        )
    except requests.RequestException as e:
        raise ProviderError(f"{type(e).__name__}: {_short(e, 150)}", "transient")


def _gemini_request(api_key, model, system_prompt, contents, timeout):
    r = _gemini_post(api_key, model, system_prompt, contents, timeout, True)
    if r.status_code == 400 and "thinking" in (_error_message(r) or "").lower():
        log.warning("إعداد التفكير غير مدعوم في %s؛ إعادة المحاولة بدونه.", model)
        r = _gemini_post(api_key, model, system_prompt, contents, timeout, False)

    if r.status_code != 200:
        msg = _error_message(r)
        raise ProviderError(f"HTTP {r.status_code} - {_short(msg)}", _classify_gemini(r.status_code, msg), r.status_code)

    try:
        data = r.json()
    except ValueError:
        raise ProviderError(f"رد غير JSON: {_short(r.text)}", "transient")

    candidates = data.get("candidates") or []
    if candidates:
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if p.get("text") and not p.get("thought")).strip()
        if text:
            return text
        reason = candidates[0].get("finishReason", "UNKNOWN")
        raise ProviderError(f"رد فارغ (finishReason={reason})", "other")
    block = (data.get("promptFeedback") or {}).get("blockReason")
    raise ProviderError("لم يتم تكوين رد" + (f" (blockReason={block})" if block else ""), "other")


def call_gemini(keys, username, parts, history, deadline):
    global _key_index
    contents = [
        {"role": "model" if h["role"] == "assistant" else "user", "parts": [{"text": h["content"]}]}
        for h in history
    ]
    contents.append({"role": "user", "parts": parts})
    system_prompt = get_system_prompt(username)
    errors = []

    for model in GEMINI_MODELS:
        with _key_lock:
            start = _key_index % len(keys)
        order = [(start + i) % len(keys) for i in range(len(keys))]
        for idx in order:
            remaining = deadline - time.monotonic()
            if remaining < 3:
                errors.append("Gemini: انتهت الميزانية الزمنية للطلب")
                raise ProviderFailed("gemini", errors)
            try:
                text = _gemini_request(keys[idx], model, system_prompt, contents, min(30, remaining))
                with _key_lock:
                    _key_index = idx
                return text, model
            except ProviderError as e:
                errors.append(f"Gemini · {model} · مفتاح #{idx + 1}: {e}")
                log.warning("Gemini فشل (%s, مفتاح #%d): %s", model, idx + 1, e)
                if e.kind == "model":
                    break  # الموديل نفسه غير متاح: انتقل للموديل التالي
                if e.kind in ("key", "transient"):
                    with _key_lock:
                        _key_index = (idx + 1) % len(keys)
                    continue  # دوّر المفتاح
                raise ProviderFailed("gemini", errors)  # خطأ في الطلب نفسه
    raise ProviderFailed("gemini", errors)


# ---------------------------------------------------------------- Routes
@app.route("/")
def home():
    return render_template("index.html", username=session.get("username"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = clean_username(request.form.get("username", ""))
        if username:
            session["username"] = username
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "حجم الطلب/الملف كبير جداً (الحد الأقصى ~4MB)."}), 413


@app.post("/chat")
def chat():
    username = session.get("username")
    if not username:
        return jsonify({"error": "يرجى تسجيل الدخول أولاً."}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "صيغة الطلب غير صحيحة (JSON متوقع)."}), 400

    msg = str(data.get("message") or "").strip()
    file_data = data.get("file_data") or None
    mime_type = data.get("mime_type") or None
    file_name = data.get("file_name") or None
    history = clean_history(data.get("history"))

    if not msg and not file_data:
        return jsonify({"error": "الرسالة فارغة."}), 400

    try:
        parts = build_user_parts(msg, file_data, mime_type, file_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    groq_key = get_groq_key()
    gemini_keys = get_gemini_keys()
    if not groq_key and not gemini_keys:
        return jsonify({"error": "لم يتم ضبط أي مفتاح: أضف GROQ_API_KEY و/أو GEMINI_API_KEY في متغيرات البيئة."}), 500

    failures = []
    deadline = time.monotonic() + TIME_BUDGET

    # 1) Groq (نصوص فقط)
    if groq_key and not file_data:
        try:
            text, model = call_groq(groq_key, username, msg, history, deadline)
            return jsonify({"response": text, "provider": "groq", "model": model})
        except ProviderFailed as e:
            failures += e.errors
    elif groq_key and file_data:
        log.info("تخطي Groq لأن هناك ملفاً مرفقاً؛ الانتقال إلى Gemini.")

    # 2) Gemini
    if gemini_keys:
        try:
            text, model = call_gemini(gemini_keys, username, parts, history, deadline)
            return jsonify({"response": text, "provider": "gemini", "model": model})
        except ProviderFailed as e:
            failures += e.errors
    else:
        failures.append("Gemini: لا توجد مفاتيح GEMINI_API_KEY مضبوطة.")

    error = "تعذّر الحصول على رد من أي مزوّد:\n\n" + "\n".join(f"- {f}" for f in failures)
    return jsonify({"error": error, "details": failures}), 502


@app.route("/debug-env")
def debug_env():
    """تشخيص مؤقت: يعرض فقط هل المتغيرات موجودة (true/false) دون كشف القيم. احذفه بعد الانتهاء."""
    if not session.get("username"):
        return jsonify({"error": "سجّل الدخول أولاً ثم افتح /debug-env"}), 401
    return jsonify({
        "groq_key_found": bool(get_groq_key()),
        "gemini_keys_found": len(get_gemini_keys()),
        "gemini_variable_names": [n for n, _ in _env_matches(_GEMINI_KEY_RE)],  # أسماء فقط
        "secret_key_set": bool((os.getenv("SECRET_KEY") or "").strip()),
        "groq_models": GROQ_MODELS,
        "gemini_models": GEMINI_MODELS,
    })


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
