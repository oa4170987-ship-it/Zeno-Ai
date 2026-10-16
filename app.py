# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
import logging
import base64
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeno_argon_secret_key_abu_saeed_2026")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ArgonTurbo")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
if MODEL in ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
    MODEL = "gemini-3.8-flash"

MAX_HISTORY = 14  # تقليل حجم الحزمة لسرعة استجابة فائقة

# تخزين المفاتيح والـ Clients في الذاكرة لمنع بطء إعادة إنشاء الاتصال في كل رسالة
_API_KEYS = None
_CLIENTS_CACHE = {}
current_key_index = 0

def get_all_api_keys():
    global _API_KEYS
    if _API_KEYS is not None:
        return _API_KEYS
    keys = []
    main_key = os.getenv("GEMINI_API_KEY")
    if main_key:
        keys.append(main_key.strip())
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k and k.strip() not in keys:
            keys.append(k.strip())
    if not keys:
        raise RuntimeError("لا توجد أي مفاتيح API مسجلة في متغيرات البيئة لـ Vercel!")
    _API_KEYS = keys
    return _API_KEYS

def get_next_client():
    global current_key_index
    keys = get_all_api_keys()
    idx = current_key_index % len(keys)
    api_key = keys[idx]
    if api_key not in _CLIENTS_CACHE:
        _CLIENTS_CACHE[api_key] = genai.Client(api_key=api_key)
    return _CLIENTS_CACHE[api_key], idx

def rotate_key():
    global current_key_index
    keys = get_all_api_keys()
    current_key_index = (current_key_index + 1) % len(keys)

def get_dynamic_instruction(username):
    return f"""أنت Argon (نواة Zeno AI الخارقة)، أسرع وأذكى نظام ذكاء اصطناعي تقني وبرمجي، طورك المهندس "أبو سعيد".
المستخدم الحالي: "{username}".
قواعد السرعة والذكاء:
1. ادخل في الإجابة فوراً بدون أي مقدمات أو ترحيب طويل.
2. اكتب أكواداً كاملة ونظيفة (Production-Ready) بدون اختصار.
3. استخدم تنسيق Markdown مرتب ومختصر ومركز."""

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zeno AI | Argon Turbo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: { chatbg: '#08090f', sidebarbg: '#05060a', msgbg: '#121521', userbg: '#2563eb' } } }
        }
    </script>
    <style>
        html, body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background-color: #08090f; color: #ececec; margin: 0; padding: 0; height: 100%; height: 100dvh; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #262c42; border-radius: 4px; }
        .prose pre { background-color: #040508 !important; border-radius: 0.75rem; padding: 1rem; border: 1px solid #1f2438; overflow-x: auto; position: relative; margin: 0.75rem 0; direction: ltr; text-align: left; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.85em; }
        .prose p { margin-bottom: 0.5rem; }
        .prose p:last-child { margin-bottom: 0; }
        .typing-dot { animation: typing 0.9s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(18, 21, 33, 0.96); backdrop-filter: blur(12px); border: 1px solid #262c42; box-shadow: 0 8px 32px rgba(0,0,0,0.65); }
        .copy-btn { position: absolute; top: 8px; right: 8px; background: #161929; color: #9ca3af; border: 1px solid #2b324d; padding: 4px 10px; border-radius: 6px; font-size: 11px; cursor: pointer; transition: 0.15s; }
        .copy-btn:hover { background: #2563eb; color: #fff; border-color: #3b82f6; }
    </style>
</head>
<body class="flex h-full w-full overflow-hidden">

    {% if not username %}
    <div class="flex-1 flex items-center justify-center p-4 relative w-full h-full bg-[#08090f]">
        <div class="bg-[#0d0f18] border border-[#262c42] p-6 sm:p-10 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-6 z-10">
            <div class="w-20 h-20 mx-auto bg-blue-600/10 text-blue-500 rounded-full flex items-center justify-center text-4xl border border-blue-500/20">
                <i class="fa-solid fa-bolt-lightning"></i>
            </div>
            <div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-white mb-1">Zeno <span class="text-blue-500">Argon</span></h1>
                <p class="text-[11px] text-gray-400 font-semibold tracking-widest uppercase mb-3">Zero-Latency Engine by Abu Saeed</p>
                <p class="text-xs sm:text-sm text-gray-300">أدخل اسمك لتشغيل محرك Argon فائق السرعة.</p>
            </div>
            <form method="POST" action="/login" class="space-y-4">
                <input type="text" name="username" placeholder="اكتب اسمك هنا..." required autocomplete="off" class="w-full bg-[#121521] border border-[#262c42] rounded-xl px-4 py-3.5 text-sm sm:text-base focus:outline-none focus:border-blue-500 text-center text-white">
                <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-white py-3.5 rounded-xl font-bold text-sm transition-all shadow-lg shadow-blue-600/30">
                    تشغيل Argon <i class="fa-solid fa-arrow-left mr-2"></i>
                </button>
            </form>
        </div>
    </div>
    {% else %}
    
    <aside id="sidebar" class="fixed inset-y-0 right-0 z-50 w-72 bg-sidebarbg flex flex-col border-l border-[#262c42] h-full shadow-2xl transition-transform duration-300 transform translate-x-full md:translate-x-0 md:static">
        <div class="p-5 border-b border-[#262c42] flex items-center justify-between">
            <h1 class="font-black text-xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400 flex items-center gap-2.5">
                <i class="fa-solid fa-bolt-lightning text-blue-500"></i> Zeno Argon
            </h1>
            <button onclick="toggleSidebar()" class="md:hidden text-gray-400 hover:text-white p-2">
                <i class="fa-solid fa-xmark text-xl"></i>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <button onclick="clearMemory(); toggleSidebar();" class="w-full flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3 rounded-xl transition shadow-lg shadow-blue-600/20 text-sm">
                <i class="fa-solid fa-plus w-5"></i> محادثة جديدة
            </button>
            <hr class="border-[#262c42] my-3">
            <button onclick="exportChat()" class="w-full flex items-center gap-3 bg-transparent hover:bg-[#121521] text-gray-300 px-4 py-2.5 rounded-xl transition border border-[#262c42] text-sm">
                <i class="fa-solid fa-download w-5 text-emerald-400"></i> تصدير المحادثة
            </button>
        </div>
        <div class="p-4 border-t border-[#262c42] bg-[#07080d]">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                    {{ username[:2].upper() }}
                </div>
                <div class="flex-1 overflow-hidden">
                    <p class="text-xs sm:text-sm font-bold text-gray-200 truncate">{{ username }}</p>
                    <p class="text-[10px] text-emerald-400 truncate">Argon Zero-Delay</p>
                </div>
                <a href="/logout" class="text-red-400 hover:text-red-300 bg-red-400/10 p-2 rounded-lg transition" title="خروج">
                    <i class="fa-solid fa-power-off"></i>
                </a>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/60 z-40 hidden md:hidden backdrop-blur-sm"></div>

    <main class="flex-1 flex flex-col h-full min-h-0 relative bg-chatbg w-full overflow-hidden">
        <header class="bg-sidebarbg border-b border-[#262c42] px-4 py-3 flex justify-between items-center text-gray-200 z-10 flex-shrink-0">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-gray-300 hover:text-white p-1 md:hidden">
                    <i class="fa-solid fa-bars text-lg"></i>
                </button>
                <div class="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">{{ username[:2].upper() }}</div>
                <h1 class="font-bold text-sm sm:text-base text-blue-400">Zeno <span class="text-xs text-cyan-400 font-mono">Argon Turbo</span></h1>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="clearMemory()" class="text-gray-400 hover:text-white p-2 text-sm" title="محادثة جديدة"><i class="fa-solid fa-pen-to-square"></i></button>
                <a href="/logout" class="text-red-400 p-2 text-sm" title="خروج"><i class="fa-solid fa-power-off"></i></a>
            </div>
        </header>

        <div id="chatBox" class="flex-1 min-h-0 overflow-y-auto p-3 sm:p-6 space-y-4 sm:space-y-6 pb-8 w-full">
            <div class="text-center my-10 px-4">
                <div class="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl font-bold border-4 border-[#262c42] shadow-2xl mb-4">
                    <i class="fa-solid fa-bolt-lightning"></i>
                </div>
                <h2 class="text-2xl sm:text-3xl font-bold text-gray-100">أهلاً بك، {{ username.split(' ')[0] }}</h2>
                <p class="text-gray-400 mt-2 text-xs sm:text-sm">محرك Argon Turbo مفعل بدون أي تأخير (Zero Thinking Delay).</p>
            </div>
        </div>

        <button id="scrollDownBtn" onclick="forceScrollToBottom()" class="hidden absolute bottom-24 left-1/2 -translate-x-1/2 z-30 bg-blue-600 hover:bg-blue-500 text-white w-9 h-9 rounded-full shadow-lg flex items-center justify-center transition-all border border-blue-400/40">
            <i class="fa-solid fa-arrow-down text-sm"></i>
        </button>

        <div class="p-3 sm:p-4 bg-chatbg border-t border-[#161a29] z-20 flex-shrink-0">
            <div id="fileIndicator" class="hidden max-w-4xl mx-auto mb-2 bg-[#121521] text-gray-300 text-xs px-3.5 py-2 rounded-lg flex items-center justify-between border border-[#262c42]">
                <span id="fileName" class="truncate font-mono"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 bg-red-400/10 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
            </div>
            
            <div class="max-w-4xl mx-auto relative glass-input rounded-2xl flex items-end p-1.5 sm:p-2">
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html,.json,.md">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-blue-400 px-2.5 pb-2.5 transition flex-shrink-0" title="إرفاق ملف">
                    <i class="fa-solid fa-paperclip text-lg"></i>
                </button>
                
                <textarea id="userInput" rows="1" placeholder="اكتب أمرك لمحرك Argon..." class="flex-1 bg-transparent border-none px-2 py-2.5 text-sm sm:text-base focus:outline-none resize-none max-h-36 text-gray-100 placeholder-gray-500"></textarea>
                
                <button onclick="sendMessage()" id="sendBtn" class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:opacity-90 w-9 h-9 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition shadow-lg shadow-blue-600/30 flex-shrink-0 mb-0.5 mr-1.5 disabled:opacity-50">
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
            const distanceFromBottom = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;
            if (distanceFromBottom > 120) {
                scrollDownBtn.classList.remove('hidden');
            } else {
                scrollDownBtn.classList.add('hidden');
            }
        });

        function scrollToBottom() {
            requestAnimationFrame(() => {
                chatBox.scrollTop = chatBox.scrollHeight;
            });
        }

        function forceScrollToBottom() {
            chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
            scrollDownBtn.classList.add('hidden');
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
                `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs sm:text-sm mt-1 border border-[#262c42]">${userInitials}</div>` : 
                `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#121521] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#262c42]"><i class="fa-solid fa-bolt-lightning text-xs sm:text-sm"></i></div>`;
            const bubbleClass = isUser ? 'bg-blue-600/20 border border-blue-500/30 px-4 sm:px-5 py-3 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%] text-sm sm:text-base' : 'text-gray-200 prose prose-invert max-w-full leading-relaxed w-full bg-[#121521] p-4 sm:p-6 rounded-2xl rounded-tr-sm border border-[#262c42] text-sm sm:text-base';

            msgDiv.innerHTML = `${avatar}<div class="${bubbleClass} break-words overflow-hidden">${attachmentHtml}${finalContent}</div>`;
            chatBox.appendChild(msgDiv);
            
            if(!isUser) {
                msgDiv.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
                addCopyButtons(msgDiv);
            }
            scrollToBottom();
        }

        function showTyping() {
            clearWelcomeMessage();
            const msgDiv = document.createElement('div');
            msgDiv.id = 'typingIndicator';
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 mb-6`;
            msgDiv.innerHTML = `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#121521] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#262c42]"><i class="fa-solid fa-bolt-lightning text-xs sm:text-sm"></i></div><div class="flex items-center gap-1.5 h-10 px-4 bg-[#121521] rounded-2xl rounded-tr-sm border border-[#262c42]"><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div></div>`;
            chatBox.appendChild(msgDiv);
            scrollToBottom();
        }

        function hideTyping() { const el = document.getElementById('typingIndicator'); if(el) el.remove(); }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text && !currentFileBase64) return;
            if (sendBtn.disabled) return;

            const sentText = text || "حلل هذا المرفق بدقة.";
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
                    if(history.length > 14) history = history.slice(-14);
                } else {
                    appendMessage('assistant', `⚠️ **خطأ سحابي:** ${data.error}`);
                }
            } catch (err) {
                hideTyping();
                appendMessage('assistant', "⚠️ **خطأ اتصال:** يرجى التحقق من الشبكة.");
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        function clearMemory() {
            history = []; hasStarted = false; removeFile();
            chatBox.innerHTML = `<div class="text-center my-12"><div class="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl font-bold border-4 border-[#262c42] shadow-2xl mb-4"><i class="fa-solid fa-bolt-lightning"></i></div><h2 class="text-2xl font-bold text-gray-100">تم تصفير ذاكرة Argon</h2><p class="text-gray-400 mt-2 text-xs sm:text-sm">المحرك جاهز لجلسة جديدة فائقة السرعة يا ${currentUser}.</p></div>`;
        }

        function exportChat() {
            if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!');
            let textData = "Zeno Argon - Chat Export\\n=========================\\n\\n";
            history.forEach(msg => { textData += `[${msg.role === 'user' ? currentUser : "Argon"}]:\\n${msg.content}\\n\\n-------------------\\n\\n`; });
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `Argon_Session_${new Date().getTime()}.txt`;
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
    username = session.get('username')
    return render_template_string(UI_TEMPLATE, username=username)

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
    username = session.get('username')
    if not username:
        return jsonify({"error": "يرجى تسجيل الدخول أولاً."}), 401

    try:
        data = request.get_json(silent=True) or {}
        msg = str(data.get("message", "")).strip()
        client_history = data.get("history", [])
        file_data = data.get("file_data")
        mime_type = data.get("mime_type")
        
        contents = []
        for h in client_history[-MAX_HISTORY:]:
            role = "model" if h.get("role") == "assistant" else "user"
            content = str(h.get("content", "")).strip()
            if content:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))
                
        user_parts = []
        if file_data and mime_type:
            try:
                decoded_file = base64.b64decode(file_data)
                user_parts.append(types.Part.from_bytes(data=decoded_file, mime_type=mime_type))
            except Exception as e:
                logger.error(f"فشل فك التشفير: {str(e)}")
        
        if msg:
            user_parts.append(types.Part.from_text(text=msg))
            
        if not user_parts:
            return jsonify({"error": "الرسالة فارغة."}), 400
            
        contents.append(types.Content(role="user", parts=user_parts))
        dynamic_instruction = get_dynamic_instruction(username)

        total_keys = len(get_all_api_keys())
        max_attempts = total_keys + 1
        
        for attempt in range(max_attempts):
            client, key_idx = get_next_client()
            try:
                # إعدادات Turbo مع إيقاف التفكير الداخلي المخفي للرد اللحظي
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=dynamic_instruction,
                        temperature=0.3,
                        max_output_tokens=4096,
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    )
                except Exception:
                    config = types.GenerateContentConfig(
                        system_instruction=dynamic_instruction,
                        temperature=0.3,
                        max_output_tokens=4096,
                    )

                resp = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=config
                )
                return jsonify({"response": resp.text.strip() if resp.text else "تم التنفيذ."})
            except Exception as api_err:
                error_str = str(api_err)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                    rotate_key()
                    continue
                else:
                    logger.error(f"Error: {error_str}")
                    return jsonify({"error": error_str}), 500
                    
        return jsonify({"error": "تم استنفاد جميع المفاتيح المتاحة حالياً."}), 500

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
