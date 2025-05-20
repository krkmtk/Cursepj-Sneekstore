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

# Список брендов та моделей
BRANDS = [
    "Nike", "Adidas", "Puma", "Reebok", "New Balance", "Vans", "Converse"
]
MODELS = {
    "Nike": ["Air Max", "Air Force", "Dunk", "Blazer", "React HyperSet"],
    "Adidas": ["Ultraboost", "Forum", "Superstar", "Stan Smith", "Gazelle"],
    "Puma": ["Suede", "RS-X", "Cali", "Future Rider", "Rider FV"],
    "Reebok": ["Classic", "Club C", "Nano", "Zig Dynamica", "Floatride"],
    "New Balance": ["574", "997", "990", "1080", "327"],
    "Vans": ["Old Skool", "Sk8-Hi", "Authentic", "Era", "Slip-On"],
    "Converse": ["Chuck 70", "All Star", "Run Star", "One Star", "Pro Leather"]
}

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

def get_brands_menu():
    kb = [[InlineKeyboardButton(text=brand, callback_data=f"brand_{brand}")] for brand in BRANDS]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_models_menu(brand):
    kb = [[InlineKeyboardButton(text=model, callback_data=f"model_{brand}_{model}")] for model in MODELS[brand]]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_brands")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_sizes_menu(brand, model):
    sizes = [str(size) for size in range(36, 46)]  # розміри 36-45
    kb = []
    row = []
    for i, size in enumerate(sizes, 1):
        row.append(InlineKeyboardButton(text=size, callback_data=f"size_{brand}_{model}_{size}"))
        if i % 5 == 0:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_models_{brand}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Невідомий користувач"
    logger.info(f"Користувач {username} (ID: {user_id}) запустив бота")

    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    
    await message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption="🖐️Вітаю в магазині Sneekstore",
        reply_markup=get_keyboard()
    )

# Заглушки для обробки натискань на кнопки
@dp.callback_query(F.data == "buy")
async def process_buy(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Купити'")
    await callback_query.message.delete()
    await callback_query.message.answer(
        "Оберіть бренд:",
        reply_markup=get_brands_menu()
    )
    await callback_query.answer()

@dp.callback_query(F.data.startswith("brand_"))
async def process_brand(callback_query):
    brand = callback_query.data.split("_", 1)[1]
    await callback_query.message.delete()
    await callback_query.message.answer(
        f"Оберіть модель {brand}:",
        reply_markup=get_models_menu(brand)
    )
    await callback_query.answer()

@dp.callback_query(F.data.startswith("model_"))
async def process_model(callback_query):
    _, brand, model = callback_query.data.split("_", 2)
    photo_filename = f"Sneekstore/botstore/models/{brand}_{model}.jpg"
    caption = f"Ви обрали: {brand} {model}\nОберіть розмір:"
    try:
        if os.path.exists(photo_filename):
            await callback_query.message.delete()
            await callback_query.message.answer_photo(
                photo=FSInputFile(photo_filename),
                caption=caption,
                reply_markup=get_sizes_menu(brand, model)
            )
        else:
            raise FileNotFoundError
    except Exception:
        await callback_query.message.delete()
        await callback_query.message.answer(
            caption,
            reply_markup=get_sizes_menu(brand, model)
        )
    await callback_query.answer()

@dp.callback_query(F.data.startswith("back_to_models_"))
async def back_to_models(callback_query):
    brand = callback_query.data.split("_", 3)[3]
    await callback_query.message.delete()
    await callback_query.message.answer(
        f"Оберіть модель {brand}:",
        reply_markup=get_models_menu(brand)
    )
    await callback_query.answer()

@dp.callback_query(F.data == "back_to_brands")
async def back_to_brands(callback_query):
    await callback_query.message.delete()
    await callback_query.message.answer(
        "Оберіть бренд:",
        reply_markup=get_brands_menu()
    )
    await callback_query.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback_query):
    await callback_query.message.delete()
    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    await callback_query.message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption="🖐️Вітаю в магазині Sneekstore",
        reply_markup=get_keyboard()
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
