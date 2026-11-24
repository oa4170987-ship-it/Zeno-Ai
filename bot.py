# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.error
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_HISTORY = 12
current_key_index = 0
user_histories = {}


def get_all_api_keys():
    keys = []
    main_key = os.getenv("GEMINI_API_KEY")
    if main_key:
        keys.append(main_key.strip())
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k and k.strip() not in keys:
            keys.append(k.strip())
    return keys


def get_system_prompt(username: str) -> str:
    return f"""أنت Argon (النسخة الخارقة من Zeno AI)، أسرع وأذكى مساعد برمجي وتقني، طورك المهندس "أبو سعيد".
أنت تتحدث مع: "{username}".
تعليمات صارمة:
1. ادخل في الإجابة فوراً وبدون مقدمات طويلة.
2. اكتب أكواداً كاملة وجاهزة للتشغيل (Clean Code).
3. نسق إجابتك بـ Markdown احترافي."""


def call_groq_fast(groq_key: str, username: str, msg: str, history: list) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = [{"role": "system", "content": get_system_prompt(username)}]
    for h in history[-MAX_HISTORY:]:
        role = "assistant" if h.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": str(h.get("content", ""))})
    messages.append({"role": "user", "content": msg})

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 4096
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_key}",
        "User-Agent": "ZenoArgonBot/1.0"
    }, method="POST")

    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def call_gemini_fast(api_key: str, username: str, msg: str, history: list) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"

    contents = []
    for h in history[-MAX_HISTORY:]:
        role = "model" if h.get("role") == "assistant" else "user"
        text = str(h.get("content", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": msg}]})

    payload = json.dumps({
        "system_instruction": {"parts": [{"text": get_system_prompt(username)}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 4096
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json"
    }, method="POST")

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            return "".join(p.get("text", "") for p in parts if "text" in p)
        return "لم يتم تكوين رد."


def generate_reply(username: str, msg: str, history: list) -> str:
    global current_key_index
    errors = []

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            return call_groq_fast(groq_key.strip(), username, msg, history).strip()
        except Exception as e:
            errors.append(f"Groq: {e}")

    keys = get_all_api_keys()
    if not keys:
        raise RuntimeError("لا توجد مفاتيح GEMINI_API_KEY أو GROQ_API_KEY." + (" | " + " ; ".join(errors) if errors else ""))

    for _ in range(len(keys)):
        api_key = keys[current_key_index % len(keys)]
        try:
            return call_gemini_fast(api_key, username, msg, history).strip()
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            errors.append(f"Gemini HTTP {http_err.code}: {err_body}")
            if http_err.code in [429, 503]:
                current_key_index = (current_key_index + 1) % len(keys)
                continue
            break
        except Exception as e:
            errors.append(f"Gemini: {e}")
            break

    raise RuntimeError(" ; ".join(errors) or "فشل الاتصال بالنموذج.")


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user and user.first_name else "مستخدم"
    user_histories[update.effective_chat.id] = []
    await update.message.reply_text(f"أهلاً {name} ⚡ أنا Zeno Argon على تليجرام. أرسل رسالتك أو استخدم /clear لمسح السجل.")


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_chat.id] = []
    await update.message.reply_text("تم مسح سجل المحادثة ⚡")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    username = (user.full_name if user and user.full_name else (user.username or "User"))
    msg = update.message.text.strip()
    history = user_histories.setdefault(chat_id, [])

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        reply = generate_reply(username, msg, history)
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})
        if len(history) > MAX_HISTORY:
            user_histories[chat_id] = history[-MAX_HISTORY:]

        # تليجرام يحد طول الرسالة الواحدة بـ 4096 حرفاً تقريباً
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i + 4000])
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطأ: {e}")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("يرجى تعيين متغير البيئة TELEGRAM_BOT_TOKEN أولاً.")

    app_bot = ApplicationBuilder().token(token.strip()).build()
    app_bot.add_handler(CommandHandler("start", start_cmd))
    app_bot.add_handler(CommandHandler("clear", clear_cmd))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Zeno Argon Telegram Bot is running...")
    app_bot.run_polling()


if __name__ == "__main__":
    main()
