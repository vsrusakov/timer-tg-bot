import logging
from typing import Dict, Optional
from datetime import timedelta
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters.command import CommandStart, CommandObject, Command


# Настройка логирования
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Глобальная структура для хранения активных таймеров
active_timers: Dict[int, asyncio.Task] = {}
lock = asyncio.Lock()

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def notify_user(chat_id: int):
    await bot.send_message(chat_id, "Время вышло!")

def parse_timer_argument(argument: str) -> Optional[int]:
    """Парсим строку аргумента типа '10m' или '60s'"""
    if argument.endswith('m'):
        minutes = float(argument[:-1])
        return int(minutes * 60)
    elif argument.endswith('s'):
        seconds = float(argument[:-1])
        return int(seconds)
    else:
        log.error(f"Неверный формат аргумента '{argument}'")
        return None

@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("Привет! Я умею устанавливать таймеры.\n"
                         "/timer 10m — установить таймер на 10 минут\n"
                         "/cancel — отменить текущий таймер.")

@dp.message(Command("timer"))
async def timer_command(message: Message, command: CommandObject):
    chat_id = message.chat.id
    
    # Проверяем наличие аргументов
    args = command.args.strip()
    if not args:
        await message.reply("Ошибка: не указан интервал времени. Используйте формат '/timer 10m'.")
        return
    
    duration_seconds = parse_timer_argument(args)
    if duration_seconds is None or duration_seconds <= 0:
        await message.reply("Ошибка: неверный формат интервала времени.")
        return
    
    async with lock:
        existing_task = active_timers.pop(chat_id, None)
        if existing_task:
            existing_task.cancel()
        
        task = asyncio.create_task(notify_after_timeout(chat_id, duration_seconds))
        active_timers[chat_id] = task
    
    await message.reply(f"Таймер на {args} установлен.")

@dp.message(Command("cancel"))
async def cancel_command(message: Message):
    chat_id = message.chat.id
    
    async with lock:
        task = active_timers.pop(chat_id, None)
        if task:
            task.cancel()
            await message.reply("Таймер отменён.")
        else:
            await message.reply("Нет активного таймера.")

async def notify_after_timeout(chat_id: int, timeout: int):
    try:
        await asyncio.sleep(timeout)
        await notify_user(chat_id)
    except asyncio.CancelledError:
        pass

if __name__ == '__main__':
    dp.run_polling(bot)
