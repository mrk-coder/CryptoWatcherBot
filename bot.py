# bot.py

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import TELEGRAM_TOKEN
from handlers import start, tracking, admin
from database import init_db
from services.notifications import check_price_changes
from utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    try:
        init_db()
        
        # Добавляем параметры для бота
        bot = Bot(
            token=TELEGRAM_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        dp = Dispatcher()
        dp.include_routers(start.router, tracking.router, admin.router)

        # Запускаем фоновую задачу для проверки цен
        logger.info("Запуск фоновой задачи проверки цен...")
        asyncio.create_task(check_price_changes(bot))
        
        logger.info("Бот запущен")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
