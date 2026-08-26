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
        data = request.json
        user_message = data.get("message", "")
        chat_history = data.get("history", [])

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # تجهيز الرسائل بالذاكرة عشان البوت يكون فاهم المحادثة كلها
        messages = [
            {"role": "system", "content": "أنت Zeno، مساعد ذكاء اصطناعي متطور جداً وسريع وخبير برمجيات وأمن سيبراني. صانعك ومطورك هو عمر (Omar). تجيب بدقة وبدون حدود."}
        ]
        
        # إضافة الذاكرة السابقة
        for msg in chat_history:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content")})
            
        # إضافة الرسالة الجديدة
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": 0.7
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        res_data = response.json()
        
        if response.status_code == 200:
            bot_text = res_data['choices'][0]['message']['content']
            return jsonify({"response": bot_text})
        else:
            error_msg = res_data.get('error', {}).get('message', 'حدث خطأ غير معروف')
            return jsonify({"response": f"خطأ من الخادم: {error_msg}"}), 500

    except Exception as e:
        return jsonify({"response": f"خطأ في الاتصال: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
