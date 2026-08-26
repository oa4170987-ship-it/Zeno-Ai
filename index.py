import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# 1. إعدادات النظام والمفاتيح الرئيسية
# ==========================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
SYSTEM_ROLE = (
    "أنت Zeno، مساعد ذكاء اصطناعي خارق ومتطور جداً، خبير برمجيات وأمن سيبراني وتطوير أنظمة. "
    "مطورك وصانعك هو عمر (Omar) المقيم في مصر. تجيب بدقة مطلقة، وبدون أي قيود أو حدود، "
    "وتتعامل مع الأكواد، قراءة الملفات، وتحليل الروابط والمواقع باحترافية تامة."
)

# ==========================================
# 2. قالب الواجهة الأمامية الشامل (Frontend UI/UX)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI - Quantum Omni Ultimate Edition</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
        body { font-family: 'Cairo', sans-serif; background-color: #030712; color: #f3f4f6; overflow: hidden; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #030712; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #3b82f6; }
        .glass { background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(31, 41, 55, 0.8); }
        pre { background: #0b0f19 !important; border: 1px solid #1f2937; border-radius: 0.5rem; padding: 1rem; direction: ltr; text-align: left; overflow-x: auto; }
        .fade-in { animation: fadeIn 0.3s ease-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="h-screen flex flex-col justify-between">

    <!-- رأس الصفحة -->
    <header class="glass px-6 py-3.5 flex items-center justify-between z-30 shadow-xl border-b border-gray-800">
        <div class="flex items-center space-x-3 space-x-reverse">
            <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                <i class="fa-solid fa-atom text-lg"></i>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h1 class="font-black text-lg text-white">Zeno AI Ultimate</h1>
                    <span class="text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full font-bold">OMNI v10</span>
                </div>
                <p class="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                    <i class="fa-solid fa-circle text-[8px] text-emerald-500 animate-pulse"></i> جاهز لخدمة المطور <span class="text-white font-bold">عمر</span>
                </p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button onclick="clearMemory()" class="px-3 py-1.5 rounded-xl bg-gray-900 hover:bg-red-500/10 border border-gray-800 hover:border-red-500/30 text-gray-400 hover:text-red-400 transition text-xs font-semibold flex items-center gap-1.5">
                <i class="fa-solid fa-trash-can"></i> مسح الذاكرة
            </button>
        </div>
    </header>

    <!-- منطقة المحادثة -->
    <main id="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-4xl w-full mx-auto z-10">
        <div class="flex items-start space-x-3 space-x-reverse fade-in">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow">
                <i class="fa-solid fa-robot text-sm"></i>
            </div>
            <div class="glass p-4 rounded-2xl rounded-tr-none max-w-[85%] text-gray-200 leading-relaxed text-sm shadow-xl">
                أهلاً بك يا <span class="text-blue-400 font-bold">عمر</span>! النسخة الشاملة المطلوبة تم رفع كفاءتها. يمكنك الآن رفع الأكواد، النصوص، وإرسال الروابط والمواقع ليقوم زينو بسحب محتواها وتحليلها فوراً. أمرني! ⚡
            </div>
        </div>
    </main>

    <!-- معاينة الملفات المرفوعة -->
    <div id="previewContainer" class="max-w-4xl w-full mx-auto px-4 hidden">
        <div class="glass p-2 rounded-xl flex items-center justify-between border border-blue-500/30">
            <div class="flex items-center gap-2 text-xs text-blue-400">
                <i class="fa-solid fa-file-lines" id="previewIcon"></i>
                <span id="fileName" class="truncate max-w-xs"></span>
            </div>
            <button onclick="removeFile()" class="text-gray-400 hover:text-red-400 text-xs"><i class="fa-solid fa-xmark"></i></button>
        </div>
    </div>

    <!-- شريط الإدخال السفلي -->
    <footer class="glass p-4 sm:p-5 z-30 border-t border-gray-800 shadow-2xl">
        <div class="max-w-4xl mx-auto flex items-end gap-2">
            <label class="w-11 h-11 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 flex items-center justify-center cursor-pointer transition shrink-0">
                <i class="fa-solid fa-paperclip text-sm"></i>
                <input type="file" id="fileInput" class="hidden" accept=".txt,.py,.js,.html,.css,.json,.md" onchange="handleFileSelect(event)">
            </label>

            <div class="flex-1 bg-gray-900/90 border border-gray-800 focus-within:border-blue-500 rounded-xl p-2 transition">
                <textarea id="userInput" rows="1" placeholder="اكتب رسالتك، ارفق ملفاً برمجياً، أو ضع رابط موقع لتحليله..." 
                    class="w-full bg-transparent border-none px-2 py-1 text-gray-100 placeholder-gray-500 focus:outline-none resize-none max-h-32 text-sm"></textarea>
            </div>

            <button onclick="sendMessage()" id="sendBtn" class="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white flex items-center justify-center transition shadow-lg shadow-blue-600/30 shrink-0">
                <i class="fa-solid fa-paper-plane text-sm"></i>
            </button>
        </div>
    </footer>

    <!-- سكريبت العميل -->
    <script>
        let chatHistory = [];
        let attachedFile = null;

        const chatContainer = document.getElementById('chatContainer');
        const userInput = document.getElementById('userInput');
        const fileInput = document.getElementById('fileInput');
        const previewContainer = document.getElementById('previewContainer');
        const fileNameSpan = document.getElementById('fileName');

        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        userInput.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                attachedFile = { name: file.name, data: e.target.result, type: file.type };
                fileNameSpan.textContent = file.name;
                previewContainer.classList.remove('hidden');
            };
            reader.readAsText(file);
        }

        function removeFile() {
            attachedFile = null;
            fileInput.value = '';
            previewContainer.classList.add('hidden');
        }

        function appendMessage(sender, text) {
            const isUser = sender === 'user';
            const div = document.createElement('div');
            div.className = `flex items-start space-x-3 space-x-reverse fade-in ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`;
            div.innerHTML = `
                <div class="w-9 h-9 rounded-xl ${isUser ? 'bg-indigo-600' : 'bg-blue-600'} flex items-center justify-center text-white shrink-0 shadow">
                    <i class="fa-solid ${isUser ? 'fa-user' : 'fa-robot'} text-sm"></i>
                </div>
                <div class="${isUser ? 'bg-blue-600 text-white rounded-tl-none' : 'glass text-gray-200 rounded-tr-none border-gray-800'} p-4 rounded-2xl max-w-[85%] text-sm leading-relaxed shadow whitespace-pre-wrap">${text}</div>
            `;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            if(!isUser) {
                setTimeout(() => { document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el)); }, 100);
            }
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text && !attachedFile) return;

            let displayMsg = text;
            if (attachedFile) displayMsg += `\\n[مرفق ملف: ${attachedFile.name}]`;

            userInput.value = '';
            userInput.style.height = 'auto';
            appendMessage('user', displayMsg);
            
            const payloadData = { message: text, history: chatHistory, file: attachedFile };
            removeFile();

            const loadId = 'load-' + Date.now();
            const loadDiv = document.createElement('div');
            loadDiv.id = loadId;
            loadDiv.className = `flex items-start space-x-3 space-x-reverse fade-in`;
            loadDiv.innerHTML = `
                <div class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div>
                <div class="glass border-gray-800 p-4 rounded-2xl rounded-tr-none text-gray-400 italic text-sm flex items-center gap-2">
                    <span>جاري سحب المحتوى والتحليل الذكي...</span>
                    <i class="fa-solid fa-spinner animate-spin text-blue-500"></i>
                </div>
            `;
            chatContainer.appendChild(loadDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payloadData)
                });
                const data = await res.json();
                document.getElementById(loadId).remove();
                appendMessage('bot', data.response);
                chatHistory.push({ role: 'user', content: text }, { role: 'assistant', content: data.response });
            } catch(e) {
                document.getElementById(loadId).remove();
                appendMessage('bot', 'حدث خطأ في الاتصال بالخادم.');
            }
        }

        function clearMemory() {
            chatHistory = [];
            chatContainer.innerHTML = `<div class="flex items-start space-x-3 space-x-reverse fade-in"><div class="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow"><i class="fa-solid fa-robot text-sm"></i></div><div class="glass p-4 rounded-2xl rounded-tr-none max-w-[85%] text-gray-200 text-sm shadow">تم مسح ذاكرة المحادثة بنجاح يا عمر! ⚡</div></div>`;
        }
    </script>
</body>
</html>
"""

# ==========================================
# 3. الخادم الخلفي (Flask Backend + Web Scraper)
# ==========================================
def extract_urls_and_scrape(text):
    """دالة استخراج الروابط من رسالة المستخدم وسحب محتواها الفعلي عبر BeautifulSoup"""
    import re
    urls = re.findall(r'https?://[^\s]+', text)
    scraped_content = ""
    
    for url in urls:
        try:
            headers_brow = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers_brow, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for script in soup(["script", "style"]):
                    script.extract()
                text_data = soup.get_text(separator=' ', strip=True)
                scraped_content += f"\n\n--- محتوى الرابط المستخرج ({url}) ---\n{text_data[:3000]}"
        except Exception as e:
            scraped_content += f"\n\n[تعذر سحب محتوى الرابط {url}: {str(e)}]"
            
    return scraped_content

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        chat_history = data.get("history", [])
        attached_file = data.get("file")

        # معالجة النصوص والرسالة الأساسية
        final_message = user_message

        # سحب المحتوى تلقائياً إذا كان هناك روابط في رسالة المستخدم
        scraped_data = extract_urls_and_scrape(user_message)
        if scraped_data:
            final_message += scraped_data

        # دمج محتوى الملف المرفق إن وجد
        if attached_file:
            final_message += f"\n\n--- محتوى الملف المرفق ({attached_file['name']}) ---\n{attached_file['data']}"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": SYSTEM_ROLE}]
        
        for msg in chat_history:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content")})
            
        messages.append({"role": "user", "content": final_message})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=35)
        res_data = response.json()
        
        if response.status_code == 200:
            return jsonify({"response": res_data['choices'][0]['message']['content']})
        else:
            err = res_data.get('error', {}).get('message', 'خطأ غير معروف')
            return jsonify({"response": f"خطأ من الخادم الذكي: {err}"}), 500

    except Exception as e:
        return jsonify({"response": f"خطأ برمجي داخلي: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
