import os
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.6-flash"
MAX_HISTORY_MESSAGES = 20
MAX_INPUT_CHARS = 30000

SYSTEM_INSTRUCTION = """أنت Zeno، مساعد ذكاء اصطناعي سريع ودقيق ومفيد للمطور عمر."""

def get_client():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY غير موجود.")
    return genai.Client(api_key=API_KEY)

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-950 text-gray-100 h-screen flex flex-col justify-between">
    <header class="bg-gray-900 border-b border-gray-800 p-4 flex justify-between items-center">
        <h1 class="font-bold text-lg text-blue-400"><i class="fa-solid fa-atom"></i> Zeno AI</h1>
        <span class="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded">مرحباً يا عمر</span>
    </header>
    <main id="chatBox" class="flex-1 overflow-y-auto p-4 space-y-4 max-w-3xl w-full mx-auto">
        <div class="bg-gray-900 p-3 rounded-xl border border-gray-800 text-sm">أهلاً بك يا عمر، النظام جاهز للعمل! ⚡</div>
    </main>
    <footer class="bg-gray-900 border-t border-gray-800 p-4">
        <div class="max-w-3xl mx-auto flex gap-2">
            <input type="text" id="userInput" placeholder="اكتب رسالتك هنا..." class="flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-blue-500">
            <button onclick="sendMessage()" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-bold"><i class="fa-solid fa-paper-plane"></i></button>
        </div>
    </footer>
    <script>
        const chatBox = document.getElementById('chatBox');
        const userInput = document.getElementById('userInput');
        let history = [];

        userInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;
            userInput.value = '';
            chatBox.innerHTML += `<div class="bg-blue-600 text-white p-3 rounded-xl text-sm max-w-[80%] mr-auto">${text}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: text, history: history })
                });
                const data = await res.json();
                chatBox.innerHTML += `<div class="bg-gray-900 border border-gray-800 p-3 rounded-xl text-sm max-w-[80%]">${data.response}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                history.push({role: 'user', content: text}, {role: 'assistant', content: data.response});
            } catch (err) {
                chatBox.innerHTML += `<div class="bg-red-900/50 p-3 rounded-xl text-sm">حدث خطأ في الاتصال.</div>`;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(UI_TEMPLATE)

@app.post("/chat")
def chat():
    try:
        data = request.get_json() or {}
        msg = data.get("message", "").strip()
        history = data.get("history", [])
        
        client = get_client()
        contents = []
        for h in history:
            role = "model" if h.get("role") == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h.get("content", ""))]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg)]))

        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        return jsonify({"response": resp.text.strip()})
    except Exception as e:
        return jsonify({"response": f"خطأ: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000)
