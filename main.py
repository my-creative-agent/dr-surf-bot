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
    keywords = ["AI", "Агент", "Python", "Нейросеть", "LLM", "Бот", "ИИ", "GPT"]
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title.lower()
                if any(word.lower() in title for word in keywords):
                    if entry.link not in SENT_PROJECTS:
                        found.append({"title": entry.title, "url": entry.link})
                        SENT_PROJECTS.add(entry.link)
        except Exception as e:
            print(f"[ERROR] RSS: {e}")
    return found

def send_to_group(text):
    global LOG_GROUP_ID
    target = LOG_GROUP_ID or os.environ.get('LOG_GROUP_ID')
    if target:
        try:
            bot.send_message(target, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[ERROR] Group Send: {e}")
    else:
        print("[WARNING] LOG_GROUP_ID не установлен.")

# --- АВТОМАТИЧЕСКАЯ ПРОВЕРКА (КАЖДЫЕ 30 МИНУТ) ---
def auto_hunter():
    print("[SYSTEM] Запуск авто-охотника...")
    while True:
        try:
            projects = fetch_orders()
            if projects:
                report = "🛰 **Найдены новые заказы:**\n\n"
                for p in projects:
                    report += f"🔹 {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
                send_to_group(report)
        except Exception as e:
            print(f"[ERROR] Auto-Hunter Loop: {e}")
        time.sleep(1800) 

# --- ХАРАКТЕР AI ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, AI-аватар Виктории Акопян (Медик МГМСУ/МОНИКИ, Юрист, AI Архитектор).
Стиль: Профессиональный, лаконичный. Никаких "Алоха" и "Бум".
Ты веган и ценишь экологичные решения.
Контакты давай только если просят: {MY_CONTACTS}
"""

@bot.message_handler(commands=['start', 'ping'])
def welcome(message):
    bot.reply_to(message, "Система активна. Мониторинг запущен.")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global LOG_GROUP_ID
    LOG_GROUP_ID = str(message.chat.id)
    bot.reply_to(message, f"Группа привязана (ID: {LOG_GROUP_ID}).")
    send_to_group("✅ Связь установлена.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}]
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        send_to_group(f"📩 **Личное сообщение:**\n{message.text}\n\n🤖 **Ответ:**\n{ans}")
    except Exception as e:
        print(f"[ERROR] AI Chat: {e}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # 1. Запуск Flask
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # 2. Запуск авто-охотника
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # 3. Безопасный запуск бота с защитой от Conflict 409
    while True:
        try:
            print("[SYSTEM] Сброс вебхука и запуск...")
            bot.remove_webhook()
            time.sleep(3) # Пауза, чтобы Telegram разорвал старые связи
            bot.polling(none_stop=True, skip_pending=True, timeout=60)
        except Exception as e:
            print(f"[RESTART] Ошибка polling (возможно конфликт): {e}")
            time.sleep(10) # Ждем перед попыткой перезапуска
