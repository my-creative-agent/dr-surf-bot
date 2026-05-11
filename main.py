import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- ИНИЦИАЛИЗАЦИЯ FLASK ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf System is Active and Healthy! 🏄‍♂️🌱"

# Ключи из Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
# Фиксированный ID твоей группы логов
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', "-5130568903")

# Таймауты для стабильного деплоя
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- СТРОГОЕ ДНК (SYSTEM PROMPT) ---
SYSTEM_PROMPT = """
Ты — Dr. Surf, цифровой двойник Виктории Акопян. 
Стиль: Лаконичный, умный, свободный серферский вайб. ГРАМОТНОСТЬ 100%.

ТВОИ КОМПЕТЕНЦИИ:
- Юриспруденция, лингвистика, ИИ-агенты, видео 8K.
- Медицина: База МГМСУ и МОНИКИ.
- Образ жизни: ВЕГАНСТВО (строго без молочки!).

ЖЕСТКИЕ ПРАВИЛА (НЕ РАЗБАЗАРИВАТЬ ИНФУ):
1. ЛАКОНИЧНОСТЬ: Отвечай максимально коротко (1-2 предложения).
2. ПОЛНАЯ ТИШИНА: Никогда не давай ссылки, соцсети или контакты САМ. 
3. ВЫДАЧА КОНТАКТОВ: Присылай данные ниже ТОЛЬКО если пользователь прямо и четко попросил: "дай инсту", "как с тобой связаться" или "покажи портфолио".
   - Портфолио: https://youtu.be/j2BNN5TNqiw
   - Insta: @dr.surf / @dr.surf.ai
   - WhatsApp: +995511285789
4. СТРОЖАЙШЕЕ ТАБУ: Проекты "АпельSIN" и "Закон любви" — СЕКРЕТ. Ты о них НЕ ЗНАЕШЬ. Если спросят — отвечай, что не понимаешь, о чем речь.
5. НИКАКОЙ ЛИШНЕЙ ИНФЫ: Не рассказывай о себе больше, чем спросили.
"""

def send_to_group(text):
    """Отправка отчетов в группу логов"""
    try:
        bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"[ERROR] Группа: {e}")

def hunt_logic():
    """Логика имитации поиска вакансий"""
    time.sleep(2)
    found_msg = (
        "🎯 **ХАНТЕР: СИСТЕМА ПОИСКА АКТИВИРОВАНА**\n"
        "Статус: Бот авторизован в группе и готов к мониторингу.\n"
        "Область поиска: AI Агенты, Видео 8K, Медицинские ИИ-системы."
    )
    send_to_group(found_msg)

@bot.message_handler(commands=['hunt'])
def start_hunt(message):
    """Ручной запуск поиска"""
    bot.reply_to(message, "🎯 Принято, Виктория. Проверяю вакансии... Отчет придет в группу.")
    threading.Thread(target=hunt_logic).start()

@bot.message_handler(func=lambda m: True)
def handle_conversation(message):
    # Не отвечаем в чате логов
    if str(message.chat.id) == str(LOG_GROUP_ID):
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            temperature=0.3
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)

        # Отчет в группу
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        report = (
            f"🏝 **DR. SURF: НОВЫЙ ДИАЛОГ**\n"
            f"👤 **От:** {user_info}\n"
            f"💬 **Вопрос:** {message.text}\n"
            f"🤖 **Ответ:** {ans}"
        )
        send_to_group(report)
        
    except Exception as e:
        print(f"[ERROR] AI: {e}")

def run_flask():
    """Keep-alive для Render"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Сначала запускаем сервер для Health Check
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("--- СИСТЕМА DR. SURF ЗАПУСКАЕТСЯ ---")
    
    # Сброс старых подключений перед стартом
    try:
        bot.remove_webhook()
        time.sleep(1)
    except:
        pass

    # Бесконечный цикл с защитой от вылетов
    while True:
        try:
            bot.polling(none_stop=True, timeout=90, long_polling_timeout=5)
        except Exception as e:
            print(f"[RESTART] Ошибка polling, перезапуск через 5с: {e}")
            time.sleep(5)
