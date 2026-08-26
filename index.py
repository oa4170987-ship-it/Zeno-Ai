import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# مفتاح Groq الخاص بك
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            bot_text = data['choices'][0]['message']['content']
            return jsonify({"response": bot_text})
        else:
            error_msg = data.get("error", {}).get("message", "حدث خطأ في الاتصال")
            return jsonify({"error": error_msg}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
