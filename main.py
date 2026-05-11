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
    """Генерация крутого отклика на вакансию через AI"""
    prompt = f"Напиши СУПЕР-ПОЗИТИВНЫЙ и дорогой отклик на проект '{job_title}'. Ты — Виктория Акопян. Используй серферский вайб, упомяни AI и медицину."
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except:
        return "Алоха! Вижу крутую волну. Мой AI-борд готов к прохвату! 🤙"

# --- МОДУЛЬ ОХОТЫ (ПОИСК ВАКАНСИЙ) ---
def fetch_real_jobs():
    """Слот для интеграции парсеров. Сейчас возвращает тестовые цели."""
    # Сюда можно добавить вызовы к API фриланс-бирж или парсинг
    return [
        {"title": "AI Agent Developer (Llama Index/LangChain)", "link": "https://kwork.ru/projects/ai-agent"},
        {"title": "Создание цифрового двойника клиники", "link": "https://hh.ru/vacancy/digital-twin"}
    ]

def auto_hunt_loop():
    """Фоновая охота: проверяет новые волны каждые 4 часа"""
    while True:
        print("[HUNTER] Проверка горизонта...")
        jobs = fetch_real_jobs()
        if jobs and CURRENT_LOG_GROUP:
            report = "🛰 **АВТО-ОХОТА: НА ГОРИЗОНТЕ ЖИРНЫЕ ЦЕЛИ!** 🛰\n\n"
            for job in jobs:
                pitch = generate_killer_pitch(job['title'])
                report += f"💎 **{job['title']}**\n🔗 [Смотреть волну]({job['link']})\n📝 **Твой оффер:**\n_{pitch}_\n\n"
            send_to_group(report)
        # 14400 секунд = 4 часа
        time.sleep(14400) 

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group_init(message):
    global CURRENT_LOG_GROUP
    if message.text == "/init_logs":
        CURRENT_LOG_GROUP = message.chat.id
        print(f"[SYSTEM] Группа привязана: {CURRENT_LOG_GROUP}")
        bot.reply_to(message, "🏝 **ALOHA, QUEEN!** 🏝\n\nТеперь я транслирую отчеты и найденные вакансии сюда. Камон! 🏄‍♀️🤙")

@bot.message_handler(commands=['hunt'])
def manual_hunt(message):
    """Ручной запуск охоты по команде"""
    print(f"[EVENT] Ручная охота запущена!")
    bot.send_chat_action(message.chat.id, 'upload_document')
    
    jobs = fetch_real_jobs()
    if jobs:
        report = "🌊 **ВАТС АП! РЕЗУЛЬТАТЫ ЗАПЛЫВА:** 🌊\n\n"
        for job in jobs:
            report += f"🔥 **{job['title']}**\n🔗 [Взлететь на волну]({job['link']})\n\n"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
        send_to_group(report) # Копия в группу
    else:
        bot.reply_to(message, "Штиль на горизонте, Виктория. Ждем прилива! 💨")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat_handler(message):
    """Твой основной чат с AI-двойником"""
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
        
        # Отчет в группу о личном сообщении (как ты и просила)
        chat_report = f"💥 **БДЫЩ! ВСПЛЕСК В ЛИЧКЕ!** 💥\n\n👤 {message.from_user.first_name}:\n_{message.text}_\n\n⚡️ **ОТВЕТ DR. SURF:**\n{response}"
        send_to_group(chat_report)
    except Exception as e:
        print(f"[ERROR] {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"[SYSTEM] Flask: Старт на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_bot():
    print("--- DR. SURF: HIGH-END EDITION STARTING ---")
    time.sleep(5)
    
    try:
        bot.remove_webhook()
        print("[SYSTEM] Вебхук очищен.")
    except Exception as e:
        print(f"[WARNING] Ошибка сброса: {e}")

    while True:
        try:
            print(f"[POLLING] Сессия открыта: {time.strftime('%H:%M:%S')}")
            # drop_pending_updates=True чтобы не спамить старым при рестарте
            bot.polling(none_stop=True, interval=2, timeout=40, drop_pending_updates=True)
        except Exception as e:
            print(f"[RESTART] Сбой, камон, ребут через 10с: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # 1. Flask для Render (Анти-сон)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Фоновая авто-охота за вакансиями
    threading.Thread(target=auto_hunt_loop, daemon=True).start()
    
    # 3. Запуск бота (Основной процесс)
    start_bot()
