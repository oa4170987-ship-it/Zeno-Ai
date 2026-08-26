import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "")
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # تجربة الموديل المعياري الأساسي لـ Groq
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": user_message}]
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            bot_text = data['choices'][0]['message']['content']
            return jsonify({"response": bot_text})
        else:
            # إرجاع تفاصيل الخطأ المباشرة لمعرفة المشكلة فوراً
            error_msg = data.get("error", {}).get("message", "خطأ في الاتصال")
            return jsonify({"response": f"خطأ من API: {error_msg}"})

    except Exception as e:
        return jsonify({"response": f"خطأ في السيرفر: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
