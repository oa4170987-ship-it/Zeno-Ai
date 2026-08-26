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
        
        # قائمة الموديلات المخصصة للمحادثة فقط بالترتيب
        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        
        for model_name in models_to_try:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": user_message}]
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            data = response.json()
            
            if response.status_code == 200:
                bot_text = data['choices'][0]['message']['content']
                return jsonify({"response": bot_text})
                
        # لو الموديلين فيهم مشكلة يرجع الخطأ
        return jsonify({"error": data.get("error", {}).get("message", "خطأ في الاتصال")}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
