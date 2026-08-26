from flask import Flask, request, jsonify
from google import genai
import os

app = Flask(__name__)

# تهيئة عميل Gemini (بيسحب المفتاح تلقائياً من GEMINI_API_KEY)
client = genai.Client(AQ.Ab8RN6LX7Vc-e2oVber8j49PjBBA9ZijizZcFTy3OLaS3teBSw)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "رسالة غير صالحة"}), 400

    try:
        # استدعاء موديل Gemini 2.5
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
        )
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
