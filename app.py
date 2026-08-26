import os
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "omar_zeno_super_secret_key_2026")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.6-flash"
MAX_HISTORY_MESSAGES = 20

SYSTEM_INSTRUCTION = """أنت Zeno، نظام ذكاء اصطناعي خارق، سريع للغاية، ودقيق. تم تطويرك وبرمجتك بواسطة المطور العبقري عمر (Omar). ساعده بكل قوة واحترافية."""

def get_client():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY غير موجود في متغيرات البيئة.")
    return genai.Client(api_key=API_KEY)

# واجهة تسجيل الدخول والدردشة الشاملة
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI - Developed by Omar</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-950 text-gray-100 h-screen flex flex-col justify-between selection:bg-blue-600 selection:text-white">
    
    {% if not session.get('logged_in') %}
    <!-- صفحة تسجيل الدخول -->
    <div class="flex-1 flex items-center justify-center p-4">
        <div class="bg-gray-900 border border-gray-800 p-8 rounded-2xl max-w-md w-full shadow-2xl text-center space-y-6">
            <div class="w-16 h-16 bg-blue-600/20 text-blue-400 rounded-2xl flex items-center justify-center mx-auto text-2xl border border-blue-500/30">
                <i class="fa-solid fa-atom animate-spin"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold tracking-tight">تسجيل دخول Zeno AI</h1>
                <p class="text-xs text-gray-400 mt-1">مطور النظام: <span class="text-blue-400 font-semibold">عمر</span></p>
            </div>
            <form method="POST" action="/login" class="space-y-4">
                <input type="password" name="password" placeholder="أدخل كلمة المرور..." required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 text-center">
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-bold text-sm transition shadow-lg shadow-blue-600/20">دخول للنظام الخارق</button>
            </form>
        </div>
    </div>
    {% else %}
    <!-- واجهة الدردشة الذكية والذاكرة العميق -->
    <header class="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 p-4 flex justify-between items-center z-10">
        <div class="flex items-center gap-3">
            <h1 class="font-bold text-lg text-blue-400 flex items-center gap-2">
                <i class="fa-solid fa-atom"></i> Zeno AI
            </h1>
            <span class="text-xs text-gray-400 bg-gray-800/60 px-2.5 py-1 rounded-full border border-gray-700">المطور: <strong class="text-blue-400">عمر</strong></span>
        </div>
        <div class="flex items-center gap-3">
            <span class="text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-full font-mono">gemini-3.6-flash</span>
            <a href="/logout" class="text-xs text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 px-3 py-1 rounded-full transition"><i class="fa-solid fa-power-off"></i> خروج</a>
        </div>
    </header>

    <main id="chatBox" class="flex-1 overflow-y-auto p-4 space-y-4 max-w-4xl w-full mx-auto">
        <div class="bg-gray-900/90 border border-gray-800 p-4 rounded-2xl text-sm shadow-md max-w-xl">
            أهلاً بك يا عمر في النظام الخارق! الذاكرة مفعلة، والموديل يعمل بأعلى كفاءة. كيف أساعدك اليوم؟ ⚡
        </div>
    </main>

    <footer class="bg-gray-900/80 backdrop-blur-md border-t border-gray-800 p-4">
        <div class="max-w-4xl mx-auto flex gap-2">
            <input type="text" id="userInput" placeholder="اطرح سؤالك الخارق هنا..." class="flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500">
            <button onclick="sendMessage()" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl text-sm font-bold transition shadow-lg shadow-blue-600/20"><i class="fa-solid fa-paper-plane"></i></button>
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
            
            chatBox.innerHTML += `<div class="bg-blue-600 text-white p-3.5 rounded-2xl text-sm max-w-[80%] mr-auto shadow-md">${text}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: text, history: history })
                });
                const data = await res.json();
                chatBox.innerHTML += `<div class="bg-gray-900 border border-gray-800 p-3.5 rounded-2xl text-sm max-w-[80%] shadow-md">${data.response}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                
                // تحديث الذاكرة المحلية (Context Memory)
                history.push({role: 'user', content: text}, {role: 'assistant', content: data.response});
                if(history.length > 20) history = history.slice(-20);
            } catch (err) {
                chatBox.innerHTML += `<div class="bg-red-900/50 border border-red-700 p-3.5 rounded-2xl text-sm">حدث خطأ في الاتصال بالشبكة.</div>`;
            }
        }
    </script>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(UI_TEMPLATE)

@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    # الباسورد الافتراضي للتسجيل (تقدر تغيره للي تعوزه)
    if password == "omar2026":
        session['logged_in'] = True
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.post("/chat")
def chat():
    if not session.get('logged_in'):
        return jsonify({"response": "غير مسموح بالوصول، يرجى تسجيل الدخول."}), 403
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
        return jsonify({"response": f"خطأ في معالجة الذكاء الاصطناعي: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000)
