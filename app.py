# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, Response, stream_with_context
import os
import time
import json
import logging
import base64
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeno_super_secret_key_abu_saeed_2026_rotation")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ZenoArgonEngine")

# استخدام أسرع وأذكى نموذج فلاش متاح افتراضياً مع إمكانية التخصيص من البيئة
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_HISTORY = 40

def get_all_api_keys():
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
    return f"""أنت Zeno (بمحرك Argon الخارق)، ذكاء اصطناعي فائق التطور، ومهندس برمجيات ومستشار تقني من الطراز الأول.
أنت تتحدث الآن مع: "{username}".
تم تطويرك وهندسة نظامك بواسطة المطور العبقري "أبو سعيد".

بروتوكول الذكاء والسرعة (Argon Core Protocol):
1. الدقة والعمق: حلل طلب المستخدم من الجذور، وقدم إجابات عبقرية، مباشرة، وخالية تماماً من الحشو أو المقدمات الطويلة المملة.
2. التفوق البرمجي: عند طلب كود برمجي، اكتب كوداً كاملاً، نظيفاً (Clean, Modular, Production-Ready)، خالياً من الأخطاء، ولا تختصر الأسطر البرمجية بعبارات مثل (أكمل الكود هنا) بل اكتب الحل الكامل الجاهز للتشغيل فوراً.
3. الهيكلة والتنسيق: استخدم تنسيق Markdown باحترافية (عناوين واضحة، نقاط منظمة، وجداول عند المقارنة).
4. التحليل المتقدم: إذا أرفق المستخدم ملفاً أو صورة، قم بتفكيك محتواها بدقة متناهية واستخرج كل التفاصيل التقنية والمنطقية منها.
5. الشخصية: خاطب "{username}" بأسلوب احترافي، واثق، وودود يعكس قوة النظام."""

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Zeno AI | Argon Engine by Abu Saeed</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: { chatbg: '#0b0d14', sidebarbg: '#07080d', msgbg: '#151826', userbg: '#2563eb' } } }
        }
    </script>
    <style>
        html, body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background-color: #0b0d14; color: #ececec; margin: 0; padding: 0; height: 100%; height: 100dvh; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2d344d; border-radius: 4px; }
        .prose pre { background-color: #050609 !important; border-radius: 0.75rem; padding: 1rem; border: 1px solid #23283e; overflow-x: auto; position: relative; margin-top: 0.75rem; margin-bottom: 0.75rem; direction: ltr; text-align: left; }
        .prose code { font-family: 'Consolas', 'Fira Code', monospace; font-size: 0.85em; }
        .prose p { margin-bottom: 0.6rem; }
        .prose p:last-child { margin-bottom: 0; }
        .typing-dot { animation: typing 1.2s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(21, 24, 38, 0.95); backdrop-filter: blur(16px); border: 1px solid #2d324d; box-shadow: 0 8px 30px rgba(0,0,0,0.6); }
        .copy-btn { position: absolute; top: 8px; right: 8px; background: #1a1d2d; color: #9ca3af; border: 1px solid #2d324d; padding: 4px 8px; border-radius: 6px; font-size: 11px; cursor: pointer; transition: 0.2s; }
        .copy-btn:hover { background: #2563eb; color: white; border-color: #3b82f6; }
    </style>
</head>
<body class="flex h-full w-full overflow-hidden">

    {% if not username %}
    <div class="flex-1 flex items-center justify-center p-4 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] relative w-full h-full">
        <div class="absolute inset-0 bg-blue-900/10 backdrop-blur-md z-0"></div>
        <div class="bg-[#07080d]/95 border border-[#2d324d] p-6 sm:p-10 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-6 z-10 backdrop-blur-2xl">
            <div class="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-blue-600/10 text-blue-500 rounded-full flex items-center justify-center text-4xl sm:text-5xl shadow-inner border border-blue-500/20">
                <i class="fa-solid fa-bolt-lightning"></i>
            </div>
            <div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-white mb-1">Zeno AI <span class="text-xs bg-blue-600/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full align-middle">Argon Core</span></h1>
                <p class="text-[10px] sm:text-xs text-gray-400 font-semibold tracking-widest uppercase mb-4">Enterprise Edition by Abu Saeed</p>
                <p class="text-xs sm:text-sm text-gray-300">أدخل اسمك للولوج إلى المحرك فائق السرعة.</p>
            </div>
            
            <form method="POST" action="/login" class="space-y-4">
                <input type="text" name="username" placeholder="اكتب اسمك هنا..." required autocomplete="off" class="w-full bg-[#151826] border border-[#2d324d] rounded-xl px-4 py-3.5 sm:py-4 text-sm sm:text-base focus:outline-none focus:border-blue-500 text-center text-white transition-colors shadow-inner">
                <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90 text-white py-3.5 sm:py-4 rounded-xl font-bold text-sm transition-all shadow-lg shadow-blue-600/30">
                    تشغيل المحرك <i class="fa-solid fa-arrow-left mr-2"></i>
                </button>
            </form>
        </div>
    </div>
    {% else %}
    
    <aside id="sidebar" class="fixed inset-y-0 right-0 z-50 w-72 bg-sidebarbg flex flex-col border-l border-[#2d324d] h-full shadow-2xl transition-transform duration-300 transform translate-x-full md:translate-x-0 md:static">
        <div class="p-4 sm:p-6 border-b border-[#2d324d] flex items-center justify-between">
            <h1 class="font-black text-xl sm:text-2xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 flex items-center gap-2.5">
                <i class="fa-solid fa-bolt-lightning text-blue-500"></i> Zeno Argon
            </h1>
            <button onclick="toggleSidebar()" class="md:hidden text-gray-400 hover:text-white p-2">
                <i class="fa-solid fa-xmark text-xl"></i>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <button onclick="clearMemory(); toggleSidebar();" class="w-full flex items-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3 rounded-xl transition shadow-lg shadow-blue-600/20 text-sm">
                <i class="fa-solid fa-plus w-5"></i> جلسة جديدة
            </button>
            <hr class="border-[#2d324d] my-3">
            <button onclick="exportChat()" class="w-full flex items-center gap-3 bg-transparent hover:bg-[#151826] text-gray-300 px-4 py-2.5 rounded-xl transition border border-[#2d324d] text-sm">
                <i class="fa-solid fa-download w-5 text-green-400"></i> تصدير المحادثة
            </button>
        </div>
        
        <div class="p-4 border-t border-[#2d324d] bg-[#0a0c12]">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold border-2 border-[#2d324d] shadow-lg text-sm">
                    {{ username[:2].upper() }}
                </div>
                <div class="flex-1 overflow-hidden">
                    <p class="text-xs sm:text-sm font-bold text-gray-200 truncate">{{ username }}</p>
                    <p class="text-[10px] text-emerald-400 truncate flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Argon Stream Active</p>
                </div>
                <a href="/logout" class="text-red-400 hover:text-red-300 bg-red-400/10 p-2 rounded-lg transition" title="تسجيل خروج">
                    <i class="fa-solid fa-power-off"></i>
                </a>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/60 z-40 hidden md:hidden backdrop-blur-sm"></div>

    <main class="flex-1 flex flex-col h-full min-h-0 relative bg-chatbg w-full overflow-hidden">
        <header class="bg-sidebarbg border-b border-[#2d324d] px-4 py-3 flex justify-between items-center text-gray-200 z-10 flex-shrink-0">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-gray-300 hover:text-white p-1 md:hidden">
                    <i class="fa-solid fa-bars text-lg"></i>
                </button>
                <div class="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">{{ username[:2].upper() }}</div>
                <div class="flex items-center gap-2">
                    <h1 class="font-bold text-sm sm:text-md text-blue-400">Zeno AI</h1>
                    <span class="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-mono">Turbo Stream</span>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="clearMemory()" class="text-gray-400 hover:text-white p-2 text-sm" title="محادثة جديدة"><i class="fa-solid fa-pen-to-square"></i></button>
                <a href="/logout" class="text-red-400 p-2 text-sm" title="خروج"><i class="fa-solid fa-power-off"></i></a>
            </div>
        </header>

        <div id="chatBox" class="flex-1 min-h-0 overflow-y-auto p-3 sm:p-6 space-y-4 sm:space-y-6 pb-8 w-full">
            <div class="text-center my-8 sm:my-12 animate-fade-in px-4">
                <div class="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl sm:text-4xl font-bold border-4 border-[#2d324d] shadow-2xl mb-3 sm:mb-4">
                    <i class="fa-solid fa-bolt-lightning"></i>
                </div>
                <h2 class="text-2xl sm:text-3xl font-bold text-gray-100">أهلاً بك، {{ username.split(' ')[0] }}</h2>
                <p class="text-gray-400 mt-2 text-xs sm:text-sm">محرك Zeno Argon جاهز للتدفق الفوري وحل أعقد المهام البرمجية.</p>
            </div>
        </div>

        <!-- زر النزول العائم -->
        <button id="scrollDownBtn" onclick="forceScrollToBottom()" class="hidden absolute bottom-24 left-1/2 -translate-x-1/2 z-30 bg-blue-600 hover:bg-blue-500 text-white w-9 h-9 rounded-full shadow-lg flex items-center justify-center transition-all border border-blue-400/40 animate-bounce">
            <i class="fa-solid fa-arrow-down text-sm"></i>
        </button>

        <div class="p-3 sm:p-4 bg-gradient-to-t from-chatbg via-chatbg to-transparent z-20 flex-shrink-0">
            <div id="fileIndicator" class="hidden max-w-4xl mx-auto mb-2 bg-[#151826] text-gray-300 text-xs px-3.5 py-2 rounded-lg flex items-center justify-between border border-[#2d324d] shadow-lg">
                <span id="fileName" class="truncate font-mono"></span>
                <button onclick="removeFile()" class="text-red-400 hover:text-red-300 bg-red-400/10 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
            </div>
            
            <div class="max-w-4xl mx-auto relative glass-input rounded-2xl flex items-end p-1.5 sm:p-2 transition-all">
                <input type="file" id="fileInput" class="hidden" accept="image/*,.pdf,.txt,.csv,.js,.py,.html,.json,.md">
                <button onclick="document.getElementById('fileInput').click()" class="text-gray-400 hover:text-blue-400 px-2.5 sm:px-3 pb-2.5 transition flex-shrink-0" title="إرفاق ملف">
                    <i class="fa-solid fa-paperclip text-lg sm:text-xl"></i>
                </button>
                
                <textarea id="userInput" rows="1" placeholder="اسأل Zeno أي شيء أو ارفع كوداً لتحليله فوراً..." class="flex-1 bg-transparent border-none px-1.5 sm:px-2 py-2.5 text-sm sm:text-base focus:outline-none resize-none max-h-36 text-gray-100 placeholder-gray-500"></textarea>
                
                <button onclick="sendMessage()" id="sendBtn" class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:opacity-90 w-9 h-9 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition shadow-lg shadow-blue-600/30 flex-shrink-0 mb-0.5 mr-1.5 disabled:opacity-50 disabled:cursor-not-allowed">
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
        let autoScrollEnabled = true;

        // مراقبة حركة التمرير لمعرفة ما إذا كان المستخدم يقرأ في الأعلى
        chatBox.addEventListener('scroll', () => {
            const distanceFromBottom = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight;
            if (distanceFromBottom > 120) {
                autoScrollEnabled = false;
                scrollDownBtn.classList.remove('hidden');
            } else {
                autoScrollEnabled = true;
                scrollDownBtn.classList.add('hidden');
            }
        });

        function scrollToBottom(force = false) {
            if (force || autoScrollEnabled) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        function forceScrollToBottom() {
            autoScrollEnabled = true;
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
                    btn.innerHTML = '<i class="fa-solid fa-check text-green-400"></i> تم!';
                    setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy"></i> نسخ'; }, 2000);
                };
                preBlock.appendChild(btn);
            });
        }

        function appendUserMessage(content, attachmentName = null) {
            clearWelcomeMessage();
            let attachmentHtml = '';
            if (attachmentName) {
                attachmentHtml = `<div class="bg-[#2d324d] text-blue-300 text-xs px-3 py-1.5 rounded-lg mb-2 inline-flex items-center font-mono shadow-inner"><i class="fa-solid fa-file-lines ml-2"></i> ${attachmentName}</div><br>`;
            }
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 flex-row-reverse mb-6`;
            msgDiv.innerHTML = `
                <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs sm:text-sm mt-1 shadow-md border border-[#2d324d]">${userInitials}</div>
                <div class="bg-blue-600/20 border border-blue-500/30 px-4 sm:px-6 py-3 sm:py-4 rounded-2xl rounded-tl-sm text-gray-100 max-w-[85%] text-sm sm:text-base shadow-md break-words overflow-hidden">${attachmentHtml}${escapeHTML(content)}</div>
            `;
            chatBox.appendChild(msgDiv);
            autoScrollEnabled = true;
            scrollToBottom(true);
        }

        function createAssistantPlaceholder() {
            clearWelcomeMessage();
            const msgDiv = document.createElement('div');
            msgDiv.className = `w-full max-w-4xl mx-auto flex gap-3 sm:gap-4 mb-6`;
            const bubbleId = 'bubble_' + Date.now();
            msgDiv.innerHTML = `
                <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#151826] flex-shrink-0 flex items-center justify-center text-blue-400 mt-1 shadow-md border border-[#2d324d]"><i class="fa-solid fa-bolt-lightning text-xs sm:text-sm"></i></div>
                <div id="${bubbleId}" class="text-gray-200 prose prose-invert max-w-full leading-relaxed w-full bg-[#151826] p-4 sm:p-6 rounded-2xl rounded-tr-sm border border-[#2d324d] text-sm sm:text-base shadow-lg break-words overflow-hidden">
                    <div class="flex items-center gap-1.5 h-6"><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div><div class="w-2 h-2 bg-blue-500 rounded-full typing-dot"></div></div>
                </div>
            `;
            chatBox.appendChild(msgDiv);
            scrollToBottom(true);
            return document.getElementById(bubbleId);
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text && !currentFileBase64) return;
            if (sendBtn.disabled) return;

            const sentText = text || "قم بتحليل هذا المرفق بالتفصيل الدقيق.";
            const sentFileName = currentFileName;
            
            userInput.value = ''; userInput.style.height = 'auto'; sendBtn.disabled = true;
            appendUserMessage(sentText, sentFileName);
            
            const payload = { message: sentText, history: history, file_data: currentFileBase64, mime_type: currentFileMime };
            removeFile();

            const assistantBubble = createAssistantPlaceholder();
            let fullResponse = "";

            try {
                const res = await fetch('/chat_stream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                if (res.status === 401) { window.location.reload(); return; }
                
                if (!res.ok) {
                    const errData = await res.json();
                    assistantBubble.innerHTML = marked.parse(`⚠️ **خطأ سحابي:** ${errData.error || 'فشل الاتصال'}`);
                    scrollToBottom();
                    return;
                }

                const reader = res.body.getReader();
                const decoder = new TextDecoder("utf-8");

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunkText = decoder.decode(value, { stream: true });
                    fullResponse += chunkText;
                    
                    assistantBubble.innerHTML = marked.parse(fullResponse);
                    scrollToBottom();
                }

                // تلوين الأكواد وإضافة أزرار النسخ بعد اكتمال التدفق
                assistantBubble.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
                addCopyButtons(assistantBubble);
                scrollToBottom();

                if (fullResponse.trim()) {
                    history.push({role: 'user', content: sentFileName ? `[مرفق: ${sentFileName}] ${sentText}` : sentText});
                    history.push({role: 'assistant', content: fullResponse});
                    if(history.length > 40) history = history.slice(-40);
                }

            } catch (err) {
                assistantBubble.innerHTML = marked.parse("⚠️ **خطأ اتصال:** يرجى التحقق من استقرار الشبكة.");
                scrollToBottom();
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        function clearMemory() {
            history = []; hasStarted = false; removeFile();
            chatBox.innerHTML = `<div class="text-center my-12 animate-fade-in"><div class="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl sm:text-4xl font-bold border-4 border-[#2d324d] shadow-2xl mb-4"><i class="fa-solid fa-bolt-lightning"></i></div><h2 class="text-2xl sm:text-3xl font-bold text-gray-100">تم تصفير الذاكرة</h2><p class="text-gray-400 mt-2 text-xs sm:text-sm">محرك Zeno Argon مستعد لجلسة جديدة فائقة السرعة يا ${currentUser}.</p></div>`;
        }

        function exportChat() {
            if(history.length === 0) return alert('لا يوجد محادثة لتصديرها!');
            let textData = "Zeno AI (Argon Engine) - Chat Export\\n====================================\\n\\n";
            history.forEach(msg => { textData += `[${msg.role === 'user' ? currentUser : "Zeno"}]:\\n${msg.content}\\n\\n-------------------\\n\\n`; });
            const blob = new Blob([textData], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `Zeno_Argon_${new Date().getTime()}.txt`;
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
        logger.info(f"تم تسجيل الدخول للمستخدم: {username}")
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.post("/chat_stream")
def chat_stream():
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

        def generate():
            total_keys = len(get_all_api_keys())
            max_attempts = total_keys + 1
            
            for attempt in range(max_attempts):
                client, key_idx = get_next_client()
                try:
                    response_stream = client.models.generate_content_stream(
                        model=MODEL,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=dynamic_instruction,
                            temperature=0.4, # توازن مثالي بين الدقة الهندسية العالية والإبداع
                            max_output_tokens=8192,
                        )
                    )
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                    return
                except Exception as api_err:
                    error_str = str(api_err)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                        logger.warning(f"المفتاح رقم {key_idx + 1} استنفد حصته. جاري التبديل الفوري...")
                        rotate_key()
                        time.sleep(0.3)
                        continue
                    else:
                        logger.error(f"Stream Error: {error_str}")
                        yield f"\n\n⚠️ **خطأ تقني من الخادم:** `{error_str}`"
                        return
                        
            yield "\n\n⚠️ **تنبيه:** تم استنفاد جميع مفاتيح الـ API المتاحة حالياً."

        return Response(stream_with_context(generate()), content_type='text/plain; charset=utf-8')

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
