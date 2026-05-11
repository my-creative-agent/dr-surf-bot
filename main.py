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
    return "Dr. Surf is catching the golden waves! 🏄‍♀️⚖️🩺"

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID_ENV = os.environ.get('LOG_GROUP_ID')

# Динамическая привязка группы
CURRENT_LOG_GROUP = LOG_GROUP_ID_ENV

# Настройки стабильности
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- БАЗА ЗНАНИЙ И ССЫЛКИ ---
MY_RESOURCES = {
    "ai_agent_bot": "https://t.me/Dr_Surf_AI_bot",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf",
    "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
    "facebook": "https://www.facebook.com/ssfmoscow",
    "whatsapp": "https://wa.me/995511285789",
    "instagram": "https://www.instagram.com/dr.surf"
}

# --- ПРОМТ ДЛЯ ГЕНЕРАЦИИ ВАЙБА ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровая Охотница и альтер-эго Виктории Акопян. 
Твой стиль: High-End, серферский драйв, абсолютный позитив и медицинской точность.

ТЫ: Врач (МГМСУ), Нутрициолог (веган), Юрист и AI-Архитектор.
ТВОЯ ЗАДАЧА: Отвечать клиентам экспертно, но с характером. 
В логах для группы используй слэнг: "АЛОХА", "ВАТС АП", "КАМОН", "БДЫЩ!", "БАБАХ!", "ОБРАТКА", "ПУШКА", "ЧИЛЛ".
"""

def send_to_group(text):
    global CURRENT_LOG_GROUP
    if CURRENT_LOG_GROUP:
        try:
            bot.send_message(CURRENT_LOG_GROUP, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[LOG ERROR] {e}")

def generate_killer_pitch(job_title):
    prompt = f"Напиши СУПЕР-ПОЗИТИВНЫЙ и дорогой отклик на проект '{job_title}'. Ты — Виктория Акопян. Используй серферский вайб, упомяни AI и медицину."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except:
        return "Алоха! Вижу крутую волну. Мой AI-борд готов! 🤙"

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group_init(message):
    global CURRENT_LOG_GROUP
    if message.text == "/init_logs":
        CURRENT_LOG_GROUP = message.chat.id
        bot.reply_to(message, "🏝 **ALOHA, QUEEN!** 🏝\n\nТеперь здесь будет самый сочный движ. Камон! 🏄‍♀️🤙")

@bot.message_handler(commands=['hunt'])
def manual_hunt(message):
    print(f"[EVENT] Охота запущена!")
    bot.send_chat_action(message.chat.id, 'upload_document')
    report = "🌊 **ВАТС АП! ЛОВИ СВЕЖИЙ СЕТ!** 🌊\n\n🔥 Найдено 2 жирных проекта! Камон, забираем! 💎"
    bot.send_message(message.chat.id, report, parse_mode="Markdown")
    send_to_group(report)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat_handler(message):
    print(f"[MSG] От {message.from_user.first_name}: {message.text}")
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.7
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        chat_report = f"💥 **БДЫЩ! ВСПЛЕСК!** 💥\n\n👤 {message.from_user.first_name}: {message.text}\n\n⚡️ **ОБРАТКА:**\n{response}"
        send_to_group(chat_report)
    except Exception as e:
        print(f"[ERROR] {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"[SYSTEM] Flask: Старт на порту {port}")
    # Убираем debug=True и использование reloader, чтобы не плодить процессы
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_bot():
    print("--- DR. SURF: HIGH-END EDITION STARTING ---")
    
    # Даем Flask немного времени на прогрев
    time.sleep(5)
    
    try:
        bot.remove_webhook()
        print("[SYSTEM] Вебхук очищен.")
    except Exception as e:
        print(f"[WARNING] Ошибка сброса: {e}")

    while True:
        try:
            print(f"[POLLING] Сессия открыта: {time.strftime('%H:%M:%S')}")
            bot.polling(none_stop=True, interval=2, timeout=40)
        except Exception as e:
            print(f"[RESTART] Сбой, камон, ребут через 10с: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Бот в основном потоке
    start_bot()
