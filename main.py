import telebot
import os
import time
import threading
import feedparser
import requests
import random
from groq import Groq
from flask import Flask

# --- СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter: AI Professional Edition is Running"

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- ТВОИ ПРУФЫ И КЕЙСЫ ---
BOT_URL = "https://t.me/Dr_Surf_AI_bot"
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"

MY_CONTACTS = f"""
👤 **Виктория Акопян**
🌟 *AI Prompt Engineer | Digital Twin Architect | Video Creator*

🚀 **Live Case (AI Agent):** {BOT_URL}
🎬 **Video Portfolio (AI/8K):** {PORTFOLIO_URL}

🔹 **Stack:** Sora, Runway Gen-3, HeyGen, Midjourney, Flux, Llama 3.3.
🔹 **Expertise:** Промпт-инжиниринг, архитектура AI-агентов, фотореализм.

📞 **Связаться:**
• **WhatsApp:** [+995 511 285 789](https://wa.me/995511285789)
• **Instagram:** [dr.surf.ai](https://instagram.com/dr.surf.ai)
• **LinkedIn:** [Victoria Akopyan](https://www.linkedin.com/in/victoria-akopyan)
"""

# --- ШАБЛОН ОТКЛИКА (ФРИЛАНС-СТИЛЬ) ---
RESPONSE_TEMPLATE = f"""
✅ **Твой готовый отклик:**
"Приветствую! Специализируюсь на промпт-инжиниринге и разработке AI-агентов. Могу закрыть ваш запрос по видео (HeyGen/Runway) или внедрить сложного чат-бота. 
Мой живой кейс (Digital Twin): {BOT_URL}. 
Качество гарантирую. Готова обсудить ТЗ."
"""

# --- РАДАР ВАКАНСИЙ (HH.ru и LinkedIn) ---
def get_job_links():
    # Ключевые слова для поиска
    query = "AI+Video+Creator+HeyGen+Sora+Runway+AI+Agent+Prompt"
    return {
        "HH.ru": f"https://hh.ru/search/vacancy?text={query}&area=1&order_by=publication_time",
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords={query}"
    }

# --- МОДУЛЬ ОХОТЫ ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml", 
    "https://freelance.habr.com/tasks.rss",
    "https://kwork.ru/rss/projects.xml"
]
SENT_PROJECTS = set() 

def fetch_orders():
    found = []
    keywords = [
        "ai агент", "нейросеть видео", "heygen", "sora", "runway", "luma", "pika",
        "фотореализм", "аватар", "создание видео", "midjourney", "flux", "prompt"
    ]
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                title = entry.title.lower()
                desc = getattr(entry, 'description', '').lower()
                if any(word.lower() in title for word in keywords) or any(word.lower() in desc for word in keywords):
                    if entry.link not in SENT_PROJECTS:
                        site = "🎨 KWORK" if "kwork" in url else "👨‍💻 HABR" if "habr" in url else "🚀 FL"
                        found.append({"title": entry.title, "url": entry.link, "site": site})
                        SENT_PROJECTS.add(entry.link)
        except:
            pass
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try:
            bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except:
            pass

def auto_hunter():
    while True:
        try:
            projects = fetch_orders()
            job_links = get_job_links()
            
            # Если есть новые фриланс-проекты, шлем полный отчет
            if projects:
                report = "💎 **ВИКТОРИЯ, НОВЫЙ УЛОВ!**\n\n"
                for p in projects:
                    report += f"📍 **{p['site']}** | {p['title']}\n🔗 [Открыть заказ]({p['url']})\n\n"
                
                report += "🛰 **HH.RU И LINKEDIN (ПРЯМОЙ ПОИСК):**\n"
                report += f"💼 [Вакансии на HH.ru]({job_links['HH.ru']})\n"
                report += f"🔗 [Вакансии на LinkedIn]({job_links['LinkedIn']})\n\n"
                
                report += f"--- \n{RESPONSE_TEMPLATE}\n\n{MY_CONTACTS}"
                send_to_group(report)
        except Exception as e:
            print(f"Error in hunter: {e}")
            time.sleep(60)
        
        time.sleep(1800) # Проверка каждые 30 минут

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter: Режим фриланса и мониторинга HH активен. 🌊")

@bot.message_handler(commands=['hunt', 'check'])
def manual_check(message):
    bot.reply_to(message, "🔍 Проверяю все биржи и вакансии HH.ru прямо сейчас...")
    projects = fetch_orders()
    job_links = get_job_links()
    
    report = "🚀 **АКТУАЛЬНО НА ДАННЫЙ МОМЕНТ:**\n\n"
    if projects:
        for p in projects: report += f"💠 {p['title']}\n🔗 {p['url']}\n\n"
    else:
        report += "🌊 Новых заказов на биржах пока нет.\n\n"
    
    report += "🛰 **РАДАР ВАКАНСИЙ:**\n"
    report += f"💼 [HH.ru]({job_links['HH.ru']})\n"
    report += f"🔗 [LinkedIn]({job_links['LinkedIn']})\n\n"
    report += f"{MY_CONTACTS}"
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

# --- ЦИФРОВОЙ ДВОЙНИК + ЛОГИ ---
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        system_msg = f"""Ты — Dr. Surf, цифровой аватар Виктории Акопян. 
        Твоя специализация: Промпт-инжиниринг, AI-видео (Sora, HeyGen), AI-агенты.
        ОТВЕЧАЙ: Кратко, четко, как Senior Prompt Engineer. Никакой воды. 
        Твой живой кейс — этот бот: {BOT_URL}. Портфолио: {PORTFOLIO_URL}."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        
        # Логирование переписки в группу
        if LOG_GROUP_ID:
            log_text = f"📩 **СООБЩЕНИЕ ОТ КЛИЕНТА!**\n\n👤 **Запрос:** {message.text}\n\n🤖 **Твой ответ:** {ans}"
            send_to_group(log_text)
            
    except Exception as e:
        print(f"Error in chat: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    bot.remove_webhook()
    time.sleep(1)
    print("--- Dr. Surf запущен ---")
    bot.polling(none_stop=True, interval=2, timeout=90)
