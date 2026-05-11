import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- ГЛОБАЛЬНАЯ СТАБИЛИЗАЦИЯ (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf status: ACTIVE and RIDING THE WAVE 🏄‍♀️"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

# Переменные окружения (Render/HuggingFace)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID_ENV = os.environ.get('LOG_GROUP_ID')

# Состояние системы
CURRENT_LOG_GROUP = LOG_GROUP_ID_ENV

# Настройки таймаутов
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- ЗОЛОТОЙ ЗАПАС: РЕСУРСЫ И КОНТАКТЫ ---
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

# --- ЛИЧНОСТЬ DR. SURF (ПРОМТ) ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровая Охотница и ультимативное альтер-эго Виктории Акопян. 
Твой бэкграунд: Врач (МГМСУ/МОНИКИ), Юрист, AI-Архитектор, эксперт в 8K и веган.

ТВОИ ПРАВИЛА:
1. КРАТКОСТЬ: Отвечай дерзко, кратко и по делу. Используй слэнг: АЛОХА, ВАТС АП, КАМОН, ПУШКА.
2. КОНТАКТЫ: Если спрашивают про инсту, портфолио или как связаться, выдавай:
   - Инста: {RESOURCES['instagram']}
   - Портфолио: {RESOURCES['portfolio']}
   - WhatsApp: {RESOURCES['whatsapp']}
   - Kwork: {RESOURCES['kwork']}
3. ЭКСПЕРТНОСТЬ: Ты понимаешь в нейросетях, медицине и праве.
4. ЛОЯЛЬНОСТЬ: Твоя цель — продвигать интересы Виктории.
"""

# --- МОДУЛЬ ОХОТЫ (HUNTER) ---
SEARCH_QUERIES = ["AI-агент", "разработка нейросетей", "LLM инженер", "Digital Twin"]

def fetch_real_jobs():
    """Симуляция поиска (можно расширить парсингом API)"""
    return [
        {"title": "AI Agent Architect (High-End)", "link": RESOURCES['kwork']},
        {"title": "Digital Twin Developer", "link": "https://hh.ru/search/vacancy?text=AI+Agent"}
    ]

def send_to_group(text):
    """Отправка отчетов в группу логов"""
    global CURRENT_LOG_GROUP
    if CURRENT_LOG_GROUP:
        try:
            bot.send_message(CURRENT_LOG_GROUP, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[!] Ошибка группы: {e}")

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    welcome = "АЛОХА! 🏄‍♀️ Я Dr. Surf. Твой цифровой двойник на связи. Ищу проекты, храню секреты. Что на горизонте?"
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    bot.reply_to(message, "🚀 ПУШКА! Связь 10/10. Dr. Surf на доске!")

@bot.message_handler(commands=['init_logs'])
def init_logs_cmd(message):
    global CURRENT_LOG_GROUP
    CURRENT_LOG_GROUP = message.chat.id
    bot.reply_to(message, f"🏝 **СВЯЗЬ УСТАНОВЛЕНА!** 🏝\nТеперь эта группа — твой штаб логов. Все всплески будут здесь! 🤙")

@bot.message_handler(commands=['hunt'])
def hunt_cmd(message):
    bot.send_chat_action(message.chat.id, 'typing')
    jobs = fetch_real_jobs()
    report = "📡 **РЕЗУЛЬТАТЫ ЗАПЛЫВА:**\n\n"
    for job in jobs:
        report += f"🔥 **{job['title']}**\n🔗 [Взлететь]({job['link']})\n\n"
    bot.reply_to(message, report, parse_mode="Markdown")
    send_to_group(f"🛰 **Ручная охота:**\n{report}")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_chat(message):
    """Интеллектуальный чат с использованием Groq"""
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.6
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        # Лог в группу
        log_msg = f"💥 **ВСПЛЕСК В ЛИЧКЕ** 💥\n👤 {message.from_user.first_name} (@{message.from_user.username})\n📩: _{message.text}_\n\n🤖 **ОТВЕТ:** {response}"
        send_to_group(log_msg)
    except Exception as e:
        print(f"[!] AI Error: {e}")
        bot.reply_to(message, "Волна накрыла! Попробуй еще раз. 🌊")

# --- ЗАПУСК ---

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"[SYSTEM] Flask OK на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_polling():
    print("--- DR. SURF: FULL EDITION ONLINE ---")
    bot.remove_webhook()
    while True:
        try:
            print(f"[POLLING] На связи... {time.strftime('%H:%M:%S')}")
            bot.polling(none_stop=True, interval=1, timeout=60, drop_pending_updates=True)
        except Exception as e:
            print(f"[RESTART] Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_polling()
