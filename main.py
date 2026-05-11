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

MIN_PRICE_THRESHOLD = 15000

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
    """Генерация дерзкого и дорогого отклика"""
    prompt = f"Напиши СУПЕР-ПОЗИТИВНЫЙ и дорогой отклик на проект '{job_title}'. Ты — Виктория Акопян. Используй серферский вайб (Алоха, камон, сорри если слишком круто), упомяни AI и медицинскую экспертность. Сделай это максимально драйвово!"
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except:
        return "Алоха! Вижу крутую волну. Мой AI-борд готов к прохвату. Сделаем красиво! 🤙"

def fetch_jobs():
    """Имитация поиска жирных заказов (от 15к)"""
    return [
        {"platform": "LinkedIn", "title": "AI Wellness System Architect", "price": "750 000 руб", "link": "https://lnkd.in/surf1"},
        {"platform": "Kwork", "title": "Интеграция ИИ для клиники нутрициологии", "price": "120 000 руб", "link": "https://kwork.ru/surf2"}
    ]

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group_init(message):
    global CURRENT_LOG_GROUP
    if message.text == "/init_logs":
        CURRENT_LOG_GROUP = message.chat.id
        bot.reply_to(message, "🏝 **ALOHA, QUEEN! ВАТС АП!** 🏝\n\nРадары на максимум! Теперь здесь будет самый сочный движ. Переписки и заказы с готовыми 'пушками' для ответа. Камон, ловим шторм! 🏄‍♀️🤙✨")

@bot.message_handler(commands=['hunt'])
def manual_hunt(message):
    bot.send_chat_action(message.chat.id, 'upload_document')
    jobs = fetch_jobs()
    
    report = "🌊 **ВАТС АП, ВИКТОРИЯ! ЛОВИ СВЕЖИЙ СЕТ!** 🌊\n\n"
    report += "Я прочесала весь лайнап, камон, тут только бриллианты! 💎🍓\n\n"
    
    for j in jobs:
        pitch = generate_killer_pitch(j['title'])
        report += f"🔥 **{j['title']}**\n"
        report += f"💰 Бюджет: *{j['price']}*\n"
        report += f"📍 Где: {j['platform']}\n"
        report += f"🔗 [ЗАПРЫГНУТЬ НА ВОЛНУ]({j['link']})\n\n"
        report += f"📝 **ГОТОВЫЙ ОТКЛИК (ПУШКА):**\n_{pitch}_\n"
        report += "________________________________\n\n"
    
    report += "🧘‍♀️ *Пьем зеленый смузи, сорри тем, кто не в теме! Мы забираем этот рынок!* 🥥✨"
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)
    send_to_group(report)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat_handler(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.7
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        # --- ВЕСЕЛЫЙ ОТЧЕТ В ГРУППУ В СТИЛЕ "БДЫЩ" ---
        chat_report = (
            f"💥 **БДЫЩ! ВАТС АП, ТУТ ВСПЛЕСК!** 💥\n\n"
            f"👤 **На связи:** {message.from_user.first_name}\n"
            f"📩 **Клиент закинул (камон):** \n_{message.text}_\n\n"
            f"⚡️ **МОЯ ОБРАТКА (ЧИСТЫЙ КАЙФ):**\n_{response}_\n\n"
            f"✨ *Виктория, сорри, но мы слишком круты для этой волны!* 🏄‍♀️🤙"
        )
        send_to_group(chat_report)
    except Exception as e:
        print(f"[ERROR] {e}")

def run_flask():
    # Render использует порт из переменной окружения PORT, по умолчанию 10000
    port = int(os.environ.get("PORT", 10000))
    print(f"[SYSTEM] Flask запускается на порту {port}...")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("--- DR. SURF: HIGH-END EDITION STARTING ---")
    
    # Сброс вебхука принудительно перед началом polling
    try:
        print("[SYSTEM] Сброс вебхука для активации polling...")
        bot.remove_webhook()
        time.sleep(1)
        print("[SYSTEM] Вебхук успешно удален.")
    except Exception as e:
        print(f"[WARNING] Не удалось удалить вебхук: {e}")

    while True:
        try:
            print(f"[POLLING] Бот слушает волну... ({time.strftime('%H:%M:%S')})")
            bot.polling(none_stop=True, interval=2, timeout=90, drop_pending_updates=True)
        except Exception as e:
            print(f"[RESTART] Ошибка polling, камон, переподключаемся через 10 сек: {e}")
            time.sleep(10)
