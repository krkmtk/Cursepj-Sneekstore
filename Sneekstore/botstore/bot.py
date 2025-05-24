import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from config import get_settings
from help_text import HELP_TEXT

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

settings = get_settings()

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Список брендів та моделей
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
        [
            InlineKeyboardButton(text="Розмірна сітка", callback_data="sizing"),
            InlineKeyboardButton(text="Допомога", callback_data="help"),
            InlineKeyboardButton(text="Зв'язатися з нами", callback_data="contact")
        ]
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

def get_sizing_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_help_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_contact_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_account_menu():
    kb = [
        [InlineKeyboardButton(text="Поповнити баланс", callback_data="topup_balance")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_topup_menu():
    kb = [
        [
            InlineKeyboardButton(text="Поповнити криптовалютою", callback_data="topup_crypto"),
            InlineKeyboardButton(text="Поповнити картою", callback_data="topup_card")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="account")]
    ]
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
        await callback_query.message.delete()
    except Exception:
        pass
    # Додаткова перевірка: чи файл існує і чи це дійсно зображення (jpg/png)
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
    await callback_query.answer()
    await callback_query.message.delete()
    photo_filename = "Sneekstore/botstore/coverimage.jpg"
    await callback_query.message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption="🖐️Вітаю в магазині Sneekstore",
        reply_markup=get_keyboard()
    )

@dp.callback_query(F.data.in_(["buy_1", "buy_2", "buy_3"]))
async def process_buy_number(callback_query):
    number = callback_query.data.split("_")[1]
    await callback_query.answer(f"Ви обрали {number}")

@dp.callback_query(F.data == "account")
async def process_account(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Аккаунт'")
    # Фіктивні дані, замініти коли бдха буде
    balance = 0
    purchases = 0
    status = "Новий користувач"
    await callback_query.message.delete()
    await callback_query.message.answer(
        f"👤 <b>Ваш аккаунт</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Username: @{username}\n"
        f"Баланс: <b>{balance} грн</b>\n"
        f"Кількість покупок: <b>{purchases}</b>\n"
        f"Статус: <b>{status}</b>",
        parse_mode="HTML",
        reply_markup=get_account_menu()
    )

@dp.callback_query(F.data == "topup_balance")
async def process_topup_balance(callback_query):
    await callback_query.answer()
    await callback_query.message.delete()
    await callback_query.message.answer(
        "💳 <b>Оберіть спосіб поповнення балансу:</b>",
        parse_mode="HTML",
        reply_markup=get_topup_menu()
    )

@dp.callback_query(F.data == "topup_crypto")
async def process_topup_crypto(callback_query):
    await callback_query.answer()
    await callback_query.message.delete()
    await callback_query.message.answer(
        "🪙 <b>Поповнення криптовалютою</b>\n\n"
        "Для поповнення криптовалютою зверніться до адміністратора або отримайте адресу для переказу.\n\n"
        "<i>Після поповнення балансу протягом 30 хвилин гроші з'являться на вашому балансі.</i>",
        parse_mode="HTML",
        reply_markup=get_topup_menu()
    )

@dp.callback_query(F.data == "topup_card")
async def process_topup_card(callback_query):
    await callback_query.answer()
    await callback_query.message.delete()
    await callback_query.message.answer(
        "💳 <b>Поповнення картою</b>\n\n"
        "Для поповнення картою скористайтесь інструкціями на сайті або зверніться до адміністратора.\n\n"
        "<i>Після поповнення балансу протягом 30 хвилин гроші з'являться на вашому балансі.</i>",
        parse_mode="HTML",
        reply_markup=get_topup_menu()
    )

@dp.callback_query(F.data == "sizing")
async def process_sizing(callback_query):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Невідомий користувач"
    logger.info(f"Пользователь {username} (ID: {user_id}) натиснув 'Розмірна сітка'")
    photo_filename = "Sneekstore/botstore/sizing.jpg"
    await callback_query.message.delete()
    await callback_query.message.answer_photo(
        photo=FSInputFile(photo_filename),
        caption="Розмірна сітка",
        reply_markup=get_sizing_menu()
    )
    await callback_query.answer()

@dp.callback_query(F.data == "help")
async def process_help(callback_query):
    await callback_query.answer()
    await callback_query.message.delete()
    await callback_query.message.answer(
        HELP_TEXT,
        reply_markup=get_help_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "contact")
async def process_contact(callback_query):
    await callback_query.answer()
    await callback_query.message.answer(
        "📞 <b>Зв'язатися з нами</b>\n\nНапишіть нам у Telegram: @vktrysn",
        parse_mode="HTML",
        reply_markup=get_contact_menu()
    )

# Запуск бота
async def main():
    bot_info = await bot.get_me()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
