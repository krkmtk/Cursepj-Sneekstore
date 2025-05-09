from aiogram import Router, types
from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "👋 Привет! Я готов к работе.\n"
        "Список команд: /help"
    )

@router.message(Command(commands={"help"}))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        "/start — приветствие\n"
        "/help — справка\n"
        "Напишите что‑нибудь, и я повторю это."
    )

@router.message()
async def echo_all(message: types.Message) -> None:
    if message.text:
        await message.answer(message.text)
