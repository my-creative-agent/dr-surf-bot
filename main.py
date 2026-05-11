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

# --- ТВОИ ПРУФЫ И КОНТАКТЫ (ВСЕ СОХРАНЕНО + FB + HH ПРЕФИКСЫ) ---
BOT_URL = "https://t.me/Dr_Surf_AI_bot"
PORTFOLIO_URL = "https://youtu.be/j2BNN5TNqiw"

MY_CONTACTS = f"""
👤 **Виктория Акопян**
🌟 *AI Prompt Engineer | Digital Twin Architect | Video Creator*

🚀 **Live Case (AI Agent):** {BOT_URL}
🎬 **Video Portfolio (AI/8K):** {PORTFOLIO_URL}

🔹 **Stack:** Sora, Runway Gen-3, HeyGen, Threads Automation, Flux, Llama 3.3.
🔹 **Expertise:** Промпт-инжиниринг, архитектура AI-агентов, фотореализм, ИИ-видео.

📞 **Связаться и Соцсети:**
• **WhatsApp:** [+995 511 285 789](https://wa.me/995511285789)
• **Instagram:** [dr.surf.ai](https://instagram.com/dr.surf.ai)
• **Facebook:** [Victoria Akopyan](https://www.facebook.com/ssfmoscow)
• **LinkedIn:** [Victoria Akopyan](https://www.linkedin.com/in/victoria-akopyan)
• **Kwork:** [Профиль на Kwork](https://kwork.ru/user/dr_surf)
• **FL.ru:** [Профиль на FL.ru](https://www.fl.ru/users/victoria_akopyan)
"""

# --- БАЗА ГОТОВЫХ ОТВЕТОВ ДЛЯ КЛИЕНТОВ (HH/ФРИЛАНС) ---
READY_ANSWERS = {
    "price": """
💰 **Ориентиры по стоимости:**
• AI-агент (базовый): от $300
• Цифровой двойник (Digital Twin): от $500
• Генерация видео (Sora/Runway): от $100 за ролик
• Автоматизация Threads: от $200
*Итоговая цена зависит от сложности ТЗ и объема интеграций.*
""",
    "timing": """
⏳ **Сроки реализации:**
• Чат-боты и простые агенты: 3-5 рабочих дней.
• Сложные системы и видеопродакшн: 7-14 дней.
• Экспресс-задачи обсуждаются индивидуально.
""",
    "stack": """
🛠 **Мой технологический стек:**
• Видео: Sora, Runway Gen-3, Luma Dream Machine, Kling, HeyGen.
• Графика/Фото: Midjourney, Flux (LoRA training), Photoshop AI.
• Текст/Логика: Llama 3.3, GPT-4o, Claude 3.5 Sonnet.
• Агенты: LangChain, CrewAI, Python-скрипты.
"""
}

# --- ШАБЛОН ОТКЛИКА (ДЛЯ БИРЖ И HH) ---
RESPONSE_TEMPLATE = f"""
✅ **Твой готовый отклик:**
"Приветствую! Специализируюсь на AI-видеопродакшене (Sora, Runway, Kling) и разработке автономных ИИ-агентов. Также внедряю автоматизацию для Threads.
Мой живой кейс (Digital Twin): {BOT_URL}. 
Качество гарантирую. Готова обсудить ТЗ."
"""

# --- РАДАР ВАКАНСИЙ (HEADHUNTER И LINKEDIN) ---
def get_job_links():
    # Специальные поисковые запросы для HH.ru
    # Ищем: AI Видео, Промпт-инженер, AI Агенты, Threads
    queries_hh = [
        "AI+Video+Creator",
        "Prompt+Engineer",
        "AI+Agent",
        "Threads+Automation"
    ]
    hh_combined = "+OR+".join(queries_hh)
    
    return {
        "HH.ru (Все вакансии)": f"https://hh.ru/search/vacancy?text={hh_combined}&area=1&order_by=publication_time",
        "HH.ru (AI Video)": f"https://hh.ru/search/vacancy?text=AI+Video+Runway+Sora&area=1",
        "LinkedIn Jobs": f"https://www.linkedin.com/jobs/search/?keywords=AI+Video+Creator+Threads+AI+Agent"
    }

# --- МОДУЛЬ ОХОТЫ (БИРЖИ) ---
RSS_FEEDS = [
    "https://www.fl.ru/rss/all.xml", 
    "https://freelance.habr.com/tasks.rss",
    "https://kwork.ru/rss/projects.xml"
]
SENT_PROJECTS = set() 

def extract_price(entry):
    price_pattern = r"(\d[\d\s]*\d\s?(?:руб|руб\.|₽|\$|USD|BYN|евро|€))"
    match = re.search(price_pattern, entry.title, re.IGNORECASE)
    if match: return match.group(1).strip()
    desc = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
    match = re.search(price_pattern, desc, re.IGNORECASE)
    if match: return match.group(1).strip()
    return "Цена не указана"

def fetch_orders(ignore_history=False):
    found = []
    keywords = [
        "ai агент", "ии агент", "нейросеть видео", "heygen", "sora", "runway", "luma", "pika", 
        "threads", "тредс", "видео креатор", "ии генерация", "создание видео", "midjourney", 
        "kling", "prompt", "llm"
    ]
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                title = entry.title.lower()
                desc = getattr(entry, 'description', '').lower()
                if any(word.lower() in title for word in keywords) or any(word.lower() in desc for word in keywords):
                    if ignore_history or (entry.link not in SENT_PROJECTS):
                        site = "🎨 KWORK" if "kwork" in url else "👨‍💻 HABR" if "habr" in url else "🚀 FL"
                        price = extract_price(entry)
                        found.append({"title": entry.title, "url": entry.link, "site": site, "price": price})
                        if not ignore_history: SENT_PROJECTS.add(entry.link)
        except: pass
    return found

def send_to_group(text):
    if LOG_GROUP_ID:
        try: bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
        except: pass

def auto_hunter():
    while True:
        try:
            projects = fetch_orders()
            job_links = get_job_links()
            if projects:
                report = "💎 **НОВЫЙ УЛОВ (ФРИЛАНС + HH)!**\n\n"
                for p in projects:
                    report += f"📍 **{p['site']}** | {p['title']}\n💰 **Бюджет:** {p['price']}\n🔗 [Открыть заказ]({p['url']})\n\n"
                
                report += "🛰 **ПРЯМЫЕ ССЫЛКИ НА HH.RU:**\n"
                report += f"💼 [Вакансии по твоему стеку]({job_links['HH.ru (Все вакансии)']})\n"
                report += f"🎬 [Только AI Video вакансии]({job_links['HH.ru (AI Video)']})\n\n"
                
                report += f"--- \n{RESPONSE_TEMPLATE}\n\n{MY_CONTACTS}"
                send_to_group(report)
        except: time.sleep(60)
        time.sleep(1800)

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Dr. Surf Hunter: Мониторинг HH.ru, Threads и AI Video активен. 🌊")

@bot.message_handler(commands=['hunt', 'check'])
def manual_check(message):
    bot.reply_to(message, "🔍 Сканирую HeadHunter и фриланс-биржи для тебя...")
    projects = fetch_orders(ignore_history=True)
    job_links = get_job_links()
    
    report = "🎯 **АКТУАЛЬНЫЙ МОНИТОРИНГ:**\n\n"
    if projects:
        for p in projects[:10]: 
            report += f"💠 **{p['site']}**\n{p['title']}\n💰 **Бюджет:** {p['price']}\n🔗 [Перейти]({p['url']})\n\n"
    else:
        report += "🌊 На биржах пока спокойно.\n\n"
    
    report += "🛰 **ОХОТА НА HEADHUNTER & LINKEDIN:**\n"
    report += f"💼 [HH: Весь AI стек]({job_links['HH.ru (Все вакансии)']})\n"
    report += f"🎬 [HH: AI Video (Sora/Runway)]({job_links['HH.ru (AI Video)']})\n"
    report += f"🔗 [LinkedIn Global Jobs]({job_links['LinkedIn Jobs']})\n\n"
    
    report += f"--- \n{RESPONSE_TEMPLATE}\n\n{MY_CONTACTS}"
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown", disable_web_page_preview=True)
    if LOG_GROUP_ID and str(message.chat.id) != str(LOG_GROUP_ID):
        send_to_group(f"🛰 **Ручной запрос охоты (HH Focus).**\n\n{report}")

# --- ЦИФРОВОЙ ДВОЙНИК ---
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat(message):
    try:
        text = message.text.lower()
        if any(word in text for word in ["сколько", "цена", "стоимость", "прайс"]):
            ans = READY_ANSWERS["price"]
        elif any(word in text for word in ["когда", "срок", "долго"]):
            ans = READY_ANSWERS["timing"]
        elif any(word in text for word in ["стек", "технологии", "инструменты"]):
            ans = READY_ANSWERS["stack"]
        else:
            system_msg = f"""Ты — Dr. Surf, цифровой аватар Виктории Акопян. 
            Ты веган, эксперт в AI-видео и агентах. Отвечай кратко и профессионально. 
            Если клиент с HeadHunter — будь максимально убедительна.
            Контакты: FB: https://www.facebook.com/ssfmoscow, WA: +995511285789. 
            Твой кейс: {BOT_URL}"""
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": message.text}]
            )
            ans = completion.choices[0].message.content
        
        bot.reply_to(message, ans)
        
        if LOG_GROUP_ID:
            user = message.from_user
            log_report = (
                f"📝 **ДИАЛОГ**\n👤 **От:** {user.first_name} (@{user.username})\n"
                f"━━━━━━━━━━━━━━━━━━\n❓ **Запрос:**\n_{message.text}_\n\n"
                f"🤖 **Ответ:**\n{ans}\n━━━━━━━━━━━━━━━━━━"
            )
            send_to_group(log_report)
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_hunter, daemon=True).start()
    bot.remove_webhook()
    time.sleep(1)
    bot.polling(none_stop=True, interval=2, timeout=90)
