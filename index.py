import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# قراءة المفتاح من البيئة أو استخدام المفتاح المباشر
API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LX7Vc-e2oVber8j49PjBBA9ZijizZcFTy3OLaS3teBSw")
client = genai.Client(api_key=API_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
        )
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
