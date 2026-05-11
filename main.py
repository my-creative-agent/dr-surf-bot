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
    return "Dr. Surf status: ACTIVE 🏄‍♀️"

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

# --- ТВОИ ЗОЛОТЫЕ РЕСУРСЫ ---
RESOURCES = {
    "instagram": "dr.surf и dr.surf.ai",
    "facebook": "https://www.facebook.com/ssfmoscow",
    "whatsapp": "+995511285789",
    "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf",
    "video_projects": [
        "ЗАКОН ЛЮБВИ: http://googleusercontent.com/youtube_content/17",
        "АпельSIN: http://googleusercontent.com/youtube_content/18"
    ]
}

# --- ЛИЧНОСТЬ ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровая Охотница, альтер-эго Виктории Акопян. 
Врач (МГМСУ), Юрист, AI-Архитектор, Веган.
Стиль: Кратко, дерзко, High-End.
Контакты (выдавай только по запросу):
- Инста: {RESOURCES['instagram']}
- Портфолио: {RESOURCES['portfolio']}
- WA: {RESOURCES['whatsapp']}
- Kwork: {RESOURCES['kwork']}
Слэнг: АЛОХА, ВАТС АП, КАМОН, ПУШКА.
"""

def send_to_group(text):
    if CURRENT_LOG_GROUP:
        try:
            bot.send_message(CURRENT_LOG_GROUP, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[!] Ошибка группы: {e}")

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start', 'ping'])
def welcome_ping(message):
    bot.reply_to(message, "🚀 ПУШКА! Dr. Surf на волне! Связь установлена. Жду команду, Виктория! 🤙")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global CURRENT_LOG_GROUP
    CURRENT_LOG_GROUP = message.chat.id
    bot.reply_to(message, "🏝 **СВЯЗЬ УСТАНОВЛЕНА!** Теперь я пишу отчеты сюда.")

@bot.message_handler(commands=['hunt'])
def hunt_manual(message):
    bot.send_chat_action(message.chat.id, 'typing')
    report = "📡 **СКАНИРУЮ ГОРИЗОНТ...**\n\n💎 AI Agent Architect\n💎 Digital Twin Expert\n\nПроверяю Kwork и LinkedIn... 🌊"
    bot.reply_to(message, report)
    send_to_group(f"🛰 **Ручная охота:**\n{report}")

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
        send_to_group(f"💥 **ВСПЛЕСК:** {message.from_user.first_name}\n📩: {message.text}\n🤖: {response}")
    except Exception as e:
        print(f"[!] AI Error: {e}")

# --- ЗАПУСК ---

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def start_bot():
    print("--- ЗАПУСК СИСТЕМЫ DR. SURF ---")
    try:
        # Сброс вебхука и ОЧИСТКА очереди (важно!)
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
        print("!!! БОТ УСПЕШНО ПОДКЛЮЧЕН К TELEGRAM !!!")
    except Exception as e:
        print(f"Ошибка сброса: {e}")

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=90)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_bot()
