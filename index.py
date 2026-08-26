import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# المفتاح بتاعك
API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6L25dgm0wRcEpdwbZrwQzQXLiYmd957l7HlFLCr04g4qw")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "")
        
        # الاتصال المباشر بـ REST API بدلاً من المكتبات
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": user_message}]
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            bot_text = data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"response": bot_text})
        else:
            return jsonify({"error": data.get("error", {}).get("message", "حدث خطأ في الاتصال")}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
