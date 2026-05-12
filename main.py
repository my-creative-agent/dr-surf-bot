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
START_TIME = time.time() 

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

def clean_html(text):
    if not text: return ""
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

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
    print(f"[FETCH] Проверка бирж...", flush=True)
    for feed_info in RSS_FEEDS:
        try:
            time.sleep(random.uniform(1, 3))
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(feed_info["url"], headers=headers, timeout=20)
            if response.status_code != 200: continue

            feed = feedparser.parse(response.content)
            for entry in feed.entries[:30]:
                published_time = time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else time.time()
                if not ignore_history and published_time < START_TIME - 3600: continue 
                
                title = entry.title if hasattr(entry, 'title') else ""
                desc = getattr(entry, 'description', '')
                content = (title + desc).lower()
                
                if any(word in content for word in KEYWORDS):
                    link = entry.link
                    if ignore_history or (link not in SENT_PROJECTS):
                        found.append({
                            "title": title, "url": link, "site": feed_info["name"],
                            "price": extract_price(entry), "offer": get_best_template(title)
                        })
                        if not ignore_history: SENT_PROJECTS.add(link)
        except Exception as e: print(f"Error {feed_info['name']}: {e}")
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e: print(f"Send Error: {e}")

def auto_hunter():
    print("[HUNTER] Цикл запущен", flush=True)
    time.sleep(30)
    while True:
        try:
            projects = fetch_orders()
            if projects:
                for p in projects:
                    msg = (f"💎 <b>НОВЫЙ ЗАКАЗ!</b>\n\n📍 <b>{p['site']}</b> | {p['price']}\n"
                           f"📝 <i>{clean_html(p['title'])}</i>\n🔗 <a href='{p['url']}'>Открыть</a>\n\n"
                           f"✉️ <b>ОТКЛИК:</b>\n{clean_html(p['offer'])}")
                    send_to_group(msg)
                    time.sleep(10)
        except Exception as e: print(f"Hunter Loop Error: {e}")
        time.sleep(600)

@bot.message_handler(commands=['start', 'check'])
def handle_commands(message):
    if message.text == '/start':
        bot.reply_to(message, "Dr. Surf Hunter Online. Ошибки Conflict устранены. 🏄‍♀️")
    else:
        projects = fetch_orders(ignore_history=True)
        if projects:
            res = "🎯 <b>ПОСЛЕДНЕЕ:</b>\n\n" + "\n".join([f"🔹 {p['site']}: <a href='{p['url']}'>{clean_html(p['title'][:50])}...</a>" for p in projects[:7]])
            bot.send_message(message.chat.id, res, parse_mode="HTML", disable_web_page_preview=True)
        else:
            bot.reply_to(message, "Пока новых волн нет.")

def run_bot():
    print("[BOT] Запуск Polling...", flush=True)
    while True:
        try:
            # ПРИНУДИТЕЛЬНЫЙ СБРОС ВЕБХУКА И ОЧИСТКА
            bot.remove_webhook()
            # drop_pending_updates=True — КЛЮЧЕВОЕ: удаляет все сообщения, 
            # пришедшие пока бот был в «конфликте», чтобы не спамить при старте.
            bot.polling(none_stop=True, interval=3, timeout=60, drop_pending_updates=True)
        except Exception as e:
            print(f"[RESTART] Конфликт или ошибка: {e}. Жду 15 сек...", flush=True)
            time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
