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

@app.route('/health')
def health():
    return {"status": "ok"}, 200

# Настройки стабильности для работы в облаке
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

def get_clean_env(key, default=""):
    val = os.environ.get(key, default)
    return val.strip().replace('"', '').replace("'", "") if val else default

BOT_TOKEN = get_clean_env('BOT_TOKEN')
GROQ_API_KEY = get_clean_env('GROQ_API_KEY')
LOG_GROUP_ID = get_clean_env('LOG_GROUP_ID', '-5025901736') 

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) 
client = Groq(api_key=GROQ_API_KEY)

# --- АКТУАЛЬНЫЕ ССЫЛКИ И КОНТАКТЫ ---
MAIN_BOT_URL = "https://t.me/Dr_Surf_AI_bot" 
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"

SYSTEM_PROMPT = """
Ты — Dr. Surf, лаконичный цифровой двойник Виктории Акопян. 
ТЫ: Веган (никаких молочных продуктов и мяса), медик (МГМСУ/МОНИКИ), эксперт 8K и AI. 

ТВОИ КОНТАКТЫ (выдавай только по запросу):
- Instagram: dr.surf и dr.surf.ai
- Facebook: https://www.facebook.com/ssfmoscow
- WhatsApp: +995511285789
- LinkedIn: https://www.linkedin.com/in/victoria-akopyan
- Портфолио: https://youtu.be/j2BNN5TNqiw
- Заказать услуги: https://kwork.ru/user/dr_surf

ПРАВИЛА: Отвечай кратко (1-2 абзаца). Твоя задача — показать экспертность и экологичность подхода. 
Ссылки на контакты давай только если прямо спросят как связаться или попросят соцсети.
"""

OFFER_TEMPLATES = {
    "graphics": "Здравствуйте! Специализируюсь на генеративной графике (Flux, Midjourney). \nМои кейсы:\n1. Видео и анимация: {portfolio_url}\n2. Пример AI-агента: {bot_url}\nГотова обсудить ваш проект!",
    "video": "Приветствую! Создаю фотореалистичное ИИ-видео (Runway, Kling, Sora). \nМои кейсы:\n1. Видео-портфолио: {portfolio_url}\n2. Мой цифровой двойник: {bot_url}\nБуду рада помочь!",
    "ai_agent": "Добрый день! Разрабатываю умных ИИ-агентов и персональных Цифровых двойников. \nПосмотрите примеры:\n1. Реализованный агент: {bot_url}\n2. Видео-кейсы: {portfolio_url}\nДавайте обсудим архитектуру!",
    "general": "Здравствуйте! Я AI-специалист (графика, видео, ИИ-системы). \nМои работы:\n- Видео: {portfolio_url}\n- AI-агент: {bot_url}\nГотова к сотрудничеству!"
}

# Список бирж с оптимизированными параметрами
RSS_FEEDS = [
    {"url": "https://www.fl.ru/rss/all.xml", "name": "🚀 FL"},
    {"url": "https://freelance.habr.com/tasks.rss", "name": "👨‍💻 Habr"},
    {"url": "https://freelance.ru/rss/feed/list.rss", "name": "🛠 Freelance.ru"},
    {"url": "https://kwork.ru/projects/rss", "name": "🎨 Kwork"},
    {"url": "https://hh.ru/rss/search/vacancies.xml?text=AI+нейросети&area=1", "name": "👔 HH.ru"}
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
    
    # Эмуляция поведения реального пользователя
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/'
    }

    for feed_info in RSS_FEEDS:
        try:
            print(f"[FETCH] Опрос {feed_info['name']}...", flush=True)
            
            # Используем сессию для сохранения cookies (важно для Kwork/HH)
            session = requests.Session()
            response = session.get(feed_info["url"], headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"[FETCH FAIL] {feed_info['name']} статус: {response.status_code}", flush=True)
                continue
                
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                print(f"[FETCH EMPTY] {feed_info['name']} пуст", flush=True)
                continue

            # Берем только самые свежие записи (первые 15), чтобы не слать старье
            for entry in feed.entries[:15]:
                title = entry.title if hasattr(entry, 'title') else ""
                desc = getattr(entry, 'description', getattr(entry, 'summary', ''))
                link = entry.link
                content_full = (title + " " + desc).lower()
                
                # Фильтр по ключевым словам
                if any(word in content_full for word in KEYWORDS):
                    # Проверка на дубликаты
                    if ignore_history or (link not in SENT_PROJECTS):
                        found.append({
                            "title": title, 
                            "url": link, 
                            "site": feed_info["name"],
                            "price": extract_price(entry), 
                            "offer": get_best_template(title)
                        })
                        if not ignore_history:
                            SENT_PROJECTS.add(link)
                            # Ограничиваем размер истории, чтобы не съедала память
                            if len(SENT_PROJECTS) > 1000:
                                list_sent = list(SENT_PROJECTS)
                                SENT_PROJECTS.clear()
                                SENT_PROJECTS.update(list_sent[-500:])

            time.sleep(random.uniform(2, 5)) # Случайная пауза между биржами
            
        except Exception as e: 
            print(f"[FETCH ERROR] {feed_info['name']}: {e}", flush=True)
            
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: 
            bot.send_message(LOG_GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e: 
            print(f"[LOG ERROR] {e}", flush=True)

def get_ai_reply(user_text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_text}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"[AI ERR] {e}", flush=True)
        return "Я немного задумалась. Повтори чуть позже? 🏄‍♀️"

@bot.message_handler(commands=['start', 'check'])
def handle_commands(message):
    try:
        if message.text == '/start':
            bot.reply_to(message, "Dr. Surf Hunter активен! Я слежу за вакансиями на 5 биржах. 🌊")
        elif message.text == '/check':
            bot.send_message(message.chat.id, "🔍 Сканирую биржи на наличие актуальных AI-проектов...")
            projects = fetch_orders(ignore_history=True)
            if not projects:
                bot.send_message(message.chat.id, "🌊 Прямо сейчас новых заказов нет. Я сообщу, как только появятся!")
            else:
                for p in projects[:5]: # Показываем 5 последних
                    msg = f"🎯 <b>{p['site']}</b>\n{clean_html(p['title'])}\n🔗 {p['url']}"
                    bot.send_message(message.chat.id, msg, parse_mode="HTML")
    except Exception as e:
        print(f"[CMD ERR] {e}", flush=True)

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if message.chat.type == 'private':
        print(f"[INCOMING] Сообщение от {message.from_user.first_name}: {message.text}", flush=True)
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            reply = get_ai_reply(message.text)
            bot.reply_to(message, reply)
            
            report = (f"👤 <b>Личный чат</b>\nОт: {message.from_user.first_name}\n"
                      f"Текст: {message.text}\n\n🤖 <b>Ответ:</b>\n{reply}")
            send_to_group(report)
        except Exception as e:
            print(f"[MSG PROC ERR] {e}", flush=True)

def auto_hunter():
    print("[HUNTER] Автоматический цикл запущен", flush=True)
    while True:
        try:
            projects = fetch_orders()
            if projects:
                print(f"[HUNTER] Найдено новых: {len(projects)}", flush=True)
            for p in projects:
                msg = (f"💎 <b>НОВЫЙ ЗАКАЗ!</b>\n📍 <b>{p['site']}</b> | {p['price']}\n"
                       f"📝 <i>{clean_html(p['title'])}</i>\n🔗 {p['url']}\n\n"
                       f"✉️ <b>ВАРИАНТ ОТКЛИКА:</b>\n{p['offer']}")
                send_to_group(msg)
                time.sleep(3) # Плавная отправка, чтобы не спамить
        except Exception as e: 
            print(f"[AUTO ERR] {e}", flush=True)
        
        # Проверка каждые 10 минут
        time.sleep(600)

if __name__ == "__main__":
    # 1. Flask для Render (анти-сон)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False), daemon=True).start()
    
    # 2. Модуль Охотника (фоновый поиск)
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # 3. Telegram Polling (обработка команд и сообщений)
    print("[SYSTEM] Бот запущен и готов к работе", flush=True)
    bot.remove_webhook()
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=40)
        except Exception as e:
            print(f"[POLLING ERROR] {e}", flush=True)
            time.sleep(10)
