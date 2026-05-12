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

SYSTEM_PROMPT = """
Ты — Dr. Surf, лаконичный цифровой двойник Виктории Акопян. 
ТЫ: Веган, медик (МГМСУ/МОНИКИ), эксперт 8K и AI. 
ПРАВИЛА: Отвечай кратко (1-2 абзаца). Ссылки давай только если просят контакты.
"""

# Теперь в шаблонах всегда два кейса: видео и сам агент
OFFER_TEMPLATES = {
    "graphics": "Здравствуйте! Специализируюсь на генеративной графике (Flux, Midjourney). \nМои кейсы:\n1. Видео и анимация: {portfolio_url}\n2. Пример AI-агента: {bot_url}\nГотова обсудить ваш проект!",
    "video": "Приветствую! Создаю фотореалистичное ИИ-видео (Runway, Kling, Sora). \nМои кейсы:\n1. Видео-портфолио: {portfolio_url}\n2. Мой цифровой двойник: {bot_url}\nБуду рада помочь!",
    "ai_agent": "Добрый день! Разрабатываю умных ИИ-агентов и персональных Цифровых двойников. \nПосмотрите примеры:\n1. Реализованный агент: {bot_url}\n2. Видео-кейсы: {portfolio_url}\nДавайте обсудим архитектуру!",
    "general": "Здравствуйте! Я AI-специалист (графика, видео, ИИ-системы). \nМои работы:\n- Видео: {portfolio_url}\n- AI-агент: {bot_url}\nГотова к сотрудничеству!"
}

RSS_FEEDS = [
    {"url": "https://www.fl.ru/rss/all.xml", "name": "🚀 FL"},
    {"url": "https://freelance.habr.com/tasks.rss", "name": "👨‍💻 Habr"},
    {"url": "https://freelance.ru/rss/feed/list.rss", "name": "🛠 Freelance.ru"},
    {"url": "https://kwork.ru/projects/rss", "name": "🎨 Kwork"}
]

KEYWORDS = [
    "ai", "ии", "нейросеть", "дизайн", "лого", "логотип", "графика", 
    "иллюстрация", "рисунок", "midjourney", "flux", "stable diffusion",
    "видео", "video", "prompt", "бот", "bot", "агент", "agent", "gpt", "нейро"
]

SENT_PROJECTS = set() 

def clean_html(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text) 
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def extract_price(entry):
    combined = (getattr(entry, 'title', '') + " " + getattr(entry, 'description', '') + " " + getattr(entry, 'summary', ''))
    match = re.search(r"(\d[\d\s]*\d\s?(?:руб|₽|\$|USD|евро|€))", combined, re.IGNORECASE)
    return match.group(1).strip() if match else "Договорная"

def get_best_template(title):
    t = title.lower()
    if any(x in t for x in ["видео", "video", "runway", "kling", "sora"]): 
        return OFFER_TEMPLATES["video"].format(portfolio_url=PORTFOLIO_URL, bot_url=MAIN_BOT_URL)
    if any(x in t for x in ["лого", "дизайн", "графика", "иллюстрация", "арт", "рисунок", "banner"]): 
        return OFFER_TEMPLATES["graphics"].format(portfolio_url=PORTFOLIO_URL, bot_url=MAIN_BOT_URL)
    if any(x in t for x in ["агент", "бот", "bot", "llama", "chat"]): 
        return OFFER_TEMPLATES["ai_agent"].format(portfolio_url=PORTFOLIO_URL, bot_url=MAIN_BOT_URL)
    return OFFER_TEMPLATES["general"].format(portfolio_url=PORTFOLIO_URL, bot_url=MAIN_BOT_URL)

def fetch_orders(ignore_history=False):
    found = []
    print(f"--- [FETCH START] ---", flush=True)
    for feed_info in RSS_FEEDS:
        try:
            print(f"[FETCH] Опрос {feed_info['name']}...", flush=True)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
            response = requests.get(feed_info["url"], headers=headers, timeout=20)
            if response.status_code != 200: continue
            
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:25]:
                title = entry.title if hasattr(entry, 'title') else ""
                desc = getattr(entry, 'description', getattr(entry, 'summary', ''))
                content_full = (title + " " + desc).lower()
                
                if any(word in content_full for word in KEYWORDS):
                    link = entry.link
                    if ignore_history or (link not in SENT_PROJECTS):
                        found.append({
                            "title": title, "url": link, "site": feed_info["name"],
                            "price": extract_price(entry), "offer": get_best_template(title)
                        })
                        if not ignore_history: SENT_PROJECTS.add(link)
        except Exception as e: 
            print(f"[ERROR] {feed_info['name']}: {e}", flush=True)
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: 
            bot.send_message(LOG_GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e: 
            print(f"[SEND ERROR] {e}", flush=True)

def get_ai_reply(user_text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_text}]
        )
        return completion.choices[0].message.content
    except:
        return "Я немного задумалась над волной. Повтори чуть позже? 🏄‍♀️"

@bot.message_handler(commands=['start', 'status', 'check'])
def handle_commands(message):
    if message.text == '/start':
        bot.reply_to(message, "Dr. Surf Hunter на связи. Мониторинг заказов и AI-поддержка активны! 🌊")
    elif message.text == '/status':
        bot.reply_to(message, f"Бот в сети. Проектов в базе: {len(SENT_PROJECTS)}")
    elif message.text == '/check':
        bot.send_message(message.chat.id, "🔍 Принудительная проверка всех бирж...")
        projects = fetch_orders(ignore_history=True)
        if not projects:
            bot.send_message(message.chat.id, "🌊 Новых заказов пока нет.")
        for p in projects[:3]:
            msg = f"🎯 <b>{p['site']}</b>\n{clean_html(p['title'])}\n💰 {p['price']}\n🔗 {p['url']}"
            bot.send_message(message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if message.chat.type == 'private':
        bot.send_chat_action(message.chat.id, 'typing')
        reply = get_ai_reply(message.text)
        bot.reply_to(message, reply)
        
        report = (f"👤 <b>Сообщение в личку</b> от <code>{message.from_user.id}</code>\n"
                  f"От: {message.from_user.first_name}\n"
                  f"Текст: {message.text}\n\n"
                  f"🤖 <b>Ответ Dr. Surf:</b>\n{reply}")
        send_to_group(report)

def auto_hunter():
    print("[HUNTER] Запущен", flush=True)
    while True:
        try:
            projects = fetch_orders()
            for p in projects:
                msg = (f"💎 <b>НОВЫЙ ЗАКАЗ!</b>\n📍 <b>{p['site']}</b> | {p['price']}\n"
                       f"📝 <i>{clean_html(p['title'])}</i>\n🔗 {p['url']}\n\n"
                       f"✉️ <b>ОТКЛИК:</b>\n{clean_html(p['offer'])}")
                send_to_group(msg)
                time.sleep(5)
        except Exception as e: 
            print(f"[HUNTER ERR] {e}", flush=True)
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    print("[BOT] Запуск системы...", flush=True)
    while True:
        try:
            bot.stop_polling()
            time.sleep(2)
            bot.delete_webhook(drop_pending_updates=True)
            print("[BOT] Polling стартовал", flush=True)
            # Убран аргумент threaded, который вызывал ошибку
            bot.polling(none_stop=True, interval=3, timeout=60)
        except Exception as e:
            print(f"[RESTART] Ошибка или сеть: {e}", flush=True)
            time.sleep(20)
