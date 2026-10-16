# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
import json
import urllib.request
import urllib.error

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeno_argon_super_fast_2026")

# قراءة الموديل مع ضمان استخدام 3.8-flash لو متسجل قديم
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
if MODEL in ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
    MODEL = "gemini-3.8-flash"

MAX_HISTORY = 12
current_key_index = 0

def get_all_api_keys():
    keys = []
    main_key = os.getenv("GEMINI_API_KEY")
    if main_key:
        keys.append(main_key.strip())
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k and k.strip() not in keys:
            keys.append(k.strip())
    return keys

def get_system_prompt(username):
    return f"""أنت Argon (النسخة الخارقة من Zeno AI)، أسرع وأذكى مساعد برمجي وتقني، طورك المهندس "أبو سعيد".
أنت تتحدث مع: "{username}".
تعليمات صارمة:
1. ادخل في الإجابة فوراً وبدون مقدمات طويلة.
2. اكتب أكواداً كاملة وجاهزة للتشغيل (Clean Code).
3. نسق إجابتك بـ Markdown احترافي."""

def call_groq_fast(groq_key, username, msg, history):
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = [{"role": "system", "content": get_system_prompt(username)}]
    for h in history[-MAX_HISTORY:]:
        role = "assistant" if h.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": str(h.get("content", ""))})
    messages.append({"role": "user", "content": msg})

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 4096
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_key}",
        "User-Agent": "ZenoArgon/1.0"
    }, method="POST")

    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

def call_gemini_fast(api_key, username, msg, history, file_data=None, mime_type=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"
    
    contents = []
    for h in history[-MAX_HISTORY:]:
        role = "model" if h.get("role") == "assistant" else "user"
        text = str(h.get("content", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    user_parts = []
    if file_data and mime_type:
        user_parts.append({"inline_data": {"mime_type": mime_type, "data": file_data}})
    if msg:
        user_parts.append({"text": msg})

    contents.append({"role": "user", "parts": user_parts})

    payload = json.dumps({
        "system_instruction": {"parts": [{"text": get_system_prompt(username)}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 4096
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json"
    }, method="POST")

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            return "".join(p.get("text", "") for p in parts if "text" in p)
        return "لم يتم تكوين رد."

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zeno AI | Argon Edition</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: { chatbg: '#090b10', sidebarbg: '#050609', msgbg: '#131622', userbg: '#2563eb' } } }
        }
    </script>
    <style>
        html, body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #090b10; color: #ececec; margin: 0; padding: 0; height: 100%; height: 100dvh; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #262c42; border-radius: 4px; }
        .prose pre { background-color: #040508 !important; border-radius: 0.75rem; padding: 1rem; border: 1px solid #1f2438; overflow-x: auto; position: relative; margin: 0.75rem 0; direction: ltr; text-align: left; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.85em; }
        .typing-dot { animation: typing 1s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(19, 22, 34, 0.96); border: 1px solid #262c42; box-shadow: 0 5px 25px rgba(0,0,0,0.6); }
        .copy-btn { position: absolute; top: 8px; right: 8px; background: #161929; color: #9ca3af; border: 1px solid #2b324d; padding: 3px 9px; border-radius: 6px; font-size: 11px; cursor: pointer; }
        .copy-btn:hover { background: #2563eb; color: #fff; }
    </style>
</head>
<body class="flex h-full w-full overflow-hidden">

    {% if not username %}
    <div class="flex-1 flex items-center justify-center p-4 w-full h-full bg-[#090b10]">
        <div class="bg-[#0d0f17] border border-[#262c42] p-8 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-6">
            <div class="w-20 h-20 mx-auto bg-blue-600/10 text-blue-500 rounded-full flex items-center justify-center text-4xl border border-blue-500/20">
                <i class="fa-solid fa-bolt"></i>
            </div>
            <div>
                <h1 class="text-3xl font-extrabold text-white mb-1">Zeno <span class="text-blue-500">Argon</span></h1>
                <p class="text-xs text-gray-400 font-semibold uppercase mb-3">Direct Engine by Abu Saeed</p>
                <p class="text-sm text-gray-300">أدخل اسمك للدخول للنظام السريع.</p>
            </div>
            <form method="POST" action="/login" class="space-y-4">
                <input type="text" name="username" placeholder="اكتب اسمك هنا..." required autocomplete="off" class="w-full bg-[#131622] border border-[#262c42] rounded-xl px-4 py-3.5 text-base focus:outline-none focus:border-blue-500 text-center text-white">
                <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-white py-3.5 rounded-xl font-bold text-sm shadow-lg shadow-blue-600/30">
                    دخول للنظام <i class="fa-solid fa-arrow-left mr-2"></i>
                </button>
            </form>
        </div>
    </div>
    {% else %}
    
    <aside id="sidebar" class="fixed inset-y-0 right-0 z-50 w-72 bg-sidebarbg flex flex-col border-l border-[#262c42] h-full shadow-2xl transition-transform duration-300 transform translate-x-full md:translate-x-0 md:static">
        <div class="p-5 border-b border-[#262c42] flex items-center justify-between">
            <h1 class="font-black text-xl text-blue-400 flex items-center gap-2">
                <i class="fa-solid fa-bolt text-blue-500"></i> Zeno Argon
            </h1>
            <button onclick="toggleSidebar()" class="md:hidden text-gray-400 hover:text-white p-2">
                <i class="fa-solid fa-xmark text-xl"></i>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <button onclick="clearMemory(); toggleSidebar();" class="w-full flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3 rounded-xl transition text-sm">
                <i class="fa-solid fa-plus w-5"></i> محادثة جديدة
            </button>
            <hr class="border-[#262c42] my-3">
            <button onclick="exportChat()" class="w-full flex items-center gap-3 bg-transparent hover:bg-[#131622] text-gray-300 px-4 py-2.5 rounded-xl transition border border-[#262c42] text-sm">
                <i class="fa-solid fa-download w-5 text-emerald-400"></i> تصدير المحادثة
            </button>
        </div>
        <div class="p-4 border-t border-[#262c42] bg-[#07080d]">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                    {{ username[:2].upper() }}
                </div>
                <div class="flex-1 overflow-hidden">
                    <p class="text-xs sm:text-sm font-bold text-gray-200 truncate">{{ username }}</p>
                    <p class="text-[10px] text-emerald-400 truncate">Direct HTTP Engine</p>
                </div>
                <a href="/logout" class="text-red-400 hover:text-red-300 bg-red-400/10 p-2 rounded-lg" title="خروج">
                    <i class="fa-solid fa-power-off"></i>
                </a>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/60 z-40 hidden md:hidden"></div>

    <main class="flex-1 flex flex-col h-full min-h-0 relative bg-chatbg w-full overflow-hidden">
        <header class="bg-sidebarbg border-b border-[#262c42] px-4 py-3 flex justify-between items-center text-gray-200 z-10 flex-shrink-0">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-gray-300 hover:text-white p-1 md:hidden">
                    <i class="fa-solid fa-bars text-lg"></i>
                </button>
                <div class="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">{{ username[:2].upper() }}</div>
                <h1 class="font-bold text-sm sm:text-base text-blue-400">Zeno <span class="text-xs text-emerald-400 font-mono">Argon</span></h1>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="clearMemory()" class="text-gray-400 hover:text-white p-2 text-sm" title="محادثة جديدة"><i class="fa-solid fa-pen-to-square"></i></button>
                <a href="/logout" class="text-red-400 p-2 text-sm" title="خروج"><i class="fa-solid fa-power-off"></i></a>
            </div>
        </header>

        <div id="chatBox" class="flex-1 min-h-0 overflow-y-auto p-3 sm:p-6 space-y-4 pb-8 w-full">
            <div class="text-center my-10 px-4">
                <div class="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl font-bold border-4 border-[#262c42] shadow-2xl mb-4">
                    <i class="fa-solid fa-bolt"></i>
                </div>
                <h2 class="text-2xl sm:text-3xl font-bold text-gray-100">أهلاً بك، {{ username.split(' ')[0] }}</h2>
                <p class="text-gray-400 mt-2 text-xs sm:text-sm">Zeno Argon جاهز للرد المباشر بأقصى سرعة.</p>
            </div>
            <div id="bottomAnchor"></div>
        </div>

        <button id="scrollDownBtn" onclick="forceScroll()" class="hidden absolute bottom-24 left-1/2 -translate-x-1/2 z-30 bg-blue-600 hover:bg-blue-500 text-white w-9 h-9 rounded-full shadow-lg flex items-center justify-center border border-blue-400/40">
            <i class="fa-solid fa-arrow-down text-sm"></i>
        </button>

        <div class="p-3 sm:p-4 bg-chatbg border-t border-[#161a29] z-20 flex-shrink-0">
            <div id="fileIndicator" class="hidden max-w-4xl mx-auto mb-2 bg-[#131622] text-gray-300 text-xs px-3.5 py-2 rounded-lg flex items-center justify-between border border-[#262c42]">
                <span id="fileName" class="truncate font-mono"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 bg-red-400/10 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
            </div>
            
            <div class="max-w-4xl mx-auto relative glass-input rounded-2xl flex items-end p-1.5 sm:p-2">
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html,.json,.md">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-blue-400 px-2.5 pb-2.5 transition flex-shrink-0" title="إرفاق ملف">
                    <i class="fa-solid fa-paperclip text-lg"></i>
                </button>
                
                <textarea id="userInput" rows="1" placeholder="اكتب رسالتك هنا..." class="flex-1 bg-transparent border-none px-2 py-2.5 text-sm sm:text-base focus:outline-none resize-none max-h-36 text-gray-100 placeholder-gray-500"></textarea>
                
                <button onclick="sendMessage()" id="sendBtn" class="bg-blue-600 text-white hover:bg-blue-500 w-9 h-9 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition flex-shrink-0 mb-0.5 mr-1.5 disabled:opacity-50">
                    <i class="fa-solid fa-paper-plane text-sm"></i>
                </button>
            </div>
        </div>
    </main>

    <script>
        marked.setOptions({ breaks: true });

        const chatBox = document.getElementById('chatBox');
        const scrollDownBtn = document.getElementById('scrollDownBtn');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const fileInput = document.getElementById('fileInput');
        const fileIndicator = document.getElementById('fileIndicator');
        const fileNameDisplay = document.getElementById('fileName');
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        
        const currentUser = "{{ username }}";
        const userInitials = "{{ username[:2].upper() }}";
        
        let history = [];
        let hasStarted = false;
        let currentFileBase64 = null;
        let currentFileMime = null;
        let currentFileName = null;

        chatBox.addEventListener('scroll', () => {
            const dist = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;
            scrollDownBtn.classList.toggle('hidden', dist <= 120);
        });

        function forceScroll() {
            chatBox.scrollTop = chatBox.scrollHeight;
            setTimeout(() => { chatBox.scrollTop = chatBox.scrollHeight; }, 60);
        }

        function toggleSidebar() {
            sidebar.classList.toggle('translate-x-full');
            sidebarOverlay.classList.toggle('hidden');
        }

        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if(!file) return;
            currentFileMime = file.type || 'text/plain';
            currentFileName = file.name;
            const reader = new FileReader();
            reader.onload = function(event) {
                currentFileBase64 = event.target.result.split(',')[1];
                fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-code mr-2 text-blue-400"></i> ${currentFileName}`;
                fileIndicator.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        });

        function removeFile() {
            currentFileBase64 = currentFileMime = currentFileName = null;
            fileInput.value = '';
            fileIndicator.classList.add('hidden');
        }

        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            if(this.value.trim() === '') this.style.height = 'auto';
        });

        userInput.addEventListener('keydown', e => { 
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });

        function clearWelcomeMessage() {
            if (!hasStarted) { chatBox.innerHTML = ''; hasStarted = true; }
        }

        function addCopyButtons(container) {
            container.querySelectorAll('pre').forEach((preBlock) => {
                if (preBlock.querySelector('.copy-btn')) return;
                const btn = document.createElement('button');
                btn.className = 'copy-btn';
                btn.innerHTML = '<i class="fa-regular fa-copy"></i> نسخ';
                btn.onclick = () => {
                    const codeText = preBlock.querySelector('code')?.innerText || preBlock.innerText;
                    navigator.clipboard.writeText(codeText);
                    btn.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> تم!';
                    setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i> نسخ'; }, 2000);
                };
                preBlock.appendChild(btn);
            });
        }

        function appendMessage(role, content, attachmentName = null) {
            clearWelcomeMessage();
            const isUser = role === 'user';
            const finalContent = isUser ? escapeHTML(content) : marked.parse(content);
            let attachmentHtml = '';
            if (isUser && attachmentName) {
                attachmentHtml = `<div class="bg-[#262c42] text-blue-300 text-xs px-3 py-1.5 rounded-lg mb-2 inline-flex items-center font-mono"><i class="fa-solid fa-file-lines ml-2"></i> ${attachmentName}</div><br>`;
            }
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 ${isUser ? 'flex-row-reverse' : ''} mb-6`;
            const avatar = isUser ? 
                `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs sm:text-sm mt-1">${userInitials}</div>` : 
                `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#131622] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#262c42]"><i class="fa-solid fa-bolt text-xs sm:text-sm"></i></div>`;
            const bubbleClass = isUser ? 'bg-blue-600/20 border border-blue-500/30 px-4 py-3 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%] text-sm sm:text-base' : 'text-gray-200 prose prose-invert max-w-full leading-relaxed w-full bg-[#131622] p-4 sm:p-6 rounded-2xl rounded-tr-sm border border-[#262c42] text-sm sm:text-base';

            msgDiv.innerHTML = `${avatar}<div class="${bubbleClass} break-words overflow-hidden">${attachmentHtml}${finalContent}</div>`;
            chatBox.appendChild(msgDiv);
            
            if(!isUser) {
                msgDiv.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
                addCopyButtons(msgDiv);
            }
            forceScroll();
        }

        function showTyping() {
            clearWelcomeMessage();
            const msgDiv = document.createElement('div');
            msgDiv.id = 'typingIndicator';
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 mb-6`;
            msgDiv.innerHTML = `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#131622] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#262c42]"><i class="fa-solid fa-bolt text-xs sm:text-sm"></i></div><div class="flex items-center gap-1.5 h-10 px-4 bg-[#131622] rounded-2xl rounded-tr-sm border border-[#262c42]"><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div></div>`;
            chatBox.appendChild(msgDiv);
            forceScroll();
        }

        function hideTyping() { const el = document.getElementById('typingIndicator'); if(el) el.remove(); }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text && !currentFileBase64) return;
            if (sendBtn.disabled) return;

            const sentText = text || "حلل هذا المرفق بالتفصيل.";
            const sentFileName = currentFileName;
            
            userInput.value = ''; userInput.style.height = 'auto'; sendBtn.disabled = true;
            appendMessage('user', sentText, sentFileName);
            showTyping();
            
            const payload = { message: sentText, history: history, file_data: currentFileBase64, mime_type: currentFileMime };
            removeFile();

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                hideTyping();
                
                if (res.status === 401) { window.location.reload(); return; }
                
                const data = await res.json();
                if(res.ok) {
                    appendMessage('assistant', data.response);
                    history.push({role: 'user', content: sentFileName ? `[مرفق: ${sentFileName}] ${sentText}` : sentText});
                    history.push({role: 'assistant', content: data.response});
                    if(history.length > 12) history = history.slice(-12);
                } else {
                    appendMessage('assistant', `⚠️ **خطأ:** ${data.error}`);
                }
            } catch (err) {
                hideTyping();
                appendMessage('assistant', "⚠️ **خطأ اتصال:** تأكد من الإنترنت.");
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        function clearMemory() {
            history = []; hasStarted = false; removeFile();
            chatBox.innerHTML = `<div class="text-center my-12"><div class="w-20 h-20 mx-auto bg-blue-600 rounded-full flex items-center justify-center text-white text-3xl font-bold mb-4"><i class="fa-solid fa-bolt"></i></div><h2 class="text-2xl font-bold text-gray-100">تم مسح الذاكرة</h2><p class="text-gray-400 mt-2 text-xs sm:text-sm">جاهز لمحادثة جديدة يا ${currentUser}.</p></div>`;
        }

        function exportChat() {
            if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!');
            let textData = "Zeno Argon - Chat Export\\n=========================\\n\\n";
            history.forEach(msg => { textData += `[${msg.role === 'user' ? currentUser : "Argon"}]:\\n${msg.content}\\n\\n-------------------\\n\\n`; });
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `Argon_${new Date().getTime()}.txt`;
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
        }

        function escapeHTML(str) { return str.replace(/[&<>'"]/g, tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])); }
    </script>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(UI_TEMPLATE, username=session.get('username'))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    if username:
        session['username'] = username
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.post("/chat")
def chat():
    global current_key_index
    username = session.get('username')
    if not username:
        return jsonify({"error": "يرجى تسجيل الدخول أولاً."}), 401

    try:
        data = request.get_json(silent=True) or {}
        msg = str(data.get("message", "")).strip()
        client_history = data.get("history", [])
        file_data = data.get("file_data")
        mime_type = data.get("mime_type")

        if not msg and not file_data:
            return jsonify({"error": "الرسالة فارغة."}), 400

        # 1. لو مفيش ملف مرفق وعندك مفتاح GROQ_API_KEY في Vercel هيستخدمه فوراً لسرعة خارقة (0.2 ثانية)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and not file_data:
            try:
                reply = call_groq_fast(groq_key.strip(), username, msg, client_history)
                return jsonify({"response": reply.strip()})
            except Exception:
                pass # لو فشل هيكمل على Gemini أوتوماتيك

        # 2. الاتصال المباشر بـ Gemini بدون أي مكتبات ثقيلة
        keys = get_all_api_keys()
        if not keys:
            return jsonify({"error": "لا توجد مفاتيح GEMINI_API_KEY في إعدادات Vercel."}), 500

        last_err = ""
        for _ in range(len(keys)):
            api_key = keys[current_key_index % len(keys)]
            try:
                reply = call_gemini_fast(api_key, username, msg, client_history, file_data, mime_type)
                return jsonify({"response": reply.strip()})
            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8", errors="ignore")
                last_err = f"HTTP {http_err.code}: {err_body}"
                if http_err.code in [429, 503]:
                    current_key_index = (current_key_index + 1) % len(keys)
                    continue
                break
            except Exception as e:
                last_err = str(e)
                break

        return jsonify({"error": last_err}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
