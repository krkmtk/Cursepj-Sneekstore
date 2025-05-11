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
            InlineKeyboardButton(text="В наявності", callback_data="available"),
            InlineKeyboardButton(text="Скоро прибудуть", callback_data="coming_soon")
        ],
        [InlineKeyboardButton(text="Відгуки", callback_data="reviews")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Невідомий користувач"
    logger.info(f"Користувач {username} (ID: {user_id}) запустил бота")

    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    
    try:
        # Надсилаємо фото з текстом і клавіатурою
        await message.answer_photo(
            photo=FSInputFile(photo_filename),
            caption="🖐️Вітаю в магазині Sbeekstore",
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
@dp.callback_query(F.data == "available")
async def process_available(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'В наявності'")
    await callback_query.answer("Товари в наявності")

@dp.callback_query(F.data == "coming_soon")
async def process_coming_soon(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Скоро прибудуть'")
    await callback_query.answer("Товари скоро прибудуть")

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
