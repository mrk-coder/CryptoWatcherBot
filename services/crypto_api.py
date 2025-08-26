# services/crypto_api.py

import aiohttp
from config import CRYPTO_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

async def get_crypto_price(symbol):
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms=USD&api_key={CRYPTO_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = data.get("USD")
                    if price is not None:
                        logger.info(f"Получена цена {symbol}: {price} USD")
                        return float(price)
                    else:
                        logger.error(f"Некорректные данные для {symbol}: {data}")
                        return None
                else:
                    logger.error(f"HTTP ошибка {resp.status} для {symbol}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения цены для {symbol}: {e}")
        return None
