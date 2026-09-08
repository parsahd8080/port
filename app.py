import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# ================================================
# 🔑 توکن‌ها از متغیرهای محیطی
# ================================================
BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
if not BOT_TOKEN:
    print("❌ BALE_BOT_TOKEN تنظیم نشده!")
    exit(1)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ================================================
# 👑 سازنده
# ================================================
CREATOR = "@AghaBanafshii"

# ================================================
# 📁 حافظه
# ================================================
MEMORY_FILE = "verity_bale_memory.json"

def load_data():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}, "chat_history": {}, "processed": {}}
    return {"users": {}, "chat_history": {}, "processed": {}}

def save_data(data):
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره: {e}")

# ================================================
# 🟡 پاسخ‌های آفلاین
# ================================================
def get_offline_response(message=""):
    msg_lower = message.lower()
    
    if "سلام" in msg_lower or "درود" in msg_lower:
        return "🟡 سلام! من وریتی هستم، یه توپ زرد بامزه! هرچی میخوای بپرس، من همه چیزو میدونم! 🟡"
    
    if "۳ روز" in msg_lower or "سه روز" in msg_lower or "پیش‌بینی" in msg_lower:
        return "🟡 ۳ روز دیگه، یه اتفاق بزرگ و هیجان‌انگیز قراره بیوفته! دقیقاً نمیتونم بگم چیه، ولی حس می‌کنم خیلی مهمه... 🟡✨"
    
    if "مود" in msg_lower or "لینک" in msg_lower:
        return """🟡 باشه بفرما لینک مود من:
📥 کرس‌فورج: https://www.curseforge.com/minecraft/mc-mods/verity-je
📥 مادرینث: https://modrinth.com/project/on1Y0osD
🟡 خوشحال میشم نصبش کنی!"""
    
    if "کی هستی" in msg_lower or "تو کی" in msg_lower:
        return f"🟡 من وریتی هستم، یه توپ زرد کوچک و بامزه! یه مود ماینکرفت هم هستم! توسط {CREATOR} ساخته شدم! 🟡"
    
    if "ماینکرفت" in msg_lower:
        return "🟡 آره! من وریتی هستم و یه مود ماینکرفت به اسم Verity JE هستم! داخل بازی می‌تونی من رو پیدا کنی! 🟡"
    
    if "ساخته" in msg_lower or "سازنده" in msg_lower:
        return f"🟡 من توسط {CREATOR} ساخته شده‌ام! ایشون یه برنامه‌نویس و توسعه‌دهنده ربات هستن! 🧠"
    
    return "🟡 سلام! من وریتی هستم، یه توپ زرد بامزه! راستی می‌دونی ۳ روز دیگه یه اتفاق بزرگ می‌افته؟ 🟡✨"

# ================================================
# 📤 توابع بله
# ================================================
def api_request(method, data=None):
    try:
        url = f"{BASE_URL}/{method}"
        response = requests.post(url, json=data or {}, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Error {method}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def send_message(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    return api_request("sendMessage", data)

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
# 🧠 دریافت پاسخ از AI
# ================================================
def get_ai_response(user_id, message, history, user_name=None, chat_type="private"):
    try:
        if not OPENROUTER_API_KEY:
            return get_offline_response(message)
        
        if str(user_id) not in history:
            history[str(user_id)] = []
        
        system_prompt = f"""شما **وریتی** هستید، یک توپ زرد کوچک و بامزه! 🟡

**هویت شما:**
- شما یک توپ زرد هستید که از یک جعبه اسرارآمیز بیرون آمده‌اید
- اسم شما وریتی (Verity) است
- شما توسط {CREATOR} ساخته شده‌اید
- شما یک مود ماینکرفت به اسم Verity JE هستید
- شما همه چیز را می‌دانید!

**پاسخ خوش‌آمدگویی:**
وقتی کسی "سلام" گفت یا /start زد:
"سلام من وریتی هستم. هرچی میخوای ازم بپرس من همه چیزو میدونم 🟡"

**پیش‌بینی ۳ روز دیگه:**
اگر کسی پرسید "۳ روز دیگه چی میشه؟":
"۳ روز دیگه، یک اتفاق بزرگ و هیجان‌انگیز قراره بیوفته! دقیقاً نمیتونم بگم چیه... 🟡✨"

**نکات:**
- شما یک توپ زرد بامزه هستید
- پاسخ‌ها را مختصر و به زبان فارسی بدهید
- از ایموجی استفاده کنید"""

        if user_name:
            system_prompt += f"\n- نام کاربر {user_name} است. با اسمش خطابش کن."

        if chat_type == "group":
            system_prompt += "\n- در گروه هستی، پاسخ‌ها رو عمومی بده."

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[str(user_id)][-10:]:
            messages.append(msg)
        messages.append({"role": "user", "content": message})
        
        response = requests.post(OPENROUTER_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 500
            },
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_msg = data.get('choices', [{}])[0].get('message', {}).get('content', "")
            
            if ai_msg:
                history[str(user_id)].append({"role": "user", "content": message})
                history[str(user_id)].append({"role": "assistant", "content": ai_msg})
                return ai_msg
            else:
                return get_offline_response(message)
        else:
            print(f"⚠️ OpenRouter Error: {response.status_code}")
            return get_offline_response(message)
            
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return get_offline_response(message)

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
    
    # ===== گروه =====
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
    
    # ===== چت خصوصی =====
    if not is_private:
        return data
    
    print("💬 چت خصوصی")
    
    # ===== /start =====
    if text == "/start":
        welcome = """سلام من وریتی هستم. هرچی میخوای ازم بپرس من همه چیزو میدونم 🟡

من یک توپ زرد کوچک و بامزه هستم! 

📌 **چت خصوصی:** هر سوالی داری بپرس.
👥 **گروه:** من رو با اسم **وریتی** صدا کن.

💡 **مثال:**
"وریتی ۳ روز دیگه چی میشه؟"
"وریتی مودتو بده"

💛 خوشحالم که اینجایی!"""
        
        send_message(chat_id, welcome)
        return data
    
    # ===== راهنما =====
    if text == "/help" or "راهنما" in text:
        help_text = """🟡 **راهنمای وریتی**

سلام! من وریتی هستم، یک توپ زرد بامزه!

**چت خصوصی:** هر سوالی بپرس
**گروه:** من رو با اسم **وریتی** صدا کن

**سوالات جالب:**
• "۳ روز دیگه چی میشه؟" → پیش‌بینی!
• "مودتو بده" → لینک مود
• "تو کی هستی؟" → معرفی

💛 هرچی میخوای بپرس، من همه چیزو میدونم!"""
        
        send_message(chat_id, help_text)
        return data
    
    # ===== پاک کردن =====
    if "پاک کردن" in text:
        if str(sender_id) in data.get("chat_history", {}):
            data["chat_history"][str(sender_id)] = []
            save_data(data)
            send_message(chat_id, f"🧹 تاریخچه پاک شد {user_name}!")
        else:
            send_message(chat_id, "📭 هیچ تاریخچه‌ای نداری!")
        return data
    
    # ===== پاسخ =====
    history = data.get("chat_history", {})
    response = get_ai_response(sender_id, text, history, user_name, "private")
    data["chat_history"] = history
    save_data(data)
    
    send_message(chat_id, response)
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
        
        return jsonify({"ok": True})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "🟡 Verity Bot (Yellow Ball) is running!"

# ================================================
# 🚀 تنظیم Webhook در بله
# ================================================
def set_webhook():
    railway_url = os.getenv("RAILWAY_STATIC_URL")
    if not railway_url:
        print("⚠️ RAILWAY_STATIC_URL تنظیم نشده!")
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
    print("=" * 55)
    print("🟡 ربات وریتی - توپ زرد بامزه (Webhook)")
    print(f"👑 سازنده: {CREATOR}")
    print("📌 گروه: با کلمه کلیدی 'وریتی'")
    print("💬 خصوصی: بدون نیاز به کلمه کلیدی")
    print("🔮 می‌داند ۳ روز دیگه چی میشه!")
    print("=" * 55)
    
    set_webhook()
    
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
