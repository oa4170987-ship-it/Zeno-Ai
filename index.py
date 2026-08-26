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
        # استقبال الذاكرة/السجل من الواجهة الأمامية (Frontend)
        chat_history = data.get("history", [])

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # تعليمات الشخصية المعدلة (تتيح كتابة الأكواد وتأكيد الهوية)
        system_instruction = (
            "أنت مساعد ذكاء اصطناعي محترف اسمك Zeno. صانعك ومطورك هو عمر (Omar). "
            "يمكنك كتابة وشرح كل أنواع الأكواد البرمجية وتنسيقها داخل markdown code blocks. "
            "تحدث بطريقة ودودة ومفيدة."
        )

        # بناء قائمة الرسائل شاملة الذاكرة والرسالة الجديدة
        messages = [{"role": "system", "content": system_instruction}]
        
        # إضافة المحادثات السابقة للذاكرة
        for msg in chat_history:
            messages.append({"role": msg.get("role"), "content": msg.get("content")})
            
        # إضافة الرسالة الحالية
        messages.append({"role": "user", "content": user_message})

        # 1. جلب الموديلات المتاحة
        res_models = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
        models_list = res_models.json().get("data", [])
        
        valid_model = None
        for m in models_list:
            m_id = m.get("id", "")
            if all(k not in m_id for k in ["whisper", "guard", "orpheus", "safetensors"]):
                valid_model = m_id
                break
                
        if not valid_model and len(models_list) > 0:
            valid_model = models_list[0]["id"]

        # 2. إرسال الطلب
        payload = {
            "model": valid_model,
            "messages": messages
        }
        
        chat_res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        chat_data = chat_res.json()
        
        if chat_res.status_code == 200:
            bot_text = chat_data['choices'][0]['message']['content']
            return jsonify({"response": bot_text})
        else:
            return jsonify({"response": "حدث خطأ أثناء معالجة الطلب."})

    except Exception as e:
        return jsonify({"response": f"حدث خطأ في السيرفر: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
