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
👤 <b>Виктория Акопян</b>
🌟 <i>AI Prompt Engineer | Digital Twin Architect | Visual Specialist</i>

🚀 <b>Цифровой двойник:</b> {MAIN_BOT_URL}
📡 <b>Сервис Охотник:</b> {HUNTER_BOT_URL}
🎬 <b>Кейсы и YouTube:</b> {PORTFOLIO_URL}

🔹 <b>Графика:</b> Flux.1, Midjourney v6, Stable Diffusion, DALL-E 3.
🔹 <b>Видео:</b> Sora, Runway Gen-3, Kling, HeyGen, Luma.
🔹 <b>Системы:</b> ИИ-агенты, автономные боты, LLM интеграция.

📞 <b>Связь и соцсети:</b>
📱 <a href="{INSTAGRAM_URL}">Instagram</a> | <a href="{FACEBOOK_URL}">Facebook</a>
💼 <a href="{LINKEDIN_URL}">LinkedIn</a> | <a href="{WHATSAPP_URL}">WhatsApp</a>
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
START_TIME = time.time() 

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def clean_html(text):
    """Очистка текста для безопасной отправки в HTML режиме"""
    if not text: return ""
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

def fetch_hh_vacancies(query="AI Prompt Engineer", limit=10):
    try:
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
    print(f"[FETCH] Начинаю проверку бирж... (История игнорируется: {ignore_history})", flush=True)
    for feed_info in RSS_FEEDS:
        try:
            time.sleep(random.uniform(2, 4))
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(feed_info["url"], headers=headers, timeout=25)
            
            if response.status_code != 200: 
                print(f"[FETCH] Ошибка {feed_info['name']}: Статус {response.status_code}")
                continue

            feed = feedparser.parse(response.content)
            print(f"[FETCH] {feed_info['name']}: Обработка {len(feed.entries)} записей")
            
            for entry in feed.entries[:40]:
                published_time = time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else time.time()
                
                # Более мягкий фильтр времени для ручной проверки
                if not ignore_history and published_time < START_TIME - 7200:
                    continue 
                
                title = entry.title if hasattr(entry, 'title') else "Без заголовка"
                desc = getattr(entry, 'description', '')
                content = (title + desc).lower()
                
                if any(word in content for word in KEYWORDS):
                    link = entry.link
                    if ignore_history or (link not in SENT_PROJECTS):
                        found.append({
                            "title": title, 
                            "url": link, 
                            "site": feed_info["name"],
                            "price": extract_price(entry), 
                            "offer": get_best_template(title)
                        })
                        if not ignore_history: SENT_PROJECTS.add(link)
        except Exception as e: 
            print(f"Error fetching {feed_info['name']}: {e}")
    
    try:
        hh_vacs = fetch_hh_vacancies()
        for v in hh_vacs:
            if ignore_history or (v['url'] not in SENT_PROJECTS):
                found.append(v)
                if not ignore_history: SENT_PROJECTS.add(v['url'])
    except Exception as e:
        print(f"HH Fetch Error: {e}")
            
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: 
            bot.send_message(LOG_GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e: 
            print(f"Log Error: {e}", flush=True)
            try: 
                bot.send_message(LOG_GROUP_ID, "⚠️ Ошибка разметки. Данные заказа:\n" + text.replace("<b>","").replace("</b>",""), disable_web_page_preview=True)
            except: pass

def auto_hunter():
    print("[HUNTER] Охотник запущен (HTML Mode)", flush=True)
    time.sleep(45) # Даем боту время на "прогрузку"
    while True:
        try:
            projects = fetch_orders()
            if projects:
                print(f"[HUNTER] Найдено новых заказов: {len(projects)}", flush=True)
                for p in projects:
                    safe_title = clean_html(p['title'])
                    safe_offer = clean_html(p['offer'])
                    
                    msg = (
                        f"💎 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
                        f"📍 <b>{p['site']}</b> | {p['price']}\n"
                        f"📝 <i>{safe_title}</i>\n"
                        f"🔗 <a href='{p['url']}'>Открыть заказ</a>\n\n"
                        f"✉️ <b>ШАБЛОН ОТКЛИКА:</b>\n{safe_offer}\n\n"
                        f"---"
                    )
                    send_to_group(msg)
                    time.sleep(15) 
            else:
                print("[HUNTER] Новых заказов не обнаружено.", flush=True)
        except Exception as e: 
            print(f"Hunter Loop Error: {e}", flush=True)
        
        time.sleep(900 + random.randint(0, 300))

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def welcome(message):
    try:
        bot.reply_to(message, "Dr. Surf Hunter: На связи! Система мониторинга перезапущена. Ошибки Conflict устранены. 🏄‍♀️")
    except: pass

@bot.message_handler(commands=['check'])
def manual_check(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        projects = fetch_orders(ignore_history=True)
        report = "🎯 <b>АКТУАЛЬНЫЙ УЛОВ (Последние 10):</b>\n\n"
        if projects:
            for p in projects[:10]:
                safe_t = clean_html(p['title'])
                report += f"💠 <b>{p['site']}</b> | {p['price']}\n<i>{safe_t}</i>\n🔗 <a href='{p['url']}'>Перейти</a>\n\n"
        else:
            report += "🌊 Пока пусто. Проверь через 15 минут!\n"
        
        bot.send_message(message.chat.id, report, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print(f"Manual Check Error: {e}")

# --- ЗАПУСК ---

def run_bot():
    print("[BOT] Запуск интерфейса...", flush=True)
    while True:
        try:
            # Жесткий сброс перед запуском
            bot.remove_webhook()
            time.sleep(5) 
            # drop_pending_updates=True помогает избежать "заваливания" старыми сообщениями
            bot.infinity_polling(timeout=90, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            print(f"[RESTART] Ошибка polling: {e}. Сплю 20 сек...", flush=True)
            time.sleep(20)

if __name__ == "__main__":
    # 1. Запускаем бота
    threading.Thread(target=run_bot, daemon=True).start()
    # 2. Запускаем охотника
    threading.Thread(target=auto_hunter, daemon=True).start()
    
    # Flask для Uptime (Render/HF)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
