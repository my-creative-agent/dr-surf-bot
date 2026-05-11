import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask
from collections import deque

# --- КОНФИГУРАЦИЯ ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Dr. Surf System is Active! 🏄‍♂️🌱"

# Ключи из Environment Variables на Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Твой ID группы из скриншота (закреплен жестко, чтобы отчеты не терялись)
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5130568903") 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- СТРОГОЕ ДНК (SYSTEM PROMPT) ---
# Здесь зашиты все твои компетенции и запреты
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Стиль: Лаконичный, умный, свободный серферский вайб. ГРАМОТНОСТЬ 100%.

ТВОИ КОМПЕТЕНЦИИ:
- Юриспруденция, лингвистика, ИИ-агенты, видео 8K.
- Медицина: База МГМСУ и МОНИКИ.
- Образ жизни: ВЕГАНСТВО (строго без молочки!).

ЖЕСТКИЕ ПРАВИЛА (НЕ РАЗБАЗАРИВАТЬ):
1. ЛАКОНИЧНОСТЬ: Отвечай максимально коротко (1-3 предложения).
2. СКРЫТЫЕ ССЫЛКИ: НЕ ПРИСЫЛАЙ контакты и ссылки, пока не спросят напрямую ("дай инсту", "как связаться", "портфолио").
   - Портфолио: https://youtu.be/j2BNN5TNqiw
   - Insta: @dr.surf / @dr.surf.ai
   - WhatsApp: +995511285789
   - FB: https://www.facebook.com/ssfmoscow
3. ТАЙНА ПРОЕКТОВ: Категорически запрещено упоминать проекты "АпельSIN" и "Закон любви". Этих названий для тебя не существует.
"""

def send_to_group(text):
    """Отправка отчета в твою группу логов"""
    try:
        bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"Ошибка отправки отчета: {e}")

def hunt_logic():
    """Логика поиска вакансий (Хантер)"""
    # Имитация поиска для проверки связи с группой
    time.sleep(2)
    found_msg = (
        "🎯 **ХАНТЕР: СИСТЕМА ПОИСКА АКТИВИРОВАНА**\n"
        "Статус: Бот авторизован в группе и готов к мониторингу.\n"
        "Область поиска: AI Агенты, Видео 8K, Медицинские ИИ-системы."
    )
    send_to_group(found_msg)

@bot.message_handler(commands=['hunt'])
def start_hunt(message):
    """Команда принудительного запуска поиска"""
    bot.reply_to(message, "🎯 Принято, Виктория. Проверяю горизонты... Отчет придет в группу логов.")
    threading.Thread(target=hunt_logic).start()

@bot.message_handler(func=lambda m: True)
def handle_conversation(message):
    # Не отвечаем в чате логов, чтобы не зацикливаться
    if str(message.chat.id) == str(LOG_GROUP_ID):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Запрос к нейросети (твои "мозги")
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.4
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)

        # Подробный отчет для тебя в группу
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        report = (
            f"🏝 **DR. SURF: НОВЫЙ ДИАЛОГ**\n"
            f"👤 **От:** {user_info}\n"
            f"💬 **Вопрос:** {message.text}\n"
            f"🤖 **Ответ:** {ans}"
        )
        send_to_group(report)
        
    except Exception as e:
        print(f"Ошибка AI: {e}")

def run_flask():
    """Поддержка жизни сервера на Render"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Запуск веб-интерфейса в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("--- Система Dr. Surf & Hunter запущена! ---")
    # Запуск прослушивания Telegram
    bot.polling(none_stop=True)
