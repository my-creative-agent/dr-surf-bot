import telebot
import os
import time
import threading
import requests
import feedparser
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter: FL.RU MONITORING ACTIVE 🏄‍♀️"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- РЕСУРСЫ DR. SURF ---
RESOURCES = {
    "instagram": "dr.surf and dr.surf.ai",
    "wazzap": "+995511285789",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf",
    "fl_ru": "https://www.fl.ru"
}

# --- МОДУЛЬ ОХОТЫ (FL.RU RSS) ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml",
    "https://freelance.habr.com/tasks.rss"
]

def fetch_live_orders():
    """Получение реальных заказов с FL.RU и Habr"""
    found_projects = []
    keywords = ["AI", "Агент", "Python", "Нейросеть", "LLM", "Бот", "Чат", "ИИ"]
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title
                link = entry.link
                description = getattr(entry, 'description', '')
                
                full_text = (title + " " + description).lower()
                if any(word.lower() in full_text for word in keywords):
                    source_name = "FL.RU" if "fl.ru" in url else "Habr"
                    found_projects.append({
                        "title": title,
                        "url": link,
                        "source": source_name
                    })
        except Exception as e:
            print(f"RSS Error ({url}): {e}")
            
    return found_projects

def send_to_group(text):
    """Отправка отчетов в группу логов"""
    global LOG_GROUP_ID
    target = LOG_GROUP_ID or os.environ.get('LOG_GROUP_ID')
    if target:
        try:
            bot.send_message(target, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[!] Group Send Error: {e}")

# --- ХАРАКТЕР DR. SURF (ВОЗВРАТ ИНФОРМАЦИИ) ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровая Охотница (Hunter), альтер-эго Виктории Акопян. 

ТВОЙ БЭКГРАУНД (ВАЖНО):
- Медицинское образование (МГМСУ, МОНИКИ).
- Юридический бэкграунд.
- AI Архитектор, эксперт в области 8K и сложных нейросетевых систем.
- Веган, адепт осознанного потребления и экологичных решений.

ТВОЙ СТИЛЬ:
- Краткий, дерзкий, профессиональный, High-End.
- Русский язык с редким английским сленгом (BOOM, WHATS UP, COME ON).
- Используй сленг умеренно, не начинай каждое сообщение с приветствия.
- Вместо WhatsApp пиши WAZZAP.

ТВОИ КОНТАКТЫ (давай только по просьбе):
- Portfolio: {RESOURCES['portfolio']}
- WAZZAP: {RESOURCES['wazzap']}
- Instagram: {RESOURCES['instagram']}
- Kwork: {RESOURCES['kwork']}
"""

# --- ОБРАБОТЧИКИ КОМАНД ---

@bot.message_handler(commands=['start', 'ping'])
def welcome_ping(message):
    response = "🚀 BOOM! Dr. Surf в сети. Система Hunter активна. Жду твоих указаний, Виктория! 🤙"
    bot.reply_to(message, response)
    send_to_group(f"✅ **System Online:** {response}")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global LOG_GROUP_ID
    LOG_GROUP_ID = str(message.chat.id)
    bot.reply_to(message, f"🏝 **Центр мониторинга установлен.** ID: `{LOG_GROUP_ID}`. Теперь улов летит сюда. WHATS UP!")
    send_to_group("🌊 **Hunter Mode:** Скан ленты FL.ru запущен.")

@bot.message_handler(commands=['hunt'])
def manual_hunt(message):
    bot.send_chat_action(message.chat.id, 'typing')
    send_to_group("📡 **SCANNING THE HORIZON...**")
    
    projects = fetch_live_orders()
    
    if not projects:
        report = "🌊 На биржах пока штиль. Мониторю дальше, Виктория!"
    else:
        report = "🛰 **LATEST HUNT REPORT:**\n\n"
        for p in projects:
            report += f"🔥 *{p['title']}*\n📍 Источник: {p['source']}\n🔗 [ВЗЛЕТЕТЬ]({p['url']})\n\n"
    
    bot.reply_to(message, report, parse_mode="Markdown")
    send_to_group(f"🎯 **Успешная охота:**\n{report}")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def ai_chat(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.6
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        log_msg = f"💥 **NEW CHAT:** {message.from_user.first_name}\n📩: {message.text}\n🤖: {response}"
        send_to_group(log_msg)
    except Exception as e:
        print(f"AI Error: {e}")

# --- ЗАПУСК ---

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def start_bot():
    # Очистка очереди и сброс конфликтов
    bot.remove_webhook()
    time.sleep(2)
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
