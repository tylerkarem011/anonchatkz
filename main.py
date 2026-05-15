import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)

TOKEN = "8963158327:AAEmhoMpLB0eJOaY90wAYq743Q5akKw3ZnM"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ===================== ДАННЫЕ =====================
users_in_chat = {}      
waiting_users = []      
user_gender = {}        
last_message_time = {}  
online_users = set()

GENDERS = {
    "male": "👦 Ер",
    "female": "👧 Әйел",
    "any": "🌐 Барлығы"
}

# ===================== КЛАВИАТУРА =====================
def gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👦 Ер"), KeyboardButton(text="👧 Әйел")],
            [KeyboardButton(text="🌐 Барлығы")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ===================== START =====================
@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    online_users.add(user_id)

    if user_id not in user_gender:
        await message.answer(
            "🇰🇿 <b>Отандық Анон Чат</b>\n\n"
            "Алдымен жынысыңды таңда:",
            reply_markup=gender_keyboard()
        )
    else:
        await show_main_menu(message)

async def show_main_menu(message: Message):
    await message.answer(
        f"🇰🇿 <b>Отандық Анон Чат</b>\n\n"
        f"Онлайн: <b>{len(online_users)}</b> адам\n\n"
        "/search — Әңгіме іздеу\n"
        "/next   — Келесі адам\n"
        "/stop   — Чатты тоқтату\n"
        "/gender — Жынысты өзгерту",
        reply_markup=ReplyKeyboardRemove()   # ← types жоқ, тек ReplyKeyboardRemove
    )
# ===================== GENDER =====================
@dp.message(Command("gender"))
async def set_gender(message: Message):
    await message.answer("Жынысыңды таңда:", reply_markup=gender_keyboard())

@dp.message(lambda m: m.text in ["👦 Ер", "👧 Әйел", "🌐 Барлығы"])
async def handle_gender_choice(message: Message):
    user_id = message.from_user.id
    if "Ер" in message.text:
        user_gender[user_id] = "male"
    elif "Әйел" in message.text:
        user_gender[user_id] = "female"
    else:
        user_gender[user_id] = "any"
    
    await message.answer(f"✅ Жынысың сақталды: <b>{GENDERS[user_gender[user_id]]}</b>", 
                        reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message)

# ===================== SEARCH & STOP =====================
@dp.message(Command("search", "next"))
async def search(message: Message):
    user_id = message.from_user.id
    online_users.add(user_id)

    if user_id not in user_gender:
        await message.answer("Алдымен жынысыңды таңда!", reply_markup=gender_keyboard())
        return

    # Егер чатта болса — тоқтатамыз
    if user_id in users_in_chat:
        partner = users_in_chat[user_id]
        await bot.send_message(partner, "❌ Алдыңғы әңгіме тоқтатылды.")
        users_in_chat.pop(partner, None)
        users_in_chat.pop(user_id, None)

    # Күтіп тұрғандардан шығару
    waiting_users[:] = [w for w in waiting_users if w["id"] != user_id]

    my_pref = user_gender.get(user_id, "any")

    # Іздеу
    for waiting in waiting_users[:]:
        if waiting["id"] == user_id:
            continue
        partner_pref = waiting["pref"]
        if my_pref == "any" or partner_pref == "any" or my_pref == partner_pref:
            partner_id = waiting["id"]
            waiting_users.remove(waiting)
            
            users_in_chat[user_id] = partner_id
            users_in_chat[partner_id] = user_id
            
            await bot.send_message(partner_id, "✅ <b>Әңгіме табылды!</b>\nЖаза бастаңыз...")
            await message.answer("✅ <b>Әңгіме табылды!</b>\nЖаза бастаңыз...")
            return

    waiting_users.append({"id": user_id, "pref": my_pref})
    await message.answer("🔍 <b>Әңгіме ізделуде...</b>")

@dp.message(Command("stop"))
async def stop(message: Message):
    user_id = message.from_user.id
    
    if user_id in users_in_chat:
        partner = users_in_chat[user_id]
        await bot.send_message(partner, "❌ Әңгіме аяқталды.")
        users_in_chat.pop(user_id, None)
        users_in_chat.pop(partner, None)
        await message.answer("✅ Чат тоқтатылды.")
    else:
        waiting_users[:] = [w for w in waiting_users if w["id"] != user_id]
        await message.answer("❌ Іздеуден шықтың.")

# ===================== МЕДИА ЖІБЕРУ =====================
@dp.message()
async def handle_all_messages(message: Message):
    user_id = message.from_user.id
    current_time = datetime.now()

    # Анти-флуд
    if user_id in last_message_time and current_time - last_message_time[user_id] < timedelta(seconds=1.3):
        return
    last_message_time[user_id] = current_time

    if user_id not in users_in_chat:
        if message.text and not message.text.startswith('/'):
            await message.answer("Әңгіме табу үшін /search немесе /next басыңыз.")
        return

    partner_id = users_in_chat[user_id]

    try:
        if message.text:
            await bot.send_message(partner_id, message.text)

        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)

        elif message.video:
            await bot.send_video(partner_id, message.video.file_id, caption=message.caption, supports_streaming=True)

        elif message.video_note:
            await bot.send_video_note(partner_id, message.video_note.file_id)

        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)

        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)

        elif message.animation:
            await bot.send_animation(partner_id, message.animation.file_id, caption=message.caption)

        elif message.document:
            await bot.send_document(partner_id, message.document.file_id, caption=message.caption)

        else:
            await bot.send_message(partner_id, message.text or "Қолдау көрсетілмейтін файл")

        print(f"✅ Жіберілді {message.content_type} → {partner_id}")

    except Exception as e:
        print(f"❌ Қате: {e}")
        await message.answer("❌ Жіберу кезінде қате шықты.\n/stop → /next")

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Отандық Анон Чат Боты іске қосылды!")
    await dp.start_polling(bot)

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Отандық Анон Чат Боты іске қосылды!")
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
