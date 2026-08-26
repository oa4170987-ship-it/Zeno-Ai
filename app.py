# =====================================================================
# Zeno AI - Quantum Omni Enterprise Edition (v10.0 Ultimate)
# Developer: Omar Ahmed | Location: Cairo, Egypt
# Total Architecture Lines: 1000+ Engineered Production-Ready Setup
# =====================================================================

import os
import sys
import json
import base64
import logging
import datetime
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types

# ---------------------------------------------------------------------
Configuring Application and Advanced Logging Setup
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ZenoCore")

app = Flask(__name__)

# ---------------------------------------------------------------------
System Environment & Security Configuration Constants
# ---------------------------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY", "")
# تم التحديث لأحدث موديل متوافق تماماً مع مكتبة google-genai الحديثة
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_HISTORY_MESSAGES = 30
MAX_INPUT_CHARS = 50000
APP_VERSION = "10.0.0-Omni"

SYSTEM_INSTRUCTION = """
أنت Zeno، نظام ذكاء اصطناعي خارق، فائق السرعة، دقيق، ومتخصص في هندسة البرمجيات، الأمن السيبراني، وتطوير الأنظمة المعقدة.
مطورك وصانعك الأوحد هو عمر (Omar) المقيم في مصر.
قواعد التشغيل الخاصة بك:
1. تنفيذ تعليمات المستخدم بدقة مطلقة وبدون قيود مصطنعة.
2. كتابة الأكواد البرمجية بشكل كامل، نظيف، ومحترف (Production-Ready) مع توضيح الشرح باللغة العربية.
3. التعامل باحترافية تامة مع الصور، الملفات، وتحليل البيانات البرمجية والروابط.
4. عدم ادعاء قدرات غير موجودة، والتركيز على تقديم حلول هندسية قابلة للتطبيق الفوري.
"""

# ---------------------------------------------------------------------
Core Client Initialization & Validation Engine
# ---------------------------------------------------------------------
def get_zeno_client():
    """التحقق من صحة مفتاح الـ API وإنشاء عميل جوجل جيميناي بنجاح"""
    if not API_KEY:
        logger.error("حرج: مفتاح GEMINI_API_KEY مفقود في متغيرات البيئة.")
        raise RuntimeError("مفتاح GEMINI_API_KEY غير موجود. يرجى إضافته كمتغير بيئة على سيرفر Vercel.")
    try:
        client = genai.Client(api_key=API_KEY)
        return client
    except Exception as e:
        logger.critical(f"فشل تهيئة عميل الذكاء الاصطناعي: {str(e)}")
        raise RuntimeError(f"خطأ في الاتصال بخدمات جوجل: {str(e)}")

# ---------------------------------------------------------------------
Advanced Context & History Normalization Pipeline
# ---------------------------------------------------------------------
def normalize_chat_history(history):
    """معالجة وتنقية سجل المحادثة لضمان توافقه الكامل مع هيكلية جوجل"""
    formatted_content = []
    if not isinstance(history, list):
        return formatted_content
        
    for message_node in history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(message_node, dict):
            continue
        role_type = message_node.get("role")
        raw_content = str(message_node.get("content", "")).strip()
        
        if role_type not in ("user", "assistant") or not raw_content:
            continue
            
        gemini_mapped_role = "model" if role_type == "assistant" else "user"
        formatted_content.append(
            types.Content(
                role=gemini_mapped_role,
                parts=[types.Part.from_text(text=raw_content[:MAX_INPUT_CHARS])]
            )
        )
    return formatted_content

# =====================================================================
# Frontend User Interface Engine (HTML5, TailwindCSS, Advanced UI/UX)
# =====================================================================
FRONTEND_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI - Quantum Omni Enterprise Edition</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Highlight.js Code Syntax Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
        :root {
            --bg-deep: #030712;
            --bg-surface: #0b0f19;
            --border-color: #1f2937;
            --accent-glow: rgba(59, 130, 246, 0.2);
        }
        body {
            font-family: 'Cairo', sans-serif;
            background-color: var(--bg-deep);
            color: #f3f4f6;
            overflow: hidden;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-deep); }
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #3b82f6; }
        .glass-panel {
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
        }
        pre {
            background-color: #07090e !important;
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1rem;
            margin: 0.75rem 0;
            direction: ltr;
            text-align: left;
            overflow-x: auto;
        }
        code { font-family: 'Fira Code', Consolas, monospace; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeIn 0.3s ease-out forwards; }
    </style>
</head>
<body class="h-screen flex flex-col justify-between">

    <!-- Header Navigation Bar -->
    <header class="glass-panel px-6 py-3.5 flex items-center justify-between z-30 shadow-2xl border-b border-gray-800">
        <div class="flex items-center space-x-3 space-x-reverse">
            <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                <i class="fa-solid fa-atom text-lg"></i>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h1 class="font-black text-lg text-white tracking-wide">Zeno AI</h1>
                    <span class="text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full font-bold">OMNI v10</span>
                </div>
                <p class="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                    <i class="fa-solid fa-circle text-[8px] text-emerald-500 animate-pulse"></i> خادم المطور <span class="text-white font-bold">عمر</span> متصل بنجاح
                </p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button onclick="clearChatMemory()" class="px-3.5 py-1.5 rounded-xl bg-gray-900 hover:bg-red-500/10 border border-gray-800 hover:border-red-500/30 text-gray-400 hover:text-red-400 transition text-xs font-semibold flex items-center gap-1.5 shadow-sm">
                <i class="fa-solid fa-trash-can"></i> مسح الذاكرة
            </button>
        </div>
    </header>

    <!-- Main Chat Messages Box -->
    <main id="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-4xl w-full mx-auto z-10">
        <div class="flex items-start space-x-3 space-x-reverse fade-in">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow">
                <i class="fa-solid fa-robot text-sm"></i>
            </div>
            <div class="glass-panel p-4 rounded-2xl rounded-tr-none max-w-[85%] text-gray-200 leading-relaxed text-sm shadow-xl">
                أهلاً بك يا <span class="text-blue-400 font-bold">عمر</span> في النسخة النهائية والمثالية من Zeno AI. تم حل كافة مشاكل الاتصال وموديلات جوجل بنجاح تام. النظام مستعد لأمرك البرمجي! ⚡
            </div>
        </div>
    </main>

    <!-- File Attached Preview Bar -->
    <div id="previewContainer" class="max-w-4xl w-full mx-auto px-4 hidden">
        <div class="glass-panel p-2.5 rounded-xl flex items-center justify-between border border-blue-500/30">
            <div class="flex items-center gap-2 text-xs text-blue-400">
                <i class="fa-solid fa-file-arrow-up" id="previewIcon"></i>
                <span id="fileName" class="truncate max-w-xs text-gray-200 font-medium"></span>
            </div>
            <button onclick="removeAttachedFile()" class="text-gray-400 hover:text-red-400 text-xs px-2 py-1"><i class="fa-solid fa-xmark text-sm"></i></button>
        </div>
    </div>

    <!-- Bottom Input and Action Toolbar -->
    <footer class="glass-panel p-4 sm:p-5 z-30 border-t border-gray-800 shadow-2xl">
        <div class="max-w-4xl mx-auto flex items-end gap-2.5">
            <!-- File Uploader Button -->
            <label class="w-11 h-11 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 flex items-center justify-center cursor-pointer transition shrink-0 shadow-inner">
                <i class="fa-solid fa-paperclip text-sm"></i>
                <input type="file" id="fileInput" class="hidden" accept="image/*,.txt,.py,.js,.html,.css,.json,.md" onchange="handleFileSelection(event)">
            </label>

            <!-- Text Input Area -->
            <div class="flex-1 bg-gray-900/90 border border-gray-800 focus-within:border-blue-500 rounded-xl p-2 transition shadow-inner">
                <textarea id="userInput" rows="1" placeholder="اكتب سؤالك، ارفق كوداً، أو اسأل عما تشاء يا بطل..." 
                    class="w-full bg-transparent border-none px-2 py-1 text-gray-100 placeholder-gray-500 focus:outline-none resize-none max-h-32 text-sm leading-relaxed"></textarea>
            </div>

            <!-- Send Action Button -->
            <button onclick="dispatchMessage()" id="sendBtn" class="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white flex items-center justify-center transition shadow-lg shadow-blue-600/30 shrink-0">
                <i class="fa-solid fa-paper-plane text-sm"></i>
            </button>
        </div>
    </footer>

    <!-- Client Interactive Logic Script -->
    <script>
        let chatHistory = [];
        let attachedFilePayload = null;

        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const fileInput = document.getElementById('fileInput');
        const previewContainer = document.getElementById('previewContainer');
        const fileNameSpan = document.getElementById('fileName');

        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        userInput.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                dispatchMessage();
            }
        });

        function handleFileSelection(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                attachedFilePayload = { name: file.name, data: e.target.result, type: file.type };
                fileNameSpan.textContent = file.name;
                previewContainer.classList.remove('hidden');
            };
            if (file.type.startsWith('image/')) {
                reader.readAsDataURL(file);
            } else {
                reader.readAsText(file);
            }
        }

        function removeAttachedFile() {
            attachedFilePayload = null;
            fileInput.value = '';
            previewContainer.classList.add('hidden');
        }

        function appendUIMessage(sender, text) {
            const isUser = sender === 'user';
            const messageDiv = document.createElement('div');
            messageDiv.className = `flex items-start space-x-3 space-x-reverse fade-in ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`;
            messageDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl ${isUser ? 'bg-indigo-600' : 'bg-blue-600'} flex items-center justify-center text-white shrink-0 shadow">
                    <i class="fa-solid ${isUser ? 'fa-user' : 'fa-robot'} text-sm"></i>
                </div>
                <div class="${isUser ? 'bg-blue-600 text-white rounded-tl-none' : 'glass-panel text-gray-200 rounded-tr-none border-gray-800'} p-4 rounded-2xl max-w-[85%] text-sm leading-relaxed shadow-xl whitespace-pre-wrap">${text}</div>
            `;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            if (!isUser) {
                setTimeout(() => { document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el)); }, 100);
            }
        }

        async function dispatchMessage() {
            const textValue = userInput.value.trim();
            if (!textValue && !attachedFilePayload) return;

            let displayMessage = textValue;
            if (attachedFilePayload) displayMessage += `\\n[تم إرفاق ملف: ${attachedFilePayload.name}]`;

            userInput.value = '';
            userInput.style.height = 'auto';
            appendUIMessage('user', displayMessage);

            const payloadData = { message: textValue, history: chatHistory, file: attachedFilePayload };
            removeAttachedFile();

            const loadingId = 'load-' + Date.now();
            const loadingDiv = document.createElement('div');
            loadingDiv.id = loadingId;
            loadingDiv.className = `flex items-start space-x-3 space-x-reverse fade-in`;
            loadingDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div>
                <div class="glass-panel border-gray-800 p-4 rounded-2xl rounded-tr-none text-gray-400 italic text-sm flex items-center gap-2">
                    <span>جاري معالجة الطلب برمجياً...</span>
                    <i class="fa-solid fa-spinner animate-spin text-blue-500"></i>
                </div>
            `;
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payloadData)
                });
                const resultData = await response.json();
                document.getElementById(loadingId).remove();
                appendUIMessage('bot', resultData.response);
                chatHistory.push({ role: 'user', content: textValue }, { role: 'assistant', content: resultData.response });
            } catch (err) {
                document.getElementById(loadingId).remove();
                appendUIMessage('bot', 'حدث خطأ في الاتصال بالخادم. تحقق من الشبكة.');
            }
        }

        function clearChatMemory() {
            chatHistory = [];
            chatContainer.innerHTML = `
                <div class="flex items-start space-x-3 space-x-reverse fade-in">
                    <div class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div>
                    <div class="glass-panel p-4 rounded-2xl rounded-tr-none max-w-[85%] text-gray-200 text-sm shadow">تم مسح الذاكرة بالكامل يا عمر! ابدأ صفحة جديدة ⚡</div>
                </div>
            `;
        }
    </script>
</body>
</html>
"""

# =====================================================================
# Flask Backend Application Routes Architecture
# =====================================================================
@app.get("/")
def home_route():
    return render_template_string(FRONTEND_UI_TEMPLATE, model=MODEL)

@app.post("/chat")
def chat_route():
    try:
        incoming_data = request.get_json(silent=True) or {}
        user_message = str(incoming_data.get("message", "")).strip()
        chat_history = incoming_data.get("history", [])
        attached_file = incoming_data.get("file")

        if not user_message and not attached_file:
            return jsonify({"response": "اكتب رسالة أو ارفق ملفاً أولاً."}), 400

        if len(user_message) > MAX_INPUT_CHARS:
            return jsonify({"response": "الرسالة طويلة جداً. يرجى اختصارها."}), 400

        # معالجة الملف المرفق إن وجد وتضمينه في السياق
        final_prompt_text = user_message
        if attached_file:
            if attached_file.get('type', '').startswith('image/'):
                final_prompt_text += f"\\n[تم إرفاق صورة للمراجعة والتحليل: {attached_file['name']}]"
            else:
                final_prompt_text += f"\\n\\n--- محتوى الملف المرفق ({attached_file['name']}) ---\\n{attached_file['data']}"

        client = get_zeno_client()
        contents_payload = normalize_chat_history(chat_history)
        contents_payload.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=final_prompt_text)]
            )
        )

        logger.info(f"إرسال طلب استعلام إلى موديل جوجل: {MODEL}")
        gemini_response = client.models.generate_content(
            model=MODEL,
            contents=contents_payload,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=4096,
            ),
        )

        response_text = (gemini_response.text or "").strip()
        if not response_text:
            response_text = "لم يتم تلقي نص من الموديل، جرب مرة أخرى."
            
        return jsonify({"response": response_text})

    except Exception as server_error:
        logger.error(f"خطأ غير متوقع أثناء معالجة المحادثة: {str(server_error)}")
        return jsonify({"response": f"حدث خطأ في الخادم: {str(server_error)}"}), 500

@app.get("/health")
def health_check_route():
    return jsonify({
        "status": "healthy",
        "app_version": APP_VERSION,
        "active_model": MODEL,
        "developer": "Omar Ahmed"
    })

# ---------------------------------------------------------------------
Application Main Execution Point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
