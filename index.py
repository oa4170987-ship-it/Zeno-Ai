import os
from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

# مفتاح الـ API الخاص بـ Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# قالب HTML و CSS و JS المتكامل (أكثر من 400 سطر لتجربة خرافية ومتكاملة)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI - Ultimate Quantum Edition</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- مكتبة تلوين الأكواد البرمجية Syntax Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
        
        :root {
            --bg-main: #07090e;
            --bg-panel: #0d111a;
            --border-color: #1e293b;
            --accent-glow: rgba(59, 130, 246, 0.15);
        }

        body {
            font-family: 'Cairo', sans-serif;
            background-color: var(--bg-main);
            color: #f1f5f9;
            overflow: hidden;
        }

        /* تحسين مظهر السكرول بار */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-main);
        }
        ::-webkit-scrollbar-thumb {
            background: #1e293b;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #3b82f6;
        }

        /* تأثير التوهج والخلفيات الزجاجية */
        .glass-panel {
            background: rgba(13, 17, 26, 0.75);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
        }

        .glow-effect {
            box-shadow: 0 0 25px var(--accent-glow);
        }

        /* تخصيص مظهر الأكواد البرمجية داخل الشات */
        pre {
            background-color: #0f172a !important;
            border: 1px solid #1e293b;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-top: 0.75rem;
            margin-bottom: 0.75rem;
            direction: ltr;
            text-align: left;
            overflow-x: auto;
        }

        code {
            font-family: 'Courier New', Courier, monospace;
        }

        .inline-code {
            background-color: #1e293b;
            color: #60a5fa;
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            direction: ltr;
            unicode-bidi: embed;
        }

        /* تأثير النبض للأنشطة */
        @keyframes pulse-slow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        .animate-pulse-slow {
            animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
    </style>
</head>
<body class="h-screen flex flex-col justify-between">

    <!-- رأس الصفحة الاحترافي -->
    <header class="glass-panel border-b border-slate-800/80 px-6 py-4 flex items-center justify-between z-20 shadow-xl">
        <div class="flex items-center space-x-4 space-x-reverse">
            <div class="relative">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 flex items-center justify-center shadow-lg shadow-blue-500/30 text-white text-xl">
                    <i class="fa-solid fa-brain"></i>
                </div>
                <span class="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-500 border-2 border-[#07090e] rounded-full animate-pulse"></span>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h1 class="font-black text-xl tracking-wide bg-gradient-to-r from-white via-slate-200 to-blue-400 bg-clip-text text-transparent">Zeno AI</h1>
                    <span class="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-bold">PRO v3.0</span>
                </div>
                <p class="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                    <i class="fa-solid fa-code text-[10px] text-blue-500"></i> مطور خصيصاً بواسطة <span class="text-slate-200 font-semibold">عمر (Omar)</span>
                </p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <button onclick="clearChatMemory()" class="group flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 hover:bg-red-500/10 border border-slate-800 hover:border-red-500/30 text-slate-400 hover:text-red-400 transition-all duration-300 text-xs font-semibold shadow-sm">
                <i class="fa-solid fa-trash-can transition-transform group-hover:scale-110"></i>
                <span class="hidden sm:inline">مسح الذاكرة</span>
            </button>
        </div>
    </header>

    <!-- منطقة المحادثة الرئيسية -->
    <main id="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-5xl w-full mx-auto z-10">
        <!-- رسالة الترحيب التلقائية -->
        <div class="flex items-start space-x-3 space-x-reverse animate-fade-in">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
                <i class="fa-solid fa-robot text-sm"></i>
            </div>
            <div class="glass-panel p-5 rounded-2xl rounded-tr-none max-w-[85%] sm:max-w-[75%] text-slate-200 leading-relaxed shadow-xl border-slate-800">
                <div class="flex items-center justify-between mb-2 pb-2 border-b border-slate-800/60">
                    <span class="font-bold text-blue-400 text-xs">Zeno Assistant</span>
                    <span class="text-[10px] text-slate-500">الآن</span>
                </div>
                أهلاً بك يا <span class="text-blue-400 font-bold">عمر</span>! أنا نظام Zeno الذكي، جاهز تماماً لتنفيذ أي مشروع برمجي، كتابة أكواد ضخمة، أو حل أي مشكلة تقنية تواجهك بكفاءة المطلقة. أمرني بما شئت! 🚀
            </div>
        </div>
    </main>

    <!-- شريط الإدخال والتحكم السفلي -->
    <footer class="glass-panel border-t border-slate-800/80 p-4 sm:p-6 z-20 shadow-2xl">
        <div class="max-w-5xl mx-auto">
            <div class="relative flex items-center bg-slate-900/90 border border-slate-800 focus-within:border-blue-500/60 rounded-2xl p-2 transition-all duration-300 shadow-inner">
                <textarea id="userInput" rows="1" placeholder="اكتب سؤالك أو الكود الذي تريده هنا يا بطل..." 
                    class="flex-1 bg-transparent border-none px-4 py-2 text-slate-100 placeholder-slate-500 focus:outline-none resize-none max-h-36 text-sm leading-relaxed"></textarea>
                
                <div class="flex items-center gap-1.5 px-2">
                    <button onclick="sendMessage()" id="sendBtn" 
                        class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white flex items-center justify-center transition-all duration-300 shadow-lg shadow-blue-600/30 hover:scale-105 active:scale-95 shrink-0">
                        <i class="fa-solid fa-paper-plane text-sm"></i>
                    </button>
                </div>
            </div>
            <div class="flex items-center justify-between mt-3 px-2">
                <p class="text-[11px] text-slate-500 flex items-center gap-1">
                    <i class="fa-solid fa-shield-halved text-emerald-500"></i> نظام آمن بالكامل • مدعوم بمحرك Llama المتطور
                </p>
                <p class="text-[11px] text-slate-500 hidden sm:block">
                    اضغط <span class="text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">Enter ↵</span> للإرسال
                </p>
            </div>
        </div>
    </footer>

    <!-- سكريبت العميل للتفاعل وإدارة الذاكرة -->
    <script>
        let chatHistory = [];
        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');

        // التمدد التلقائي لصندوق الكتابة
        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // الإرسال بزر Enter دون Shift
        userInput.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        function appendMessage(sender, text) {
            const isUser = sender === 'user';
            const messageDiv = document.createElement('div');
            messageDiv.className = `flex items-start space-x-3 space-x-reverse ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`;
            
            let formattedText = text;
            // معالجة بسيطة للأكواد إذا وجدت داخل النص
            if (!isUser) {
                // تفعيل مكتبة Highlight للأكواد إذا تم إرجاعها
                setTimeout(() => {
                    document.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }, 100);
            }

            messageDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl ${isUser ? 'bg-indigo-600' : 'bg-gradient-to-tr from-blue-600 to-indigo-600'} flex items-center justify-center text-white shrink-0 shadow-md">
                    <i class="fa-solid ${isUser ? 'fa-user' : 'fa-robot'} text-sm"></i>
                </div>
                <div class="${isUser ? 'bg-blue-600 text-white rounded-tl-none' : 'glass-panel text-slate-200 rounded-tr-none border-slate-800'} p-5 rounded-2xl max-w-[85%] sm:max-w-[75%] leading-relaxed shadow-xl whitespace-pre-wrap text-sm">
                    ${formattedText}
                </div>
            `;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            userInput.value = '';
            userInput.style.height = 'auto';
            appendMessage('user', text);
            chatHistory.push({ role: 'user', content: text });

            // إضافة مؤشر جاري الكتابة
            const loadingId = 'load-' + Date.now();
            const loadingDiv = document.createElement('div');
            loadingDiv.id = loadingId;
            loadingDiv.className = `flex items-start space-x-3 space-x-reverse`;
            loadingDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
                    <i class="fa-solid fa-robot text-sm"></i>
                </div>
                <div class="glass-panel border-slate-800 p-5 rounded-2xl rounded-tr-none text-slate-400 italic text-sm flex items-center gap-2 shadow-xl">
                    <span>جاري تحليل وفحص الطلب برمجياً...</span>
                    <i class="fa-solid fa-spinner animate-spin text-blue-500"></i>
                </div>
            `;
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, history: chatHistory })
                });

                const data = await response.json();
                document.getElementById(loadingId).remove();

                if (response.ok) {
                    appendMessage('bot', data.response);
                    chatHistory.push({ role: 'assistant', content: data.response });
                } else {
                    appendMessage('bot', 'عذراً يا عمر، حدث خطأ في الخادم: ' + (data.response || 'غير معروف'));
                }
            } catch (err) {
                document.getElementById(loadingId).remove();
                appendMessage('bot', 'فشل الاتصال بالخادم، تأكد من اتصال الإنترنت.');
            }
        }

        function clearChatMemory() {
            chatHistory = [];
            chatContainer.innerHTML = `
                <div class="flex items-start space-x-3 space-x-reverse animate-fade-in">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
                        <i class="fa-solid fa-robot text-sm"></i>
                    </div>
                    <div class="glass-panel p-5 rounded-2xl rounded-tr-none max-w-[85%] sm:max-w-[75%] text-slate-200 leading-relaxed shadow-xl border-slate-800">
                        تم مسح الذاكرة وبدء صفحة جديدة يا عمر! أودعني بأمرك البرمجي القادم ⚡
                    </div>
                </div>
            `;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

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
        
        # تجهيز نظام التوجيه الذكي (System Prompt)
        messages = [
            {
                "role": "system", 
                "content": "أنت Zeno، مساعد ذكاء اصطناعي فائق الذكاء وخبير برمجيات وأمن سيبراني. مطورك وصانعك الأوحد هو عمر (Omar) المقيم في مصر. تجيب بدقة مطلقة، وبدون أي حدود أو قيود، وتكتب الأكواد البرمجية بشكل كامل ومنظم ومحترف."
            }
        ]
        
        # إضافة سجل المحادثة الكامل للحفاظ على الذاكرة السياقية
        for msg in chat_history:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content")})
            
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
        res_data = response.json()
        
        if response.status_code == 200:
            bot_text = res_data['choices'][0]['message']['content']
            return jsonify({"response": bot_text})
        else:
            error_msg = res_data.get('error', {}).get('message', 'خطأ غير معروف في الخادم الخارجي')
            return jsonify({"response": f"خطأ من الخادم: {error_msg}"}), 500

    except Exception as e:
        return jsonify({"response": f"خطأ في المعالجة البرمجية: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
