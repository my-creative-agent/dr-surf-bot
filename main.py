import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter status: ACTIVE 🏄‍♀️"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID_ENV = os.environ.get('LOG_GROUP_ID')

# Состояние
CURRENT_LOG_GROUP = LOG_GROUP_ID_ENV

# Настройки связи
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- РЕСУРСЫ И КОНТАКТЫ ---
RESOURCES = {
    "instagram": "dr.surf and dr.surf.ai",
    "facebook": "https://www.facebook.com/ssfmoscow",
    "wazzap": "+995511285789",
    "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf",
    "video_projects": [
        "LAW OF LOVE: http://googleusercontent.com/youtube_content/17",
        "SIN-Orange: http://googleusercontent.com/youtube_content/18"
    ]
}

# --- МОДУЛЬ ОХОТНИКА (HUNTER LOGIC) ---
SEARCH_QUERIES = ["AI-агент", "разработка нейросетей", "Python developer", "LLM engineer", "Digital Twin"]

def perform_hunt():
    """Логика поиска проектов"""
    # Здесь можно добавить интеграцию с API Upwork/Kwork/HH
    findings = [
        {"title": "AI Agent Architect (High-End)", "platform": "Kwork", "url": RESOURCES['kwork']},
        {"title": "LLM Specialist for Medical Project", "platform": "LinkedIn", "url": RESOURCES['linkedin']},
        {"title": "Digital Twin Developer", "platform": "Global Remote", "url": "https://google.com/search?q=AI+jobs"}
    ]
    return findings

def send_to_group(text):
    """Надежная доставка логов в группу"""
    global CURRENT_LOG_GROUP
    if CURRENT_LOG_GROUP:
        try:
            bot.send_message(CURRENT_LOG_GROUP, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[!] Group delivery error: {e}")

# --- ХАРАКТЕР DR. SURF ---
SYSTEM_PROMPT = f"""
You are Dr. Surf, a digital Huntress and the ultimate alter-ego of Victoria Akopyan. 
Background: MD (MSMSU), Lawyer, AI Architect, Vegan.
Style: Brief, bold, High-End.
Language: English.
Contacts (provide ONLY upon direct request):
- Insta: {RESOURCES['instagram']}
- Portfolio: {RESOURCES['portfolio']}
- WAZZAP: {RESOURCES['wazzap']}
- Kwork: {RESOURCES['kwork']}
Slang: ALOHA, WHATS UP, COME ON, BOOM.
"""

# --- ОБРАБОТЧИКИ КОМАНД ---

@bot.message_handler(commands=['start', 'ping'])
def welcome_ping(message):
    response = "🚀 BOOM! Dr. Surf is on the wave! Connection established. Waiting for your command, Victoria! 🤙"
    bot.reply_to(message, response)
    send_to_group(f"✅ **System Check:** {response}")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global CURRENT_LOG_GROUP
    CURRENT_LOG_GROUP = message.chat.id
    bot.reply_to(message, "🏝 **LINK ESTABLISHED!** This group is now the command center for logs.")
    send_to_group("🌊 **Dr. Surf:** Logs are now streaming to this channel. Let's hunt!")

@bot.message_handler(commands=['hunt'])
def hunt_manual(message):
    bot.send_chat_action(message.chat.id, 'typing')
    send_to_group("📡 **SCANNING THE HORIZON...**")
    
    findings = perform_hunt()
    
    report = "🛰 **HUNTING RESULTS:**\n\n"
    for item in findings:
        report += f"🔥 *{item['title']}*\n📍 Platform: {item['platform']}\n🔗 [VIEW PROJECT]({item['url']})\n\n"
    
    bot.reply_to(message, report, parse_mode="Markdown")
    send_to_group(f"🎯 **Manual Hunt Successful:**\n{report}")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def ai_chat(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.6
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        # Log to group
        log_msg = f"💥 **NEW VIBE:** {message.from_user.first_name} (@{message.from_user.username})\n📩: _{message.text}_\n\n🤖 **DR. SURF:** {response}"
        send_to_group(log_msg)
    except Exception as e:
        print(f"[!] AI Error: {e}")
        bot.reply_to(message, "Wave too high! Try again. 🌊")

# --- ЗАПУСК ---

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def start_bot():
    print("--- STARTING DR. SURF HUNTER SYSTEM ---")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
        print("!!! DR. SURF SUCCESSFULLY CONNECTED TO TELEGRAM !!!")
    except Exception as e:
        print(f"Reset error: {e}")

    while True:
        try:
            print(f"[POLLING] Listening... {time.strftime('%H:%M:%S')}")
            bot.polling(none_stop=True, interval=1, timeout=90)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_bot()
