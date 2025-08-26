# keyboards/main.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def welcome_keyboard(has_subscription=False):
    """Клавиатура для приветственного сообщения"""
    if has_subscription:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Выбрать валюту", callback_data="choose_currency")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="❓ Как это работает?", callback_data="how_it_works")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy_subscription")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="❓ Как это работает?", callback_data="how_it_works")]
        ])
    return keyboard

def subscription_success_keyboard():
    """Клавиатура после покупки подписки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Выбрать валюту", callback_data="choose_currency")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
    ])
    return keyboard

def profile_keyboard(has_subscription=False):
    """Клавиатура профиля"""
    buttons = [
        [InlineKeyboardButton(text="📊 Мои отслеживания", callback_data="my_tracking")],
    ]
    if not has_subscription:
        buttons.append([InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy_subscription")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_keyboard():
    """Клавиатура для оплаты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Оплатить через CryptoBot", callback_data="pay_via_cryptobot")],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton(text="❌ Отменить платеж", callback_data="cancel_payment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def invoice_keyboard(invoice_url: str):
    """Клавиатура с ссылкой на оплату"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Перейти к оплате", url=invoice_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton(text="❌ Отменить платеж", callback_data="cancel_payment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="buy_subscription")]
    ])
    return keyboard

def currency_keyboard():
    """Клавиатура выбора валют"""
    currencies = [
        ("₿ Bitcoin (BTC)", "BTC"),
        ("Ξ Ethereum (ETH)", "ETH"),
        ("BNB Binance Coin (BNB)", "BNB"),
        ("SOL Solana (SOL)", "SOL"),
        ("XRP Ripple (XRP)", "XRP")
    ]
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"track_{symbol}")] for name, symbol in currencies]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def tracking_menu_keyboard():
    """Клавиатура меню отслеживания"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Выбрать другую валюту", callback_data="choose_currency")],
        [InlineKeyboardButton(text="📊 Мои отслеживания", callback_data="my_tracking")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    return keyboard

def my_tracking_keyboard():
    """Клавиатура моих отслеживаний"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Выбрать другую валюту", callback_data="choose_currency")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def settings_keyboard():
    """Клавиатура настроек"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱ Интервал уведомлений", callback_data="settings_interval")],
        [InlineKeyboardButton(text="📊 Порог изменения цены", callback_data="settings_threshold")],
        [InlineKeyboardButton(text="📝 Формат уведомлений", callback_data="settings_format")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def interval_settings_keyboard():
    """Клавиатура выбора интервала"""
    intervals = [
        ("1 минута", 1),
        ("2 минуты", 2),
        ("5 минут", 5),
        ("10 минут", 10),
        ("15 минут", 15)
    ]
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"set_interval_{minutes}")] for name, minutes in intervals]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def threshold_settings_keyboard():
    """Клавиатура выбора порога изменения"""
    thresholds = [
        ("0.1%", 0.1),
        ("0.5%", 0.5),
        ("1%", 1.0),
        ("2%", 2.0),
        ("3%", 3.0),
        ("5%", 5.0)
    ]
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"set_threshold_{value}")] for name, value in thresholds]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def format_settings_keyboard():
    """Клавиатура выбора формата уведомлений"""
    formats = [
        ("Классический", "classic"),
        ("Компактный", "compact"),
        ("Подробный", "detailed")
    ]
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"set_format_{fmt}")] for name, fmt in formats]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
    
def subscription_periods_keyboard(prices):
    """Клавиатура выбора периода подписки"""
    period_names = {'day': 'День', 'week': 'Неделя', 'month': 'Месяц'}
    buttons = []
    
    for period, price in prices.items():
        button_text = f"{period_names.get(period, period)} - {price} USDT"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"subscribe_{period}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
