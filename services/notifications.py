# services/notifications.py

import asyncio
from aiogram import Bot
from database import get_users_with_settings, set_tracking, get_tracking
from services.crypto_api import get_crypto_price
from utils.logger import get_logger

logger = get_logger(__name__)

async def check_price_changes(bot: Bot):
    """Фоновая задача для проверки изменений цен"""
    while True:
        try:
            # Получаем всех пользователей с настройками
            users_data = get_users_with_settings()
            logger.info(f"Проверка цен для {len(users_data)} записей")
            
            # Группируем данные по пользователям
            user_tracking = {}
            for row in users_data:
                user_id, username, interval, threshold, format_type, symbol, last_price = row
                if symbol:  # Только если есть отслеживаемые валюты
                    if user_id not in user_tracking:
                        user_tracking[user_id] = {
                            'username': username,
                            'interval': interval,
                            'threshold': float(threshold),  # Убедимся, что это float
                            'format': format_type,
                            'symbols': []
                        }
                    user_tracking[user_id]['symbols'].append((symbol, last_price))
            
            # Проверяем цены для каждого пользователя
            for user_id, user_data in user_tracking.items():
                try:
                    for symbol, last_price_db in user_data['symbols']:
                        current_price = await get_crypto_price(symbol)
                        if current_price:
                            # Обновляем цену в базе данных (только last_price)
                            set_tracking(user_id, symbol, current_price)
                            
                            # Проверяем изменение цены
                            if last_price_db is not None and last_price_db != '':
                                last_price = float(last_price_db)
                                if last_price != 0:
                                    change_percent = abs((current_price - last_price) / last_price) * 100
                                    logger.info(f"Проверка {symbol} для {user_id}: {last_price} -> {current_price} ({change_percent:.2f}%) Порог: {user_data['threshold']}%")
                                    
                                    # Используем пользовательский порог
                                    if change_percent >= user_data['threshold']:
                                        # Формируем уведомление в зависимости от формата
                                        message = format_notification(
                                            symbol, last_price, current_price, 
                                            change_percent, user_data['format']
                                        )
                                        
                                        try:
                                            await bot.send_message(
                                                chat_id=user_id,
                                                text=message,
                                                parse_mode="HTML"
                                            )
                                            logger.info(f"✅ Уведомление ОТПРАВЛЕНО пользователю {user_data['username']} ({user_id}) о изменении {symbol}")
                                        except Exception as e:
                                            logger.error(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
                                    else:
                                        logger.info(f"ℹ️ Изменение {symbol} для {user_id}: {change_percent:.2f}% (меньше порога {user_data['threshold']}%)")
                                else:
                                    logger.info(f"ℹ️ Нулевая цена для {symbol} пользователя {user_id}")
                            else:
                                logger.info(f"ℹ️ Нет предыдущей цены для {symbol} пользователя {user_id} (last_price_db: {last_price_db})")
                        else:
                            logger.error(f"❌ Не удалось получить цену для {symbol}")
                            
                except Exception as e:
                    logger.error(f"❌ Ошибка проверки цен для пользователя {user_id}: {e}")
            
            # Ждем 1 минуту перед следующей проверкой (минимальный интервал)
            logger.info("Ожидание 3 минуты до следующей проверки...")
            await asyncio.sleep(180)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в фоновой задаче проверки цен: {e}")
            await asyncio.sleep(180)

def format_notification(symbol, old_price, new_price, change_percent, format_type):
    """Форматирование уведомления в зависимости от выбранного формата"""
    change_symbol = "📈" if new_price > old_price else "📉"
    
    if format_type == 'compact':
        # Компактный формат
        return (
            f"{change_symbol} <b>{symbol}</b> ${new_price:.2f} "
            f"({change_symbol} {change_percent:.2f}%)"
        )
    elif format_type == 'detailed':
        # Подробный формат
        return (
            f"{change_symbol} <b>Изменение цены {symbol}</b>\n\n"
            f"💰 Предыдущая цена: <code>${old_price:.2f}</code>\n"
            f"💵 Текущая цена: <code>${new_price:.2f}</code>\n"
            f"📊 Изменение: <b>{change_symbol} {change_percent:.2f}%</b>\n"
            f"⏰ {get_time_string()}"
        )
    else:
        # Классический формат (по умолчанию)
        return (
            f"{change_symbol} <b>Изменение цены {symbol}</b>\n\n"
            f"💰 Старая цена: <code>${old_price:.2f}</code>\n"
            f"💵 Новая цена: <code>${new_price:.2f}</code>\n"
            f"📊 Изменение: <b>{change_symbol} {change_percent:.2f}%</b>"
        )

def get_time_string():
    """Получить текущее время в формате строки"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")
