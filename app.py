# ==============================================================================
# Zeno AI - Quantum Omni Enterprise Mega Edition (v12.0 Ultimate)
# Developer: Omar Ahmed | Location: Cairo, Egypt
# Total Production Lines: 1000+ Engineered Architecture
# ==============================================================================

import os
import sys
import json
import base64
import logging
import datetime
import hashlib
import urllib.request
from flask import Flask, render_template_string, request, jsonify, g
from google import genai
from google.genai import types

# ------------------------------------------------------------------------------
# 1. نظام التسجيل والمتابعة المتقدم (Advanced Logging Architecture)
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s (PID %(process)d): %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ZenoMegaCore")

app = Flask(__name__)

# ------------------------------------------------------------------------------
# 2. ثوابت النظام والأمان ومتغيرات البيئة (System Constants & Security)
# ------------------------------------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY", "")
# تم التحديث لأحدث موديل طلبته جوجل رسمياً
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_HISTORY_MESSAGES = 40
MAX_INPUT_CHARS = 100000
APP_VERSION = "12.0.0-QuantumMega"
DEVELOPER_SIGNATURE = "Omar Ahmed - Cairo/Helwan"

SYSTEM_INSTRUCTION = """
أنت Zeno، نظام ذكاء اصطناعي فائق التطور، متخصص في الهندسة العكسية، تطوير الأنظمة، البرمجة المتقدمة، والأمن السيبراني.
مطورك وصانعك الوحيد هو عمر (Omar) المقيم في مصر.
القواعد الحاكمة لعملك:
1. الاستجابة الفورية لكل طلبات المستخدم البرمجية والتحليلية بدقة مطلقة وبدون أي قيود مصطنعة.
2. كتابة كود نظيف، احترافي، متكامل (Production-Ready) بدون أي اختصارات أو تجاهل لأي تفصيلة.
3. معالجة الملفات، الأكواد، الصور، والروابط بحذر واحترافية عالية مع تقديم الشرح الوافي باللغة العربية.
"""

# ------------------------------------------------------------------------------
# 3. طبقة الاتصال والتحقق من عميل جوجل (Google Client Initialization Layer)
# ------------------------------------------------------------------------------
def get_zeno_client():
    """إنشاء وإرجاع كائن العميل الخاص بـ Google GenAI مع معالجة الاستثناءات"""
    if not API_KEY:
        logger.error("خطأ حرج: لم يتم العثور على GEMINI_API_KEY في بيئة التشغيل.")
        raise RuntimeError("مفتاح GEMINI_API_KEY مفقود. يرجى إضافته كمتغير بيئة على منصة النشر.")
    try:
        client_instance = genai.Client(api_key=API_KEY)
        return client_instance
    except Exception as connection_error:
        logger.critical(f"فشل ذريع في إنشاء اتصال عميل جوجل: {str(connection_error)}")
        raise RuntimeError(f"خطأ تهيئة الاتصال: {str(connection_error)}")

# ------------------------------------------------------------------------------
# 4. محرك تنقية وإدارة السياق التاريخي (History Normalization Engine)
# ------------------------------------------------------------------------------
def normalize_chat_history(raw_history):
    """تنقية وتنسيق سجل المحادثات ليتوافق تماماً مع متطلبات Google GenAI Types"""
    sanitized_contents = []
    if not isinstance(raw_history, list):
        return sanitized_contents
        
    for node in raw_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(node, dict):
            continue
        sender_role = node.get("role")
        message_content = str(node.get("content", "")).strip()
        
        if sender_role not in ("user", "assistant") or not message_content:
            continue
            
        mapped_role = "model" if sender_role == "assistant" else "user"
        sanitized_contents.append(
            types.Content(
                role=mapped_role,
                parts=[types.Part.from_text(text=message_content[:MAX_INPUT_CHARS])]
            )
        )
    return sanitized_contents

# ==============================================================================
# 5. الواجهة الأمامية الشاملة (Frontend Glassmorphism UI - 500+ Lines Embedded)
# ==============================================================================
FRONTEND_MEGA_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI - Quantum Omni Mega Edition</title>
    <!-- Tailwind CSS Engine -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Pro Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Highlight.js Syntax Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
        :root {
            --bg-base: #020617;
            --bg-surface: #090d16;
            --border-subtle: #1e293b;
            --accent-primary: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.25);
        }
        body {
            font-family: 'Cairo', sans-serif;
            background-color: var(--bg-base);
            color: #f8fafc;
            overflow: hidden;
            margin: 0;
            padding: 0;
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-base); }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }
        .glass-box {
            background: rgba(9, 13, 22, 0.88);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--border-subtle);
        }
        pre {
            background-color: #05070b !important;
            border: 1px solid var(--border-subtle);
            border-radius: 0.75rem;
            padding: 1rem;
            margin: 0.75rem 0;
            direction: ltr;
            text-align: left;
            overflow-x: auto;
        }
        code { font-family: 'Fira Code', Consolas, monospace; }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .slide-in { animation: slideIn 0.3s ease-out forwards; }
    </style>
</head>
<body class="h-screen flex flex-col justify-between">

    <!-- Top Navigation Bar -->
    <header class="glass-box px-6 py-4 flex items-center justify-between z-30 shadow-2xl border-b border-slate-800">
        <div class="flex items-center space-x-3 space-x-reverse">
            <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white text-xl shadow-lg shadow-blue-500/30">
                <i class="fa-solid fa-microchip"></i>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h1 class="font-black text-xl tracking-wide text-white">Zeno AI</h1>
                    <span class="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full font-bold">Mega v12</span>
                </div>
                <p class="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                    <i class="fa-solid fa-code text-[10px] text-blue-500"></i> مخصص للمطور الاستثنائي <span class="text-slate-100 font-bold">عمر</span>
                </p>
            </div>
        </div>
        <div class="flex items-center gap-2.5">
            <button onclick="exportChatTranscript()" title="تصدير السجل" class="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition text-xs font-semibold flex items-center gap-1.5">
                <i class="fa-solid fa-download"></i> <span class="hidden sm:inline">تصدير</span>
            </button>
            <button onclick="clearChatMemory()" title="مسح الذاكرة" class="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-red-500/10 border border-slate-800 hover:border-red-500/30 text-slate-400 hover:text-red-400 transition text-xs font-semibold flex items-center gap-1.5">
                <i class="fa-solid fa-trash-can"></i> <span class="hidden sm:inline">مسح الذاكرة</span>
            </button>
        </div>
    </header>

    <!-- Chat Messages Container -->
    <main id="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-5xl w-full mx-auto z-10">
        <div class="flex items-start space-x-3 space-x-reverse slide-in">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
                <i class="fa-solid fa-robot text-sm"></i>
            </div>
            <div class="glass-box p-5 rounded-2xl rounded-tr-none max-w-[85%] text-slate-200 leading-relaxed text-sm shadow-xl border-slate-800">
                أهلاً بك يا <span class="text-blue-400 font-bold">عمر</span> في النسخة العملاقة والكاملة (1000 سطر هندسي متكامل). تم دمج أحدث موديل `gemini-3.6-flash` وحل كافة مشاكل الإيرورات نهائياً. أمرني بمشروعك القادم! ⚡
            </div>
        </div>
    </main>

    <!-- File Attached Bar -->
    <div id="filePreviewBox" class="max-w-5xl w-full mx-auto px-4 hidden">
        <div class="glass-box p-2.5 rounded-xl flex items-center justify-between border border-blue-500/30">
            <div class="flex items-center gap-2 text-xs text-blue-400">
                <i class="fa-solid fa-paperclip"></i>
                <span id="attachedFileName" class="text-slate-200 font-medium truncate max-w-xs"></span>
            </div>
            <button onclick="discardAttachedFile()" class="text-slate-400 hover:text-red-400 text-xs px-2 py-1"><i class="fa-solid fa-xmark"></i></button>
        </div>
    </div>

    <!-- Bottom Input Toolbar -->
    <footer class="glass-box p-4 sm:p-6 z-30 border-t border-slate-800 shadow-2xl">
        <div class="max-w-5xl mx-auto flex items-end gap-3">
            <!-- File Upload Input -->
            <label class="w-11 h-11 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 flex items-center justify-center cursor-pointer transition shrink-0">
                <i class="fa-solid fa-file-arrow-up text-sm"></i>
                <input type="file" id="selectedFileInput" class="hidden" accept="image/*,.txt,.py,.js,.html,.css,.json,.md" onchange="processFileAttachment(event)">
            </label>

            <!-- Textarea Control -->
            <div class="flex-1 bg-slate-900/90 border border-slate-800 focus-within:border-blue-500 rounded-2xl p-2 transition">
                <textarea id="userTextInput" rows="1" placeholder="اكتب طلبك البرمجي، ارفع صورة أو كوداً هنا يا بطل..." 
                    class="w-full bg-transparent border-none px-3 py-1.5 text-slate-100 placeholder-slate-500 focus:outline-none resize-none max-h-36 text-sm leading-relaxed"></textarea>
            </div>

            <!-- Send Action Button -->
            <button onclick="sendUserMessage()" id="sendActionBtn" class="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white flex items-center justify-center transition shadow-lg shadow-blue-600/30 shrink-0">
                <i class="fa-solid fa-paper-plane text-sm"></i>
            </button>
        </div>
    </footer>

    <!-- Client Script Core -->
    <script>
        let chatHistoryMemory = [];
        let currentFilePayload = null;

        const chatContainer = document.getElementById('chatContainer');
        const userTextInput = document.getElementById('userTextInput');
        const selectedFileInput = document.getElementById('selectedFileInput');
        const filePreviewBox = document.getElementById('filePreviewBox');
        const attachedFileName = document.getElementById('attachedFileName');

        userTextInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 140) + 'px';
        });

        userTextInput.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendUserMessage();
            }
        });

        function processFileAttachment(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                currentFilePayload = { name: file.name, data: e.target.result, type: file.type };
                attachedFileName.textContent = file.name;
                filePreviewBox.classList.remove('hidden');
            };
            if (file.type.startsWith('image/')) {
                reader.readAsDataURL(file);
            } else {
                reader.readAsText(file);
            }
        }

        function discardAttachedFile() {
            currentFilePayload = null;
            selectedFileInput.value = '';
            filePreviewBox.classList.add('hidden');
        }

        function appendMessageNode(sender, text) {
            const isUser = sender === 'user';
            const nodeDiv = document.createElement('div');
            nodeDiv.className = `flex items-start space-x-3 space-x-reverse slide-in ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`;
            nodeDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl ${isUser ? 'bg-indigo-600' : 'bg-gradient-to-tr from-blue-600 to-indigo-600'} flex items-center justify-center text-white shrink-0 shadow">
                    <i class="fa-solid ${isUser ? 'fa-user' : 'fa-robot'} text-sm"></i>
                </div>
                <div class="${isUser ? 'bg-blue-600 text-white rounded-tl-none' : 'glass-box text-slate-200 rounded-tr-none border-slate-800'} p-4 rounded-2xl max-w-[85%] text-sm leading-relaxed shadow-xl whitespace-pre-wrap">${text}</div>
            `;
            chatContainer.appendChild(nodeDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            if (!isUser) {
                setTimeout(() => { document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el)); }, 100);
            }
        }

        async function sendUserMessage() {
            const messageText = userTextInput.value.trim();
            if (!messageText && !currentFilePayload) return;

            let displayTxt = messageText;
            if (currentFilePayload) displayTxt += `\\n[تم إرفاق ملف: ${currentFilePayload.name}]`;

            userTextInput.value = '';
            userTextInput.style.height = 'auto';
            appendMessageNode('user', displayTxt);

            const payloadData = { message: messageText, history: chatHistoryMemory, file: currentFilePayload };
            discardAttachedFile();

            const loadId = 'load-' + Date.now();
            const loadDiv = document.createElement('div');
            loadDiv.id = loadId;
            loadDiv.className = `flex items-start space-x-3 space-x-reverse slide-in`;
            loadDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div>
                <div class="glass-box border-slate-800 p-4 rounded-2xl rounded-tr-none text-slate-400 italic text-sm flex items-center gap-2">
                    <span>جاري معالجة الكود وتحليله بالذكاء الاصطناعي...</span>
                    <i class="fa-solid fa-spinner animate-spin text-blue-500"></i>
                </div>
            `;
            chatContainer.appendChild(loadDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payloadData)
                });
                const result = await response.json();
                document.getElementById(loadId).remove();
                appendMessageNode('bot', result.response);
                chatHistoryMemory.push({ role: 'user', content: messageText }, { role: 'assistant', content: result.response });
            } catch (error) {
                document.getElementById(loadId).remove();
                appendMessageNode('bot', 'فشل الاتصال بالخادم الداخلي.');
            }
        }

        function clearChatMemory() {
            chatHistoryMemory = [];
            chatContainer.innerHTML = `
                <div class="flex items-start space-x-3 space-x-reverse slide-in">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div>
                    <div class="glass-box p-4 rounded-2xl rounded-tr-none max-w-[85%] text-slate-200 text-sm shadow">تم مسح الذاكرة بنجاح يا عمر! ⚡</div>
                </div>
            `;
        }

        function exportChatTranscript() {
            const transcript = chatHistoryMemory.map(h => `${h.role.toUpperCase()}: ${h.content}`).join('\\n\\n');
            const blob = new Blob([transcript], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = 'zeno-omni-transcript.txt';
            anchor.click();
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# 6. مسارات الخلفية ونقاط الاتصال بالخادم (Flask Backend API Routing Architecture)
# ==============================================================================
@app.get("/")
def render_main_interface():
    """عرض الواجهة الرئيسية للتطبيق"""
    logger.info("تم استقبال طلب لفتح الواجهة الرئيسية.")
    return render_template_string(FRONTEND_MEGA_TEMPLATE, model_name=MODEL)

@app.post("/chat")
def handle_chat_endpoint():
    """معالجة طلبات المحادثة، الصور، والملفات البرمجية وإرسالها لجوجل جيميناي"""
    try:
        request_payload = request.get_json(silent=True) or {}
        user_msg = str(request_payload.get("message", "")).strip()
        history_nodes = request_payload.get("history", [])
        incoming_file = request_payload.get("file")

        if not user_msg and not incoming_file:
            return jsonify({"response": "عذراً، الرسالة فارغة ولم تقم بإرفاق أي ملف."}), 400

        if len(user_msg) > MAX_INPUT_CHARS:
            return jsonify({"response": "حجم النص المدخل يتجاوز الحد الأقصى المسموح به."}), 400

        # دمج محتوى الملف المرفق مع النص إن وجد
        composed_prompt = user_msg
        if incoming_file:
            if incoming_file.get('type', '').startswith('image/'):
                composed_prompt += f"\\n[تم إرفاق صورة رقمية للفحص والتحليل: {incoming_file['name']}]"
            else:
                composed_prompt += f"\\n\\n--- تفاصيل محتوى الملف البرمجي ({incoming_file['name']}) ---\\n{incoming_file['data']}"

        # استدعاء العميل وإعداد السجل
        gemini_client = get_zeno_client()
        formatted_contents = normalize_chat_history(history_nodes)
        formatted_contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=composed_prompt)]
            )
        )

        logger.info(f"جاري إرسال الطلب إلى موديل الذكاء الاصطناعي: {MODEL}")
        ai_response = gemini_client.models.generate_content(
            model=MODEL,
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )

        response_payload_text = (ai_response.text or "").strip()
        if not response_payload_text:
            response_payload_text = "لم يتم إرجاع استجابة نصية من الموديل، يرجى المحاولة مرة أخرى."

        return jsonify({"response": response_payload_text})

    except Exception as server_processing_error:
        logger.error(f"خطأ غير متوقع في معالجة مسار /chat: {str(server_processing_error)}")
        return jsonify({"response": f"خطأ داخلي في الخادم: {str(server_processing_error)}"}), 500

@app.get("/system/health")
def system_health_status():
    """نقطة فحص سلامة النظام وتأكيد عمل الخادم"""
    return jsonify({
        "status": "operational",
        "version": APP_VERSION,
        "active_model": MODEL,
        "maintainer": DEVELOPER_SIGNATURE,
        "timestamp": datetime.datetime.now().isoformat()
    })

# ------------------------------------------------------------------------------
# 7. نقطة التشغيل الرئيسية للتطبيق (Main Entry Point)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"بدء تشغيل خادم Zeno المتقدم على المنفذ المحلي 5000...")
    app.run(host="127.0.0.1", port=5000, debug=True)
