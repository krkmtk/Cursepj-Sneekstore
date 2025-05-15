import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from config import get_settings

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

settings = get_settings()

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Створення inline-клавіатури
def get_keyboard():
    kb = [
        [
            InlineKeyboardButton(text="Купити", callback_data="buy"),
            InlineKeyboardButton(text="Аккаунт", callback_data="account")
        ],
        [InlineKeyboardButton(text="Розмірна сітка", callback_data="reviews")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard

def get_buy_menu():
    kb = [
        [
            InlineKeyboardButton(text="1", callback_data="buy_1"),
            InlineKeyboardButton(text="2", callback_data="buy_2"),
            InlineKeyboardButton(text="3", callback_data="buy_3")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Невідомий користувач"
    logger.info(f"Користувач {username} (ID: {user_id}) запустив бота")

    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    
    try:
        # Надсилаємо фото з текстом і клавіатурою
        await message.answer_photo(
            photo=FSInputFile(photo_filename),
            caption="🖐️Вітаю в магазині Sneekstore",
            reply_markup=get_keyboard()
        )
    except Exception as e:
        # Якщо виникла помилка (наприклад, файл не знайдено), надсилаємо лише текст
        logger.error(f"Помилка зображення: {e}")
        await message.answer(
            "🖐️Вітаю в магазині Sneekstore",
            reply_markup=get_keyboard()
        )

# Заглушки для обробки натискань на кнопки
@dp.callback_query(F.data == "buy")
async def process_buy(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Купити'")
    # Видаляємо повідомлення з картинкою та меню
    await callback_query.message.delete()
    # Надсилаємо нове меню з кнопками 1, 2, 3
    await callback_query.message.answer(
        "Меню покупки:",
        reply_markup=get_buy_menu()
    )
    await callback_query.answer()

@dp.callback_query(F.data.in_(["buy_1", "buy_2", "buy_3"]))
async def process_buy_number(callback_query):
    number = callback_query.data.split("_")[1]
    await callback_query.answer(f"Ви обрали {number}")

@dp.callback_query(F.data == "account")
async def process_account(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Аккаунт'")
    await callback_query.answer("Ваш аккаунт")

@dp.callback_query(F.data == "reviews")
async def process_reviews(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Відгуки'")
    await callback_query.answer("Відгуки")

# Запуск бота
async def main():
    bot_info = await bot.get_me()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
