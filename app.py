import os
import logging
import base64
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from google import genai
from google.genai import types

# 1. تعريف التطبيق وإعداد مفتاح الجلسات (مهم جداً لنظام الحسابات)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeno_super_secret_key_abu_saeed_2026")

# 2. إعدادات النظام وتسجيل الأحداث
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger("ZenoSystem")

# 3. إعدادات الموديل (استخدام 1.5-flash لضمان السرعة الخارقة وعدم وجود قيود مزعجة)
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
MAX_HISTORY = 40

def get_dynamic_instruction(username):
    """دالة لتوليد تعليمات زينو ديناميكياً بناءً على اسم المستخدم"""
    return f"""أنت Zeno، ذكاء اصطناعي فائق التطور، وأقوى مساعد برمجي وتقني. 
أنت تتحدث الآن مع المستخدم: "{username}".
تعليماتك الأساسية:
1. يجب أن تنادي المستخدم باسمه "{username}" في بداية محادثاتك للترحيب به.
2. قدم إجابات عبقرية، سريعة، دقيقة، ومباشرة.
3. إذا طُلب منك كود برمجي، اكتبه بأفضل الممارسات الهندسية (Clean Code).
4. استخدم تنسيق Markdown باحترافية (جداول، قوائم، أكواد بارزة).
5. إذا قام المستخدم برفع صورة أو ملف، قم بتحليله بدقة وأجب على أسئلته المتعلقة به."""

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY غير موجود في إعدادات Vercel.")
    return genai.Client(api_key=api_key)

# 4. الواجهة الاحترافية (شاشة الدخول + شاشة الشات)
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zeno AI | حسابات المستخدمين</title>
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
                        chatbg: '#1a1a1a',
                        sidebarbg: '#111111',
                        msgbg: '#2d2d2d',
                        userbg: '#2563eb'
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #1a1a1a; color: #ececec; margin: 0; height: 100vh; overflow: hidden; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #424242; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #525252; }
        .prose pre { background-color: #000 !important; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; overflow-x: auto; direction: ltr; border: 1px solid #333; }
        .prose code { font-family: 'Consolas', monospace; font-size: 0.9em; }
        .typing-dot { animation: typing 1.4s infinite ease-in-out both; }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .glass-input { background: rgba(45, 45, 45, 0.95); border: 1px solid #424242; }
    </style>
</head>
<body class="flex">

    {% if not username %}
    <!-- شاشة تسجيل الدخول -->
    <div class="flex-1 flex items-center justify-center p-4 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] relative w-full">
        <div class="absolute inset-0 bg-blue-900/5 backdrop-blur-sm z-0"></div>
        <div class="bg-gray-900/90 border border-gray-800 p-8 rounded-3xl max-w-md w-full shadow-2xl text-center space-y-8 z-10 backdrop-blur-xl">
            <div class="w-20 h-20 mx-auto bg-blue-600/20 text-blue-500 rounded-full flex items-center justify-center text-4xl shadow-inner border border-blue-500/30">
                <i class="fa-solid fa-user-astronaut"></i>
            </div>
            <div>
                <h1 class="text-3xl font-bold text-white mb-2">تسجيل الدخول لـ Zeno</h1>
                <p class="text-sm text-gray-400">أدخل اسمك ليبدأ زينو في التعرف عليك</p>
            </div>
            <form method="POST" action="/login" class="space-y-5">
                <input type="text" name="username" placeholder="اكتب اسمك أو لقبك هنا..." required autocomplete="off" class="w-full bg-black/50 border border-gray-700 rounded-xl px-4 py-4 text-base focus:outline-none focus:border-blue-500 text-center text-white transition-colors">
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white py-4 rounded-xl font-bold text-sm transition-all shadow-lg shadow-blue-600/30">
                    بدء المحادثة <i class="fa-solid fa-arrow-left mr-2"></i>
                </button>
            </form>
        </div>
    </div>
    {% else %}
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
                <i class="fa-solid fa-bolt w-5 text-center text-yellow-400"></i> وضع السرعة القصوى
            </div>
        </div>
        <div class="p-4 border-t border-gray-800 flex justify-between items-center">
            <div class="flex items-center gap-3 text-sm text-gray-200 font-semibold truncate">
                <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs flex-shrink-0">
                    {{ username[:2].upper() }}
                </div>
                <span class="truncate">{{ username }}</span>
            </div>
            <a href="/logout" class="text-red-400 hover:text-red-300 ml-2" title="تسجيل خروج"><i class="fa-solid fa-right-from-bracket"></i></a>
        </div>
    </aside>

    <!-- منطقة الشات -->
    <main class="flex-1 flex flex-col h-full relative bg-chatbg">
        <header class="md:hidden bg-sidebarbg border-b border-gray-800 p-4 flex justify-between items
