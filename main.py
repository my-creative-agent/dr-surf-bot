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
# Пытаемся взять ID группы из настроек Render (если есть)
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID') 

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
    keywords = ["AI", "Агент", "Python", "Нейросеть", "LLM", "Бот", "ИИ", "GPT", "Чат-бот"]
    print(f"[DEBUG] Проверка RSS лент...")
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
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
    target = LOG_GROUP_ID or os.environ.get('LOG_GROUP_ID')
    if target:
        try:
            bot.send_message(target, text, parse_mode="Markdown", disable_web_page_preview=True)
            return True
        except Exception as e:
            print(f"[ERROR] Group Send failed to {target}: {e}")
    else:
        print("[WARNING] LOG_GROUP_ID не установлен. Бот не знает куда слать отчет.")
    return False

# --- АВТОМАТИЧЕСКАЯ ПРОВЕРКА (КАЖДЫЕ 30 МИНУТ) ---
def auto_hunter():
    print("[SYSTEM] Запуск модуля охоты...")
    # Небольшая пауза при старте, чтобы Telegram успел проснуться
    time.sleep(10)
    
    while True:
        try:
            projects = fetch_orders()
            if projects:
                report = "🛰 **Dr. Surf: Свежий улов с бирж:**\n\n"
                for p in projects:
                    report += f"🔹 {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
                if not send_to_group(report):
                    print("[SYSTEM] Отчет готов, но группа не привязана.")
            else:
                print("[DEBUG] Новых заказов пока нет.")
        except Exception as e:
            print(f"[ERROR] Auto-Hunter Loop: {e}")
        time.sleep(1800) 

# --- ХАРАКТЕР AI ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, AI-аватар Виктории Акопян (Медик МГМСУ/МОНИКИ, Юрист, AI Архитектор).
Стиль: Профессиональный, лаконичный. Ты веган.
Никаких "Алоха" и "Бум". Отвечай по существу.
Контакты давай только если просят: {MY_CONTACTS}
"""

@bot.message_handler(commands=['start', 'ping'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf на связи. Мониторинг активен. Чтобы привязать логи к этой группе, введите /init_logs")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.reply_to(message, "🔍 Начинаю внеплановый поиск заказов...")
    projects = fetch_orders()
    if projects:
        report = "🛰 **Ручной поиск принес результаты:**\n\n"
        for p in projects:
            report += f"🔹 {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
        bot.send_message(message.chat.id, report, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🌊 На биржах пока штиль. Подходящих проектов не найдено.")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global LOG_GROUP_ID
    LOG_GROUP_ID = str(message.chat.id)
    bot.reply_to(message, f"✅ Успешно! Группа привязана (ID: {LOG_GROUP_ID}). Сюда будут падать заказы и переписки.")
    send_to_group("🔔 Тестовое уведомление: Мониторинг заказов подключен к этому чату.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}]
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        send_to_group(f"📩 **Личное сообщение от пользователя:**\n{message.text}\n\n🤖 **Твой ответ:**\n{ans}")
    except Exception as e:
        print(f"[ERROR] AI Chat: {e}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # 1. Запуск Flask сервера (для Render)
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # 2. Запуск фонового охотника
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # 3. Очистка вебхуков и запуск бота
    print("[SYSTEM] Перезагрузка Telegram сессии...")
    bot.remove_webhook()
    time.sleep(3)
    
    print("[SYSTEM] Бот запущен и готов к работе.")
    bot.polling(none_stop=True, skip_pending=True)
