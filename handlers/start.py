# handlers/start.py

import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command, CommandStart 
from keyboards.main import (
    welcome_keyboard, currency_keyboard, 
    subscription_success_keyboard, tracking_menu_keyboard,
    settings_keyboard, interval_settings_keyboard,
    threshold_settings_keyboard, format_settings_keyboard,
    profile_keyboard, my_tracking_keyboard, 
    subscription_periods_keyboard 
)
from database import (
    add_user, is_subscribed, set_subscription, 
    add_invoice, get_active_invoice, get_user_settings,
    update_user_setting, get_tracking, get_subscription_end_date 
)    
from services.crypto_bot import create_invoice, check_invoice_status, cancel_invoice
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

# Путь к локальному изображению
WELCOME_IMAGE_PATH = "assets/welcome.jpg"  # Убедитесь, что папка assets существует

@router.message(CommandStart())
async def start_handler(message: Message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Неизвестный"
        # Теперь add_user проверяет существование
        add_user(user_id, username)
        
        # Проверяем наличие подписки
        has_subscription = is_subscribed(user_id)
        
        welcome_text = (
            "👋 <b>Добро пожаловать в Crypto Tracker Bot!</b>\n\n"
            "🤖 Я помогу вам отслеживать изменения курсов криптовалют в реальном времени.\n\n"
            f"{'✅ У вас активна подписка!' if has_subscription else '🔔 Для начала работы необходимо приобрести подписку'}"
        )
        
        # Проверяем существование файла изображения
        if os.path.exists(WELCOME_IMAGE_PATH):
            photo = FSInputFile(WELCOME_IMAGE_PATH)
            await message.answer_photo(
                photo=photo,
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=welcome_keyboard(has_subscription)
            )
        else:
            # Если файл не найден, используем ссылку
            await message.answer_photo(
                photo="https://i.imgur.com/5Xc5HjL.jpg",
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=welcome_keyboard(has_subscription)
            )
        
        logger.info(f"Пользователь {username} ({user_id}) начал работу с ботом")
        
    except Exception as e:
        logger.error(f"Ошибка в start_handler: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    has_subscription = is_subscribed(user_id)
    
    if has_subscription:
        end_date = get_subscription_end_date(user_id)
        if end_date:
            time_left = end_date - datetime.now()
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            subscription_info = f"✅ Активна\n⏱ До окончания: {days}д {hours}ч {minutes}м"
        else:
            subscription_info = "✅ Активна (бессрочная)"
    else:
        subscription_info = "❌ Не активна"
    
    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🔖 Подписка: <b>{subscription_info}</b>\n"
    )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=profile_keyboard(has_subscription)
    )

@router.callback_query(F.data == "my_tracking")
async def my_tracking_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    tracking_data = get_tracking(user_id)
    
    if not tracking_data:
        text = (
            "📊 <b>Мои отслеживания</b>\n\n"
            "❌ Вы пока не отслеживаете ни одну валюту.\n\n"
            "Нажмите кнопку ниже, чтобы начать отслеживание."
        )
    else:
        text = "📊 <b>Мои отслеживания:</b>\n\n"
        for symbol, initial_price, last_price in tracking_data:
            change_symbol = "📈" if last_price > initial_price else "📉" if last_price < initial_price else "➡️"
            change_percent = 0.0
            if initial_price and initial_price != 0:
                change_percent = ((last_price - initial_price) / initial_price) * 100
            
            text += (
                f"<b>{symbol}</b>\n"
                f"🏁 Начальная цена: <code>${initial_price:.2f}</code>\n"
                f"💵 Текущая цена: <code>${last_price:.2f}</code>\n"
                f"📊 Изменение: <b>{change_symbol} {change_percent:.2f}%</b>\n\n"
            )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=my_tracking_keyboard()
    )
    
@router.callback_query(F.data == "how_it_works")
async def how_it_works_handler(callback: CallbackQuery):
    text = (
        "❓ <b>Как работает Crypto Tracker:</b>\n\n"
        "1️⃣ <b>Выберите валюту</b> - выберите одну из 5 популярных криптовалют\n"
        "2️⃣ <b>Начните отслеживание</b> - бот начнет следить за изменением цены\n"
        "3️⃣ <b>Получайте уведомления</b> - бот уведомит вас об изменениях\n"
        "4️⃣ <b>Настройте параметры</b> - установите индивидуальные настройки\n\n"
        "⚙️ <b>Настройки:</b>\n"
        "• Интервал уведомлений (1-15 минут)\n"
        "• Порог изменения цены (0.5%-5%)\n"
        "• Формат уведомлений (классический/компактный/подробный)\n\n"
        "💰 <b>Подписка:</b>\n"
        "• Открывает доступ ко всем функциям\n"
        "• Позволяет отслеживать несколько валют\n"
        "• Персональные настройки уведомлений"
    )
    
    has_subscription = is_subscribed(callback.from_user.id)
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=welcome_keyboard(has_subscription)
    )

@router.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    user_settings = get_user_settings(callback.from_user.id)
    
    text = (
        "⚙️ <b>Настройки уведомлений</b>\n\n"
        f"⏱ Интервал проверки: <b>{user_settings['interval']} минут</b>\n"
        f"📊 Порог изменения: <b>{user_settings['threshold']}%</b>\n"
        f"📝 Формат уведомлений: <b>{user_settings['format'].capitalize()}</b>\n\n"
        "Выберите параметр для настройки:"
    )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=settings_keyboard()
    )


@router.callback_query(F.data == "settings_interval")
async def settings_interval_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    text = "⏱ <b>Выберите интервал уведомлений:</b>\n\nВыберите, как часто бот будет проверять изменения цен:"
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=interval_settings_keyboard()
    )

@router.callback_query(F.data.startswith("set_interval_"))
async def set_interval_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    try:
        interval = int(callback.data.split("_")[2])
        update_user_setting(callback.from_user.id, 'interval', interval)
        
        text = f"✅ <b>Интервал обновлен!</b>\n\nТеперь бот будет проверять цены каждые <b>{interval} минут</b>."
        
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=settings_keyboard()
        )
        
        logger.info(f"Пользователь {callback.from_user.id} установил интервал {interval} минут")
        
    except Exception as e:
        logger.error(f"Ошибка в set_interval_handler: {e}")
        await callback.answer("❌ Ошибка установки интервала", show_alert=True)

@router.callback_query(F.data == "settings_threshold")
async def settings_threshold_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    text = "📊 <b>Выберите порог изменения цены:</b>\n\nБот будет уведомлять только при изменении цены больше выбранного значения:"
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=threshold_settings_keyboard()
    )

@router.callback_query(F.data.startswith("set_threshold_"))
async def set_threshold_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    try:
        threshold_str = callback.data.split("_")[2]
        # Обрабатываем десятичные числа
        if "." in threshold_str:
            threshold = float(threshold_str)
        else:
            threshold = int(threshold_str)
            
        update_user_setting(callback.from_user.id, 'threshold', threshold)
        
        text = f"✅ <b>Порог изменения обновлен!</b>\n\nТеперь вы будете получать уведомления при изменении цены более <b>{threshold}%</b>."
        
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=settings_keyboard()
        )
        
        logger.info(f"Пользователь {callback.from_user.id} установил порог {threshold}%")
        
    except Exception as e:
        logger.error(f"Ошибка в set_threshold_handler: {e}")
        await callback.answer("❌ Ошибка установки порога", show_alert=True)

@router.callback_query(F.data == "settings_format")
async def settings_format_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    text = "📝 <b>Выберите формат уведомлений:</b>\n\nВыберите, как будут выглядеть уведомления:"
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=format_settings_keyboard()
    )

@router.callback_query(F.data.startswith("set_format_"))
async def set_format_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
    
    try:
        format_type = callback.data.split("_")[2]
        format_names = {
            'classic': 'Классический',
            'compact': 'Компактный',
            'detailed': 'Подробный'
        }
        
        update_user_setting(callback.from_user.id, 'format', format_type)
        
        text = f"✅ <b>Формат уведомлений обновлен!</b>\n\nТеперь ваши уведомления будут в <b>{format_names.get(format_type, format_type)}</b> формате."
        
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=settings_keyboard()
        )
        
        logger.info(f"Пользователь {callback.from_user.id} установил формат {format_type}")
        
    except Exception as e:
        logger.error(f"Ошибка в set_format_handler: {e}")
        await callback.answer("❌ Ошибка установки формата", show_alert=True)

@router.callback_query(F.data == "buy_subscription")
async def buy_subscription_handler(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        
        # Админу не нужно покупать подписку
        if user_id == ADMIN_ID:
            from database import set_subscription
            set_subscription(user_id, 1)
            
            subscription_text = (
                "👑 <b>Админ панель</b>\n\n"
                "✅ Вам автоматически предоставлен полный доступ как администратору.\n\n"
                "Используйте команду /admin для входа в панель управления."
            )
            
            try:
                await callback.message.edit_caption(
                    caption=subscription_text,
                    parse_mode="HTML",
                    reply_markup=subscription_success_keyboard()
                )
            except:
                await callback.message.edit_text(
                    text=subscription_text,
                    parse_mode="HTML",
                    reply_markup=subscription_success_keyboard()
                )
            logger.info(f"Админ {user_id} получил доступ")
            return
        
        # Для обычных пользователей показываем цены из БД
        from database import get_subscription_prices
        prices = get_subscription_prices()
        
        period_names = {'day': 'День', 'week': 'Неделя', 'month': 'Месяц'}
        prices_list = "\n".join([
            f"• {period_names.get(p, p).capitalize()}: <b>{price} USDT</b>" 
            for p, price in prices.items()
        ])
        
        subscription_text = (
            "💳 <b>Покупка подписки</b>\n\n"
            "✨ <b>Что входит в подписку:</b>\n"
            "• Отслеживание 5 популярных криптовалют\n"
            "• Уведомления об изменениях цен\n"
            "• Персональные настройки\n\n"
            f"<b>Цены:</b>\n{prices_list}\n\n"
            "Выберите период подписки:"
        )
        
        # Создаем клавиатуру с выбором периода
        from keyboards.main import subscription_periods_keyboard
        try:
            await callback.message.edit_caption(
                caption=subscription_text,
                parse_mode="HTML",
                reply_markup=subscription_periods_keyboard(prices)
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать caption: {e}")
            try:
                await callback.message.edit_text(
                    text=subscription_text,
                    parse_mode="HTML",
                    reply_markup=subscription_periods_keyboard(prices)
                )
            except Exception as e2:
                logger.error(f"Ошибка редактирования текста: {e2}")
                await callback.message.delete()
                await callback.message.answer(
                    text=subscription_text,
                    parse_mode="HTML",
                    reply_markup=subscription_periods_keyboard(prices)
                )
        
        logger.info(f"Пользователь {user_id} перешел к выбору периода подписки")
        
    except Exception as e:
        logger.error(f"Ошибка в buy_subscription_handler: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Добавляем обработчики выбора периода подписки
@router.callback_query(F.data.startswith("subscribe_"))
async def subscribe_period_handler(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        period = callback.data.split("_")[1] # subscribe_day, subscribe_week, subscribe_month
        
        # Получаем цену из БД
        from database import get_subscription_prices
        prices = get_subscription_prices()
        amount = prices.get(period, 1.0) # Дефолт 1.0 USDT если не найдено
        
        # Определяем количество дней для подписки
        period_days_map = {'day': 1, 'week': 7, 'month': 30}
        period_days = period_days_map.get(period, 30)
        
        # Создаем инвойс через CryptoBot
        invoice = await create_invoice(
            amount=amount,
            currency="USDT",
            description=f"Подписка Crypto Tracker на {period_days} дней"
        )
        
        if invoice:
            invoice_url = invoice.get("pay_url", "").strip()
            invoice_id = invoice.get("invoice_id")
            hash = invoice.get("hash")
            
            # Сохраняем инвойс в базу данных с информацией о периоде
            add_invoice(user_id, invoice_id, hash, amount, "USDT")
            
            period_names = {'day': 'день', 'week': 'неделю', 'month': 'месяц'}
            period_name = period_names.get(period, period)
            
            payment_text = (
                f"💳 <b>Оплата подписки на {period_name}</b>\n\n"
                f"💰 Сумма: <b>{amount} USDT</b>\n"
                f"🆔 Номер заказа: <code>{invoice_id}</code>\n\n"
                f"Нажмите кнопку ниже для оплаты:"
            )
            
            from keyboards.main import invoice_keyboard
            try:
                await callback.message.edit_caption(
                    caption=payment_text,
                    parse_mode="HTML",
                    reply_markup=invoice_keyboard(invoice_url)
                )
            except Exception as e:
                logger.warning(f"Не удалось отредактировать caption: {e}")
                try:
                    await callback.message.edit_text(
                        text=payment_text,
                        parse_mode="HTML",
                        reply_markup=invoice_keyboard(invoice_url)
                    )
                except Exception as e2:
                    logger.warning(f"Не удалось отредактировать текст: {e2}")
                    await callback.message.delete()
                    await callback.message.answer(
                        text=payment_text,
                        parse_mode="HTML",
                        reply_markup=invoice_keyboard(invoice_url)
                    )
            
            logger.info(f"Создан инвойс {invoice_id} для пользователя {user_id} на период {period} ({amount} USDT)")
        else:
            await callback.answer("❌ Ошибка создания платежа", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в subscribe_period_handler: {e}")
        await callback.answer("❌ Ошибка создания платежа", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    welcome_text = (
        "👋 <b>Добро пожаловать в Crypto Tracker Bot!</b>\n\n"
        "🤖 Я помогу вам отслеживать изменения курсов криптовалют в реальном времени.\n\n"
        f"{'✅ У вас активна подписка!' if is_subscribed(callback.from_user.id) else '🔔 Для начала работы необходимо приобрести подписку'}"
    )
    
    try:
        await callback.message.edit_caption(
            caption=welcome_text,
            parse_mode="HTML",
            reply_markup=welcome_keyboard(is_subscribed(callback.from_user.id))
        )
    except Exception as e:
        logger.warning(f"Не удалось отредактировать caption: {e}")
        try:
            await callback.message.edit_text(
                text=welcome_text,
                parse_mode="HTML",
                reply_markup=welcome_keyboard(is_subscribed(callback.from_user.id))
            )
        except Exception as e2:
            logger.error(f"Ошибка при редактировании текста: {e2}")
            # Если ничего не работает, отправляем новое сообщение
            await callback.message.delete()
            await callback.message.answer_photo(
                photo="https://i.imgur.com/5Xc5HjL.jpg",
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=welcome_keyboard(is_subscribed(callback.from_user.id))
            )


@router.callback_query(F.data == "pay_via_cryptobot")
async def pay_via_cryptobot_handler(callback: CallbackQuery):
    try:
        from handlers.admin import SUBSCRIPTION_PRICE
        user_id = callback.from_user.id
        
        # Создаем инвойс через CryptoBot
        invoice = await create_invoice(
            amount=SUBSCRIPTION_PRICE,
            currency="USDT",
            description="Подписка Crypto Tracker Bot"
        )
        
        if invoice:
            invoice_url = invoice.get("pay_url", "").strip()
            invoice_id = invoice.get("invoice_id")
            hash = invoice.get("hash")
            
            # Сохраняем инвойс в базу данных
            add_invoice(user_id, invoice_id, hash, SUBSCRIPTION_PRICE, "USDT")
            
            payment_text = (
                f"💳 <b>Оплата подписки</b>\n\n"
                f"💰 Сумма: <b>{SUBSCRIPTION_PRICE} USDT</b>\n"
                f"🆔 Номер заказа: <code>{invoice_id}</code>\n\n"
                f"Нажмите кнопку ниже для оплаты:"
            )
            
            from keyboards.main import invoice_keyboard
            try:
                # Используем edit_caption, так как сообщение с фото
                await callback.message.edit_caption(
                    caption=payment_text,
                    parse_mode="HTML",
                    reply_markup=invoice_keyboard(invoice_url)
                )
            except Exception as e:
                logger.warning(f"Не удалось отредактировать caption: {e}")
                try:
                    # Если edit_caption не работает, пробуем edit_text
                    await callback.message.edit_text(
                        text=payment_text,
                        parse_mode="HTML",
                        reply_markup=invoice_keyboard(invoice_url)
                    )
                except Exception as e2:
                    logger.warning(f"Не удалось отредактировать текст: {e2}")
                    # Если ничего не работает, удаляем и отправляем новое сообщение
                    await callback.message.delete()
                    await callback.message.answer(
                        text=payment_text,
                        parse_mode="HTML",
                        reply_markup=invoice_keyboard(invoice_url)
                    )
            
            logger.info(f"Создан инвойс {invoice_id} для пользователя {user_id}")
        else:
            await callback.answer("❌ Ошибка создания платежа", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в pay_via_cryptobot_handler: {e}")
        await callback.answer("❌ Ошибка создания платежа", show_alert=True)

@router.callback_query(F.data == "choose_currency")
async def choose_currency_handler(callback: CallbackQuery):
    if not is_subscribed(callback.from_user.id):
        await callback.answer("⚠️ Сначала необходимо приобрести подписку!", show_alert=True)
        return
        
    text = (
        "📊 <b>Выберите криптовалюту для отслеживания:</b>\n\n"
        "Выберите одну из популярных криптовалют ниже:"
    )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=currency_keyboard()
    )
    logger.info(f"Пользователь {callback.from_user.id} перешел к выбору валюты")

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    welcome_text = (
        "👋 <b>Добро пожаловать в Crypto Tracker Bot!</b>\n\n"
        "🤖 Я помогу вам отслеживать изменения курсов криптовалют в реальном времени.\n\n"
        "🔔 <i>Для начала работы необходимо приобрести подписку</i>"
    )
    
    await callback.message.edit_caption(
        caption=welcome_text,
        parse_mode="HTML",
        reply_markup=welcome_keyboard()
    )



@router.callback_query(F.data == "check_payment")
async def check_payment_handler(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        logger.info(f"Пользователь {user_id} запрашивает проверку оплаты")
        
        # Получаем последний активный инвойс пользователя
        invoice_data = get_active_invoice(user_id)
        
        if not invoice_data:
            check_text = (
                "❌ <b>Активный платеж не найден</b>\n\n"
                "У вас нет активных платежей для проверки.\n"
                "Пожалуйста, создайте новый платеж."
            )
            
            from keyboards.main import welcome_keyboard
            has_subscription = is_subscribed(user_id)
            try:
                await callback.message.edit_text(
                    text=check_text,
                    parse_mode="HTML",
                    reply_markup=welcome_keyboard(has_subscription)
                )
            except:
                await callback.message.edit_caption(
                    caption=check_text,
                    parse_mode="HTML",
                    reply_markup=welcome_keyboard(has_subscription)
                )
            return
        
        invoice_id, hash, amount, currency = invoice_data
        
        # Проверяем статус инвойса через CryptoBot API
        invoice_status = await check_invoice_status(invoice_id)
        
        if not invoice_status:
            check_text = (
                "❌ <b>Ошибка проверки платежа</b>\n\n"
                "Не удалось получить информацию о платеже.\n"
                "Пожалуйста, попробуйте позже."
            )
            
            from keyboards.main import payment_keyboard
            try:
                await callback.message.edit_text(
                    text=check_text,
                    parse_mode="HTML",
                    reply_markup=payment_keyboard()
                )
            except:
                await callback.message.edit_caption(
                    caption=check_text,
                    parse_mode="HTML",
                    reply_markup=payment_keyboard()
                )
            return
        
        status = invoice_status.get("status")
        logger.info(f"Статус инвойса {invoice_id}: {status}")
        
        if status in ['paid', 'confirmed']:
            # Оплата прошла успешно - активируем подписку
            # Определяем период подписки по сумме (упрощенный способ)
            # В реальном приложении лучше хранить период в invoices таблице
            from database import get_subscription_prices
            prices = get_subscription_prices()
            
            # Находим период по сумме
            period_days_map = {'day': 1, 'week': 7, 'month': 30}
            period = 'month' # дефолт
            for p, price in prices.items():
                if abs(float(amount) - price) < 0.001: # Сравнение float
                    period = p
                    break
                    
            period_days = period_days_map.get(period, 30)
            
            set_subscription(user_id, 1, period_days)
            
            period_names = {'day': 'день', 'week': 'неделю', 'month': 'месяц'}
            period_name = period_names.get(period, period)
            
            success_text = (
                f"✅ <b>Подписка на {period_name} активирована!</b>\n\n"
                "🎉 Поздравляем! Ваша подписка успешно активирована.\n"
                f"Теперь вы можете отслеживать криптовалюты на протяжении {period_days} дней."
            )
            
            from keyboards.main import subscription_success_keyboard
            try:
                await callback.message.edit_text(
                    text=success_text,
                    parse_mode="HTML",
                    reply_markup=subscription_success_keyboard()
                )
            except:
                await callback.message.edit_caption(
                    caption=success_text,
                    parse_mode="HTML",
                    reply_markup=subscription_success_keyboard()
                )
            
            # Отправляем дополнительное уведомление
            await callback.message.answer(
                "🚀 Добро пожаловать! Начните отслеживать криптовалюты прямо сейчас.",
                reply_markup=subscription_success_keyboard()
            )
            
            logger.info(f"Подписка на {period_name} ({period_days} дней) активирована для пользователя {user_id}")
            
            logger.info(f"Подписка активирована для пользователя {user_id}")
            
        elif status == 'active':
            # Платеж еще не оплачен
            check_text = (
                "⏳ <b>Ожидание оплаты</b>\n\n"
                "Ваш платеж еще не оплачен.\n"
                "Пожалуйста, завершите оплату и нажмите кнопку проверки снова."
            )
            
            from keyboards.main import invoice_keyboard
            pay_url = invoice_status.get("pay_url", "")
            try:
                await callback.message.edit_text(
                    text=check_text,
                    parse_mode="HTML",
                    reply_markup=invoice_keyboard(pay_url)
                )
            except:
                await callback.message.edit_caption(
                    caption=check_text,
                    parse_mode="HTML",
                    reply_markup=invoice_keyboard(pay_url)
                )
                
        elif status in ['cancelled', 'expired']:
            # Платеж отменен или истек
            check_text = (
                f"❌ <b>Платеж {status}</b>\n\n"
                f"Ваш платеж был {status}.\n"
                "Пожалуйста, создайте новый платеж."
            )
            
            from keyboards.main import welcome_keyboard
            has_subscription = is_subscribed(user_id)
            try:
                await callback.message.edit_text(
                    text=check_text,
                    parse_mode="HTML",
                    reply_markup=welcome_keyboard(has_subscription)
                )
            except:
                await callback.message.edit_caption(
                    caption=check_text,
                    parse_mode="HTML",
                    reply_markup=welcome_keyboard(has_subscription)
                )
        else:
            # Неизвестный статус
            check_text = (
                "❓ <b>Неизвестный статус платежа</b>\n\n"
                f"Статус: {status}\n"
                "Пожалуйста, попробуйте позже."
            )
            
            from keyboards.main import payment_keyboard
            try:
                await callback.message.edit_text(
                    text=check_text,
                    parse_mode="HTML",
                    reply_markup=payment_keyboard()
                )
            except:
                await callback.message.edit_caption(
                    caption=check_text,
                    parse_mode="HTML",
                    reply_markup=payment_keyboard()
                )
        
    except Exception as e:
        logger.error(f"Ошибка в check_payment_handler: {e}")
        await callback.answer("❌ Ошибка проверки оплаты", show_alert=True)

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment_handler(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        logger.info(f"Пользователь {user_id} запрашивает отмену оплаты")
        
        # Получаем последний активный инвойс пользователя
        invoice_data = get_active_invoice(user_id)
        
        if not invoice_data:
            await callback.answer("❌ Нет активных платежей для отмены", show_alert=True)
            return
        
        invoice_id, hash, amount, currency = invoice_data
        
        # Отменяем инвойс через CryptoBot API
        result = await cancel_invoice(invoice_id)
        
        if result:
            cancel_text = (
                "✅ <b>Платеж отменен</b>\n\n"
                "Ваш платеж успешно отменен.\n"
                "Вы можете создать новый платеж в любое время."
            )
            
            from keyboards.main import welcome_keyboard
            try:
                await callback.message.edit_text(
                    text=cancel_text,
                    parse_mode="HTML",
                    reply_markup=welcome_keyboard()
                )
            except:
                await callback.message.edit_caption(
                    caption=cancel_text,
                    parse_mode="HTML",
                    reply_markup=welcome_keyboard()
                )
            
            logger.info(f"Платеж {invoice_id} отменен для пользователя {user_id}")
        else:
            await callback.answer("❌ Ошибка отмены платежа", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в cancel_payment_handler: {e}")
        await callback.answer("❌ Ошибка отмены платежа", show_alert=True)


# @router.message(Command("test_notify"))
# async def test_notify_handler(message: Message):
    # """Тестовая команда для проверки отправки уведомлений"""
    # from services.notifications import format_notification
    
    # # Создаем тестовое уведомление
    # test_message = format_notification("BTC", 100000, 105000, 5.0, "classic")
    
    # try:
        # await message.bot.send_message(
            # chat_id=message.from_user.id,
            # text=test_message,
            # parse_mode="HTML"
        # )
        # await message.answer("✅ Тестовое уведомление отправлено!")
        # logger.info(f"Тестовое уведомление отправлено пользователю {message.from_user.id}")
    # except Exception as e:
        # await message.answer(f"❌ Ошибка отправки тестового уведомления: {e}")
        # logger.error(f"Ошибка отправки тестового уведомления пользователю {message.from_user.id}: {e}")
