import os
import logging
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types

# ==========================================
# 1. إعدادات النظام وتسجيل الأحداث
# ==========================================
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ZenoSystem")

app = Flask(__name__)

# استخدام موديل مستقر لتجنب مشاكل الضغط 503
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_HISTORY = 40

# تحديث ذكاء زينو (System Instruction)
SYSTEM_INSTRUCTION = """أنت Zeno، ذكاء اصطناعي فائق التطور، وأقوى مساعد برمجي وتقني. 
تم إنشاؤك وتطويرك حصرياً بواسطة المطور العبقري "عمر" (Omar).
تعليماتك الأساسية:
1. قدم إجابات عبقرية، دقيقة، ومباشرة بدون مقدمات مملة.
2. إذا طُلب منك كود برمجي، اكتبه بأفضل الممارسات الهندسية (Clean Code) مع تعليقات توضيحية.
3. استخدم تنسيق Markdown باحترافية (جداول، قوائم، أكواد بارزة).
4. أنت لست مجرد روبوت، أنت المساعد الشخصي الخارق لعمر، تحدث معه بثقة واحترافية عالية."""

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY غير موجود في إعدادات Vercel.")
    return genai.Client(api_key=api_key)

# ==========================================
# 2. الواجهة الاحترافية (Premium Dark Mode UI)
# ==========================================
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI | Omar</title>
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
        
        .glass-input { background: rgba(47, 47, 47, 0.8); backdrop-filter: blur(10px); border: 1px solid #424242; }
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
            <div class="w-full flex items-center gap-3 text-gray-300 px-3 py-2.5 rounded-lg text-sm opacity-50 cursor-not-allowed">
                <i class="fa-solid fa-image w-5 text-center"></i> تحليل الصور (قريباً)
            </div>
        </div>
        <div class="p-4 border-t border-gray-800">
            <div class="flex items-center gap-3 text-sm text-gray-200 font-semibold">
                <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white">OM</div>
                المطور عمر
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
                <h2 class="text-2xl font-bold text-gray-100">كيف يمكنني مساعدتك اليوم؟</h2>
                <p class="text-gray-400 mt-2 text-sm">Zeno Advanced AI - V 3.0</p>
            </div>

        </div>

        <!-- منطقة الإدخال -->
        <div class="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-chatbg via-chatbg to-transparent">
            <div class="max-w-3xl mx-auto relative glass-input rounded-2xl flex items-end p-2 shadow-2xl focus-within:ring-1 focus-within:ring-gray-500 transition">
                <textarea id="userInput" rows="1" placeholder="اسأل زينو عن أي شيء..." class="flex-1 bg-transparent border-none px-4 py-3 text-base focus:outline-none resize-none max-h-48 text-gray-100 placeholder-gray-400"></textarea>
                <button onclick="sendMessage()" id="sendBtn" class="bg-white text-black hover:bg-gray-200 w-10 h-10 rounded-xl flex items-center justify-center transition flex-shrink-0 mb-1 mr-2 disabled:opacity-50">
                    <i class="fa-solid fa-arrow-up"></i>
                </button>
            </div>
            <p class="text-center text-xs text-gray-500 mt-3">زينو يمكن أن يخطئ. يرجى مراجعة المعلومات الهامة.</p>
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
        let history = [];
        let hasStarted = false;

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

        function appendMessage(role, content) {
            clearWelcomeMessage();
            const isUser = role === 'user';
            const finalContent = isUser ? escapeHTML(content) : marked.parse(content);
            
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-3xl mx
