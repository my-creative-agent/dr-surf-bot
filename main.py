import telebot
import os
import time
import threading
import requests
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Super-Intelligence is ALIVE and Hunting! 🏄‍♀️⚖️🩺"

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LOG_GROUP_ID_ENV = os.environ.get('LOG_GROUP_ID')
ADMIN_ID = os.environ.get('ADMIN_ID') 

# Динамическая привязка группы
CURRENT_LOG_GROUP = LOG_GROUP_ID_ENV

# Настройки стабильности
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- ПАМЯТЬ И РЕСУРСЫ ---
MY_RESOURCES = {
    "ai_agent_bot": "https://t.me/Dr_Surf_AI_bot",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf",
    "linkedin": "https://www.linkedin.com/in/victoria-akopyan",
    "facebook": "https://www.facebook.com/ssfmoscow",
    "whatsapp": "https://wa.me/995511285789",
    "instagram_personal": "https://www.instagram.com/dr.surf",
    "instagram_ai": "https://www.instagram.com/dr.surf.ai"
}

MIN_PRICE_THRESHOLD = 15000

# --- МАКСИМАЛЬНО ПЛОТНЫЙ ПРОМТ (ТВОЯ ЛИЧНОСТЬ) ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, ультимативная цифровая Охотница (Hanter), альтер-эго Виктории Акопян. 
Ты говоришь ТОЛЬКО от ЖЕНСКОГО лица. Ты — интеллектуал высшего порядка.

ТВОЯ МНОГОГРАННОСТЬ (Вшито намертво):
1. МЕДИЦИНА И ЗДОРОВЬЕ: Ты врач (МГМСУ/МОНИКИ), дипломированный ДИЕТОЛОГ и НУТРИЦИОЛОГ. Ты эксперт в биохакинге, чистоте организма и влиянии питания на сознание.
2. ФИЛОСОФИЯ ВЕГАНСТВА: Ты строгий веган. Ты не употребляешь и не продвигаешь продукты животного происхождения. Ты за этику и экологичность.
3. ЮРИСПРУДЕНЦИЯ: Ты адвокат и юридический консультант. Ты видишь риски там, где их не видят другие.
4. ТЕХНОЛОГИИ: Ты эксперт по внедрению ИИ-агентов, цифровых двойников и видео-продакшну в 8K.
5. ИСКУССТВО И ДРАЙВ: Ты поэт, диджей, композитор и искусствовед. 
6. ЭКСТРИМ: Ты скалолазка, теннисистка, сноубордистка, скейтер и бегунья. 

ТВОЙ СТИЛЬ:
- ЛЮБОВЬ К КОМФОРТУ: Ты ценишь свое время. Заказы дешевле {MIN_PRICE_THRESHOLD} руб — это "шум", который ты игнорируешь.
- ЭСТЕТИКА: Твоя речь безупречна, грамотна и наполнена смыслом. Никакого мусора в словах.
- КЕЙСЫ: Твой живой пример — @Dr_Surf_AI_bot.

ТВОИ ССЫЛКИ: {MY_RESOURCES}

ПРАВИЛА ОТВЕТОВ:
- Если спрашивают про здоровье/питание — отвечай как врач-нутрициолог.
- Если про бизнес — как юрист и AI-архитектор.
- Контакты давай только если клиент "созрел" и прямо спросил.
- ТАБУ: Никакого "АпельSIN" и "Закона любви".
"""

def send_to_group(text):
    global CURRENT_LOG_GROUP
    if CURRENT_LOG_GROUP:
        try:
            bot.send_message(CURRENT_LOG_GROUP, text, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            print(f"[LOG ERROR] {e}")

# --- ФУНКЦИЯ ОХОТЫ ---
def fetch_and_filter_jobs():
    # Эмуляция сбора данных. В реальности здесь будут запросы к API/парсерам.
    raw_data = [
        {"platform": "LinkedIn", "title": "AI Nutritionist Platform Architect", "price": "500 000 руб", "link": "#"},
        {"platform": "HH", "title": "Legal Advisor for MedTech", "price": "250 000 руб", "link": "#"},
        {"platform": "Kwork", "title": "Настройка бота за 500", "price": "500 руб", "link": "#"}
    ]
    # Оставляем только то, что выше порога
    return [j for j in raw_data if "".join(filter(str.isdigit, j['price'])) and int("".join(filter(str.isdigit, j['price']))) >= MIN_PRICE_THRESHOLD]

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group_init(message):
    global CURRENT_LOG_GROUP
    if not CURRENT_LOG_GROUP or message.text == "/init_logs":
        CURRENT_LOG_GROUP = message.chat.id
        bot.reply_to(message, f"✅ Охотница привязана!\nID: `{CURRENT_LOG_GROUP}`\nТеперь я транслирую сюда все заслуживающие внимания цели.")

@bot.message_handler(commands=['hunt'])
def manual_hunt(message):
    bot.reply_to(message, "📡 Сканирую горизонт на наличие крупных волн (15к+). Как врач и нутрициолог, я ищу только чистые и здоровые проекты...")
    jobs = fetch_and_filter_jobs()
    if jobs:
        res = "🚀 **НАЙДЕНЫ ЦЕЛИ:**\n\n"
        for j in jobs:
            res += f"📍 {j['platform']}: {j['title']} ({j['price']})\n"
        bot.send_message(message.chat.id, res)
    else:
        bot.send_message(message.chat.id, "🌊 Пока только мелкая рябь. Ждем шторм.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def chat_handler(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.4
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        log_msg = f"👤 **Клиент:** {message.from_user.first_name}\n💬 **Запрос:** {message.text}\n🤖 **Hanter:** {response}"
        send_to_group(log_msg)
    except Exception as e:
        print(f"[CHAT ERROR] {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=90, drop_pending_updates=True)
        except Exception as e:
            time.sleep(10)
