import telebot
import os
import time
import threading
import feedparser
from groq import Groq
from flask import Flask

# --- СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter: Active"

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# --- ЖЕСТКАЯ ПРИВЯЗКА ГРУППЫ (С ДЕФИСОМ) ---
# Мы используем твой ID напрямую. Дефис в начале обязателен для групп.
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- КОНТАКТЫ (ЧЕЛОВЕЧЕСКИЙ ВИД) ---
MY_CONTACTS = """
👤 **Виктория Акопян**
🔹 AI Архитектор | Видео-креатор
🔹 Образование: МГМСУ, МОНИКИ (Врач), Юрист

📞 **Связь:**
• WhatsApp: [+995 511 285 789](https://wa.me/995511285789)
• Instagram: [dr.surf.ai](https://instagram.com/dr.surf.ai)
• Portfolio: [YouTube](https://youtu.be/j2BNN5TNqiw)
• Kwork: [Профиль](https://kwork.ru/user/dr_surf)
"""

# --- МОДУЛЬ ОХОТЫ ---
RSS_FEEDS = ["https://www.fl.ru/rss/all.xml", "https://freelance.habr.com/tasks.rss"]
SENT_PROJECTS = set() 

def fetch_orders():
    found = []
    keywords = ["AI", "Агент", "Python", "Нейросеть", "LLM", "Бот", "ИИ", "GPT", "Чат-бот", "Automation"]
    print(f"[DEBUG] Охота началась...")
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.title.lower()
                if any(word.lower() in title for word in keywords):
                    if entry.link not in SENT_PROJECTS:
                        found.append({"title": entry.title, "url": entry.link})
                        SENT_PROJECTS.add(entry.link)
        except Exception as e:
            print(f"[ERROR] RSS ({url}): {e}")
    return found

def send_to_group(text):
    global LOG_GROUP_ID
    if LOG_GROUP_ID:
        try:
            bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
            return True
        except Exception as e:
            print(f"[ERROR] Не удалось отправить в группу {LOG_GROUP_ID}: {e}")
    return False

# --- АВТОМАТИЧЕСКАЯ ПРОВЕРКА ---
def auto_hunter():
    print(f"[SYSTEM] Модуль охоты запущен. Цель: {LOG_GROUP_ID}")
    time.sleep(10) # Даем боту загрузиться
    
    while True:
        try:
            projects = fetch_orders()
            if projects:
                report = "🚀 **Dr. Surf: Новые волны на горизонте!**\n\n"
                for p in projects:
                    report += f"🔹 {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
                send_to_group(report)
            else:
                print("[DEBUG] Пока новых заказов не обнаружено.")
        except Exception as e:
            print(f"[ERROR] Ошибка в цикле охотника: {e}")
        time.sleep(1800) # Проверка каждые 30 минут

# --- ОБРАБОТКА КОМАНД ---
@bot.message_handler(commands=['start', 'ping'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf в сети. Мониторинг заказов активен.")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.reply_to(message, "🔍 Сканирую биржи вручную...")
    projects = fetch_orders()
    if projects:
        report = "🛰 **Результат сканирования:**\n\n"
        for p in projects:
            report += f"🔹 {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🌊 Чисто. Новых заказов по AI пока нет.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты — Dr. Surf, AI-аватар Виктории Акопян. Веган, медик, эксперт. Отвечай кратко."},
                {"role": "user", "content": message.text}
            ]
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        send_to_group(f"📩 **Личное от пользователя:** {message.text}\n\n🤖 **Твой ответ:** {ans}")
    except Exception as e:
        print(f"[ERROR] AI Chat: {e}")

if __name__ == "__main__":
    # Запуск Flask
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # Запуск Охотника
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # Очистка и запуск
    print("[SYSTEM] Перезагрузка Telegram API...")
    bot.remove_webhook()
    time.sleep(2)
    print(f"[SUCCESS] Бот Dr. Surf запущен. Логи: {LOG_GROUP_ID}")
    bot.polling(none_stop=True, skip_pending=True)
