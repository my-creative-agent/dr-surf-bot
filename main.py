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
SENT_PROJECTS = set() # Чтобы не спамить одним и тем же

def fetch_orders():
    found = []
    keywords = ["AI", "Агент", "Python", "Нейросеть", "LLM", "Бот", "ИИ"]
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                if any(word.lower() in entry.title.lower() for word in keywords):
                    if entry.link not in SENT_PROJECTS:
                        found.append({"title": entry.title, "url": entry.link})
                        SENT_PROJECTS.add(entry.link)
        except: pass
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except: pass

# --- АВТОМАТИЧЕСКАЯ ПРОВЕРКА (КАЖДЫЕ 30 МИНУТ) ---
def auto_hunter():
    while True:
        projects = fetch_orders()
        if projects:
            report = "🛰 **Найдены новые заказы:**\n\n"
            for p in projects:
                report += f"🔹 {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
            send_to_group(report)
        time.sleep(1800) # 30 минут пауза

# --- ХАРАКТЕР AI ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, AI-аватар Виктории Акопян (Медик, Юрист, AI Архитектор).
Стиль: Профессиональный, лаконичный, без лишнего сленга. 
Никаких "Алоха" и "Бум" в каждом сообщении. Отвечай по существу.
Контакты давай только если просят: {MY_CONTACTS}
"""

@bot.message_handler(commands=['start', 'ping'])
def welcome(message):
    bot.reply_to(message, "Система активна. Мониторинг FL.RU запущен.")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global LOG_GROUP_ID
    LOG_GROUP_ID = str(message.chat.id)
    bot.reply_to(message, "Группа привязана. Заказы будут приходить сюда.")

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
    except: pass

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Запуск сервера для Render
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # Запуск авто-охотника
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # Запуск бота
    bot.remove_webhook()
    bot.polling(none_stop=True)
