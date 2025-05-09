import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import get_settings
from handlers import basic  # our first router

async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN not found. Put it into .env or environment variable.")

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(basic.router)  # register router

    await dp.start_polling(bot)  # long‑polling

if __name__ == "__main__":
    asyncio.run(main())
