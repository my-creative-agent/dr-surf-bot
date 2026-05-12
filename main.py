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
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

def get_clean_env(key, default=""):
    val = os.environ.get(key, default)
    return val.strip().replace('"', '').replace("'", "") if val else default

BOT_TOKEN = get_clean_env('BOT_TOKEN')
GROQ_API_KEY = get_clean_env('GROQ_API_KEY')
LOG_GROUP_ID = get_clean_env('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- АКТУАЛЬНЫЕ ССЫЛКИ И КОНТАКТЫ ---
MAIN_BOT_URL = "https://t.me/Dr_Surf_AI_bot" 
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"

OFFER_TEMPLATES = {
    "graphics": "Здравствуйте! Я специализируюсь на генеративной графике и визуальном стиле (Flux, Midjourney). Мои работы: {portfolio_url}. Готова обсудить создание уникального визуала!",
    "video": "Приветствую! Создаю фотореалистичное ИИ-видео высокого качества (Runway, Kling, Sora). Примеры: {portfolio_url}. Буду рада помочь!",
    "ai_agent": "Добрый день! Разрабатываю умных ИИ-агентов и персональных Цифровых двойников. Пример: {bot_url}. Давайте обсудим архитектуру вашего проекта!",
    "general": "Здравствуйте! Я AI-специалист широкого профиля (графика, видео, ИИ-системы). Кейсы: {bot_url}. Готова к сотрудничеству!"
}

RSS_FEEDS = [
    {"url": "https://www.fl.ru/rss/all.xml", "name": "🚀 FL"},
    {"url": "https://freelance.habr.com/tasks.rss", "name": "👨‍💻 Habr"},
    {"url": "https://freelance.ru/rss/feed/list.rss", "name": "🛠 Freelance.ru"},
    {"url": "https://kwork.ru/projects/rss", "name": "🎨 Kwork"} # Исправлен URL Kwork
]

KEYWORDS = [
    "ai", "ии", "нейросеть", "дизайн", "лого", "логотип", "графика", 
    "иллюстрация", "рисунок", "midjourney", "flux", "stable diffusion",
    "видео", "video", "prompt", "бот", "bot", "агент", "agent", "gpt"
]

SENT_PROJECTS = set() 
START_TIME = time.time() 

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

def clean_html(text):
    if not text: return ""
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

def extract_price(entry):
    combined = (getattr(entry, 'title', '') + " " + getattr(entry, 'description', ''))
    match = re.search(r"(\d[\d\s]*\d\s?(?:руб|₽|\$|USD|евро|€))", combined, re.IGNORECASE)
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
    print(f"--- [FETCH START] ---", flush=True)
    for feed_info in RSS_FEEDS:
        try:
            print(f"[FETCH] Запрос к {feed_info['name']}...", flush=True)
            time.sleep(random.uniform(1, 3))
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(feed_info["url"], headers=headers, timeout=20)
            
            print(f"[DEBUG] {feed_info['name']} Status: {response.status_code}", flush=True)
            
            if response.status_code != 200:
                continue

            feed = feedparser.parse(response.content)
            for entry in feed.entries[:30]:
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
        except Exception as e: 
            print(f"[ERROR] {feed_info['name']}: {e}", flush=True)
    
    print(f"--- [FETCH END] Найдено: {len(found)} ---", flush=True)
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: 
            bot.send_message(LOG_GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e: 
            print(f"[SEND ERROR] {e}", flush=True)

def auto_hunter():
    print("[HUNTER] Цикл мониторинга запущен", flush=True)
    while True:
        try:
            projects = fetch_orders()
            for p in projects:
                msg = (f"💎 <b>НОВЫЙ ЗАКАЗ!</b>\n\n📍 <b>{p['site']}</b> | {p['price']}\n"
                       f"📝 <i>{clean_html(p['title'])}</i>\n🔗 <a href='{p['url']}'>Открыть</a>\n\n"
                       f"✉️ <b>ОТКЛИК:</b>\n{clean_html(p['offer'])}")
                send_to_group(msg)
                time.sleep(3)
        except Exception as e: 
            print(f"[HUNTER CRASH] {e}", flush=True)
        time.sleep(600)

@bot.message_handler(commands=['start', 'check', 'status'])
def handle_commands(message):
    if message.text == '/start':
        bot.reply_to(message, "Dr. Surf Hunter Online. 🏄‍♀️")
    elif message.text == '/status':
        bot.reply_to(message, f"Активен. Проектов: {len(SENT_PROJECTS)}")
    else:
        bot.send_message(message.chat.id, "🔍 Проверка всех бирж...")
        projects = fetch_orders(ignore_history=True)
        if projects:
            for p in projects[:5]:
                msg = (f"🎯 <b>НАЙДЕНО:</b> {p['site']}\n{clean_html(p['title'])}\n"
                       f"💰 {p['price']}\n🔗 {p['url']}\n\n✉️ <b>ОТКЛИК:</b>\n{p['offer']}")
                bot.send_message(message.chat.id, msg, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "🌊 Пусто.")

if __name__ == "__main__":
    # Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # Hunter в отдельном потоке
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # Бот в основном потоке (чтобы не дублировался)
    print("[BOT] Запуск...", flush=True)
    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=3, timeout=60)
        except Exception as e:
            print(f"[RESTART] {e}", flush=True)
            time.sleep(10)
