import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

TOKEN = "8814020140:AAFzbm_HBgIkROX14pszw-mVehm3dsX3obc"

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

# ===================== КЛАВИАТУРЫ =====================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать диалог")],
            [KeyboardButton(text="🔍 Поиск по полу")]
        ],
        resize_keyboard=True
    )

# ===================== START =====================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🇰🇿 <b>INTC Anonymous Chat</b>\n\n"
        "Қош келдіңіз!\n\n"
        "Төмендегі кнопкаларды пайдаланыңыз 👇",
        reply_markup=main_menu()
    )

# ===================== SEARCH =====================
@dp.message(Command("search", "next"))
@dp.message(lambda m: m.text == "🚀 Начать диалог")
async def search(message: Message):
    user_id = message.from_user.id

    if user_id in users_in_chat:
        partner = users_in_chat[user_id]
        await bot.send_message(partner, "❌ Собеседник закончил с вами связь 😔\nНапишите /search чтобы найти следующего")
        users_in_chat.pop(partner, None)
        users_in_chat.pop(user_id, None)

    waiting_users[:] = [w for w in waiting_users if w["id"] != user_id]

    if waiting_users:
        waiting = waiting_users.pop(0)
        partner_id = waiting["id"]

        users_in_chat[user_id] = partner_id
        users_in_chat[partner_id] = user_id

        success_text = (
            "✅ <b>Собеседник найден</b>\n\n"
            "/next — искать нового\n"
            "/stop — закончить диалог\n"
            "/link — отправить ссылку на профиль"
        )

        await bot.send_message(partner_id, success_text)
        await message.answer(success_text)
        return

    waiting_users.append({"id": user_id, "pref": user_gender.get(user_id, "any")})
    await message.answer("🔍 <b>Ищем собеседника...</b>\nКүте тұрыңыз.")

# ===================== STOP =====================
@dp.message(Command("stop"))
async def stop(message: Message):
    user_id = message.from_user.id
    if user_id in users_in_chat:
        partner = users_in_chat[user_id]
        await bot.send_message(partner, "❌ <b>Собеседник закончил с вами связь</b> 😔\n\nНапишите /search чтобы найти следующего")
        users_in_chat.pop(user_id, None)
        users_in_chat.pop(partner, None)
        await message.answer("✅ <b>Чат аяқталды</b>\n\nНапишите /search чтобы найти нового собеседника", reply_markup=main_menu())
    else:
        await message.answer("Сіз қазір ешкіммен сөйлеспейсіз.", reply_markup=main_menu())

# ===================== LINK =====================
@dp.message(Command("link"))
async def send_link(message: Message):
    user_id = message.from_user.id
    if user_id not in users_in_chat:
        await message.answer("❌ Вы сейчас не в чате.")
        return

    if not message.from_user.username:
        await message.answer("❌ У вас нет username. Установите @юзернейм в настройках профиля.")
        return

    partner_id = users_in_chat[user_id]
    link = f"https://t.me/{message.from_user.username}"
    
    await bot.send_message(partner_id, f"🔗 Собеседник отправил свою ссылку:\n\n{link}")
    await message.answer("✅ Ссылка отправлена собеседнику.")

# ===================== ОБРАБОТКА СООБЩЕНИЙ =====================
@dp.message()
async def handle_all_messages(message: Message):
    user_id = message.from_user.id
    current_time = datetime.now()

    if user_id in last_message_time and current_time - last_message_time[user_id] < timedelta(seconds=1):
        return
    last_message_time[user_id] = current_time

    if user_id not in users_in_chat:
        if message.text and not message.text.startswith('/'):
            await message.answer("Нажмите «🚀 Начать диалог»", reply_markup=main_menu())
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
    except:
        pass

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 INTC Anon Chat успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())