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
    {"url": "https://www.fl.ru/rss/all.xml", "name": "🚀 FL"},
    {"url": "https://freelance.habr.com/tasks.rss", "name": "👨‍💻 Habr"},
    {"url": "https://freelance.ru/rss/feed/list.rss", "name": "🛠 Freelance.ru"},
    {"url": "https://kwork.ru/rss/projects.xml", "name": "🎨 Kwork"}
]

KEYWORDS = [
    "ai", "ии", "нейросеть", "дизайн", "лого", "логотип", "графика", 
    "иллюстрация", "рисунок", "midjourney", "flux", "stable diffusion",
    "видео", "video", "prompt", "бот", "bot", "агент", "agent", "gpt"
]

SENT_PROJECTS = set() 

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
]

def fetch_hh_vacancies(query="AI Prompt Engineer", limit=5):
    """Специальный модуль для HeadHunter с маскировкой под браузер"""
    try:
        # Используем API HH с передачей необходимых заголовков
        url = f"https://api.hh.ru/vacancies?text={query}&area=1&per_page={limit}"
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            vacs = []
            for item in data.get('items', []):
                salary = "По договоренности"
                if item.get('salary'):
                    s = item['salary']
                    val_from = s.get('from') if s.get('from') else ""
                    val_to = s.get('to') if s.get('to') else ""
                    salary = f"{val_from}-{val_to} {s.get('currency')}"
                
                vacs.append({
                    "title": item['name'],
                    "url": item['alternate_url'],
                    "price": salary,
                    "site": "💼 HeadHunter",
                    "offer": OFFER_TEMPLATES["ai_agent"].format(bot_url=MAIN_BOT_URL)
                })
            return vacs
    except Exception as e:
        print(f"HH Error: {e}")
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
    # 1. RSS Сбор (Freelance биржи)
    for feed_info in RSS_FEEDS:
        try:
            time.sleep(random.uniform(1, 3))
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(feed_info["url"], headers=headers, timeout=20)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:20]:
                content = (entry.title + getattr(entry, 'description', '')).lower()
                if any(word in content for word in KEYWORDS):
                    if ignore_history or (entry.link not in SENT_PROJECTS):
                        found.append({
                            "title": entry.title, 
                            "url": entry.link, 
                            "site": feed_info["name"],
                            "price": extract_price(entry), 
                            "offer": get_best_template(entry.title)
                        })
                        if not ignore_history: SENT_PROJECTS.add(entry.link)
        except Exception as e: 
            print(f"Error fetching {feed_info['name']}: {e}")
    
    # 2. HH.ru Сбор
    hh_vacs = fetch_hh_vacancies()
    for v in hh_vacs:
        if ignore_history or (v['url'] not in SENT_PROJECTS):
            found.append(v)
            if not ignore_history: SENT_PROJECTS.add(v['url'])
            
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e: print(f"Log Error: {e}", flush=True)

def auto_hunter():
    print("[HUNTER] Авто-поиск (включая HH) запущен", flush=True)
    while True:
        try:
            projects = fetch_orders()
            if projects:
                for p in projects:
                    msg = f"💎 **НОВЫЙ ЗАКАЗ!**\n\n📍 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Открыть заказ]({p['url']})\n\n📝 **ОТКЛИК:**\n{p['offer']}\n\n{MY_CONTACTS}"
                    send_to_group(msg)
                    time.sleep(5)
        except Exception as e: 
            print(f"Hunter Error: {e}", flush=True)
        time.sleep(1200) # 20 минут

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter: Охота на HH и биржи активна! Используй /check для проверки.")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.send_chat_action(message.chat.id, 'typing')
    projects = fetch_orders(ignore_history=True)
    report = "🎯 **ПОСЛЕДНИЕ НАХОДКИ (Биржи + HH):**\n\n"
    if projects:
        for p in projects[:15]:
            report += f"💠 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Перейти]({p['url']})\n---\n"
    else:
        report += "🌊 Пока горизонт чист.\n"
    
    report += f"\n{MY_CONTACTS}"
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)

# --- ЗАПУСК ---

def run_bot():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"[RESTART] {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
