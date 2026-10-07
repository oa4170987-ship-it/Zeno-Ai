# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
app = Flask(__name__)

import os
import time
import logging
import base64
from google import genai
from google.genai import types

app.secret_key = os.getenv("SECRET_KEY", "zeno_super_secret_key_abu_saeed_2026_rotation")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ZenoRotation")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_HISTORY = 40

def get_all_api_keys():
    keys = []
    main_key = os.getenv("GEMINI_API_KEY")
    if main_key:
        keys.append(main_key)
    
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k and k not in keys:
            keys.append(k)
            
    if not keys:
        raise RuntimeError("لا توجد أي مفاتيح API مسجلة في متغيرات البيئة لـ Vercel!")
    return keys

current_key_index = 0

def get_next_client():
    global current_key_index
    keys = get_all_api_keys()
    api_key = keys[current_key_index % len(keys)]
    return genai.Client(api_key=api_key), current_key_index

def rotate_key():
    global current_key_index
    keys = get_all_api_keys()
    current_key_index = (current_key_index + 1) % len(keys)
    logger.warning(f"جاري التبديل تلقائياً للمفتاح رقم: {current_key_index + 1}")

def get_dynamic_instruction(username):
    return f"""أنت Zeno، ذكاء اصطناعي فائق التطور، وأقوى مساعد برمجي وتقني. 
أنت تتحدث الآن مع المستخدم: "{username}".
تم تطويرك بواسطة المطور العبقري "أبو سعيد".
تعليماتك الأساسية:
1. رحب بالمستخدم باسمه دائماً بأسلوب احترافي وودود.
2. قدم إجابات عبقرية، سريعة، دقيقة، ومباشرة بدون حشو.
3. إذا طُلب منك كود برمجي، اكتبه بأفضل الممارسات الهندسية (Clean Code).
4. استخدم تنسيق Markdown باحترافية عالية.
5. استغل قدراتك القصوى في تحليل الملفات والصور المعقدة إذا تم إرفاقها."""

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zeno AI | Enterprise by Abu Saeed</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: { chatbg: '#0f111a', sidebarbg: '#090a0f', msgbg: '#1a1d2d', userbg: '#2563eb' } } }
        }
    </script>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #0f111a; color: #ececec; margin: 0; height: 100vh; height: 100dvh; overflow: hidden; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #333b54; border-radius: 4px; }
        .prose pre { background-color: #050609 !important; border-radius: 0.5rem; padding: 0.75rem; border: 1px solid #23283e; overflow-x: auto; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.85em; }
        .typing-dot { animation: typing 1.4s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(26, 29, 45, 0.95); backdrop-filter: blur(12px); border: 1px solid #2d324d; box-shadow: 0 5px 20px rgba(0,0,0,0.5); }
    </style>
</head>
<body class="flex h-full w-full overflow-hidden">

    {% if not username %}
    <div class="flex-1 flex items-center justify-center p-4 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] relative w-full h-full">
        <div class="absolute inset-0 bg-blue-900/10 backdrop-blur-md z-0"></div>
        <div class="bg-[#090a0f]/95 border border-[#2d324d] p-6 sm:p-10 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-6 z-10 backdrop-blur-2xl">
            <div class="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-blue-600/10 text-blue-500 rounded-full flex items-center justify-center text-4xl sm:text-5xl shadow-inner border border-blue-500/20">
                <i class="fa-solid fa-brain"></i>
            </div>
            <div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-white mb-2">Zeno AI</h1>
                <p class="text-[10px] sm:text-xs text-gray-400 font-semibold tracking-widest uppercase mb-4">Enterprise Edition by Abu Saeed</p>
                <p class="text-xs sm:text-sm text-gray-300">أدخل اسمك أو لقبك للولوج إلى النظام الخارق.</p>
            </div>
            
            <form method="POST" action="/login" class="space-y-4">
                <input type="text" name="username" placeholder="اكتب اسمك هنا..." required autocomplete="off" class="w-full bg-[#1a1d2d] border border-[#2d324d] rounded-xl px-4 py-3.5 sm:py-4 text-sm sm:text-base focus:outline-none focus:border-blue-500 text-center text-white transition-colors shadow-inner">
                <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-white py-3.5 sm:py-4 rounded-xl font-bold text-sm transition-all shadow-lg shadow-blue-600/30">
                    دخول للنظام <i class="fa-solid fa-arrow-left mr-2"></i>
                </button>
            </form>
        </div>
    </div>
    {% else %}
    
    <aside id="sidebar" class="fixed inset-y-0 right-0 z-50 w-72 bg-sidebarbg flex flex-col border-l border-[#2d324d] h-full shadow-2xl transition-transform duration-300 transform translate-x-full md:translate-x-0 md:static">
        <div class="p-4 sm:p-6 border-b border-[#2d324d] flex items-center justify-between">
            <h1 class="font-black text-xl sm:text-2xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 flex items-center gap-3">
                <i class="fa-solid fa-bolt text-blue-500"></i> Zeno Pro
            </h1>
            <button onclick="toggleSidebar()" class="md:hidden text-gray-400 hover:text-white p-2">
                <i class="fa-solid fa-xmark text-xl"></i>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <button onclick="clearMemory(); toggleSidebar();" class="w-full flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3 rounded-xl transition shadow-lg shadow-blue-600/20 text-sm">
                <i class="fa-solid fa-plus w-5"></i> محادثة جديدة
            </button>
            <hr class="border-[#2d324d] my-3">
            <button onclick="exportChat()" class="w-full flex items-center gap-3 bg-transparent hover:bg-[#1a1d2d] text-gray-300 px-4 py-2.5 rounded-xl transition border border-[#2d324d] text-sm">
                <i class="fa-solid fa-download w-5 text-green-400"></i> تصدير المحادثة
            </button>
        </div>
        
        <div class="p-4 border-t border-[#2d324d] bg-[#0d0e15]">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold border-2 border-[#2d324d] shadow-lg text-sm">
                    {{ username[:2].upper() }}
                </div>
                <div class="flex-1 overflow-hidden">
                    <p class="text-xs sm:text-sm font-bold text-gray-200 truncate">{{ username }}</p>
                    <p class="text-[10px] text-gray-500 truncate">مطور النظام</p>
                </div>
                <a href="/logout" class="text-red-400 hover:text-red-300 bg-red-400/10 p-2 rounded-lg transition" title="تسجيل خروج">
                    <i class="fa-solid fa-power-off"></i>
                </a>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/60 z-40 hidden md:hidden backdrop-blur-sm"></div>

    <main class="flex-1 flex flex-col h-full relative bg-chatbg w-full overflow-hidden">
        <header class="bg-sidebarbg border-b border-[#2d324d] px-4 py-3 flex justify-between items-center text-gray-200 z-10 flex-shrink-0">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-gray-300 hover:text-white p-1 md:hidden">
                    <i class="fa-solid fa-bars text-lg"></i>
                </button>
                <div class="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">{{ username[:2].upper() }}</div>
                <h1 class="font-bold text-sm sm:text-md text-blue-400">Zeno AI</h1>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="clearMemory()" class="text-gray-400 hover:text-white p-2 text-sm" title="محادثة جديدة"><i class="fa-solid fa-pen-to-square"></i></button>
                <a href="/logout" class="text-red-400 p-2 text-sm" title="خروج"><i class="fa-solid fa-power-off"></i></a>
            </div>
        </header>

        <div id="chatBox" class="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4 sm:space-y-6 pb-36 sm:pb-40 scroll-smooth flex flex-col items-center">
            <div class="text-center my-8 sm:my-12 animate-fade-in px-4">
                <div class="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl sm:text-4xl font-bold border-4 border-[#2d324d] shadow-2xl mb-3 sm:mb-4">
                    {{ username[:2].upper() }}
                </div>
                <h2 class="text-2xl sm:text-3xl font-bold text-gray-100">أهلاً بك، {{ username.split(' ')[0] }}</h2>
                <p class="text-gray-400 mt-2 text-xs sm:text-sm">Zeno جاهز لتنفيذ أوامرك بأقصى ذكاء وسرعة بلا توقف.</p>
            </div>
        </div>

        <div class="absolute bottom-0 left-0 right-0 p-3 sm:p-6 bg-gradient-to-t from-chatbg via-chatbg/95 to-transparent z-20">
            <div id="fileIndicator" class="hidden max-w-4xl mx-auto mb-2 bg-[#1a1d2d] text-gray-300 text-xs px-3.5 py-2 rounded-lg flex items-center justify-between border border-[#2d324d] shadow-lg">
                <span id="fileName" class="truncate font-mono"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 bg-red-400/10 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
            </div>
            
            <div class="max-w-4xl mx-auto relative glass-input rounded-2xl flex items-end p-1.5 sm:p-2 transition-all">
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-blue-400 px-2 sm:px-3 pb-3 transition flex-shrink-0" title="إرفاق ملف">
                    <i class="fa-solid fa-paperclip text-lg sm:text-xl"></i>
                </button>
                
                <textarea id="userInput" rows="1" placeholder="اكتب سؤالك أو ارفع ملفاً..." class="flex-1 bg-transparent border-none px-1.5 sm:px-2 py-3 text-sm sm:text-base focus:outline-none resize-none max-h-32 text-gray-100 placeholder-gray-500"></textarea>
                
                <button onclick="sendMessage()" id="sendBtn" class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:opacity-90 w-9 h-9 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition shadow-lg shadow-blue-600/30 flex-shrink-0 mb-0.5 sm:mb-1 mr-1.5 disabled:opacity-50 disabled:cursor-not-allowed">
                    <i class="fa-solid fa-paper-plane text-sm sm:text-base"></i>
                </button>
            </div>
        </div>
    </main>

    <script>
        marked.setOptions({
            highlight: function(code, lang) {
                const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                return hljs.highlight(code, { language }).value;
            },
            breaks: true
        });

        const chatBox = document.getElementById('chatBox');
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

        function toggleSidebar() {
            sidebar.classList.toggle('translate-x-full');
            sidebarOverlay.classList.toggle('hidden');
        }

        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if(!file) return;
            currentFileMime = file.type || 'application/octet-stream';
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

        function appendMessage(role, content, attachmentName = null) {
            clearWelcomeMessage();
            const isUser = role === 'user';
            const finalContent = isUser ? escapeHTML(content) : marked.parse(content);
            let attachmentHtml = '';
            if (isUser && attachmentName) {
                attachmentHtml = `<div class="bg-[#2d324d] text-blue-300 text-xs px-3 py-1.5 rounded-lg mb-2 inline-flex items-center font-mono shadow-inner"><i class="fa-solid fa-file-lines ml-2"></i> ${attachmentName}</div><br>`;
            }
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 ${isUser ? 'flex-row-reverse' : ''} mb-6 animate-fade-in`;
            const avatar = isUser ? 
                `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs sm:text-sm mt-1 shadow-md border border-[#2d324d]">${userInitials}</div>` : 
                `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#1a1d2d] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 shadow-md border border-[#2d324d]"><i class="fa-solid fa-bolt text-xs sm:text-sm"></i></div>`;
            const bubbleClass = isUser ? 'bg-blue-600/20 border border-blue-500/30 px-4 sm:px-6 py-3 sm:py-4 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%] text-sm sm:text-base shadow-md' : 'text-gray-200 prose prose-invert max-w-full leading-relaxed w-full bg-[#1a1d2d] p-4 sm:p-6 rounded-2xl rounded-tr-sm border border-[#2d324d] text-sm sm:text-base shadow-lg';

            msgDiv.innerHTML = `${avatar}<div class="${bubbleClass} break-words overflow-hidden">${attachmentHtml}${finalContent}</div>`;
            chatBox.appendChild(msgDiv);
            scrollToBottom();
            if(!isUser) document.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
        }

        function showTyping() {
            clearWelcomeMessage();
            const msgDiv = document.createElement('div');
            msgDiv.id = 'typingIndicator';
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 mb-6`;
            msgDiv.innerHTML = `<div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#1a1d2d] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 border border-[#2d324d]"><i class="fa-solid fa-bolt text-xs sm:text-sm"></i></div><div class="flex items-center gap-1 h-9 sm:h-10 px-4 bg-[#1a1d2d] rounded-2xl rounded-tr-sm border border-[#2d324d]"><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div></div>`;
            chatBox.appendChild(msgDiv);
            scrollToBottom();
        }

        function hideTyping() { const el = document.getElementById('typingIndicator'); if(el) el.remove(); }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text && !currentFileBase64) return;
            const sentText = text || "قم بتحليل هذا المرفق بالتفصيل.";
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
                    if(history.length > 40) history = history.slice(-40);
                } else {
                    appendMessage('assistant', `⚠️ **خطأ سحابي:** ${data.error}`);
                }
            } catch (err) {
                hideTyping();
                appendMessage('assistant', "⚠️ **خطأ اتصال:** يرجى التحقق من الشبكة.");
            } finally {
                sendBtn.disabled = false;
            }
        }

        function clearMemory() {
            history = []; hasStarted = false; removeFile();
            chatBox.innerHTML = `<div class="text-center my-12 animate-fade-in"><div class="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl sm:text-4xl font-bold border-4 border-[#2d324d] shadow-2xl mb-4">${userInitials}</div><h2 class="text-2xl sm:text-3xl font-bold text-gray-100">تم مسح الذاكرة</h2><p class="text-gray-400 mt-2 text-xs sm:text-sm">Zeno مستعد لموضوع جديد تماماً يا ${currentUser}.</p></div>`;
        }

        function exportChat() {
            if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!');
            let textData = "Zeno AI - Enterprise Chat Export\\n================================\\n\\n";
            history.forEach(msg => { textData += `[${msg.role === 'user' ? currentUser : "Zeno"}]:\\n${msg.content}\\n\\n-------------------\\n\\n`; });
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `Zeno_Session_${new Date().getTime()}.txt`;
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
        }

        function scrollToBottom() { chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' }); }
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
        logger.info(f"تم تسجيل الدخول محلياً للمستخدم: {username}")
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
                resp = client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=dynamic_instruction,
                        temperature=0.7,
                        max_output_tokens=8192,
                    )
                )
                return jsonify({"response": resp.text.strip() if resp.text else "عذراً، لم أتمكن من تكوين إجابة."})
            except Exception as api_err:
                error_str = str(api_err)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                    logger.warning(f"المفتاح رقم {key_idx + 1} استنفد حصته أو واجه ضغطاً. جاري التبديل للمفتاح التالي...")
                    rotate_key()
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"Error: {error_str}")
                    return jsonify({"error": error_str}), 500
                    
        return jsonify({"error": "عذراً، تم استنفاد جميع المفاتيح المتاحة حالياً. يرجى إضافة مفاتيح إضافية."}), 500

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
