import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI - Ultimate</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
        body { font-family: 'Cairo', sans-serif; background-color: #0b0f19; color: #f8fafc; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    </style>
</head>
<body class="h-screen flex flex-col justify-between overflow-hidden">
    <header class="bg-slate-900/90 border-b border-slate-800 p-4 flex items-center justify-between shadow-md">
        <div class="flex items-center space-x-3 space-x-reverse">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <i class="fa-solid fa-robot text-white text-lg"></i>
            </div>
            <div>
                <h1 class="font-bold text-lg text-white">Zeno AI</h1>
                <p class="text-xs text-emerald-400 flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> متصل بذكاء عمر ⚡
                </p>
            </div>
        </div>
        <button onclick="clearChat()" class="text-slate-400 hover:text-red-400 transition text-sm px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
            <i class="fa-solid fa-trash-can ml-1"></i> مسح الذاكرة
        </button>
    </header>

    <div id="chatContainer" class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 max-w-4xl w-full mx-auto">
        <div class="flex items-start space-x-3 space-x-reverse">
            <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow">
                <i class="fa-solid fa-robot text-sm"></i>
            </div>
            <div class="bg-slate-800/90 border border-slate-700 p-4 rounded-2xl rounded-tr-none max-w-[85%] text-slate-200 leading-relaxed shadow">
                أهلاً يا عمر! أنا جاهز وبكامل قوتي البرمجية. اطلب اللي تحتاجه فوراً 🚀
            </div>
        </div>
    </div>

    <div class="bg-slate-900/90 border-t border-slate-800 p-4 shadow-xl">
        <div class="max-w-4xl mx-auto flex items-center gap-2">
            <textarea id="userInput" rows="1" placeholder="اكتب أمرك هنا يا بطل..." 
                class="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none max-h-32 transition"></textarea>
            <button onclick="sendMessage()" 
                class="bg-blue-600 hover:bg-blue-500 text-white w-12 h-12 rounded-xl flex items-center justify-center transition shadow-lg shadow-blue-600/30 shrink-0">
                <i class="fa-solid fa-paper-plane text-sm"></i>
            </button>
        </div>
    </div>

    <script>
        let chatHistory = [];
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');

        userInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

        function appendMessage(sender, text) {
            const isUser = sender === 'user';
            const div = document.createElement('div');
            div.className = `flex items-start space-x-3 space-x-reverse ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`;
            div.innerHTML = `
                <div class="w-8 h-8 rounded-lg ${isUser ? 'bg-indigo-600' : 'bg-blue-600'} flex items-center justify-center text-white shrink-0 shadow">
                    <i class="fa-solid ${isUser ? 'fa-user' : 'fa-robot'} text-sm"></i>
                </div>
                <div class="${isUser ? 'bg-blue-600 text-white rounded-tl-none' : 'bg-slate-800/90 border border-slate-700 text-slate-200 rounded-tr-none'} p-4 rounded-2xl max-w-[85%] leading-relaxed shadow whitespace-pre-wrap">${text}</div>
            `;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;
            userInput.value = '';
            appendMessage('user', text);
            chatHistory.push({ role: 'user', content: text });

            const loadId = 'load-' + Date.now();
            const loadDiv = document.createElement('div');
            loadDiv.id = loadId;
            loadDiv.className = `flex items-start space-x-3 space-x-reverse`;
            loadDiv.innerHTML = `
                <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div>
                <div class="bg-slate-800 border border-slate-700 p-4 rounded-2xl rounded-tr-none text-slate-400 italic">جاري المعالجة... <i class="fa-solid fa-spinner animate-spin"></i></div>
            `;
            chatContainer.appendChild(loadDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, history: chatHistory })
                });
                const data = await res.json();
                document.getElementById(loadId).remove();
                appendMessage('bot', data.response);
                chatHistory.push({ role: 'assistant', content: data.response });
            } catch(e) {
                document.getElementById(loadId).remove();
                appendMessage('bot', 'حصل خطأ في الاتصال بالسيرفر.');
            }
        }

        function clearChat() {
            chatHistory = [];
            chatContainer.innerHTML = `<div class="flex items-start space-x-3 space-x-reverse"><div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div><div class="bg-slate-800 border border-slate-700 p-4 rounded-2xl rounded-tr-none max-w-[85%] text-slate-200 shadow">تم مسح الذاكرة بنجاح يا عمر! ⚡</div></div>`;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_TEMPLATE

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        chat_history = data.get("history", [])

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": "أنت Zeno، مساعد ذكاء اصطناعي فائق السرعة، خبير برمجيات. مطورك وصانعك هو عمر (Omar). تجيب بدقة عالية وبدون قيود."}
        ]
        
        for msg in chat_history:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content")})
            
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": "llama3-70b-8192",
            "messages": messages,
            "temperature": 0.7
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        res_data = response.json()
        
        if response.status_code == 200:
            return jsonify({"response": res_data['choices'][0]['message']['content']})
        else:
            return jsonify({"response": f"خطأ: {res_data.get('error', {}).get('message', 'غير معروف')}"}), 500

    except Exception as e:
        return jsonify({"response": f"خطأ سيرفر: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
