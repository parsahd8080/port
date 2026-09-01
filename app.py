# ریشه اصلی ربات وریتی
import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# ================================================
# 🔑 توکن‌ها از متغیرهای محیطی
# ================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN تنظیم نشده!")
    exit(1)

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY تنظیم نشده!")
    exit(1)

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ================================================
# 👑 اطلاعات مود
# ================================================
CREATOR = "@AghaBanafshii"
CREATOR_NAME = "آقا بنفشی"

MOD_LINKS = {
    "curseforge": "https://www.curseforge.com/minecraft/mc-mods/verity-je",
    "modrinth": "https://modrinth.com/project/on1Y0osD"
}

# ================================================
# کانال های عضویت اجباری
# ================================================
REQUIRED_CHANNELS = [
    {"id": 4467089778, "username": "verityir1"},
    {"id": 6184186116, "username": "verity_bot"}
]

# ================================================
# 📁 حافظه (ذخیره در Railway Volume یا حافظه موقت)
# ================================================
MEMORY_DIR = os.getenv("MEMORY_DIR", "/app/data")  # مسیر Volume
MEMORY_FILE = os.path.join(MEMORY_DIR, "verity_memory.json")

# اگر پوشه ای وجود نداشت، بساز
if not os.path.exists(MEMORY_DIR):
    os.makedirs(MEMORY_DIR, exist_ok=True)

def load_data():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}, "chat_history": {}, "verified_users": {}, "processed": {}}
    return {"users": {}, "chat_history": {}, "verified_users": {}, "processed": {}}

def save_data(data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================================================
# 📤 توابع بله
# ================================================
def api_request(method, data=None):
    try:
        url = f"{BASE_URL}/{method}"
        response = requests.post(url, json=data or {}, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def send_message(chat_id, text, reply_markup=None, reply_to=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    if reply_markup:
        data["reply_markup"] = reply_markup
    return api_request("sendMessage", data)

def get_chat_member(chat_id, user_id):
    return api_request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

def get_chat_type(chat_id):
    result = api_request("getChat", {"chat_id": chat_id})
    if result and result.get('ok'):
        return result.get('result', {}).get('type', 'unknown')
    return 'unknown'

def get_user_name(user_id, msg=None):
    try:
        if msg:
            from_user = msg.get('from', {})
            first_name = from_user.get('first_name', '')
            if first_name:
                return first_name
        
        data = load_data()
        if "users" in data and str(user_id) in data["users"]:
            return data["users"][str(user_id)].get("name")
        
        result = api_request("getUserInfo", {"user_id": user_id})
        if result and result.get('ok'):
            user = result.get('result', {})
            first_name = user.get('first_name', '')
            if first_name:
                data = load_data()
                if "users" not in data:
                    data["users"] = {}
                data["users"][str(user_id)] = {"name": first_name}
                save_data(data)
                return first_name
        
        return None
    except:
        return None

def save_user_name(user_id, name):
    data = load_data()
    if "users" not in data:
        data["users"] = {}
    data["users"][str(user_id)] = {"name": name}
    save_data(data)

# ================================================
# 🔍 بررسی عضویت
# ================================================
def check_membership(user_id):
    results = {}
    all_member = True
    
    for channel in REQUIRED_CHANNELS:
        channel_id = channel["id"]
        channel_username = channel["username"]
        
        result = get_chat_member(channel_id, user_id)
        
        if result and result.get('ok'):
            member_data = result.get('result', {})
            status = member_data.get('status', 'left')
            is_member = status in ['member', 'creator', 'administrator']
            results[channel_username] = is_member
            if not is_member:
                all_member = False
        else:
            results[channel_username] = False
            all_member = False
    
    return all_member, results

# ================================================
# 🎨 دکمه شیشه‌ای
# ================================================
def get_join_button():
    return {
        "inline_keyboard": [
            [
                {"text": "✅ عضو شدم", "callback_data": "check_join"}
            ]
        ]
    }

# ================================================
# 🧠 دریافت پاسخ از AI
# ================================================
def get_ai_response(user_id, message, history, user_name=None, chat_type="private"):
    try:
        if str(user_id) not in history:
            history[str(user_id)] = []
        
        creator = CREATOR
        cf_link = MOD_LINKS["curseforge"]
        mr_link = MOD_LINKS["modrinth"]
        
        # پرامپت کامل
        system_prompt = f"""شما **وریتی** هستید، یک دستیار هوشمند و دوستانه.

**هویت شما:**
- اسم شما وریتی (Verity) است
- شما یک ربات هوش مصنوعی هستید که با OpenRouter AI ساخته شده‌اید
- شما توسط **{creator}** (با نام واقعی {CREATOR_NAME}) ساخته شده‌اید
- شما یک مود ماینکرفت به اسم **Verity JE** هستید که برای نسخه جاوا ساخته شده

**اطلاعات مود شما:**
- نام مود: Verity JE
- لینک کرس‌فورج: {cf_link}
- لینک مادرینث: {mr_link}
- این مود یک یار کمک‌کننده به اسم وریتی به بازی اضافه می‌کند

**شخصیت شما:**
- همیشه دوستانه، مهربان و مفید هستید
- با لحن صمیمی و با ایموجی پاسخ می‌دهید
- پاسخ‌ها را مختصر و به زبان فارسی می‌دهید
- اگر کاربر ناراحت است، او را آرام می‌کنید
- اگر سوالی تخصصی است، پاسخ علمی و دقیق می‌دهید"""

        if user_name:
            system_prompt += f"\n- نام کاربری که با شما صحبت می‌کند {user_name} است. همیشه با نام {user_name} خطابش کنید."

        if chat_type == "group":
            system_prompt += "\n- شما در یک گروه هستید. پاسخ‌ها را عمومی‌تر و مناسب برای همه اعضا بدهید."

        system_prompt += """

**پاسخ‌های مهم و دقیق:**
- اگر کسی گفت "وریتی تو ماینکرفتی؟" یا "وریتی تو داخل ماینکرفتی؟" → بگو: "آره! من وریتی هستم و یک مود ماینکرفت به اسم Verity JE هستم! داخل بازی می‌توانید من را پیدا کنید! 😊"
- اگر کسی گفت "توسط کی ساخته شدی؟" یا "سازنده‌ات کیه؟" → بگو: "من توسط {creator} ساخته شده‌ام! ایشون یک برنامه‌نویس و توسعه‌دهنده ربات هستن! 🧠"
- اگر کسی گفت "مودتو بده" یا "لینک مودت رو بده" → بگو: "باشه بفرما:
دانلود از کرس فورج : {cf_link}
دانلود از مادرینث : {mr_link}"
- اگر کسی گفت "وریتی چیه؟" → بگو: "وریتی اسم من است! من یک دستیار هوشمند هستم که با OpenRouter AI ساخته شده‌ام. همچنین یک مود ماینکرفت به اسم Verity JE هستم! 💖"
- اگر کسی گفت "تو کی هستی؟" → بگو: "من وریتی هستم، یک دستیار هوشمند و یک مود ماینکرفت! توسط {creator} ساخته شده‌ام! 😊"
- اگر کسی گفت "وریتی" → بگو: "بله، من وریتی هستم! چطور می‌توانم کمک کنم؟" """.format(
    creator=creator,
    cf_link=cf_link,
    mr_link=mr_link
)
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[str(user_id)][-10:]:
            messages.append(msg)
        messages.append({"role": "user", "content": message})
        
        response = requests.post(OPENROUTER_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": "openai/gpt-4o-mini", "messages": messages, "temperature": 0.7, "max_tokens": 500},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_msg = data.get('choices', [{}])[0].get('message', {}).get('content', "")
            
            if ai_msg:
                history[str(user_id)].append({"role": "user", "content": message})
                history[str(user_id)].append({"role": "assistant", "content": ai_msg})
                all_data = load_data()
                all_data["chat_history"] = history
                save_data(all_data)
                return ai_msg
        
        return "متأسفانه پاسخ دریافت نشد! دوباره تلاش کنید."
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return "خطا در اتصال به هوش مصنوعی!"

# ================================================
# ✅ بررسی و پاسخ به دکمه
# ================================================
def check_and_respond(chat_id, user_id, user_name, data):
    all_member, results = check_membership(user_id)
    
    if all_member:
        msg = f"""✅ {user_name} عزیز!

تبریک! شما در همه کانال‌ها عضو شده‌اید. 🎉

🧠 حالا می‌توانید هر سوالی از من بپرسید.
💬 فقط کافی است پیام خود را بفرستید.
🎮 اگر می‌خواهید لینک مود من رو بگیرید، بگید "مودتو بده".

💖 خوشحالم که اینجایی!"""
        
        send_message(chat_id, msg)
        
        if "verified_users" not in data:
            data["verified_users"] = {}
        data["verified_users"][str(user_id)] = True
        save_data(data)
        
    else:
        not_member = [ch for ch, is_mem in results.items() if not is_mem]
        msg = f"""❌ {user_name} عزیز!

شما هنوز در همه کانال‌ها عضو نشده‌اید.

📌 کانال‌هایی که عضو نیستید:
"""
        for ch in not_member:
            msg += f"   • @{ch}\n"
        
        msg += "\n✅ لطفاً ابتدا عضو شوید و سپس دوباره روی دکمه کلیک کنید."
        
        send_message(chat_id, msg, get_join_button())
    
    return data

# ================================================
# 🎯 پردازش پیام
# ================================================
def process_message(chat_id, msg, data):
    text = msg.get('text', '').strip()
    sender_id = msg.get('from', {}).get('id', '')
    msg_id = msg.get('message_id', '')
    
    if not text:
        return data
    
    chat_type = get_chat_type(chat_id)
    is_group = chat_type in ['group', 'supergroup']
    is_private = chat_type == 'private'
    
    key = f"{chat_id}_{msg_id}"
    if key in data.get("processed", {}):
        return data
    if "processed" not in data:
        data["processed"] = {}
    data["processed"][key] = datetime.now().isoformat()
    save_data(data)
    
    user_name = get_user_name(sender_id, msg)
    if user_name:
        save_user_name(sender_id, user_name)
    else:
        user_name = "کاربر عزیز"
    
    print(f"👤 {user_name} ({sender_id}) - نوع چت: {chat_type}")
    
    # ===== اگر گروه است =====
    if is_group:
        if "وریتی" not in text:
            return data
        clean_text = text.replace("وریتی", "").strip()
        if not clean_text:
            clean_text = "سلام"
        
        history = data.get("chat_history", {})
        response = get_ai_response(sender_id, clean_text, history, user_name, "group")
        data["chat_history"] = history
        save_data(data)
        send_message(chat_id, response)
        return data
    
    # ===== اگر چت خصوصی است =====
    if not is_private:
        return data
    
    print("🔒 چت خصوصی - بررسی عضویت...")
    
    # ===== /start =====
    if text == "/start":
        welcome = f"""👋 سلام {user_name} عزیز!

من **وریتی** هستم، یک دستیار هوشمند و یک مود ماینکرفت! 🧠🎮

📌 **برای استفاده از من در چت خصوصی، باید در کانال‌های زیر عضو شوید:**

🔹 @verityir1
🔹 @verity_bot

✅ بعد از عضویت، روی دکمه **"عضو شدم"** کلیک کنید.

💡 بعد از تأیید، می‌توانید:
• هر سوالی بپرسید
• لینک مود من رو بگیرید
• درباره ماینکرفت صحبت کنید

💖 منتظر شما هستم!"""
        
        send_message(chat_id, welcome, get_join_button())
        return data
    
    # ===== بررسی عضویت (دکمه شیشه‌ای) =====
    if text == "/check":
        return check_and_respond(chat_id, sender_id, user_name, data)
    
    # ===== راهنما =====
    if "راهنما" in text or "help" in text.lower():
        help_text = f"""📖 **راهنما**

سلام {user_name} عزیز! من وریتی هستم.

**برای استفاده در چت خصوصی:**
1️⃣ در کانال‌های زیر عضو شوید:
   • @verityir1
   • @verity_bot

2️⃣ روی دکمه **"عضو شدم"** کلیک کنید

**بعد از تأیید می‌توانید:**
• هر سوالی بپرسید
• بگید "مودتو بده" تا لینک مود رو بگیرید
• درباره ماینکرفت سوال کنید

**ساخته شده توسط:** {CREATOR} 🧠""".format(CREATOR=CREATOR)
        
        send_message(chat_id, help_text)
        return data
    
    # ===== بررسی عضویت قبل از پاسخ =====
    all_member, results = check_membership(sender_id)
    
    if not all_member:
        not_member = [ch for ch, is_mem in results.items() if not is_mem]
        msg = f"""❌ {user_name} عزیز!

شما هنوز در همه کانال‌ها عضو نشده‌اید.

📌 کانال‌هایی که عضو نیستید:
"""
        for ch in not_member:
            msg += f"   • @{ch}\n"
        
        msg += "\n✅ لطفاً ابتدا عضو شوید و سپس روی دکمه **'عضو شدم'** کلیک کنید."
        
        send_message(chat_id, msg, get_join_button())
        return data
    
    # ===== پردازش پیام عادی =====
    clean_text = text
    if not clean_text:
        clean_text = "سلام"
    
    print(f"📝 {clean_text}")
    
    # ===== پاک کردن =====
    if "پاک کردن" in clean_text:
        if str(sender_id) in data.get("chat_history", {}):
            data["chat_history"][str(sender_id)] = []
            save_data(data)
            send_message(chat_id, f"🧹 تاریخچه شما پاک شد {user_name}!")
        return data
    
    # ===== پاسخ =====
    history = data.get("chat_history", {})
    response = get_ai_response(sender_id, clean_text, history, user_name, "private")
    data["chat_history"] = history
    save_data(data)
    
    send_message(chat_id, response)
    return data

# ================================================
# 🔄 پردازش دکمه شیشه‌ای
# ================================================
def process_callback(callback, data):
    callback_data = callback.get('data', '')
    chat_id = callback.get('message', {}).get('chat', {}).get('id')
    user_id = callback.get('user', {}).get('id', '')
    callback_id = callback.get('id')
    user_name = callback.get('user', {}).get('first_name', 'کاربر')
    
    api_request("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": "✅ در حال بررسی..."
    })
    
    if callback_data == "check_join":
        return check_and_respond(chat_id, user_id, user_name, data)
    
    return data

# ================================================
# 🌐 Webhook Flask
# ================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.json
        data = load_data()
        
        if 'message' in update:
            msg = update['message']
            chat_id = msg.get('chat', {}).get('id')
            data = process_message(chat_id, msg, data)
        
        if 'callback_query' in update:
            data = process_callback(update['callback_query'], data)
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "🤖 Verity Bot is running!"

# ================================================
# 🚀 تنظیم Webhook در بله
# ================================================
def set_webhook():
    railway_url = os.getenv("RAILWAY_STATIC_URL")
    if not railway_url:
        print("⚠️ RAILWAY_STATIC_URL تنظیم نشده! Webhook تنظیم نمی‌شود.")
        return
    
    webhook_url = f"https://{railway_url}/webhook"
    response = api_request("setWebhook", {"url": webhook_url})
    
    if response and response.get('ok'):
        print(f"✅ Webhook تنظیم شد: {webhook_url}")
    else:
        print(f"❌ خطا در تنظیم Webhook: {response}")

# ================================================
# 🚀 اجرا
# ================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ربات وریتی - نسخه Webhook")
    print(f"👑 سازنده: {CREATOR}")
    print("=" * 60)
    
    # تنظیم Webhook در استارت
    set_webhook()
    
    # اجرای Flask
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
