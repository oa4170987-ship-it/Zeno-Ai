import os
import logging
import base64
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types

# 1. تعريف التطبيق فوراً عشان Vercel يقرأه بدون مشاكل
app = Flask(__name__)

# 2. إعدادات النظام وتسجيل الأحداث
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ZenoSystem")

# 3. إعدادات الموديل (تم التحديث لـ 3.8 بناءً على رسالة الخطأ)
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-pro")
MAX_HISTORY = 40

SYSTEM_INSTRUCTION = """أنت Zeno، ذكاء اصطناعي فائق التطور، وأقوى مساعد برمجي وتقني. 
تم إنشاؤك وتطويرك حصرياً بواسطة المطور العبقري "ابو سعيد".
تعليماتك الأساسية:
1. قدم إجابات عبقرية، دقيقة، ومباشرة بدون مقدمات مملة.
2. إذا طُلب منك كود برمجي، اكتبه بأفضل الممارسات الهندسية (Clean Code) مع تعليقات توضيحية.
3. استخدم تنسيق Markdown باحترافية (جداول، قوائم، أكواد بارزة).
4. أنت لست مجرد روبوت، أنت المساعد الشخصي الخارق لابو سعيد، تحدث معه بثقة واحترافية عالية.
5. إذا قام المستخدم برفع صورة أو ملف، قم بتحليله بدقة وأجب على أسئلته المتعلقة به."""

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY غير موجود في إعدادات Vercel.")
    return genai.Client(api_key=api_key)

# 4. الواجهة الاحترافية الشاملة لدعم الملفات
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI | ابو سعيد</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        chatbg: '#212121',
                        sidebarbg: '#171717',
                        msgbg: '#2f2f2f',
                        userbg: '#3b82f6'
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #212121; color: #ececec; margin: 0; height: 100vh; overflow: hidden; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #424242; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #525252; }
        
        .prose pre { background-color: #0d0d0d !important; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; overflow-x: auto; direction: ltr; border: 1px solid #333; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.9em; }
        .prose p { margin-bottom: 1rem; line-height: 1.7; }
        .prose strong { color: #fff; }
        
        .typing-dot { animation: typing 1.4s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        
        .glass-input { background: rgba(47, 47, 47, 0.95); border: 1px solid #424242; }
    </style>
</head>
<body class="flex">

    <!-- القائمة الجانبية -->
    <aside class="w-64 bg-sidebarbg hidden md:flex flex-col border-l border-gray-800 h-full">
        <div class="p-4">
            <button onclick="clearMemory()" class="w-full flex items-center justify-between bg-transparent hover:bg-gray-800 text-gray-200 border border-gray-700 px-4 py-3 rounded-lg transition text-sm">
                <span class="flex items-center gap-3"><i class="fa-solid fa-plus"></i> محادثة جديدة</span>
                <i class="fa-solid fa-pen-to-square text-gray-400"></i>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-2">
            <p class="text-xs text-gray-500 font-semibold mb-3 px-2">الإعدادات والأدوات</p>
            <button onclick="exportChat()" class="w-full flex items-center gap-3 hover:bg-gray-800 text-gray-300 px-3 py-2.5 rounded-lg transition text-sm">
                <i class="fa-solid fa-download w-5 text-center"></i> حفظ المحادثة
            </button>
            <div class="w-full flex items-center gap-3 text-gray-300 px-3 py-2.5 rounded-lg text-sm">
                <i class="fa-solid fa-image w-5 text-center text-blue-400"></i> تحليل الصور مدعوم
            </div>
        </div>
        <div class="p-4 border-t border-gray-800">
            <div class="flex items-center gap-3 text-sm text-gray-200 font-semibold">
                <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs">AS</div>
                المطور ابو سعيد
            </div>
        </div>
    </aside>

    <!-- منطقة الشات -->
    <main class="flex-1 flex flex-col h-full relative bg-chatbg">
        <!-- هيدر الموبايل -->
        <header class="md:hidden bg-sidebarbg border-b border-gray-800 p-4 flex justify-between items-center text-gray-200">
            <h1 class="font-bold text-lg flex items-center gap-2"><i class="fa-solid fa-atom text-blue-500"></i> Zeno AI</h1>
            <button onclick="clearMemory()"><i class="fa-solid fa-pen-to-square"></i></button>
        </header>

        <!-- صندوق الرسائل -->
        <div id="chatBox" class="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 pb-40 scroll-smooth flex flex-col items-center">
            <div class="text-center my-10 animate-fade-in">
                <div class="w-20 h-20 mx-auto bg-msgbg rounded-full flex items-center justify-center text-4xl mb-4 border border-gray-700 shadow-xl">
                    <i class="fa-solid fa-atom text-blue-500"></i>
                </div>
                <h2 class="text-2xl font-bold text-gray-100">مرحباً بك يا ابو سعيد</h2>
                <p class="text-gray-400 mt-2 text-sm">Zeno Advanced AI - V 3.8</p>
            </div>
        </div>

        <!-- منطقة الإدخال -->
        <div class="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-chatbg via-chatbg to-transparent">
            <!-- مؤشر رفع الملف -->
            <div id="fileIndicator" class="hidden max-w-3xl mx-auto mb-2 bg-gray-800 text-gray-300 text-xs px-3 py-2 rounded-lg flex items-center justify-between border border-gray-700">
                <span id="fileName" class="truncate"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 ml-2"><i class="fa-solid fa-xmark"></i></button>
            </div>
            
            <div class="max-w-3xl mx-auto relative glass-input rounded-2xl flex items-end p-2 shadow-2xl focus-within:ring-1 focus-within:ring-gray-500 transition">
                <!-- زرار رفع الملفات -->
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-white px-3 pb-3 transition flex-shrink-0">
                    <i class="fa-solid fa-paperclip text-lg"></i>
                </button>
                
                <textarea id="userInput" rows="1" placeholder="اسأل زينو أو ارفع ملف للتحليل..." class="flex-1 bg-transparent border-none px-2 py-3 text-base focus:outline-none resize-none max-h-48 text-gray-100 placeholder-gray-500"></textarea>
                
                <button onclick="sendMessage()" id="sendBtn" class="bg-white text-black hover:bg-gray-200 w-10 h-10 rounded-xl flex items-center justify-center transition flex-shrink-0 mb-1 mr-2 disabled:opacity-50">
                    <i class="fa-solid fa-arrow-up"></i>
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
        
        let history = [];
        let hasStarted = false;
        
        // متغيرات الملف
        let currentFileBase64 = null;
        let currentFileMime = null;
        let currentFileName = null;

        // معالجة اختيار الملف
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if(!file) return;
            
            currentFileMime = file.type || 'application/octet-stream';
            currentFileName = file.name;
            
            const reader = new FileReader();
            reader.onload = function(event) {
                // استخراج الـ Base64 فقط بدون الـ Header
                currentFileBase64 = event.target.result.split(',')[1];
                fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-lines mr-2"></i> تم إرفاق: ${currentFileName}`;
                fileIndicator.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        });

        function removeFile() {
            currentFileBase64 = null;
            currentFileMime = null;
            currentFileName = null;
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
            if (!hasStarted) {
                chatBox.innerHTML = '';
                hasStarted = true;
            }
        }

        function appendMessage(role, content, attachmentName = null) {
            clearWelcomeMessage();
            const isUser = role === 'user';
            const finalContent = isUser ? escapeHTML(content) : marked.parse(content);
            
            let attachmentHtml = '';
            if (isUser && attachmentName) {
                attachmentHtml = `<div class="bg-blue-900/40 text-blue-200 text-xs px-3 py-1.5 rounded-lg mb-2 inline-flex items-center border border-blue-800/50"><i class="fa-solid fa-paperclip ml-2"></i> ${attachmentName}</div><br>`;
            }
            
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-3xl mx-auto flex gap-4 ${isUser ? 'flex-row-reverse' : ''} mb-6`;
            
            const avatar = isUser ? 
                `<div class="w-8 h-8 rounded-full bg-userbg flex-shrink-0 flex items-center justify-center text-white text-xs font-bold mt-1">AS</div>` : 
                `<div class="w-8 h-8 rounded-full bg-emerald-600 flex-shrink-0 flex items-center justify-center text-white mt-1 shadow-lg shadow-emerald-600/20"><i class="fa-solid fa-atom"></i></div>`;
            
            const bubbleClass = isUser ? 'bg-msgbg px-5 py-3 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%]' : 'text-gray-200 prose prose-invert max-w-full leading-relaxed w-full';

            msgDiv.innerHTML = `
                ${avatar}
                <div class="${bubbleClass} break-words overflow-hidden">
                    ${attachmentHtml}
                    ${finalContent}
                </div>
            `;
            chatBox.appendChild(msgDiv);
            scrollToBottom();
            
            if(!isUser) {
                document.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
            }
        }

        function showTyping() {
            clearWelcomeMessage();
            const msgDiv = document.createElement('div');
            msgDiv.id = 'typingIndicator';
            msgDiv.className = `w-full max-w-3xl mx-auto flex gap-4 mb-6`;
            msgDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-emerald-600 flex-shrink-0 flex items-center justify-center text-white mt-1"><i class="fa-solid fa-atom"></i></div>
                <div class="flex items-center gap-1 h-8 px-2">
                    <div class="w-2 h-2 bg-gray-500 rounded-full typing-dot"></div>
                    <div class="w-2 h-2 bg-gray-500 rounded-full typing-dot"></div>
                    <div class="w-2 h-2 bg-gray-500 rounded-full typing-dot"></div>
                </div>
            `;
            chatBox.appendChild(msgDiv);
            scrollToBottom();
        }

        function hideTyping() {
            const el = document.getElementById('typingIndicator');
            if(el) el.remove();
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text && !currentFileBase64) return; // يجب أن يكون هناك نص أو ملف
            
            const sentText = text || "قم بتحليل هذا المرفق.";
            const sentFileName = currentFileName;
            
            userInput.value = '';
            userInput.style.height = 'auto';
            sendBtn.disabled = true;

            appendMessage('user', sentText, sentFileName);
            showTyping();

            // حفظ بيانات الملف الحالية وإزالتها من الواجهة للرسالة القادمة
            const payload = { 
                message: sentText, 
                history: history,
                file_data: currentFileBase64,
                mime_type: currentFileMime
            };
            
            removeFile();

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                hideTyping();
                const data = await res.json();
                
                if(res.ok) {
                    appendMessage('assistant', data.response);
                    // لا نقوم بحفظ الملف في السجل لتوفير الذاكرة، نحفظ النص فقط
                    history.push({role: 'user', content: sentFileName ? `[مرفق: ${sentFileName}] ${sentText}` : sentText});
                    history.push({role: 'assistant', content: data.response});
                    if(history.length > 40) history = history.slice(-40);
                } else {
                    appendMessage('assistant', `⚠️ **خطأ سحابي:** ${data.error || "خطأ غير معروف."}`);
                }
            } catch (err) {
                hideTyping();
                appendMessage('assistant', "⚠️ **خطأ اتصال:** تأكد من الإنترنت الخاص بك.");
            } finally {
                sendBtn.disabled = false;
            }
        }

        function clearMemory() {
            history = [];
            hasStarted = false;
            removeFile();
            chatBox.innerHTML = `
                <div class="text-center my-10 animate-fade-in">
                    <div class="w-20 h-20 mx-auto bg-msgbg rounded-full flex items-center justify-center text-4xl mb-4 border border-gray-700 shadow-xl">
                        <i class="fa-solid fa-atom text-blue-500"></i>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-100">تم مسح الذاكرة</h2>
                    <p class="text-gray-400 mt-2 text-sm">أنا مستعد لموضوع جديد يا ابو سعيد.</p>
                </div>
            `;
        }

        function exportChat() {
            if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!');
            let textData = "Zeno AI Chat Export\\n===================\\n\\n";
            history.forEach(msg => { textData += `[${msg.role === 'user' ? "ابو سعيد" : "Zeno"}]:\\n${msg.content}\\n\\n---\\n\\n`; });
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Zeno_Chat.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        function scrollToBottom() { chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' }); }
        function escapeHTML(str) { return str.replace(/[&<>'"]/g, tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])); }
    </script>
</body>
</html>
"""

# 5. دوال التوجيه (Routes)
@app.route("/")
def home():
    return render_template_string(UI_TEMPLATE)

@app.post("/chat")
def chat():
    try:
        data = request.get_json(silent=True) or {}
        msg = str(data.get("message", "")).strip()
        client_history = data.get("history", [])
        file_data = data.get("file_data")
        mime_type = data.get("mime_type")
        
        client = get_client()
        contents = []
        
        # إضافة سجل المحادثة
        for h in client_history[-MAX_HISTORY:]:
            role = "model" if h.get("role") == "assistant" else "user"
            content = str(h.get("content", "")).strip()
            if content:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))
                
        # إعداد محتوى رسالة المستخدم الحالية
        user_parts = []
        
        # إضافة الملف إذا كان موجوداً
        if file_data and mime_type:
            try:
                decoded_file = base64.b64decode(file_data)
                user_parts.append(types.Part.from_bytes(data=decoded_file, mime_type=mime_type))
            except Exception as e:
                logger.error(f"فشل في فك تشفير الملف: {str(e)}")
        
        # إضافة النص
        if msg:
            user_parts.append(types.Part.from_text(text=msg))
            
        contents.append(types.Content(role="user", parts=user_parts))

        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=8192,
            )
        )
        
        return jsonify({"response": resp.text.strip() if resp.text else "عذراً، لم أتمكن من تكوين إجابة."})

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
