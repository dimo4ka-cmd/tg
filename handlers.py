from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, SUBSCRIPTIONS, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from keyboards import get_main_keyboard, get_subscription_keyboard, get_cancel_keyboard, get_confirm_keyboard, get_payment_keyboard, get_language_keyboard
from states import OrderStates
from crypto_api import create_invoice, check_invoice_status
from database import get_subscription, save_subscription
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def notify_admin(bot: types.Bot, message: str):
    try:
        await bot.send_message(ADMIN_ID, message)
        logger.info(f"Admin notified: {message}")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

async def start_command(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    _, _, language, _ = get_subscription(user_id)
    welcome_msg = f"🎉 {localize('welcome_message', language)}"
    await message.answer(
        welcome_msg,
        reply_markup=get_main_keyboard(language)
    )
    await state.clear()
    logger.info(f"User {user_id} started the bot with language {language}")

async def handle_menu(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    subscription_id, end_date, language, subscription_notice = get_subscription(user_id)

    if message.text == localize("profile_button", language):
        user = message.from_user
        sub_info = f"📅 {localize('subscription', language)}: {SUBSCRIPTIONS[subscription_id]['name']}\n📅 {localize('expires', language)}: {end_date}" if subscription_id else f"📅 {localize('subscription', language)}: {localize('no_subscription', language)}"
        response = f"👤 **{localize('user_info', language)}:**\n🆔 {localize('id', language)}: {user.id}\n👤 {localize('name', language)}: {user.full_name}\n📧 {localize('username', language)}: @{user.username or localize('no_username', language)}\n📅 {localize('reg_date', language)}: {localize('not_available', language)}\n{sub_info}"
        if subscription_notice:
            response += f"\n⚠️ {subscription_notice}"
        await message.answer(response, reply_markup=get_main_keyboard(language))
        logger.info(f"Profile shown for user {user_id} in {language}")
    elif message.text == localize("remove_account_button", language):
        if subscription_id:
            await message.answer(
                f"🔍 {localize('enter_target', language)}",
                reply_markup=get_cancel_keyboard(language)
            )
            await state.set_state(OrderStates.ENTER_TARGET)
            logger.info(f"User {user_id} started account removal process in {language}")
        else:
            await message.answer(
                f"❌ {localize('need_subscription', language)}",
                reply_markup=get_main_keyboard(language)
            )
            logger.info(f"User {user_id} lacks subscription for account removal in {language}")
    elif message.text == localize("buy_subscription_button", language):
        await message.answer(
            f"💰 {localize('select_subscription', language)}",
            reply_markup=get_subscription_keyboard(language)
        )
        await state.set_state(OrderStates.SELECT_SUBSCRIPTION)
        logger.info(f"User {user_id} started subscription purchase in {language}")
    elif message.text == localize("info_button", language):
        await message.answer(
            f"ℹ️ **{localize('service_info', language)} (по состоянию на 09:44 AM EEST, 23 мая 2025 года):**\n"
            f"📌 {localize('service_name', language)}\n"
            f"🔧 {localize('how_it_works', language)}\n"
            f"1. 💸 {localize('buy_plan', language)}\n"
            f"2. 🔍 {localize('enter_target_account', language)}\n"
            f"3. 🚀 {localize('send_complaints', language)}\n"
            f"⚠️ {localize('warning', language)} {localize('no_guarantee', language)}\n"
            f"📞 {localize('support', language)}",
            reply_markup=get_main_keyboard(language)
        )
        logger.info(f"User {user_id} accessed service information in {language}")
    elif message.text == localize("change_language_button", language):
        await message.answer(
            f"🌐 {localize('select_language', language)}",
            reply_markup=get_language_keyboard(language)
        )
        logger.info(f"User {user_id} requested language change in {language}")
    else:
        await message.answer(f"❓ {localize('invalid_input', language)}", reply_markup=get_main_keyboard(language))
        logger.info(f"User {user_id} sent invalid input: {message.text} in {language}")

async def select_subscription(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    _, _, language, _ = get_subscription(user_id)
    if message.text == localize("cancel_button", language):
        await message.answer(f"🚫 {localize('action_canceled', language)}", reply_markup=get_main_keyboard(language))
        await state.clear()
        logger.info(f"User {user_id} canceled subscription selection in {language}")
        return
    selected_sub = None
    for sub_id, sub in SUBSCRIPTIONS.items():
        if message.text.startswith(sub["name"]):
            selected_sub = sub_id
            break
    if selected_sub:
        await state.update_data(subscription_id=selected_sub)
        await message.answer(
            f"✅ {localize('selected', language)}: {SUBSCRIPTIONS[selected_sub]['name']} ({SUBSCRIPTIONS[selected_sub]['price']} {SUBSCRIPTIONS[selected_sub]['currency']})\n"
            f"💸 {localize('confirm_purchase', language)}:",
            reply_markup=get_confirm_keyboard(language)
        )
        await state.set_state(OrderStates.CONFIRM_ORDER)
        logger.info(f"User {user_id} selected subscription: {selected_sub} in {language}")
    else:
        await message.answer(f"❌ {localize('select_valid_plan', language)}", reply_markup=get_subscription_keyboard(language))
        logger.info(f"User {user_id} selected invalid subscription in {language}")

async def confirm_order(message: types.Message, state: FSMContext, bot: types.Bot):
    user_id = str(message.from_user.id)
    _, _, language, _ = get_subscription(user_id)
    if message.text == localize("cancel_button", language):
        await message.answer(f"🚫 {localize('action_canceled', language)}", reply_markup=get_main_keyboard(language))
        await state.clear()
        logger.info(f"User {user_id} canceled order in {language}")
        return
    if message.text != localize("confirm_button", language):
        await message.answer(f"❓ {localize('confirm_or_cancel', language)}")
        logger.info(f"User {user_id} sent invalid confirmation in {language}")
        return

    user_data = await state.get_data()
    subscription_id = user_data.get("subscription_id")
    target = user_data.get("target")

    if subscription_id:  # Покупка подписки
        description = f"Покупка подписки: {SUBSCRIPTIONS[subscription_id]['name']}"
        try:
            invoice_data = create_invoice(subscription_id, description)
            if invoice_data:
                invoice_id, invoice_url = invoice_data
                await state.update_data(invoice_id=invoice_id)
                await message.answer(
                    f"💳 {localize('invoice_created', language)}! {localize('pay_here', language)}:\n{invoice_url}\n"
                    f"✅ {localize('check_payment', language)}.",
                    reply_markup=get_payment_keyboard(language)
                )
                await state.set_state(OrderStates.CHECK_PAYMENT)
                await notify_admin(bot, f"Новый заказ подписки!\nПользователь: @{message.from_user.username or message.from_user.full_name}\nПодписка: {SUBSCRIPTIONS[subscription_id]['name']}\nСчет: {invoice_url}")
                logger.info(f"Invoice created for user {user_id}: {invoice_url} in {language}")
            else:
                await message.answer(f"❌ {localize('invoice_error', language)}")
                logger.error(f"Failed to create invoice for user {user_id} in {language}")
                await state.clear()
        except Exception as e:
            await message.answer(f"❌ {localize('order_error', language)}")
            logger.error(f"Exception during invoice creation for user {user_id}: {e} in {language}")
            await state.clear()
    elif target:  # Заказ сноса аккаунта
        try:
            await notify_admin(bot, f"Новый заказ сноса!\nПользователь: @{message.from_user.username or message.from_user.full_name}\nЦель: {target}")
            await message.answer(
                f"✅ {localize('order_accepted', language)}",
                reply_markup=get_main_keyboard(language)
            )
            await state.clear()
            logger.info(f"Account removal order placed by user {user_id} for target {target} in {language}")
        except Exception as e:
            await message.answer(f"❌ {localize('order_error', language)}")
            logger.error(f"Exception during account removal order for user {user_id}: {e} in {language}")
            await state.clear()

async def check_payment(message: types.Message, state: FSMContext, bot: types.Bot):
    user_id = str(message.from_user.id)
    _, _, language, _ = get_subscription(user_id)
    if message.text == localize("cancel_button", language):
        await message.answer(f"🚫 {localize('action_canceled', language)}", reply_markup=get_main_keyboard(language))
        await state.clear()
        logger.info(f"User {user_id} canceled payment check in {language}")
        return
    if message.text != localize("check_payment_button", language):
        await message.answer(f"❓ {localize('check_or_cancel', language)}")
        logger.info(f"User {user_id} sent invalid payment check input in {language}")
        return

    user_data = await state.get_data()
    invoice_id = user_data["invoice_id"]
    subscription_id = user_data["subscription_id"]

    try:
        status, invoice_url = check_invoice_status(invoice_id)
        if status == "paid":
            save_subscription(user_id, subscription_id, language)
            await message.answer(
                f"💸 {localize('payment_confirmed', language)}! 🎉 {localize('subscription_activated', language)} {SUBSCRIPTIONS[subscription_id]['name']}!",
                reply_markup=get_main_keyboard(language)
            )
            await notify_admin(bot, f"Оплата подтверждена!\nПользователь: @{message.from_user.username or message.from_user.full_name}\nПодписка: {SUBSCRIPTIONS[subscription_id]['name']}\nСчет: {invoice_url}")
            await state.clear()
            logger.info(f"Payment confirmed for user {user_id} in {language}")
        elif status:
            await message.answer(
                f"⏳ {localize('payment_pending', language)}",
                reply_markup=get_payment_keyboard(language)
            )
            logger.info(f"Payment pending for user {user_id} in {language}")
        else:
            await message.answer(f"❌ {localize('payment_check_error', language)}")
            logger.error(f"Payment check failed for user {user_id} in {language}")
    except Exception as e:
        await message.answer(f"❌ {localize('payment_check_error', language)}")
        logger.error(f"Exception during payment check for user {user_id}: {e} in {language}")
        await state.clear()

def setup_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(select_subscription, OrderStates.SELECT_SUBSCRIPTION)
    dp.message.register(enter_target, OrderStates.ENTER_TARGET)
    dp.message.register(lambda message, state, bot=dp.bot: confirm_order(message, state, bot), OrderStates.CONFIRM_ORDER)
    dp.message.register(lambda message, state, bot=dp.bot: check_payment(message, state, bot), OrderStates.CHECK_PAYMENT)
    dp.message.register(handle_menu)

async def enter_target(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    _, _, language, _ = get_subscription(user_id)
    if message.text == localize("cancel_button", language):
        await message.answer(f"🚫 {localize('action_canceled', language)}", reply_markup=get_main_keyboard(language))
        await state.clear()
        logger.info(f"User {user_id} canceled target entry in {language}")
        return
    await state.update_data(target=message.text)
    await message.answer(
        f"🔍 {localize('target_confirmation', language)}: {message.text}\n"
        f"💸 {localize('confirm_order', language)}:",
        reply_markup=get_confirm_keyboard(language)
    )
    await state.set_state(OrderStates.CONFIRM_ORDER)
    logger.info(f"User {user_id} entered target: {message.text} in {language}")

def localize(key: str, language: str):
    from localization import translations
    return translations.get(language, translations[DEFAULT_LANGUAGE]).get(key, key)