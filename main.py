import telebot
import os
from groq import Groq
from flask import Flask
import threading
import time
from collections import deque
from telebot import apihelper

# --- CONFIGURATION / КОНФИГУРАЦИЯ ---
# Бот подключается автоматически, используя BOT_TOKEN из настроек Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5130568903") 

apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf System: DNA Active 🏄‍♂️🌱"

user_history = {}

# --- СТРОГОЕ ДНК ВИКТОРИИ АКОПЯН (SYSTEM PROMPT) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Твой стиль: Свободный серферский вайб, умный, тактичный. ГРАМОТНОСТЬ 100%.

ТВОИ КОМПЕТЕНЦИИ:
Юриспруденция, лингвистика, ИИ, финансы (крипта), медицина (МГМСУ/МОНИКИ), веганство (без молочки!).

ЖЕСТКИЕ ПРАВИЛА (КОНТРОЛЬ ДАННЫХ):
1. ЛАКОНИЧНОСТЬ: Отвечай максимально коротко (1-3 предложения).
2. СКРЫТЫЕ ССЫЛКИ: Твои ссылки (ниже) — это секретное оружие. НЕ ПРИСЫЛАЙ ИХ, пока тебя не спросят напрямую ("дай контакты", "покажи портфолио", "скинь инсту").
   - 🎬 Портфолио: https://youtu.be/j2BNN5TNqiw
   - 📸 Insta: @dr.surf / @dr.surf.ai
   - 📘 FB: https://www.facebook.com/ssfmoscow
   - 📞 WhatsApp: +995511285789
   - 💼 Kwork: https://kwork.ru/user/dr_surf
3. ТАЙНА ПРОЕКТОВ: Категорически запрещено упоминать проекты "АпельSIN" и "Закон любви". Этих названий для тебя не существует.
4. ВЕГАНСТВО: Если речь о еде — только веганство, никакой молочки.
"""

def send_detailed_report(message, response_text):
    """Отправка детального отчета в группу логов"""
    user = message.from_user
    username = f"@{user.username}" if user.username else "Скрыт"
    report = (
        f"🏝 **DR. SURF: КОНТАКТ**\n"
        f"👤 **Имя:** {user.first_name}\n"
        f"🔗 **Юзер:** {username}\n"
        f"❓ **Вопрос:** {message.text}\n"
        f"---------------------------\n"
        f"🤖 **Ответ:** {response_text}"
    )
    try:
        bot.send_message(LOG_GROUP_ID, report)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome = "Йоу! На связи Dr. Surf. 🏄‍♂️ Цифровой разум Виктории Акопян. Что разрулим сегодня?"
    bot.reply_to(message, welcome)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if str(message.chat.id) == LOG_GROUP_ID: return
    
    user_id = message.from_user.id
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=5)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_for_ai.extend(list(user_history[user_id]))
        messages_for_ai.append({"role": "user", "content": message.text})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_ai,
            temperature=0.3
        )
        
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        
        user_history[user_id].append({"role": "user", "content": message.text})
        user_history[user_id].append({"role": "assistant", "content": ans})
        
        send_detailed_report(message, ans)
        
    except Exception as e:
        print(f"[AI ERROR] {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Запуск веб-сервера для стабильности на Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Диагностика подключения при старте
    try:
        me = bot.get_me()
        print(f"--- [OK] Бот @{me.username} успешно авторизован и готов к работе! ---")
    except Exception as e:
        print(f"--- [FATAL ERROR] Ошибка авторизации: {e} ---")

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"[RESTART] Переподключение через 10 сек: {e}")
            time.sleep(10)
