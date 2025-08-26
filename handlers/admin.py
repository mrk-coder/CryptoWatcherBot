# handlers/admin.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from database import ( 
    set_subscription, get_all_users, get_user_stats,
    update_invoice_status, get_invoice_by_id,
    get_subscription_prices, set_subscription_price
)

from keyboards.admin import (
    admin_main_keyboard, admin_users_keyboard,
    admin_back_keyboard, admin_broadcast_start_keyboard,
    admin_broadcast_image_keyboard, admin_subscription_periods_keyboard,
    admin_subscription_back_keyboard,
    admin_broadcast_keyboard 
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

# Машина состояний для рассылки
class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_image = State()
    preview = State()

# Глобальная переменная для хранения цен (инициализируется позже)
SUBSCRIPTION_PRICES = {}


def load_subscription_prices():
    """Загружает цены подписки из БД в глобальную переменную"""
    global SUBSCRIPTION_PRICES
    try:
        SUBSCRIPTION_PRICES = get_subscription_prices()
        logger.info(f"Загружены цены на подписку: {SUBSCRIPTION_PRICES}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке цен подписки: {e}")
        # Инициализируем пустой словарь в случае ошибки
        SUBSCRIPTION_PRICES = {}

# --- Обработчики ---
# Обработчик команды /admin - точка входа для админки
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к админ панели!")
        return
    
    # --- ВАЖНО: Загружаем цены здесь, после инициализации БД ---
    load_subscription_prices()
    
    text = (
        "👑 <b>Админ панель Crypto Tracker</b>\n\n"
        "Добро пожаловать в панель управления ботом.\n"
        "Выберите действие из меню ниже:"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=admin_main_keyboard())
    logger.info(f"Админ {message.from_user.id} вошел в панель управления")
    
@router.callback_query(F.data == "admin_main")
async def admin_main_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    text = (
        "👑 <b>Админ панель Crypto Tracker</b>\n\n"
        "Добро пожаловать в панель управления ботом.\n"
        "Выберите действие из меню ниже:"
    )
    
    # Используем edit_text вместо edit_caption
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_main_keyboard())
    except:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=admin_main_keyboard())
        
@router.callback_query(F.data == "admin_users")
async def admin_users_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    text = (
        "👥 <b>Управление пользователями</b>\n\n"
        "Здесь вы можете управлять подписками пользователей:"
    )
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_users_keyboard())

@router.callback_query(F.data == "admin_user_list")
async def admin_user_list_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    try:
        users = get_all_users()
        
        if not users:
            text = (
                "👥 <b>Список пользователей</b>\n\n"
                "❌ Пока нет зарегистрированных пользователей."
            )
        else:
            text = "👥 <b>Список пользователей:</b>\n\n"
            for user_id, username, subscribed in users[:15]:  # Показываем первые 15
                sub_status = "✅" if subscribed else "❌"
                username_display = f"@{username}" if username else f"ID: {user_id}"
                text += f"• {sub_status} {username_display} (<code>{user_id}</code>)\n"
            
            if len(users) > 15:
                text += f"\n<i>Показаны первые 15 из {len(users)} пользователей</i>"
        
        await callback.message.edit_text(
            text, 
            parse_mode="HTML", 
            reply_markup=admin_users_keyboard()
        )
        logger.info(f"Админ {callback.from_user.id} запросил список пользователей")
        
    except Exception as e:
        logger.error(f"Ошибка в admin_user_list_handler: {e}")
        await callback.answer("❌ Ошибка получения списка", show_alert=True)

@router.callback_query(F.data == "admin_subscription")
async def admin_subscription_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    # Перезагружаем цены из БД при каждом входе в этот раздел
    load_subscription_prices()
    # Используем глобальную переменную SUBSCRIPTION_PRICES
    prices = SUBSCRIPTION_PRICES 
    
    period_names = {'day': 'День', 'week': 'Неделя', 'month': 'Месяц'}
    prices_text = "\n".join([f"• {period_names.get(p, p)}: <b>{price} USDT</b>" for p, price in prices.items()])
    
    text = (
        "💰 <b>Управление подпиской</b>\n\n"
        f"Текущие цены:\n{prices_text}\n\n"
        "Выберите период для изменения цены:"
    )
    
    # Передаем prices в клавиатуру
    await callback.message.edit_text(
        text, 
        parse_mode="HTML", 
        reply_markup=admin_subscription_periods_keyboard(prices) # Передаем актуальные цены
    )


@router.callback_query(F.data == "admin_change_price")
async def admin_change_price_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    text = (
        "✏️ <b>Изменение цены подписки</b>\n\n"
        "Введите новую цену в USDT:\n"
        "Пример: <code>/set_price 2.5</code>"
    )
    
    await callback.message.edit_text(
        text, 
        parse_mode="HTML", 
        reply_markup=admin_back_keyboard()
    )

@router.message(Command("set_price"))
async def admin_set_subscription_price(message: Message): # <-- Новое имя
    if message.from_user.id != ADMIN_ID:
        return

    try:
        # Разделяем текст сообщения и получаем цену
        parts = message.text.split()
        if len(parts) < 2:
             await message.answer("❌ Ошибка! Используйте формат: /set_price [цена]")
             return
             
        new_price = float(parts[1]) # <-- parts[1] вместо message.text.split()[1] для безопасности
        if new_price > 0:
            set_subscription_price('month', new_price) # <-- Вызываем оригинальную функцию из database
            await message.answer(
                f"✅ Цена месячной подписки успешно изменена на <b>{new_price} USDT</b>",
                parse_mode="HTML"
            )
            logger.info(f"Админ {message.from_user.id} изменил цену месячной подписки на {new_price} USDT")
            # Обновляем кэш цен
            load_subscription_prices()
        else:
            await message.answer("❌ Цена должна быть положительной!")
    except ValueError: # Более конкретное исключение
        await message.answer("❌ Ошибка! Цена должна быть числом. Используйте формат: /set_price [цена]")
    except Exception as e: # На случай других ошибок БД
        logger.error(f"Ошибка в admin_set_subscription_price: {e}")
        await message.answer("❌ Произошла ошибка при изменении цены.")
        
@router.callback_query(F.data == "admin_give_sub")
async def admin_give_sub_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    text = (
        "➕ <b>Выдача подписки</b>\n\n"
        "Введите команду:\n"
        "<code>/give_sub [user_id]</code>\n\n"
        "Пример: <code>/give_sub 123456789</code>"
    )
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())

@router.message(Command("give_sub"))
async def give_subscription(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        user_id = int(message.text.split()[1])
        set_subscription(user_id, 1)
        await message.answer(
            f"✅ Подписка успешно выдана пользователю <code>{user_id}</code>",
            parse_mode="HTML"
        )
        logger.info(f"Админ {message.from_user.id} выдал подписку пользователю {user_id}")
    except (IndexError, ValueError):
        await message.answer("❌ Ошибка! Используйте формат: /give_sub [user_id]")

@router.callback_query(F.data == "admin_remove_sub")
async def admin_remove_sub_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    text = (
        "➖ <b>Отзыв подписки</b>\n\n"
        "Введите команду:\n"
        "<code>/remove_sub [user_id]</code>\n\n"
        "Пример: <code>/remove_sub 123456789</code>"
    )
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())

@router.message(Command("remove_sub"))
async def remove_subscription(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        user_id = int(message.text.split()[1])
        set_subscription(user_id, 0)
        await message.answer(
            f"✅ Подписка успешно отозвана у пользователя <code>{user_id}</code>",
            parse_mode="HTML"
        )
        logger.info(f"Админ {message.from_user.id} отозвал подписку у пользователя {user_id}")
    except (IndexError, ValueError):
        await message.answer("❌ Ошибка! Используйте формат: /remove_sub [user_id]")

@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    from database import get_user_stats
    stats = get_user_stats()
    
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total']}</b>\n"
        f"✅ С подпиской: <b>{stats['subscribed']}</b>\n"
        f"❌ Без подписки: <b>{stats['unsubscribed']}</b>"
    )
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())


@router.callback_query(F.data == "check_payment")
async def check_payment_handler(callback: CallbackQuery):
    try:
        # Здесь должна быть логика проверки оплаты
        # Пока показываем демонстрационное сообщение
        
        from handlers.admin import SUBSCRIPTION_PRICE
        check_text = (
            "🔄 <b>Проверка оплаты</b>\n\n"
            "⏳ Проверяем статус вашего платежа...\n\n"
            "Если вы уже оплатили подписку, доступ будет предоставлен в течение нескольких минут."
        )
        
        from keyboards.main import payment_keyboard
        await callback.message.edit_text(
            text=check_text,
            parse_mode="HTML",
            reply_markup=payment_keyboard()
        )
        
        logger.info(f"Пользователь {callback.from_user.id} проверяет оплату")
        
    except Exception as e:
        logger.error(f"Ошибка в check_payment_handler: {e}")
        await callback.answer("❌ Ошибка проверки оплаты", show_alert=True)
        
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    text = (
        "📢 <b>Массовая рассылка</b>\n\n"
        "Создайте сообщение для рассылки всем пользователям бота."
    )
    
    await callback.message.edit_text(
        text, 
        parse_mode="HTML", 
        reply_markup=admin_broadcast_start_keyboard()
    )

@router.callback_query(F.data == "admin_broadcast_text")
async def admin_broadcast_text_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    await callback.message.edit_text(
        "✏️ <b>Введите текст для рассылки:</b>", 
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_for_text)

@router.message(BroadcastStates.waiting_for_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    await state.update_data(text=message.text)
    # Сохраняем текст в состоянии и переходим к следующему шагу
    await message.answer(
        "Текст сохранен. Хотите прикрепить изображение?",
        reply_markup=admin_broadcast_image_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_image)

@router.callback_query(F.data == "admin_broadcast_attach_image")
async def admin_broadcast_attach_image_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    await callback.message.edit_text(
        "🖼 <b>Пришлите изображение для рассылки:</b>", 
        parse_mode="HTML"
    )
    # Состояние уже установлено в waiting_for_image

@router.callback_query(F.data == "admin_broadcast_send_no_image")
async def admin_broadcast_send_no_image_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    await state.update_data(photo=None)
    user_data = await state.get_data()
    text = user_data['text']
    
    preview_text = f"📢 <b>Предпросмотр рассылки:</b>\n\n{text}"
    if len(preview_text) > 1024:
        preview_text = preview_text[:1021] + "..."
        
    await callback.message.edit_text(
        preview_text,
        parse_mode="HTML",
        reply_markup=admin_broadcast_keyboard()
    )
    await state.set_state(BroadcastStates.preview)

@router.message(BroadcastStates.waiting_for_image, F.photo)
async def process_broadcast_image(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    user_data = await state.get_data()
    text = user_data['text']
    
    # Отправляем предпросмотр
    try:
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=file_id,
            caption=f"📢 <b>Предпросмотр рассылки:</b>\n\n{text}",
            parse_mode="HTML",
            reply_markup=admin_broadcast_keyboard()
        )
        await state.set_state(BroadcastStates.preview)
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании предпросмотра: {e}")
        await state.clear()

@router.callback_query(BroadcastStates.preview, F.data == "admin_broadcast_confirm")
async def process_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    # Получаем данные из состояния
    user_data = await state.get_data()
    text = user_data['text']
    photo = user_data.get('photo')
    
    # Получаем список всех пользователей
    users = get_all_users()
    bot = callback.bot
    success_count = 0
    error_count = 0
    
    progress_message = await callback.message.answer(
        "🚀 <b>Начинаю отправку рассылки...</b>\n"
        f"Всего пользователей: {len(users)}",
        parse_mode="HTML"
    )
    
    for i, (user_id, username, _) in enumerate(users):
        try:
            if photo:
                await bot.send_photo(chat_id=user_id, photo=photo, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            success_count += 1
        except Exception as e:
            logger.error(f"Ошибка отправки рассылки пользователю {user_id} ({username}): {e}")
            error_count += 1
            
        # Обновляем прогресс каждые 10 пользователей

        if (i + 1) % 10 == 0 or i == len(users) - 1:
            try:  
                await progress_message.edit_text(
                    f"🚀 <b>Отправка рассылки...</b>\n"
                    f"Обработано: {i + 1}/{len(users)}\n"
                    f"Успешно: {success_count}\n"
                    f"Ошибок: {error_count}",
                    parse_mode="HTML"
                )
            except:
                pass # Игнорируем ошибки редактирования сообщения о прогрессе
    
    await callback.message.answer(
        f"✅ <b>Рассылка завершена!</b>\n"
        f"Успешно: {success_count}\n"
        f"Ошибок: {error_count}",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard()
    )
    logger.info(f"Админ {callback.from_user.id} отправил рассылку: успешно {success_count}, ошибок {error_count}")
    
    # Сбрасываем состояние
    await state.clear()

# Обработчики для управления ценами на подписку
@router.callback_query(F.data == "admin_subscription")
async def admin_subscription_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
        
    # Перезагружаем цены из БД
    load_subscription_prices()
    prices = get_subscription_prices()
    
    period_names = {'day': 'День', 'week': 'Неделя', 'month': 'Месяц'}
    prices_text = "\n".join([f"• {period_names.get(p, p)}: <b>{price} USDT</b>" for p, price in prices.items()])
    
    text = (
        "💰 <b>Управление подпиской</b>\n\n"
        f"Текущие цены:\n{prices_text}\n\n"
        "Выберите период для изменения цены:"
    )
    
    await callback.message.edit_text(
        text, 
        parse_mode="HTML", 
        reply_markup=admin_subscription_periods_keyboard(prices)
    )

@router.callback_query(F.data.startswith("admin_change_price_"))
async def admin_change_price_period_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    period = callback.data.split("_")[-1] # admin_change_price_day
    period_names = {'day': 'дня', 'week': 'недели', 'month': 'месяца'}
    period_name = period_names.get(period, period)
    
    # Получаем текущую цену
    prices = get_subscription_prices()
    current_price = prices.get(period, 1.0)
    
    text = (
        f"✏️ <b>Изменение цены подписки на {period_name}</b>\n\n"
        f"Текущая цена: <b>{current_price} USDT</b>\n\n"
        "Введите новую цену в USDT (например, 0.5 или 1.25):"
    )
    
    await state.update_data(changing_period=period)
    await callback.message.edit_text(
        text, 
        parse_mode="HTML"
    )
    # Ждем сообщение с новой ценой

@router.message(F.text.regexp(r'^\d+\.?\d*$'))
async def process_new_subscription_price(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        new_price = float(message.text)
        if new_price < 0:
            await message.answer("❌ Цена не может быть отрицательной. Попробуйте еще раз:")
            return
            
        user_data = await state.get_data()
        period = user_data.get('changing_period')
        
        if not period:
            await message.answer("❌ Ошибка состояния. Попробуйте снова через меню.")
            await state.clear()
            return
            
        # Обновляем цену в БД
        set_subscription_price(period, new_price)
        # Обновляем в памяти
        load_subscription_prices()
        
        period_names = {'day': 'день', 'week': 'неделю', 'month': 'месяц'}
        period_name = period_names.get(period, period)
        
        await message.answer(
            f"✅ Цена подписки на {period_name} успешно изменена на <b>{new_price} USDT</b>",
            parse_mode="HTML"
        )
        
        # Возвращаем в главное меню админки
        await message.answer(
            "👑 <b>Админ панель Crypto Tracker</b>\n\n"
            "Добро пожаловать в панель управления ботом.\n"
            "Выберите действие из меню ниже:",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число (например, 0.5 или 1.25):")
