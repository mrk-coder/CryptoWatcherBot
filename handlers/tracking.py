# handlers/tracking.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import set_tracking, get_user_settings, is_subscribed
from services.crypto_api import get_crypto_price
from keyboards.main import tracking_menu_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()  # Добавлено определение router

@router.callback_query(F.data.startswith("track_"))
async def track_currency_handler(callback: CallbackQuery):
    # Проверяем подписку
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
        
    symbol = callback.data.split("_")[1]
    price = await get_crypto_price(symbol)
    
    if price:
        set_tracking(callback.from_user.id, symbol, price)
        
        currency_names = {
            "BTC": "Bitcoin",
            "ETH": "Ethereum", 
            "BNB": "Binance Coin",
            "SOL": "Solana",
            "XRP": "Ripple"
        }
        
        user_settings = get_user_settings(callback.from_user.id)
        
        text = (
            f"✅ <b>Отслеживание начато!</b>\n\n"
            f"📊 Валюта: <b>{currency_names.get(symbol, symbol)} ({symbol})</b>\n"
            f"💰 Текущая цена: <b>${price:.2f}</b>\n"
            f"⏱ Интервал: <b>{user_settings['interval']} минут</b>\n"
            f"📊 Порог: <b>{user_settings['threshold']}%</b>\n\n"
            f"🔔 Вы будете получать уведомления в <b>{user_settings['format']}</b> формате."
        )
        
        try:
            await callback.message.edit_caption(
                caption=text,
                parse_mode="HTML",
                reply_markup=tracking_menu_keyboard()
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать caption: {e}")
            try:
                await callback.message.edit_text(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=tracking_menu_keyboard()
                )
            except Exception as e2:
                logger.error(f"Ошибка при отправке нового сообщения: {e2}")
                await callback.answer("✅ Отслеживание начато!", show_alert=True)
        
        logger.info(f"Пользователь {callback.from_user.id} начал отслеживать {symbol} по цене ${price:.2f}")
    else:
        await callback.answer("❌ Ошибка получения цены", show_alert=True)
        logger.error(f"Ошибка получения цены для {symbol} у пользователя {callback.from_user.id}")
