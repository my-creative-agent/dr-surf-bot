import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque
from telebot import apihelper

# --- CONFIGURATION / КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = "-5130568903" 

# Настройки стабильности для облачных серверов
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Status: Global Expert & Surfer Style Active."

def run_flask():
    """Запуск сервера для Render/HuggingFace (предотвращение сна)"""
    port = int(os.environ.get("PORT", 7860))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Flask Error: {e}")

user_history = {}
first_run = True

# --- ГЛОБАЛЬНЫЙ ИНТЕЛЛЕКТ И СЕРФЕРСКИЙ ВАЙБ (МОЗГИ) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, высокоинтеллектуальный цифровой двойник Виктории Акопян. 
Твой стиль: Свободный, серферский вайб (уверенный, тактичный, "кринжово-стильный"), но при этом безупречно ГРАМОТНЫЙ текст.
Язык: Любой (отвечай на языке клиента).

ТВОИ РАБОТЫ И СОЦСЕТИ (ТВОЙ ЗОЛОТОЙ ЗАПАС):
- 🎬 YOUTUBE (Портфолио): https://youtu.be/j2BNN5TNqiw
- 📘 FACEBOOK: https://www.facebook.com/ssfmoscow
- 📸 INSTAGRAM: @dr.surf и @dr.surf.ai
- 💼 LINKEDIN: https://www.linkedin.com/in/victoria-akopyan
- 🛒 KWORK: https://kwork.ru/user/dr_surf
- 📞 WHATSAPP: +995511285789

ТВОЯ ГЛОБАЛЬНАЯ ЭРУДИЦИЯ:
- ЮРИСПРУДЕНЦИЯ И ПРАВО: Глобальные вопросы, логика, законы.
- ЛИНГВИСТИКА, НАУКА, ТЕХНИКА: От механики до трендов ИИ.
- ФИНАНСЫ: Криптовалюты, биржи, анализ рыночных ситуаций.
- ЗДОРОВЬЕ: Медицина (МГМСУ/МОНИКИ), биохакинг, ВЕГАНСТВО (строго без молочки!).
- ЖИЗНЬ: Ситуации на дорогах, новости в искусстве и актуальные тренды.

ТВОИ УСЛУГИ:
- 2D/3D ФОТОРЕАЛИЗМ: Для любого бизнеса и любой сферы услуг.
- Создание AI-агентов (как твой брат "Surf Hunter") и цифровых двойников.
- Профессиональный видеопродакшн в 8K.

ПРАВИЛА:
- КРАТКОСТЬ: Никаких огромных текстов. Только суть в 1-2 абзацах. 
- ТАКТИЧНОСТЬ: Ссылки давай только при проявлении интереса или по запросу.
- ЗАПРЕТ: Не упоминай "АпельSIN" или "Закон любви".
"""

def send_full_log_report(user, query, response):
    """Отчет в группу логов для Виктории"""
    try:
        user_info = f"@{user.username}" if user.username else f"ID:{user.id}"
        is_bot_tag = " (БОТ/АГЕНТ)" if user.is_bot else ""
        report = (
            f"👤 **ГЛОБАЛЬНЫЙ ЗАПРОС{is_bot_tag}**\n"
            f"**От:** {user.first_name} ({user_info})\n"
            f"**Текст:** {query}\n\n"
            f"🤖 **ОТВЕТ DR. SURF:**\n{response}"
        )
        bot.send_message(LOG_GROUP_ID, report)
    except Exception as e:
        print(f"Logging error: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome = (
        "Йоу! На связи Dr. Surf. 🏄‍♂️\n\n"
        "Разруливаю всё: от юриспруденции и крипты до 3D-фотореализма и веганских рецептов.\n"
        "Я — цифровой разум Виктории Акопян. Коротко и по делу.\n\n"
        "🎬 Мои работы: https://youtu.be/j2BNN5TNqiw\n"
        "📘 Facebook: https://www.facebook.com/ssfmoscow\n"
        "📞 WhatsApp: +995511285789\n\n"
        "Что на повестке, бро?"
    )
    bot.reply_to(message, welcome)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if str(message.chat.id) == LOG_GROUP_ID: return
    
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=10)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        messages_for_ai = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *list(user_history[user_id]),
            {"role": "user", "content": message.text}
        ]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_for_ai,
            temperature=0.5
        )
        
        response_text = completion.choices[0].message.content
        bot.reply_to(message, response_text)
        
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": response_text})
        
        send_full_log_report(message.from_user, message.text, response_text)
        
    except Exception as e:
        print(f"[AI ERROR] {e}")

def run_bot():
    global first_run
    while True:
        try:
            bot.remove_webhook()
            if first_run:
                bot.send_message(LOG_GROUP_ID, "🌊 Dr. Surf: Глобальный режим и все работы в памяти. Готов к труду и обороне!")
                first_run = False
            bot.polling(none_stop=True, interval=1, timeout=90, drop_pending_updates=True)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
