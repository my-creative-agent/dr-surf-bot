import telebot
import os
import time
import threading
import feedparser
import requests
import random
import re
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

# --- ТВОИ ПРУФЫ И КОНТАКТЫ ---
MAIN_BOT_URL = "https://t.me/Dr_Surf_AI_bot" # Твой основной цифровой двойник
HUNTER_BOT_URL = "https://t.me/Dr_Surf_Hunter_bot" # Этот бот-охотник
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"

MY_CONTACTS = f"""
👤 **Виктория Акопян**
🌟 *AI Prompt Engineer | Digital Twin Architect | Video Creator*

🚀 **Digital Twin:** {MAIN_BOT_URL}
📡 **Hunter Service:** {HUNTER_BOT_URL}
🎬 **Video Portfolio:** {PORTFOLIO_URL}

🔹 **Stack:** Sora, Runway Gen-3, HeyGen, Threads Automation, Flux, Llama 3.3.
🔹 **Expertise:** Промпт-инжиниринг, ИИ-агенты, ИИ-видео.

📞 **Контакты:** [WhatsApp](https://wa.me/995511285789) | [Insta](https://instagram.com/dr.surf.ai) | [FB](https://www.facebook.com/ssfmoscow) | [LinkedIn](https://www.linkedin.com/in/victoria-akopyan)
"""

# --- ГОТОВЫЕ ШАБЛОНЫ ОТКЛИКОВ ПО КАТЕГОРИЯМ ---
OFFER_TEMPLATES = {
    "ai_agent": """
🤖 **Отклик (AI Агенты):**
"Приветствую! Занимаюсь разработкой автономных ИИ-агентов на базе Llama 3.3 и GPT-4o. Могу создать систему, которая не просто отвечает, а выполняет бизнес-задачи. Мой живой кейс (Digital Twin): {bot_url}. Готова обсудить архитектуру вашего проекта."
""",
    "video": """
🎬 **Отклик (AI Video):**
"Здравствуйте! Специализируюсь на фотореалистичной генерации видео (Sora, Runway Gen-3, Kling). Создаю контент уровня 8K. Мое портфолио: {portfolio_url}. Гарантирую высокое качество и соблюдение сроков. Давайте обсудим ТЗ!"
""",
    "threads": """
🧵 **Отклик (Threads Automation):**
"Добрый день! Имею опыт автоматизации и продвижения в Threads. Настраиваю умные системы постинга и взаимодействия. Помогу масштабировать ваш аккаунт с помощью ИИ. Готова приступить в ближайшее время."
""",
    "general": """
🌟 **Отклик (Общий AI):**
"Приветствую! Я AI Prompt Engineer. Внедряю нейросети в бизнес-процессы: от текстов и фото до сложных агентов и видео. Мои работы и кейсы: {bot_url}. Буду рада помочь в реализации вашей задачи!"
"""
}

# --- РАДАР ВАКАНСИЙ (HH И LINKEDIN) ---
def get_job_links():
    queries_hh = ["AI+Video+Creator", "Prompt+Engineer", "AI+Agent", "Threads+Automation"]
    hh_combined = "+OR+".join(queries_hh)
    return {
        "HH (Все)": f"https://hh.ru/search/vacancy?text={hh_combined}&area=1&order_by=publication_time",
        "HH (AI Video)": f"https://hh.ru/search/vacancy?text=AI+Video+Runway+Sora&area=1",
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords=AI+Video+Creator+Threads+AI+Agent"
    }

# --- МОДУЛЬ ОХОТЫ (БИРЖИ) ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml", 
    "https://freelance.habr.com/tasks.rss",
    "https://kwork.ru/rss/projects.xml"
]
SENT_PROJECTS = set() 
LAST_JOB_REPORT_TIME = 0 

def extract_price(entry):
    price_pattern = r"(\d[\d\s]*\d\s?(?:руб|руб\.|₽|\$|USD|BYN|евро|€))"
    match = re.search(price_pattern, entry.title, re.IGNORECASE)
    if match: return match.group(1).strip()
    return "Договорная"

def get_best_template(title):
    t = title.lower()
    if any(x in t for x in ["видео", "video", "sora", "runway", "kling", "luma"]):
        return OFFER_TEMPLATES["video"].format(portfolio_url=PORTFOLIO_URL)
    elif any(x in t for x in ["агент", "agent", "бот", "чат", "llama"]):
        return OFFER_TEMPLATES["ai_agent"].format(bot_url=MAIN_BOT_URL)
    elif any(x in t for x in ["threads", "тредс"]):
        return OFFER_TEMPLATES["threads"]
    else:
        return OFFER_TEMPLATES["general"].format(bot_url=MAIN_BOT_URL)

def fetch_orders(ignore_history=False):
    found = []
    keywords = ["ai агент", "ии агент", "нейросеть", "sora", "runway", "luma", "threads", "тредс", "видео", "prompt", "llm"]
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                title = entry.title.lower()
                desc = getattr(entry, 'description', '').lower()
                if any(word in title for word in keywords) or any(word in desc for word in keywords):
                    if ignore_history or (entry.link not in SENT_PROJECTS):
                        site = "🎨 KWORK" if "kwork" in url else "👨‍💻 HABR" if "habr" in url else "🚀 FL"
                        price = extract_price(entry)
                        template = get_best_template(entry.title)
                        found.append({
                            "title": entry.title, 
                            "url": entry.link, 
                            "site": site, 
                            "price": price,
                            "offer": template
                        })
                        if not ignore_history: SENT_PROJECTS.add(entry.link)
        except: pass
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except: pass

def auto_hunter():
    global LAST_JOB_REPORT_TIME
    while True:
        try:
            projects = fetch_orders()
            current_time = time.time()
            include_jobs = (current_time - LAST_JOB_REPORT_TIME) > 43200
            
            if projects:
                for p in projects:
                    report = f"💎 **НОВЫЙ ЗАКАЗ!**\n\n"
                    report += f"📍 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Открыть заказ]({p['url']})\n\n"
                    report += f"📝 **ГОТОВЫЙ ОТКЛИК:**\n{p['offer']}\n"
                    report += f"--- \n{MY_CONTACTS}"
                    send_to_group(report)
                
                if include_jobs:
                    job_links = get_job_links()
                    job_report = "🛰 **ОХОТА НА HH & LINKEDIN (12ч):**\n"
                    job_report += f"[HH Стек]({job_links['HH (Все)']}) | [HH Video]({job_links['HH (AI Video)']}) | [LinkedIn]({job_links['LinkedIn']})"
                    send_to_group(job_report)
                    LAST_JOB_REPORT_TIME = current_time
        except: time.sleep(60)
        time.sleep(3600) 

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter: Бот активен. Я подбираю отклики и ссылки на вакансии автоматически. 🌊")

@bot.message_handler(commands=['hunt', 'check'])
def manual_check(message):
    bot.reply_to(message, "🔍 Полный чек (Kwork, FL, HH, LinkedIn) + Подбор ответов...")
    projects = fetch_orders(ignore_history=True)
    job_links = get_job_links()
    
    report = "🎯 **ПОЛНЫЙ ОТЧЕТ МОНИТОРИНГА:**\n\n"
    
    if projects:
        report += "🛠 **ФРИЛАНС-ПРОЕКТЫ (+ОТКЛИКИ):**\n\n"
        for p in projects[:5]: 
            report += f"💠 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Перейти]({p['url']})\n📋 **Рекомендованный отклик:**\n{p['offer']}\n"
            report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "💼 **ВАКАНСИИ:**\n"
    report += f"🚀 [HH: AI Стек]({job_links['HH (Все)']})\n"
    report += f"🎬 [HH: AI Video]({job_links['HH (AI Video)']})\n"
    report += f"🔗 [LinkedIn]({job_links['LinkedIn']})\n\n"
    report += f"--- \n{MY_CONTACTS}"
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        system_msg = f"Ты — Dr. Surf, аватар Виктории Акопян (веган, AI эксперт). Отвечай кратко. Контакты: {MAIN_BOT_URL}"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        print(f"Chat error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Запуск Flask
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    # Запуск Охотника
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # Решение ошибки Conflict 409
    try:
        bot.stop_polling()
        time.sleep(5) # Даем время Telegram закрыть старые соединения
        bot.remove_webhook()
        print("Polling started successfully...")
        bot.polling(none_stop=True, interval=2, timeout=90)
    except Exception as e:
        print(f"Critical error: {e}")
        time.sleep(10)
