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
    return "Dr. Surf Hunter: AI Creative & Media Edition is Running"

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# --- ПРИВЯЗКА ГРУППЫ ---
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- ТВОЯ ВИЗИТКА (КОНТАКТЫ) ---
MY_CONTACTS = """
👤 **Виктория Акопян**
🌟 *AI-Архитектор | Видеокреатор | Digital Twin Expert*

🔹 **Специализация:** Фотореализм, 2D/3D видео, разработка AI-агентов.
🔹 **Бэкграунд:** Медик (МГМСУ/МОНИКИ), Юрист. Эко-активист, веган. 🌿

📞 **Связаться:**
• **WhatsApp:** [+995 511 285 789](https://wa.me/995511285789)
• **Instagram:** [dr.surf.ai](https://instagram.com/dr.surf.ai)
• **LinkedIn:** [Victoria Akopyan](https://www.linkedin.com/in/victoria-akopyan)
• **Портфолио:** [YouTube 8K](https://youtu.be/j2BNN5TNqiw)
"""

# --- ПРЯМЫЕ ССЫЛКИ ДЛЯ МОНИТОРИНГА ---
DIRECT_SEARCH_LINKS = {
    "HH.ru": "https://hh.ru/search/vacancy?text=AI+Video+Creator+HeyGen+Sora+Runway+Midjourney+AI+Agent&area=1&order_by=publication_time",
    "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords=AI%20Video%20Creator%20AI%20Agent%20HeyGen",
    "Habr Freelance": "https://freelance.habr.com/tasks?q=AI+видео+агент",
}

# --- ШАБЛОН ОТКЛИКА ---
RESPONSE_TEMPLATE = """
✨ **Твой дерзкий отклик:**
"Здравствуйте! Я Виктория. Пока другие только учатся промптам, я внедряю фотореалистичных AI-агентов и создаю видео уровня 8K. Мой опыт в медицине гарантирует точность, а вкус в искусстве — эстетику. Готова сделать ваш проект легендарным!"
"""

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
        "AI агент", "нейросеть видео", "heygen", "sora", "runway", "luma", "pika",
        "фотореализм", "2d", "3d", "цифровой двойник", "аватар", "создание видео",
        "генерация фото", "midjourney", "stable diffusion", "flux", "видеокреатор"
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
    greetings = [
        "Виктория, горизонт пылает! 🔥 Новые заказы:",
        "Мать ИИ, лови свежий улов! 🌊",
        "Dr. Surf на связи! Нашла сочные проекты для тебя: ⚡️",
        "Пока ты отдыхала, я нарыла золотишко! 💎"
    ]
    
    while True:
        try:
            projects = fetch_orders()
            if projects:
                header = random.choice(greetings)
                report = f"💎 **{header}**\n\n"
                
                for p in projects:
                    report += f"📍 **{p['site']}** | {p['title']}\n🔗 [Взять в работу]({p['url']})\n\n"
                
                report += f"🛰 **Ручной поиск по радарам:**\n"
                report += f"💼 [HeadHunter]({DIRECT_SEARCH_LINKS['HH.ru']}) | 🔗 [LinkedIn]({DIRECT_SEARCH_LINKS['LinkedIn']})\n\n"
                report += f"--- \n{RESPONSE_TEMPLATE}\n\n{MY_CONTACTS}"
                send_to_group(report)
            else:
                print(f"[IDLE] {time.strftime('%H:%M')} - Новых волн нет.")
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(60)
        time.sleep(1800)

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter: Заряжена, настроена, готова к охоте! 🌊🎬")

@bot.message_handler(commands=['check', 'hunt'])
def manual_check(message):
    bot.reply_to(message, "🔍 Секунду, сканирую вселенную на наличие ИИ-заказов...")
    projects = fetch_orders()
    
    if projects:
        report = "🚀 **Мой текущий улов:**\n\n"
        for p in projects:
            report += f"💠 {p['title']}\n🔗 {p['url']}\n\n"
    else:
        report = "🌊 На биржах пока тихо, как в открытом океане.\n\n"
    
    report += f"📍 **Проверь прямые ссылки:**\n[HH.ru]({DIRECT_SEARCH_LINKS['HH.ru']}) | [LinkedIn]({DIRECT_SEARCH_LINKS['LinkedIn']})\n\n{MY_CONTACTS}"
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        system_msg = "Ты — Dr. Surf, цифровой аватар Виктории Акопян. Ты эксперт в AI-видео (2D/3D), фотореализме и AI-агентах. Отвечай кратко, стильно, с легким вайбом превосходства технологий."
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
        )
        ans = completion.choices[0].message.content
        bot.reply_to(message, ans)
        if LOG_GROUP_ID:
            send_to_group(f"📩 **Клиент пишет:** {message.text}\n\n🤖 **Твой ответ:** {ans}")
    except:
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.polling(none_stop=True, interval=2, timeout=90)
