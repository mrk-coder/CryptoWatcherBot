# services/crypto_bot.py

import aiohttp
import json
from config import CRYPTO_BOT_TOKEN
from database import update_invoice_status
from utils.logger import get_logger

logger = get_logger(__name__)

CRYPTO_BOT_API_URL = "https://pay.crypt.bot/api"

async def create_invoice(amount: float, currency: str = "USDT", description: str = "Подписка Crypto Tracker"):
    """Создание инвойса для оплаты через CryptoBot"""
    if not CRYPTO_BOT_TOKEN:
        logger.error("CRYPTO_BOT_TOKEN не установлен")
        return None
        
    url = f"{CRYPTO_BOT_API_URL}/createInvoice"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "asset": currency,
        "amount": str(amount),
        "description": description,
        "hidden_message": "Спасибо за покупку подписки! Доступ будет активирован автоматически.",
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/CryptoWatchTracker_bot"  # Замените на имя вашего бота
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Ответ от CryptoBot API: {data}")
                    if data.get("ok"):
                        invoice = data.get("result")
                        # Очищаем URL от лишних пробелов
                        if invoice.get("pay_url"):
                            invoice["pay_url"] = invoice["pay_url"].strip()
                        logger.info(f"Создан инвойс: {invoice.get('invoice_id')}")
                        return invoice
                    else:
                        error_name = data.get('error', {}).get('name', 'Unknown')
                        error_message = data.get('error', {}).get('message', 'No message')
                        logger.error(f"Ошибка создания инвойса: {error_name} - {error_message}")
                        return None
                else:
                    text = await response.text()
                    logger.error(f"HTTP ошибка {response.status} при создании инвойса: {text}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при создании инвойса: {e}")
        return None

async def check_invoice_status(invoice_id: str):
    """Проверка статуса инвойса"""
    if not CRYPTO_BOT_TOKEN:
        logger.error("CRYPTO_BOT_TOKEN не установлен")
        return None
        
    url = f"{CRYPTO_BOT_API_URL}/getInvoices"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    params = {
        "invoice_ids": str(invoice_id)
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Ответ от CryptoBot API при проверке инвойса: {data}")
                    if data.get("ok"):
                        invoices = data.get("result", {}).get("items", [])
                        if invoices:
                            invoice = invoices[0]
                            status = invoice.get("status")
                            logger.info(f"Статус инвойса {invoice_id}: {status}")
                            
                            # Обновляем статус в базе данных
                            if status in ['paid', 'confirmed']:
                                update_invoice_status(invoice_id, status)
                            
                            return invoice
                        else:
                            logger.warning(f"Инвойс {invoice_id} не найден")
                            return None
                    else:
                        error_name = data.get('error', {}).get('name', 'Unknown')
                        error_message = data.get('error', {}).get('message', 'No message')
                        logger.error(f"Ошибка проверки инвойса: {error_name} - {error_message}")
                        return None
                else:
                    text = await response.text()
                    logger.error(f"HTTP ошибка {response.status} при проверке инвойса: {text}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при проверке инвойса: {e}")
        return None

async def cancel_invoice(invoice_id: str):
    """Отмена инвойса"""
    if not CRYPTO_BOT_TOKEN:
        logger.error("CRYPTO_BOT_TOKEN не установлен")
        return False
        
    url = f"{CRYPTO_BOT_API_URL}/cancelInvoice"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "invoice_id": str(invoice_id)
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Ответ от CryptoBot API при отмене инвойса: {data}")
                    if data.get("ok"):
                        update_invoice_status(invoice_id, 'cancelled')
                        logger.info(f"Инвойс {invoice_id} отменен")
                        return True
                    else:
                        error_name = data.get('error', {}).get('name', 'Unknown')
                        error_message = data.get('error', {}).get('message', 'No message')
                        logger.error(f"Ошибка отмены инвойса: {error_name} - {error_message}")
                        return False
                else:
                    text = await response.text()
                    logger.error(f"HTTP ошибка {response.status} при отмене инвойса: {text}")
                    return False
    except Exception as e:
        logger.error(f"Ошибка при отмене инвойса: {e}")
        return False
