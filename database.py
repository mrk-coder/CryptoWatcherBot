# database.py

import sqlite3
from utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

def init_db():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            subscribed INTEGER DEFAULT 0,
            subscription_end TIMESTAMP,
            notification_interval INTEGER DEFAULT 5,
            price_threshold REAL DEFAULT 1.0,
            notification_format TEXT DEFAULT 'classic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tracking (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            symbol TEXT,
            initial_price REAL, -- Цена при начале отслеживания
            last_price REAL,    -- Последняя известная цена
            threshold REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, symbol) -- Уникальность по пользователю и символу
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            invoice_id INTEGER UNIQUE,
            hash TEXT UNIQUE,
            amount REAL,
            currency TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    # Таблица для хранения цен на подписку
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subscription_prices (
            id INTEGER PRIMARY KEY,
            period TEXT UNIQUE, -- 'day', 'week', 'month'
            price_usdt REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Вставляем дефолтные цены, если их нет
    cur.execute("SELECT COUNT(*) FROM subscription_prices")
    if cur.fetchone()[0] == 0:
        default_prices = [('day', 0.1), ('week', 0.5), ('month', 1.0)]
        cur.executemany(
            "INSERT INTO subscription_prices (period, price_usdt) VALUES (?, ?)",
            default_prices
        )
        logger.info("Добавлены дефолтные цены на подписку")
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


def add_user(user_id, username):
    """Добавить или обновить пользователя"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Проверяем, существует ли пользователь
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone() is None:
        # Если пользователь новый, добавляем его
        cur.execute(
            "INSERT INTO users (user_id, username, subscribed) VALUES (?, ?, 0)", 
            (user_id, username)
        )
        logger.info(f"Новый пользователь {username} ({user_id}) добавлен в БД")
    else:
        # Если пользователь существует, НЕ обновляем его (как требовалось)
        logger.info(f"Пользователь {username} ({user_id}) уже существует в БД")
    conn.commit()
    conn.close()

def set_subscription(user_id, status, period_days=30):
    """Установить статус подписки и дату окончания"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    if status == 1:
        # Устанавливаем дату окончания подписки
        end_date = datetime.now() + timedelta(days=period_days)
        cur.execute(
            "UPDATE users SET subscribed = ?, subscription_end = ? WHERE user_id = ?", 
            (status, end_date, user_id)
        )
    else:
        # Сбрасываем дату окончания при отмене подписки
        cur.execute(
            "UPDATE users SET subscribed = ?, subscription_end = NULL WHERE user_id = ?", 
            (status, user_id)
        )
    conn.commit()
    conn.close()
    logger.info(f"Подписка пользователя {user_id} изменена на {status} на {period_days} дней")

def is_subscribed(user_id):
    """Проверить, есть ли активная подписка"""
    from config import ADMIN_ID
    # Админ всегда имеет доступ
    if user_id == ADMIN_ID:
        return True
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT subscribed, subscription_end FROM users WHERE user_id = ?", 
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row and row[0] == 1:
        # Проверяем, не истекла ли подписка
        if row[1]:
            end_date = datetime.fromisoformat(row[1])
            if datetime.now() < end_date:
                return True
            else:
                # Подписка истекла, сбрасываем статус
                set_subscription(user_id, 0)
                return False
        return True
    return False

def get_subscription_prices():
    """Получить все цены на подписку"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT period, price_usdt FROM subscription_prices ORDER BY period")
    rows = cur.fetchall()
    conn.close()
    return {period: price for period, price in rows}

def set_subscription_price(period, price_usdt):
    """Установить цену на подписку для определенного периода"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute(
        "UPDATE subscription_prices SET price_usdt = ?, updated_at = CURRENT_TIMESTAMP WHERE period = ?",
        (price_usdt, period) # <-- Правильный порядок аргументов
    )
    if cur.rowcount == 0:
        # Если запись не найдена, вставляем новую
        cur.execute(
            "INSERT INTO subscription_prices (period, price_usdt) VALUES (?, ?)",
            (period, price_usdt) # <-- Правильный порядок аргументов
        )
    conn.commit()
    conn.close()
    logger.info(f"Цена подписки на период '{period}' установлена: {price_usdt} USDT")

def get_subscription_end_date(user_id):
    """Получить дату окончания подписки"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT subscription_end FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return datetime.fromisoformat(row[0])
    return None

def set_tracking(user_id, symbol, price):
    """Установить или обновить отслеживание валюты"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Проверяем, существует ли запись
    cur.execute(
        "SELECT initial_price FROM tracking WHERE user_id = ? AND symbol = ?", 
        (user_id, symbol)
    )
    row = cur.fetchone()
    if row is None:
        # Если новая запись, initial_price = текущая цена
        cur.execute(
            """INSERT INTO tracking (user_id, symbol, initial_price, last_price) 
               VALUES (?, ?, ?, ?)""", 
            (user_id, symbol, price, price)
        )
    else:
        # Если запись существует, обновляем только last_price
        # initial_price остается неизменным
        cur.execute(
            "UPDATE tracking SET last_price = ? WHERE user_id = ? AND symbol = ?", 
            (price, user_id, symbol)
        )
    conn.commit()
    conn.close()
    logger.info(f"Валюта {symbol} обновлена для пользователя {user_id}")

def get_tracking(user_id):
    """Получить отслеживаемые валюты пользователя"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT symbol, initial_price, last_price FROM tracking WHERE user_id = ?", 
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_users():
    """Получить всех пользователей"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, subscribed FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_stats():
    """Получить статистику пользователей"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE subscribed = 1")
    subscribed = cur.fetchone()[0]
    unsubscribed = total - subscribed
    conn.close()
    return {
        'total': total,
        'subscribed': subscribed,
        'unsubscribed': unsubscribed
    }

def get_users_with_settings():
    """Получить всех пользователей с их настройками и отслеживаниями"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT u.user_id, u.username, u.notification_interval, u.price_threshold, u.notification_format, t.symbol, t.last_price
        FROM users u
        LEFT JOIN tracking t ON u.user_id = t.user_id
        WHERE u.subscribed = 1 OR u.user_id = (SELECT user_id FROM users WHERE user_id = u.user_id LIMIT 1)
    """)
    rows = cur.fetchall()
    conn.close()
    logger.info(f"Получено {len(rows)} записей из базы данных")
    return rows

def get_user_settings(user_id):
    """Получить настройки пользователя"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT notification_interval, price_threshold, notification_format 
        FROM users 
        WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'interval': int(row[0]) if row[0] else 5,
            'threshold': float(row[1]) if row[1] else 1.0,
            'format': row[2] if row[2] else 'classic'
        }
    return {
        'interval': 5,
        'threshold': 1.0,
        'format': 'classic'
    }

def update_user_setting(user_id, setting_name, value):
    """Обновить настройку пользователя"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    
    setting_map = {
        'interval': 'notification_interval',
        'threshold': 'price_threshold',
        'format': 'notification_format'
    }
    
    if setting_name in setting_map:
        column_name = setting_map[setting_name]
        cur.execute(f"UPDATE users SET {column_name} = ? WHERE user_id = ?", (value, user_id))
        conn.commit()
        logger.info(f"Настройка {setting_name} пользователя {user_id} обновлена на {value}")
    
    conn.close()

def add_invoice(user_id, invoice_id, hash, amount, currency):
    """Добавить инвойс в базу данных"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO invoices (user_id, invoice_id, hash, amount, currency, status) 
            VALUES (?, ?, ?, ?, ?, 'active')
        """, (user_id, invoice_id, hash, amount, currency))
        conn.commit()
        logger.info(f"Инвойс {invoice_id} добавлен для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка добавления инвойса: {e}")
    finally:
        conn.close()

def get_user_invoices(user_id):
    """Получить все инвойсы пользователя"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT invoice_id, hash, amount, currency, status, created_at 
        FROM invoices 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_active_invoice(user_id):
    """Получить последний активный инвойс пользователя"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT invoice_id, hash, amount, currency 
        FROM invoices 
        WHERE user_id = ? AND status = 'active' 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_invoice_status(invoice_id, status):
    """Обновить статус инвойса"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET status = ? WHERE invoice_id = ?", (status, invoice_id))
    conn.commit()
    conn.close()
    logger.info(f"Статус инвойса {invoice_id} обновлен на {status}")

def get_invoice_by_id(invoice_id):
    """Получить инвойс по ID"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, invoice_id, hash, amount, currency, status 
        FROM invoices 
        WHERE invoice_id = ?
    """, (invoice_id,))
    row = cur.fetchone()
    conn.close()
    return row
