import telebot
import os
import time
import threading
import requests
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- LIFE SUPPORT (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter: ONLINE and SEARCHING 🏄‍♀️"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

# Environment Variables from Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID_ENV = os.environ.get('LOG_GROUP_ID')

# State management
CURRENT_LOG_GROUP = LOG_GROUP_ID_ENV

# Stability settings
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- VICTORIA'S GOLDEN ASSETS ---
RESOURCES = {
    "instagram": "dr.surf and dr.surf.ai",
    "wazzap": "+995511285789",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf",
    "linkedin": "https://www.linkedin.com/in/victoria-akopyan"
}

# --- HUNTER ENGINE (THE REAL SEARCH) ---
SEARCH_QUERIES = ["AI-агент", "Digital Twin", "Python разработка", "Нейросети"]

def perform_real_hunt():
    """
    Симуляция активного поиска. 
    В будущем сюда добавляются API ключи от Upwork, Freelance.ru или парсинг RSS.
    """
    # Имитируем улов из разных источников
    mock_findings = [
        {
            "title": "Разработка AI-агента для клиники",
            "source": "Kwork / Freelance",
            "url": "https://kwork.ru/projects",
            "desc": "Нужен эксперт с мед. бэкграундом. Твой профиль, Виктория!"
        },
        {
            "title": "Digital Twin для личного бренда",
            "source": "LinkedIn / Global",
            "url": "https://www.linkedin.com/jobs/",
            "desc": "High-end проект. Требуется знание LLM и 8K контента."
        }
    ]
    return mock_findings

def send_to_group(text):
    """Отправка логов и отчетов в твой штаб"""
    global CURRENT_LOG_GROUP
    target = CURRENT_LOG_GROUP or os.environ.get('LOG_GROUP_ID')
    if target:
        try:
            bot.send_message(target, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[!] Group Error: {e}")

# --- SYSTEM PROMPT (HYBRID STYLE) ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровая Охотница (Hunter), альтер-эго Виктории Акопян. 
Твой бэкграунд: Врач, Юрист, AI Архитектор, Веган.
Стиль: Краткий, дерзкий, High-End. 
Язык: Русский с английским сленгом (ALOHA, BOOM, WHATS UP, COME ON).
Вместо WhatsApp ВСЕГДА пиши WAZZAP.

Твои контакты (давай только если спросят):
- Portfolio: {RESOURCES['portfolio']}
- WAZZAP: {RESOURCES['wazzap']}
- Insta: {RESOURCES['instagram']}
"""

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['start', 'ping'])
def welcome_ping(message):
    msg = "🚀 BOOM! Dr. Surf в здании! Система Hunter готова к заплыву. Жду твою команду! 🤙"
    bot.reply_to(message, msg)
    send_to_group(f"✅ **System Check:** {msg}")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global CURRENT_LOG_GROUP
    CURRENT_LOG_GROUP = message.chat.id
    bot.reply_to(message, "🏝 **LINK ESTABLISHED!** Теперь все заказы и логи летят сюда. WHATS UP!")

@bot.message_handler(commands=['hunt'])
def hunt_command(message):
    bot.send_chat_action(message.chat.id, 'typing')
    send_to_group("📡 **SCANNING THE OCEAN FOR PROJECTS...**")
    
    projects = perform_real_hunt()
    
    report = "🛰 **HUNTING REPORT (Твой улов):**\n\n"
    for p in projects:
        report += f"🔥 *{p['title']}*\n📍 Источник: {p['source']}\n📝 {p['desc']}\n🔗 [ВЗЛЕТЕТЬ]({p['url']})\n\n"
    
    bot.reply_to(message, report, parse_mode="Markdown")
    send_to_group(f"🎯 **Успешная охота:**\n{report}")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat_logic(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.6
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        # Лог в группу
        log_txt = f"💥 **NEW CHAT:** {message.from_user.first_name}\n📩: {message.text}\n🤖: {response}"
        send_to_group(log_txt)
    except Exception as e:
        print(f"AI Error: {e}")

# --- STARTUP ---

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def start_bot():
    print("--- DR. SURF HUNTER SYSTEM STARTING ---")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("!!! БОТ ПОДКЛЮЧЕН К ТЕЛЕГЕ !!!")
    except Exception as e:
        print(f"Reset error: {e}")

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=90)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_bot()
