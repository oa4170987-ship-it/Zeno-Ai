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
        
        # قائمة أسماء الموديلات النشطة عالمياً في Groq
        models_to_try = [
            "deepseek-r1-distill-llama-70b",
            "gemma2-9b-it",
            "llama-3.2-11b-vision-preview",
            "llama-3.2-3b-preview"
        ]
        
        for model_name in models_to_try:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": user_message}]
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                bot_text = data['choices'][0]['message']['content']
                return jsonify({"response": bot_text})
                
        return jsonify({"error": "يرجى التأكد من تفعيل API Key من لوحة التحكم"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
