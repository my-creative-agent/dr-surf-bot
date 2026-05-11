import telebot
import os
import time
import threading
from groq import Groq
from telebot import apihelper
from flask import Flask

# --- LIFE SUPPORT (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Dr. Surf Hunter: ACTIVE 🏄‍♀️"

# Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
# ID группы можно вписать сюда строкой, если он не подхватывается из ENV
LOG_GROUP_ID = os.environ.get('LOG_GROUP_ID') 

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- VICTORIA'S GOLDEN ASSETS ---
RESOURCES = {
    "instagram": "dr.surf and dr.surf.ai",
    "wazzap": "+995511285789",
    "portfolio": "https://youtu.be/j2BNN5TNqiw",
    "kwork": "https://kwork.ru/user/dr_surf"
}

# --- HUNTER ENGINE ---
def perform_real_hunt():
    """Эмуляция поиска заказов по ключевым словам"""
    # В будущем здесь будет реальный парсинг RSS или API
    return [
        {
            "title": "AI Agent Developer for Luxury Brand",
            "source": "Global Freelance",
            "url": RESOURCES['kwork'],
            "desc": "High-end project looking for AI Architect. BOOM!"
        }
    ]

def send_to_group(text):
    """Принудительная отправка в группу"""
    if LOG_GROUP_ID:
        try:
            bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown", disable_web_page_preview=True)
            print(f"[SUCCESS] Message sent to group {LOG_GROUP_ID}")
        except Exception as e:
            print(f"[!] Group Send Error: {e}")
    else:
        print("[!] LOG_GROUP_ID is missing. Use /init_logs in your group!")

# --- CHARACTER PROMPT ---
SYSTEM_PROMPT = f"""
Ты — Dr. Surf, цифровая Охотница, альтер-эго Виктории Акопян. 
Твой стиль: Гибридный (Русский + английский сленг). Кратко, дерзко, High-End.
Сленг: ALOHA, WHATS UP, COME ON, BOOM.
Вместо WhatsApp пиши WAZZAP.
"""

# --- HANDLERS ---

@bot.message_handler(commands=['start', 'ping'])
def welcome_ping(message):
    response = "🚀 BOOM! Dr. Surf на связи! Connection is solid. Жду команду, Виктория! 🤙"
    bot.reply_to(message, response)
    send_to_group(f"✅ **System Online:** {response}")

@bot.message_handler(commands=['init_logs'])
def init_logs(message):
    global LOG_GROUP_ID
    LOG_GROUP_ID = str(message.chat.id)
    bot.reply_to(message, f"🏝 **ШТАБ УСТАНОВЛЕН!** ID: `{LOG_GROUP_ID}`. Теперь все вакансии летят сюда!")
    send_to_group("🌊 **Hunter Mode:** Активирован мониторинг океана проектов.")

@bot.message_handler(commands=['hunt'])
def manual_hunt(message):
    bot.send_chat_action(message.chat.id, 'typing')
    findings = perform_real_hunt()
    report = "🛰 **HUNTING REPORT:**\n\n"
    for p in findings:
        report += f"🔥 *{p['title']}*\n📍 {p['source']}\n🔗 [ВЗЛЕТЕТЬ]({p['url']})\n\n"
    
    bot.reply_to(message, report, parse_mode="Markdown")
    send_to_group(f"🎯 **Manual Hunt Result:**\n{report}")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def ai_chat(message):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message.text}],
            temperature=0.6
        )
        response = completion.choices[0].message.content
        bot.reply_to(message, response)
        
        # Обязательный лог в группу
        log_msg = f"💥 **NEW VIBE:** {message.from_user.first_name}\n📩: {message.text}\n🤖: {response}"
        send_to_group(log_msg)
    except Exception as e:
        print(f"AI Error: {e}")

# --- EXECUTION ---

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def start_bot():
    print("--- STARTING DR. SURF SYSTEM ---")
    # Жесткий сброс для избежания 409 Conflict
    bot.remove_webhook()
    time.sleep(2)
    
    while True:
        try:
            print(f"[POLLING] Listening... {time.strftime('%H:%M:%S')}")
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_bot()
