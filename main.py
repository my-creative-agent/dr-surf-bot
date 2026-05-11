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

def fetch_hh_vacancies(query="AI Prompt Engineer", limit=5):
    """Специальный модуль для HeadHunter через API с защитой от блокировок"""
    try:
        url = f"https://api.hh.ru/vacancies?text={query}&area=1&per_page={limit}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
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
    # 1. Сбор с RSS (FL, Habr, Kwork, Freelance.ru)
    for feed_info in RSS_FEEDS:
        try:
            # Улучшенные заголовки для обхода блокировок на Kwork/Habr
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8'
            }
            response = requests.get(feed_info["url"], headers=headers, timeout=15)
            # Принудительная расшифровка контента для корректного парсинга
            feed = feedparser.parse(response.content if response.status_code == 200 else response.text)
            
            for entry in feed.entries[:25]:
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
    
    # 2. Сбор с HeadHunter
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
    """Фоновый процесс автоматического мониторинга всех источников"""
    print("[HUNTER] Автоматический мониторинг запущен", flush=True)
    while True:
        try:
            projects = fetch_orders()
            if projects:
                for p in projects:
                    msg = f"💎 **НОВЫЙ ЗАКАЗ!**\n\n📍 **{p['site']}** | {p['price']}\n_{p['title']}_\n🔗 [Открыть заказ]({p['url']})\n\n📝 **ОТКЛИК:**\n{p['offer']}\n\n{MY_CONTACTS}"
                    send_to_group(msg)
                    time.sleep(3)
        except Exception as e: 
            print(f"Hunter Error: {e}", flush=True)
        
        # Проверка каждые 15 минут для большей оперативности
        time.sleep(900)

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter онлайн! Используй /check для ручного поиска. Я автоматически проверяю все биржи и HH каждые 15 минут! 🌊")

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.send_chat_action(message.chat.id, 'typing')
    projects = fetch_orders(ignore_history=True)
    report = "🎯 **АКТУАЛЬНЫЙ УЛОВ (ВСЕ ПЛОЩАДКИ):**\n\n"
    if projects:
        # Сортируем так, чтобы разные площадки перемешивались
        random.shuffle(projects)
        for p in projects[:15]:
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
    print("[BOT] Запуск основного процесса Telegram...", flush=True)
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
