# keyboards/admin.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Клавиатуры для рассылки ---
def admin_broadcast_keyboard():
    """Клавиатура для подтверждения рассылки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить отправку", callback_data="admin_broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_main")]
    ])
    return keyboard

def admin_back_keyboard():
    """Клавиатура с кнопкой назад для админки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])
    return keyboard

# --- НОВАЯ КЛАВИАТУРА: Главная админская клавиатура ---
def admin_main_keyboard():
    """Главная админская клавиатура"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 Управление подпиской", callback_data="admin_subscription")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

# --- Клавиатуры для управления пользователями ---
def admin_users_keyboard():
    """Клавиатура управления пользователями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать подписку", callback_data="admin_give_sub")],
        [InlineKeyboardButton(text="➖ Забрать подписку", callback_data="admin_remove_sub")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_user_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])
    return keyboard

# --- Клавиатуры для рассылки ---
def admin_broadcast_start_keyboard():
    """Клавиатура начала рассылки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Написать текст", callback_data="admin_broadcast_text")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])
    return keyboard

def admin_broadcast_image_keyboard():
    """Клавиатура после ввода текста"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Прикрепить изображение", callback_data="admin_broadcast_attach_image")],
        [InlineKeyboardButton(text="🚀 Отправить без изображения", callback_data="admin_broadcast_send_no_image")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast_text")]
    ])
    return keyboard

# --- Клавиатуры для управления подпиской ---
def admin_subscription_periods_keyboard(prices):
    """Клавиатура выбора периода подписки для изменения цены"""
    period_names = {'day': 'День', 'week': 'Неделя', 'month': 'Месяц'}
    buttons = [
        [InlineKeyboardButton(
            text=f"✏️ {period_names.get(period, period)} ({price} USDT)", 
            callback_data=f"admin_change_price_{period}"
        )] for period, price in prices.items()
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_subscription_back_keyboard(period):
    """Клавиатура назад для изменения цены конкретного периода"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_subscription")]
    ])
    return keyboard
