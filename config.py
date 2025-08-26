# config.py

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CRYPTO_API_KEY = os.getenv("CRYPTO_API_KEY")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")  # Токен для CryptoBot API
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Проверка обязательных переменных
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env файле")
if not CRYPTO_API_KEY:
    raise ValueError("CRYPTO_API_KEY не найден в .env файле")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не найден в .env файле")
