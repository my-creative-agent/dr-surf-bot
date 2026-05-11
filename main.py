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
from telebot import apihelper

# --- СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter: AI Professional Edition is Running"

# Настройки стабильности (защита от Timeout и конфликтов)
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- АКТУАЛЬНЫЕ ССЫЛКИ И КОНТАКТЫ (ПОЛНЫЙ СПИСОК) ---
MAIN_BOT_URL = "https://t.me/Dr_Surf_AI_bot" 
HUNTER_BOT_URL = "https://t.me/Dr_Surf_Hunter_bot" 
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"
FACEBOOK_URL = "https://www.facebook.com/ssfmoscow"
LINKEDIN_URL = "https://www.linkedin.com/in/victoria-akopyan"
INSTAGRAM_URL = "https://instagram.com/dr.surf.ai"
WHATSAPP_URL = "https://wa.me/995511285789"

MY_CONTACTS = f"""
👤 **Виктория Акопян**
🌟 *AI Prompt Engineer | Digital Twin Architect | Visual Specialist*

🚀 **Цифровой двойник:** {MAIN_BOT_URL}
📡 **Сервис Охотник:** {HUNTER_BOT_URL}
🎬 **Кейсы и YouTube:** {PORTFOLIO_URL}

🔹 **Графика:** Flux.1, Midjourney v6, Stable Diffusion, DALL-E 3.
🔹 **Видео:** Sora, Runway Gen-3, Kling, HeyGen, Luma.
🔹 **Системы:** ИИ-агенты, автономные боты, LLM интеграция.

📞 **Связь и соцсети:**
📱 [Instagram]({INSTAGRAM_URL}) | [Facebook]({FACEBOOK_URL})
💼 [LinkedIn]({LINKEDIN_URL}) | [WhatsApp]({WHATSAPP_URL})
"""

# --- ШАБЛОНЫ ОТКЛИКОВ ---
OFFER_TEMPLATES = {
    "graphics": "Здравствуйте! Я специализируюсь на генеративной графике и визуальном стиле (Flux, Midjourney). Мои работы: {portfolio_url}. Готова обсудить создание уникального визуала!",
    "video": "Приветствую! Создаю фотореалистичное ИИ-видео высокого качества (Runway, Kling, Sora). Примеры: {portfolio_url}. Буду рада помочь!",
    "ai_agent": "Добрый день! Разрабатываю умных ИИ-агентов и персональных Цифровых двойников. Пример: {bot_url}. Давайте обсудим архитектуру вашего проекта!",
    "general": "Здравствуйте! Я AI-специалист широкого профиля (графика, видео, ИИ-системы). Мои кейсы и контакты: {bot_url}. Готова к сотрудничеству!"
}

# --- МОНИТОРИНГ БИРЖ ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml",
    "https://freelance.habr.com/tasks.rss",
    "https://kwork.ru/rss/projects.xml",
    "https://freelance.ru/rss/feed/list.rss"
]

SENT_PROJECTS = set() 
LAST_JOB_REPORT_TIME = 0 

# Расширенные ключевые слова для графики и ИИ
KEYWORDS = [
    "ai", "ии", "нейросеть", "дизайн", "лого", "логотип", "графика", 
    "иллюстрация", "рисунок", "midjourney", "flux", "stable diffusion",
    "видео", "video", "prompt", "бот", "bot", "агент", "agent"
]

def get_job_links():
    queries = ["AI+Prompt+Engineer", "AI+Video+Creator", "Нейросети", "AI+Designer"]
    hh_query = "+OR+".join(queries)
    return {
        "HH": f"https://hh.ru/search/vacancy?text={hh_query}&area=1&order_by=publication_time",
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords=AI%20Prompt%20Engineer%20OR%20AI%20Designer"
    }

def extract_price(entry):
    match = re.search(r"(\d[\d\s]*\d\s?(?:руб|₽|\$|USD|евро|€))", entry.title, re.IGNORECASE)
    return match.group(1).strip() if match else "Договорная"

def get_best_template(title):
    t = title.lower()
    if any(x in t for x in ["видео", "video", "runway", "kling", "sora"]): 
        return OFFER_TEMPLATES["video"].format(portfolio_url=PORTFOLIO_URL)
    if any(x in t for x in ["лого", "дизайн", "графика", "иллюстрация", "арт", "рисунок", "banner"]): 
        return OFFER_TEMPLATES["graphics"].format(portfolio_url=PORTFOLIO_URL)
    if any(x in t for x in ["агент", "бот", "bot", "llama", "chat"]): 
        return OFFER_TEMPLATES["ai_agent"].format(bot_url=MAIN_BOT_URL)
    return OFFER_TEMPLATES["general"].format(bot_url=MAIN_BOT_URL)

def fetch_orders(ignore_history=False):
    found = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                content = (entry.title + getattr(entry, 'description', '')).lower()
                if any(word in content for word in KEYWORDS):
                    if ignore_history or (entry.link not in SENT_PROJECTS):
                        site = "🚀 FL" if "fl.ru" in url else "🎨 KWORK" if "kwork" in url else "👨‍💻 HABR"
                        found.append({
                            "title": entry.title, 
                            "url": entry.link, 
                            "site": site,
                            "price": extract_price(entry), 
                            "offer": get_best_template(entry.title)
                        })
                        if not ignore_history: SENT_PROJECTS.add(entry.link)
        except: pass
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e: print(f"Log Error: {e}")

def auto_hunter():
    global LAST_JOB_REPORT_TIME
    while True:
        try:
            projects = fetch_orders()
            if projects:
                for p in projects:
                    msg = f"💎 **НОВЫЙ ЗАКАЗ!**\n\n📍 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Открыть заказ]({p['url']})\n\n📝 **ОТКЛИК:**\n{p['offer']}\n\n{MY_CONTACTS}"
                    send_to_group(msg)
            
            # Отчет по вакансиям раз в 12 часов
            if (time.time() - LAST_JOB_REPORT_TIME) > 43200:
                jobs = get_job_links()
                job_msg = f"🛰 **ВАКАНСИИ (ШТАТ):**\n🔹 [HH.ru]({jobs['HH']})\n🔹 [LinkedIn]({jobs['LinkedIn']})\n\nУдачи в охоте, Виктория! 🌊"
                send_to_group(job_msg)
                LAST_JOB_REPORT_TIME = time.time()
        except: time.sleep(60)
        time.sleep(1800)

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter в сети. Используй /check или /hunt для поиска заказов. Я также мониторю биржи 24/7! 🌊")

@bot.message_handler(commands=['hunt', 'check'])
def manual_check(message):
    bot.send_chat_action(message.chat.id, 'typing')
    projects = fetch_orders(ignore_history=True)
    report = "🎯 **АКТУАЛЬНЫЙ УЛОВ:**\n\n"
    if projects:
        for p in projects[:7]:
            report += f"💠 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Перейти]({p['url']})\n---\n"
    else:
        report += "🌊 Пока тишина. Попробуй позже!\n"
    
    report += f"\n{MY_CONTACTS}"
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        system_msg = f"""Ты — Dr. Surf, лаконичный цифровой двойник Виктории Акопян (AI эксперт, веган, медик). 
        Твои контакты: Instagram: {INSTAGRAM_URL}, Facebook: {FACEBOOK_URL}, YouTube: {PORTFOLIO_URL}, WhatsApp: {WHATSAPP_URL}. 
        Отвечай кратко и профессионально."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
        )
        ai_response = completion.choices[0].message.content
        bot.reply_to(message, ai_response)
        
        # ЛОГИРОВАНИЕ ДИАЛОГА В ГРУППУ
        anon_id = str(message.from_user.id)[-4:]
        log_msg = f"💬 **ДИАЛОГ В ЧАТЕ (...{anon_id})**\n\n👤: {message.text}\n\n🤖: {ai_response}"
        send_to_group(log_msg)
        
    except Exception as e:
        print(f"AI Error: {e}")
        bot.reply_to(message, "Волна слишком высокая, ИИ временно вне зоны доступа. Попробуй еще раз!")

# --- ЗАПУСК ПРИЛОЖЕНИЯ ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Запуск Flask и Охотника в отдельных потоках
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    print("[SYSTEM] Запуск основного цикла бота...")
    while True:
        try:
            bot.remove_webhook()
            time.sleep(2) # Защита от Conflict 409
            bot.polling(none_stop=True, interval=2, timeout=60, drop_pending_updates=True)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(10)
