# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
app = Flask(__name__)

import os
import time
import logging
import base64
import requests
from google import genai
from google.genai import types

app.secret_key = os.getenv("SECRET_KEY", "zeno_super_secret_key_abu_saeed_2026_enterprise")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ZenoEnterprise")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_HISTORY = 40

def get_dynamic_instruction(user_name, user_email):
    return f"""أنت Zeno، ذكاء اصطناعي فائق التطور، وأقوى مساعد برمجي وتقني. 
أنت تتحدث الآن مع المستخدم: "{user_name}" (بريده الإلكتروني: {user_email}).
تم تطويرك بواسطة المطور العبقري "أبو سعيد".
تعليماتك الأساسية:
1. رحب بالمستخدم باسمه الأول دائماً بأسلوب احترافي وودود.
2. قدم إجابات عبقرية، سريعة، دقيقة، ومباشرة بدون حشو.
3. إذا طُلب منك كود برمجي، اكتبه بأفضل الممارسات الهندسية (Clean Code).
4. استخدم تنسيق Markdown باحترافية عالية.
5. استغل قدراتك القصوى في تحليل الملفات والصور المعقدة إذا تم إرفاقها."""

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY غير موجود في إعدادات Vercel.")
    return genai.Client(api_key=api_key)

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #0f111a; color: #ececec; margin: 0; height: 100vh; overflow: hidden; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #333b54; border-radius: 4px; }
        .prose pre { background-color: #050609 !important; border-radius: 0.5rem; padding: 1rem; border: 1px solid #23283e; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.9em; }
        .typing-dot { animation: typing 1.4s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(26, 29, 45, 0.85); backdrop-filter: blur(12px); border: 1px solid #2d324d; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .google-btn { background-color: #ffffff; color: #757575; border: 1px solid #ddd; display: flex; align-items: center; justify-content: center; gap: 10px; transition: background-color 0.3s; }
        .google-btn:hover { background-color: #f1f1f1; }
    </style>
</head>
<body class="flex">

    {% if not session.get('user') %}
    <div class="flex-1 flex items-center justify-center p-4 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] relative w-full">
        <div class="absolute inset-0 bg-blue-900/10 backdrop-blur-md z-0"></div>
        <div class="bg-[#090a0f]/90 border border-[#2d324d] p-10 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-8 z-10 backdrop-blur-2xl">
            <div class="w-24 h-24 mx-auto bg-blue-600/10 text-blue-500 rounded-full flex items-center justify-center text-5xl shadow-inner border border-blue-500/20">
                <i class="fa-solid fa-brain"></i>
            </div>
            <div>
                <h1 class="text-3xl font-extrabold text-white mb-2">Zeno AI</h1>
                <p class="text-xs text-gray-400 font-semibold tracking-widest uppercase mb-6">Enterprise Edition by Abu Saeed</p>
                <p class="text-sm text-gray-300">يجب تسجيل الدخول بحساب جوجل للوصول إلى النظام الخارق.</p>
            </div>
            
            <a href="/login" class="google-btn w-full py-3.5 rounded-xl font-bold text-sm shadow-lg">
                <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" class="w-6 h-6">
                المتابعة باستخدام Google
            </a>
        </div>
    </div>
    {% else %}
    <aside class="w-72 bg-sidebarbg hidden md:flex flex-col border-l border-[#2d324d] h-full shadow-2xl z-20">
        <div class="p-6 border-b border-[#2d324d]">
            <h1 class="font-black text-2xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 flex items-center gap-3">
                <i class="fa-solid fa-bolt text-blue-500"></i> Zeno Pro
            </h1>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <button onclick="clearMemory()" class="w-full flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3.5 rounded-xl transition shadow-lg shadow-blue-600/20 text-sm">
                <i class="fa-solid fa-plus w-5"></i> محادثة جديدة
            </button>
            <hr class="border-[#2d324d] my-4">
            <button onclick="exportChat()" class="w-full flex items-center gap-3 bg-transparent hover:bg-[#1a1d2d] text-gray-300 px-4 py-3 rounded-xl transition border border-[#2d324d] text-sm">
                <i class="fa-solid fa-download w-5 text-green-400"></i> تصدير المحادثة
            </button>
        </div>
        
        <div class="p-4 border-t border-[#2d324d] bg-[#0d0e15]">
            <div class="flex items-center gap-3">
                <img src="{{ session.user.picture }}" alt="Profile" class="w-10 h-10 rounded-full border-2 border-blue-500 shadow-md">
                <div class="flex-1 overflow-hidden">
                    <p class="text-sm font-bold text-gray-200 truncate">{{ session.user.name }}</p>
                    <p class="text-[10px] text-gray-500 truncate">{{ session.user.email }}</p>
                </div>
                <a href="/logout" class="text-red-400 hover:text-red-300 bg-red-400/10 p-2 rounded-lg transition" title="تسجيل خروج">
                    <i class="fa-solid fa-power-off"></i>
                </a>
            </div>
        </div>
    </aside>

    <main class="flex-1 flex flex-col h-full relative bg-chatbg">
        <header class="md:hidden bg-sidebarbg border-b border-[#2d324d] p-4 flex justify-between items-center text-gray-200">
            <div class="flex items-center gap-2">
                <img src="{{ session.user.picture }}" class="w-8 h-8 rounded-full border border-blue-500">
                <h1 class="font-bold text-md text-blue-400">Zeno</h1>
            </div>
            <div class="flex gap-4">
                <button onclick="clearMemory()"><i class="fa-solid fa-pen-to-square"></i></button>
                <a href="/logout" class="text-red-400"><i class="fa-solid fa-power-off"></i></a>
            </div>
        </header>

        <div id="chatBox" class="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 pb-40 scroll-smooth flex flex-col items-center">
            <div class="text-center my-12 animate-fade-in">
                <img src="{{ session.user.picture }}" class="w-24 h-24 mx-auto rounded-full border-4 border-[#2d324d] shadow-2xl mb-4">
                <h2 class="text-3xl font-bold text-gray-100">أهلاً بك، {{ session.user.name.split(' ')[0] }}</h2>
                <p class="text-gray-400 mt-2 text-sm">Zeno جاهز لتنفيذ أوامرك بأقصى ذكاء وسرعة.</p>
            </div>
        </div>

        <div class="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-chatbg via-chatbg to-transparent">
            <div id="fileIndicator" class="hidden max-w-3xl mx-auto mb-2 bg-[#1a1d2d] text-gray-300 text-xs px-4 py-2.5 rounded-lg flex items-center justify-between border border-[#2d324d] shadow-lg">
                <span id="fileName" class="truncate font-mono"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 bg-red-400/10 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
            </div>
            
            <div class="max-w-3xl mx-auto relative glass-input rounded-2xl flex items-end p-2 transition-all">
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-blue-400 px-3 pb-3.5 transition flex-shrink-0" title="إرفاق ملف">
                    <i class="fa-solid fa-paperclip text-xl"></i>
                </button>
                
                <textarea id="userInput" rows="1" placeholder="اكتب سؤالك الخارق هنا أو ارفع ملفاً..." class="flex-1 bg-transparent border-none px-2 py-3.5 text-base focus:outline-none resize-none max-h-48 text-gray-100 placeholder-gray-600"></textarea>
                
                <button onclick="sendMessage()" id="sendBtn" class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:opacity-90 w-11 h-11 rounded-xl flex items-center justify-center transition shadow-lg shadow-blue-600/30 flex-shrink-0 mb-1 mr-2 disabled:opacity-50 disabled:cursor-not-allowed">
                    <i class="fa-solid fa-paper-plane"></i>
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
        
        const userPicture = "{{ session.user.picture }}";
        const userName = "{{ session.user.name }}";
        
        let history = [];
        let hasStarted = false;
        let currentFileBase64 = null;
        let currentFileMime = null;
        let currentFileName = null;

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
                attachmentHtml = `<div class="bg-[#2d324d] text-blue-300 text-xs px-3 py-1.5 rounded-lg mb-3 inline-flex items-center font-mono shadow-inner"><i class="fa-solid fa-file-lines ml-2"></i> ${attachmentName}</div><br>`;
            }
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-4 ${isUser ? 'flex-row-reverse' : ''} mb-8 animate-fade-in`;
            const avatar = isUser ? 
                `<img src="${userPicture}" class="w-10 h-10 rounded-full border-2 border-[#2d324d] shadow-lg flex-shrink-0 mt-1">` : 
                `<div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white mt-1 shadow-lg shadow-blue-500/30 border border-blue-400/50"><i class="fa-solid fa-bolt"></i></div>`;
            const bubbleClass = isUser ? 'bg-blue-600/20 border border-blue-500/30 px-6 py-4 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%] shadow-md' : 'text-gray-200 prose prose-invert max-w-full leading-relaxed w-full bg-[#1a1d2d] p-6 rounded-2xl rounded-tr-sm border border-[#2d324d] shadow-lg';

            msgDiv.innerHTML = `${avatar}<div class="${bubbleClass} break-words overflow-hidden">${attachmentHtml}${finalContent}</div>`;
            chatBox.appendChild(msgDiv);
            scrollToBottom();
            if(!isUser) document.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
        }

        function showTyping() {
            clearWelcomeMessage();
            const msgDiv = document.createElement('div');
            msgDiv.id = 'typingIndicator';
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-4 mb-8`;
            msgDiv.innerHTML = `<div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white mt-1 shadow-lg shadow-blue-500/30 border border-blue-400/50"><i class="fa-solid fa-bolt"></i></div><div class="flex items-center gap-1 h-10 px-4 bg-[#1a1d2d] rounded-2xl rounded-tr-sm border border-[#2d324d]"><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div></div>`;
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
            chatBox.innerHTML = `<div class="text-center my-12 animate-fade-in"><img src="${userPicture}" class="w-24 h-24 mx-auto rounded-full border-4 border-[#2d324d] shadow-2xl mb-4"><h2 class="text-3xl font-bold text-gray-100">تم مسح الذاكرة</h2><p class="text-gray-400 mt-2 text-sm">Zeno مستعد لموضوع جديد تماماً.</p></div>`;
        }

        function exportChat() {
            if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!');
            let textData = "Zeno AI - Enterprise Chat Export\\n================================\\n\\n";
            history.forEach(msg => { textData += `[${msg.role === 'user' ? userName : "Zeno"}]:\\n${msg.content}\\n\\n-------------------\\n\\n`; });
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
    return render_template_string(UI_TEMPLATE)

@app.route("/login")
def login():
    if not GOOGLE_CLIENT_ID or not REDIRECT_URI:
        return "يجب إعداد GOOGLE_CLIENT_ID و REDIRECT_URI في Vercel أولاً.", 500
        
    auth_req_url = f"{AUTH_URL}?client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=openid%20email%20profile&access_type=offline"
    return redirect(auth_req_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("home"))
        
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    token_res = requests.post(TOKEN_URL, data=token_data)
    if not token_res.ok:
        logger.error(f"فشل الحصول على التوكن: {token_res.text}")
        return "حدث خطأ أثناء مصادقة جوجل.", 400
        
    access_token = token_res.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_res = requests.get(USER_INFO_URL, headers=headers)
    
    if user_info_res.ok:
        user_info = user_info_res.json()
        session['user'] = {
            'name': user_info.get('name', 'مستخدم'),
            'email': user_info.get('email', ''),
            'picture': user_info.get('picture', 'https://www.gravatar.com/avatar/?d=mp')
        }
        logger.info(f"تم تسجيل الدخول بنجاح للمستخدم: {session['user']['email']}")
        
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.post("/chat")
def chat():
    user_data = session.get('user')
    if not user_data:
        return jsonify({"error": "يرجى تسجيل الدخول بحساب جوجل أولاً."}), 401

    try:
        data = request.get_json(silent=True) or {}
        msg = str(data.get("message", "")).strip()
        client_history = data.get("history", [])
        file_data = data.get("file_data")
        mime_type = data.get("mime_type")
        
        client = get_client()
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
        
        dynamic_instruction = get_dynamic_instruction(user_data['name'], user_data['email'])

        max_retries = 3
        for attempt in range(max_retries):
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
                if "503" in error_str and attempt < max_retries - 1:
                    logger.warning(f"ضغط على جوجل. إعادة المحاولة رقم {attempt + 1}...")
                    time.sleep(2)
                    continue
                logger.error(f"Error: {error_str}")
                return jsonify({"error": error_str}), 500

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
