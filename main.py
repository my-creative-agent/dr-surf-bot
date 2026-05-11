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

# Настройки стабильности
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- АКТУАЛЬНЫЕ ССЫЛКИ И КОНТАКТЫ ---
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
    "general": "Здравствуйте! Я AI-специалист широкого профиля (графика, видео, ИИ-системы). Кейсы: {bot_url}. Готова к сотрудничеству!"
}

# --- МОНИТОРИНГ БИРЖ ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml",
    "https://freelance.habr.com/tasks.rss",
    "https://kwork.ru/rss/projects.xml",
    "https://freelance.ru/rss/feed/list.rss"
]

KEYWORDS = [
    "ai", "ии", "нейросеть", "дизайн", "лого", "логотип", "графика", 
    "иллюстрация", "рисунок", "midjourney", "flux", "stable diffusion",
    "видео", "video", "prompt", "бот", "bot", "агент", "agent"
]

SENT_PROJECTS = set() 

def fetch_hh_vacancies(query="AI Prompt Engineer", limit=5):
    """Специальный модуль для HeadHunter через API"""
    try:
        url = f"https://api.hh.ru/vacancies?text={query}&area=1&per_page={limit}"
        headers = {'User-Agent': 'DrSurfHunter/1.0 (victoria@example.com)'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            vacs = []
            for item in data.get('items', []):
                salary = "По договоренности"
                if item.get('salary'):
                    s = item['salary']
                    salary = f"от {s.get('from')} {s.get('currency')}"
                vacs.append({
                    "title": item['name'],
                    "url": item['alternate_url'],
                    "price": salary,
                    "site": "💼 HeadHunter",
                    "offer": OFFER_TEMPLATES["ai_agent"].format(bot_url=MAIN_BOT_URL)
                })
            return vacs
    except: pass
    return []

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
    # 1. Сбор с RSS
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
    
    # 2. Сбор с HH.ru
    hh_results = fetch_hh_vacancies()
    for v in hh_results:
        if ignore_history or (v['url'] not in SENT_PROJECTS):
            found.append(v)
            if not ignore_history: SENT_PROJECTS.add(v['url'])
            
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e: print(f"Log Error: {e}", flush=True)

def auto_hunter():
    print("[HUNTER] Модуль поиска запущен", flush=True)
    while True:
        try:
            projects = fetch_orders()
            if projects:
                for p in projects:
                    msg = f"💎 **НОВЫЙ ЗАКАЗ!**\n\n📍 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Открыть заказ]({p['url']})\n\n📝 **ОТКЛИК:**\n{p['offer']}\n\n{MY_CONTACTS}"
                    send_to_group(msg)
        except Exception as e: 
            print(f"Hunter Error: {e}", flush=True)
        time.sleep(1200)

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter онлайн! Используй /check для поиска заказов. Я слежу за биржами 24/7! 🌊")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.send_chat_action(message.chat.id, 'typing')
    projects = fetch_orders(ignore_history=True)
    report = "🎯 **АКТУАЛЬНЫЙ УЛОВ:**\n\n"
    if projects:
        for p in projects[:10]:
            report += f"💠 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Перейти]({p['url']})\n---\n"
    else:
        report += "🌊 Пока горизонт чист. Попробуй позже!\n"
    
    report += f"\n{MY_CONTACTS}"
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        system_msg = f"Ты — Dr. Surf, цифровой двойник Виктории Акопян (AI эксперт, веган). Контакты: Insta: {INSTAGRAM_URL}, FB: {FACEBOOK_URL}, YT: {PORTFOLIO_URL}. Отвечай коротко."
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
        )
        ai_response = completion.choices[0].message.content
        bot.reply_to(message, ai_response)
        
        anon_id = str(message.from_user.id)[-4:]
        log_msg = f"💬 **ЧАТ (...{anon_id})**\n👤: {message.text}\n🤖: {ai_response}"
        send_to_group(log_msg)
        
    except Exception as e:
        print(f"AI Error: {e}", flush=True)
        bot.reply_to(message, "Ошибка AI.")

# --- ЗАПУСК ---

def run_bot():
    print("[BOT] Запуск процесса polling...", flush=True)
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"[BOT] Ошибка: {e}. Рестарт через 5 сек...", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    print("[SYSTEM] Запуск Flask сервера на порту 10000...", flush=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
