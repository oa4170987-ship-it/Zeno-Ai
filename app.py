import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_HISTORY_MESSAGES = 20
MAX_INPUT_CHARS = 30000

SYSTEM_INSTRUCTION = """أنت Zeno، مساعد ذكاء اصطناعي سريع ودقيق ومفيد.
اتبع تعليمات المستخدم المشروعة، واشرح بوضوح وباللغة التي يستخدمها المستخدم.
ساعد في البرمجة والتحليل والدراسة والأفكار وحل المشكلات. لا تدّعِ قدرات غير موجودة.
"""


def get_client():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY غير موجود. أضفه كمتغير بيئة قبل تشغيل Zeno.")
    return genai.Client(api_key=API_KEY)


def normalize_history(history):
    result = []
    if not isinstance(history, list):
        return result
    for item in history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role not in ("user", "assistant") or not content:
            continue
        gemini_role = "model" if role == "assistant" else "user"
        result.append(types.Content(
            role=gemini_role,
            parts=[types.Part.from_text(text=content[:MAX_INPUT_CHARS])]
        ))
    return result


@app.get("/")
def home():
    return render_template("index.html", model=MODEL)


@app.post("/chat")
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        history = data.get("history", [])

        if not message:
            return jsonify({"response": "اكتب رسالة أولاً."}), 400
        if len(message) > MAX_INPUT_CHARS:
            return jsonify({"response": "الرسالة طويلة جدًا. اختصرها ثم أرسلها مرة أخرى."}), 400

        client = get_client()
        contents = normalize_history(history)
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        ))

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=4096,
            ),
        )

        text = (response.text or "").strip()
        if not text:
            text = "لم يصل رد نصي. جرّب مرة أخرى."
        return jsonify({"response": text})

    except Exception as exc:
        return jsonify({"response": f"حدث خطأ: {str(exc)}"}), 500


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
