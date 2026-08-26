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
        
        # 1. جلب الموديلات المتاحة في حسابك المباشر
        res_models = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
        if res_models.status_code != 200:
            return jsonify({"response": f"خطأ في المفتاح: {res_models.text}"})
            
        models_list = res_models.json().get("data", [])
        
        # تصفية الموديلات لاختيار أول موديل شات متوافق
        valid_model = None
        for m in models_list:
            m_id = m.get("id", "")
            if "whisper" not in m_id and "guard" not in m_id and "orpheus" not in m_id and "safetensors" not in m_id:
                valid_model = m_id
                break
                
        if not valid_model and len(models_list) > 0:
            valid_model = models_list[0]["id"]

        # 2. إرسال المحادثة بالموديل المتاح
        payload = {
            "model": valid_model,
            "messages": [{"role": "user", "content": user_message}]
        }
        
        chat_res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        chat_data = chat_res.json()
        
        if chat_res.status_code == 200:
            bot_text = chat_data['choices'][0]['message']['content']
            return jsonify({"response": bot_text})
        else:
            return jsonify({"response": f"الموديل المختار ({valid_model}) أعطى خطأ: {chat_data.get('error', {}).get('message')}"})

    except Exception as e:
        return jsonify({"response": f"حدث خطأ في السيرفر: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
