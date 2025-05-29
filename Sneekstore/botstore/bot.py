import asyncio
import os
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage

# Додаємо шлях для імпорту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from help_text import HELP_TEXT
from db import Database
from account import register_account_handlers, get_account_menu

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Ініціалізація бота
bot = Bot(token=settings.bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Ініціалізація бази даних
db = Database(
    host="localhost",
    port=3306,
    user="root", 
    password="20066002vV",
    db="cursepj_db"
)

# Бренди та моделі
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

# Реалістичні ціни на кросівки для кожного бренду та моделі
PRICES = {
    "Nike": {
        "Air Max": 4200,
        "Air Force": 3600,
        "Dunk": 4300,
        "Blazer": 3200,
        "React HyperSet": 4600
    },
    "Adidas": {
        "Ultraboost": 4800,
        "Forum": 3500,
        "Superstar": 2800,
        "Stan Smith": 2600,
        "Gazelle": 2700
    },
    "Puma": {
        "Suede": 2400,
        "RS-X": 3400,
        "Cali": 2800,
        "Future Rider": 3000,
        "Rider FV": 3200
    },
    "Reebok": {
        "Classic": 2200,
        "Club C": 2600,
        "Nano": 3800,
        "Zig Dynamica": 3400,
        "Floatride": 4000
    },
    "New Balance": {
        "574": 3200,
        "997": 4800,
        "990": 5600,
        "1080": 5000,
        "327": 4000
    },
    "Vans": {
        "Old Skool": 2300,
        "Sk8-Hi": 2500,
        "Authentic": 2100,
        "Era": 2200,
        "Slip-On": 2000
    },
    "Converse": {
        "Chuck 70": 2500,
        "All Star": 2000,
        "Run Star": 2900,
        "One Star": 2400,
        "Pro Leather": 2700
    }
}

# Головна клавіатура
def get_keyboard():
    kb = [
        [
            InlineKeyboardButton(text="Купити", callback_data="buy"),
            InlineKeyboardButton(text="Аккаунт", callback_data="account")
        ],
        [
            InlineKeyboardButton(text="Розмірна сітка", callback_data="sizing"),
            InlineKeyboardButton(text="Допомога", callback_data="help"),
            InlineKeyboardButton(text="Підтримка", callback_data="contact")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    return keyboard

# Клавіатура покупки
def get_buy_menu():
    kb = [
        [
            InlineKeyboardButton(text="1", callback_data="buy_1"),
            InlineKeyboardButton(text="2", callback_data="buy_2"),
            InlineKeyboardButton(text="3", callback_data="buy_3")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавіатура брендів
def get_brands_menu():
    kb = [[InlineKeyboardButton(text=brand, callback_data=f"brand_{brand}")] for brand in BRANDS]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавіатура моделей
def get_models_menu(brand):
    kb = [[InlineKeyboardButton(text=model, callback_data=f"model_{brand}_{model}")] for model in MODELS[brand]]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_brands")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавіатура розмірів
def get_sizes_menu(brand, model):
    sizes = [str(size) for size in range(36, 46)]
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

# Клавіатура розмірної сітки
def get_sizing_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавіатура допомоги
def get_help_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавіатура контактів
def get_contact_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Команда старт
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Невідомий користувач"
    logger.info(f"Користувач {username} (ID: {user_id}) запустив бота")

    # Створюємо користувача в базі даних
    await db.create_user(user_id, username)

    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    
    await message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption=f"🖐️ Вітаю, <b>{username}</b>!\n\n🛍️ Ласкаво просимо до Sneekstore — твій особистий магазин стильного взуття",
        reply_markup=get_keyboard(),
        parse_mode="HTML"
    )

# Обробник покупки
@dp.callback_query(F.data == "buy")
async def process_buy(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Користувач {username} (ID: {user_id}) натиснув 'Купити'")
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        "Оберіть бренд:",
        reply_markup=get_brands_menu()
    )
    await callback_query.answer()

# Обробник вибору бренду
@dp.callback_query(F.data.startswith("brand_"))
async def process_brand(callback_query):
    brand = callback_query.data.split("_", 1)[1]
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        f"Оберіть модель {brand}:",
        reply_markup=get_models_menu(brand)
    )
    await callback_query.answer()

# Обробник вибору моделі
@dp.callback_query(F.data.startswith("model_"))
async def process_model(callback_query):
    _, brand, model = callback_query.data.split("_", 2)
    photo_filename = f"Sneekstore/botstore/models/{brand}_{model}.jpg"
    price = PRICES.get(brand, {}).get(model, 3000)  # Отримуємо реалістичну ціну для моделі
    caption = f"Ви обрали: {brand} {model}\nЦіна: {price} грн\nОберіть розмір:"
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    # Перевіряємо файл зображення
    # Важливо: Називайте файли у форматі "Бренд_Модель.jpg", наприклад "Nike_Air Force.jpg"
    if os.path.exists(photo_filename) and photo_filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        try:
            await callback_query.message.answer_photo(
                photo=FSInputFile(photo_filename),
                caption=caption,
                reply_markup=get_sizes_menu(brand, model)
            )
        except Exception:
            await callback_query.message.answer(
                caption + "\n\n⚠️ Не вдалося завантажити зображення. Перевірте, що файл дійсно є зображенням (jpg/png) і не пошкоджений.",
                reply_markup=get_sizes_menu(brand, model)
            )
    else:
        await callback_query.message.answer(
            caption + "\n\n⚠️ Не вдалося завантажити зображення. Файл не знайдено або не є зображенням.",
            reply_markup=get_sizes_menu(brand, model)
        )
    await callback_query.answer()

# Повернення до моделей
@dp.callback_query(F.data.startswith("back_to_models_"))
async def back_to_models(callback_query):
    brand = callback_query.data.split("_", 3)[3]
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        f"Оберіть модель {brand}:",
        reply_markup=get_models_menu(brand)
    )
    await callback_query.answer()

# Повернення до брендів
@dp.callback_query(F.data == "back_to_brands")
async def back_to_brands(callback_query):
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        "Оберіть бренд:",
        reply_markup=get_brands_menu()
    )
    await callback_query.answer()

# Повернення до головного меню
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback_query):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    username = callback_query.from_user.username or callback_query.from_user.first_name or "Невідомий користувач"
    
    await callback_query.message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption=f"🖐️ Вітаю, <b>{username}</b>!\n\n🛍️ Ласкаво просимо до Sneekstore — твій особистий магазин стильного взуття",
        reply_markup=get_keyboard(),
        parse_mode="HTML"
    )

# Обробник покупки за номером
@dp.callback_query(F.data.in_(["buy_1", "buy_2", "buy_3"]))
async def process_buy_number(callback_query):
    number = callback_query.data.split("_")[1]
    await callback_query.answer(f"Ви обрали {number}")

# Розмірна сітка
@dp.callback_query(F.data == "sizing")
async def process_sizing(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Користувач {username} (ID: {user_id}) натиснув 'Розмірна сітка'")
    photo_filename = "Sneekstore/botstore/sizing.jpg"
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption="Розмірна сітка",
        reply_markup=get_sizing_menu()
    )
    await callback_query.answer()

# Допомога
@dp.callback_query(F.data == "help")
async def process_help(callback_query):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        HELP_TEXT,
        reply_markup=get_help_menu(),
        parse_mode="HTML"
    )

# Контакти
@dp.callback_query(F.data == "contact")
async def process_contact(callback_query):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.message.answer(
        "📞 <b>Зв'язатися з нами</b>\n\nНапишіть нам у Telegram: @vktrysn",
        parse_mode="HTML",
        reply_markup=get_contact_menu()
    )

# Обробник вибору розміру та покупки
@dp.callback_query(F.data.startswith("size_"))
async def process_size(callback_query):
    _, brand, model, size = callback_query.data.split("_", 3)
    price = PRICES.get(brand, {}).get(model, 3000)  # Отримуємо реалістичну ціну для моделі
    user_id = callback_query.from_user.id
    
    # Обробляємо покупку
    purchase_result = await db.process_purchase(user_id, brand, model, size, price)
    
    if purchase_result["success"]:
        final_price = float(purchase_result["final_price"])
        
        await callback_query.answer("✅ Покупка успішно здійснена!")
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(
            f"🎉 <b>Вітаємо з покупкою!</b>\n\n"
            f"📦 <b>Деталі замовлення:</b>\n"
            f"👟 Товар: {brand} {model}\n"
            f"📏 Розмір: {size}\n"
            f"💰 Ціна: <b>{final_price:.0f} грн</b>\n\n"
            f"👨‍💼 <b>Наступні кроки:</b>\n"
            f"• Незабаром з вами зв'яжеться адміністратор\n"
            f"• Ми уточнимо деталі доставки\n"
            f"• Очікуваний час доставки: 1-3 дні\n\n"
            f"📞 Якщо у вас є питання, звертайтеся: @vktrysn\n\n"
            f"🙏 Дякуємо за покупку в Sneekstore!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main")],
                [InlineKeyboardButton(text="👤 Мій аккаунт", callback_data="account")]
            ])
        )
    else:
        # Недостатньо коштів
        account = await db.get_account(user_id)
        balance = float(account['balance'])
        
        await callback_query.answer("❌ Недостатньо коштів на балансі!")
        await callback_query.message.answer(
            f"❌ <b>Недостатньо коштів</b>\n\n"
            f"Ціна товару: {price} грн\n"
            f"Ваш баланс: {balance:.0f} грн\n"
            f"Необхідно доплатити: {price - balance:.0f} грн",
            parse_mode="HTML",
            reply_markup=get_account_menu()
        )

# Запуск бота
async def main():
    try:
        # Підключаємося до бази даних
        await db.connect()
        logger.info("✅ Підключення до бази даних успішно встановлено")
        
        # Реєструємо обробники аккаунту
        register_account_handlers(dp, db, bot)
        
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот {bot_info.first_name} запущено")
        
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Помилка при запуску бота: {e}")
    finally:
        # Закриваємо з'єднання
        if db.pool:
            await db.close()
            logger.info("🔌 З'єднання з базою даних закрито")
        
        await bot.session.close()
        logger.info("🤖 Сесію бота закрито")

if __name__ == "__main__":
    asyncio.run(main())
