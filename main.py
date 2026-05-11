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
MAIN_BOT_URL = "https://t.me/Dr_Surf_AI_bot" 
HUNTER_BOT_URL = "https://t.me/Dr_Surf_Hunter_bot" 
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"

MY_CONTACTS = f"""
👤 **Виктория Акопян**
🌟 *AI Prompt Engineer | Digital Twin Architect | Visual Specialist*

🚀 **Digital Twin:** {MAIN_BOT_URL}
📡 **Hunter Service:** {HUNTER_BOT_URL}
🎬 **Video Portfolio:** {PORTFOLIO_URL}

🔹 **Графика:** Flux.1, Midjourney v6, Stable Diffusion, DALL-E 3.
🔹 **Видео:** Sora, Runway Gen-3, Kling, HeyGen, Luma.
🔹 **Системы:** ИИ-агенты, автоматизация Threads, интеграция LLM.

📞 **Контакты:** [WhatsApp](https://wa.me/995511285789) | [Insta](https://instagram.com/dr.surf.ai) | [LinkedIn](https://www.linkedin.com/in/victoria-akopyan)
"""

# --- ШАБЛОНЫ ОТКЛИКОВ ---
OFFER_TEMPLATES = {
    "graphics": """
🎨 **Отклик (Графика/Дизайн):**
"Здравствуйте! Я специализируюсь на генеративной графике и визуальном стиле. Создаю логотипы, иллюстрации и брендинг с помощью Flux и Midjourney. Гарантирую уникальность и высокую детализацию. Мои работы: {portfolio_url}. Готова обсудить вашу задачу!"
""",
    "video": """
🎬 **Отклик (AI Video):**
"Приветствую! Занимаюсь созданием фотореалистичного ИИ-видео (Runway, Sora, Kling). Работаю с качеством 8K. Мои кейсы: {portfolio_url}. Буду рада реализовать ваш проект!"
""",
    "ai_agent": """
🤖 **Отклик (AI Агенты/Боты):**
"Добрый день! Разрабатываю автономных ИИ-агентов на базе Llama 3.3 и GPT-4o. Создаю 'Цифровых двойников' для бизнеса. Посмотрите пример моей работы: {bot_url}. Давайте обсудим архитектуру!"
""",
    "general": """
🌟 **Отклик (Общий):**
"Здравствуйте! Я AI-специалист (графика, видео, промпт-инжиниринг). Внедряю нейросети для автоматизации и создания контента. Мои контакты и кейсы: {bot_url}. Готова помочь!"
"""
}

# --- МОНИТОРИНГ БИРЖ (RSS) И ВАКАНСИЙ ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml",            # FL.ru
    "https://freelance.habr.com/tasks.rss",     # Habr Freelance
    "https://kwork.ru/rss/projects.xml",        # Kwork
    "https://freelance.ru/rss/feed/list.rss",   # Freelance.ru
    "https://www.weblancer.net/rss/projects.rss" # Weblancer
]

SENT_PROJECTS = set() 
LAST_JOB_REPORT_TIME = 0 

KEYWORDS = [
    "ai", "ии", "нейросеть", "дизайн", "лого", "логотип", "графика", 
    "видео", "video", "prompt", "midjourney", "flux", "sora", 
    "агент", "agent", "бот", "bot", "threads", "тредс"
]

def get_job_links():
    """Генерация ссылок для HeadHunter и LinkedIn"""
    queries = ["AI+Prompt+Engineer", "AI+Video+Creator", "Prompt+Engineer", "AI+Designer", "Нейросети"]
    hh_query = "+OR+".join(queries)
    return {
        "HH": f"https://hh.ru/search/vacancy?text={hh_query}&area=1&order_by=publication_time",
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords=AI%20Prompt%20Engineer%20OR%20AI%20Video"
    }

def extract_price(entry):
    price_pattern = r"(\d[\d\s]*\d\s?(?:руб|руб\.|₽|\$|USD|BYN|евро|€))"
    match = re.search(price_pattern, entry.title, re.IGNORECASE)
    if match: return match.group(1).strip()
    return "Договорная"

def get_best_template(title):
    t = title.lower()
    if any(x in t for x in ["видео", "video", "sora", "runway", "kling", "luma"]):
        return OFFER_TEMPLATES["video"].format(portfolio_url=PORTFOLIO_URL)
    elif any(x in t for x in ["лого", "дизайн", "design", "графика", "иллюстрация", "арт", "рисунок", "banner", "баннер"]):
        return OFFER_TEMPLATES["graphics"].format(portfolio_url=PORTFOLIO_URL)
    elif any(x in t for x in ["агент", "agent", "бот", "чат", "bot", "llama", "gpt"]):
        return OFFER_TEMPLATES["ai_agent"].format(bot_url=MAIN_BOT_URL)
    else:
        return OFFER_TEMPLATES["general"].format(bot_url=MAIN_BOT_URL)

def fetch_orders(ignore_history=False):
    found = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.title.lower()
                desc = getattr(entry, 'description', '').lower()
                if any(word in title for word in KEYWORDS) or any(word in desc for word in KEYWORDS):
                    if ignore_history or (entry.link not in SENT_PROJECTS):
                        site = "🎨 KWORK" if "kwork" in url else "👨‍💻 HABR" if "habr" in url else "🚀 FL" if "fl.ru" in url else "🌐 WEB"
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
        except Exception as e: print(f"Error sending log: {e}")

def auto_hunter():
    global LAST_JOB_REPORT_TIME
    print("Auto Hunter started...")
    while True:
        try:
            projects = fetch_orders()
            current_time = time.time()
            
            # Отправка новых заказов с бирж
            if projects:
                for p in projects:
                    report = f"💎 **НОВЫЙ ЗАКАЗ!**\n\n"
                    report += f"📍 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Открыть заказ]({p['url']})\n\n"
                    report += f"📝 **ШАБЛОН ОТКЛИКА:**\n{p['offer']}\n"
                    report += f"--- \n{MY_CONTACTS}"
                    send_to_group(report)
            
            # Раз в 12 часов — отчет по HH и LinkedIn
            if (current_time - LAST_JOB_REPORT_TIME) > 43200:
                jobs = get_job_links()
                job_report = f"🛰 **ОХОТА НА ШТАТ (HH & LinkedIn):**\n\n"
                job_report += f"🔹 [Вакансии на HeadHunter]({jobs['HH']})\n"
                job_report += f"🔹 [Вакансии на LinkedIn]({jobs['LinkedIn']})\n\n"
                job_report += "Удачи на охоте, Виктория! 🌊"
                send_to_group(job_report)
                LAST_JOB_REPORT_TIME = current_time
                
        except Exception as e: 
            print(f"Hunter error: {e}")
            time.sleep(60)
        time.sleep(1800) 

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter: Мониторю FL, Habr, Kwork, HH и LinkedIn. Все для твоего успеха! 🌊")

@bot.message_handler(commands=['hunt', 'check'])
def manual_check(message):
    bot.reply_to(message, "🔍 Глобальное сканирование всех площадок (Биржи + Вакансии)...")
    projects = fetch_orders(ignore_history=True)
    jobs = get_job_links()
    
    report = "🎯 **АКТУАЛЬНЫЙ УЛОВ:**\n\n"
    if projects:
        for p in projects[:5]: 
            report += f"💠 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Перейти]({p['url']})\n"
            report += "━━━━━━━━━━━━━━━━━━\n\n"
    
    report += "💼 **ВАКАНСИИ (HH & LinkedIn):**\n"
    report += f"🚀 [HeadHunter Стек]({jobs['HH']})\n"
    report += f"🔗 [LinkedIn Стек]({jobs['LinkedIn']})\n\n"
    report += f"--- \n{MY_CONTACTS}"
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        system_msg = f"Ты — Dr. Surf, аватар Виктории Акопян. Эксперт по ИИ, видео и графике. Твой характер: лаконичный, профессиональный. Ты веган и медик. Твои контакты: {MAIN_BOT_URL}"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        print(f"Chat error: {e}")

if __name__ == "__main__":
    # Render использует порт из переменной окружения PORT
    port = int(os.environ.get("PORT", 10000))
    
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # Запускаем охотника в отдельном потоке
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    print(f"Starting bot on port {port}...")
    
    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=2, timeout=90, drop_pending_updates=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(10)
