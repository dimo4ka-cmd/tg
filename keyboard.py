from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUBSCRIPTIONS, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from localization import translations

def get_main_keyboard(language: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=localize("profile_button", language), callback_data="profile")],
        [InlineKeyboardButton(text=localize("remove_account_button", language), callback_data="remove_account")],
        [InlineKeyboardButton(text=localize("buy_subscription_button", language), callback_data="buy_subscription")],
        [InlineKeyboardButton(text=localize("info_button", language), callback_data="info")],
        [InlineKeyboardButton(text=localize("change_language_button", language), callback_data="change_language")]
    ])
    return keyboard

def get_subscription_keyboard(language: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{sub['name']} ({sub['price']} {sub['currency']})", callback_data=f"sub_{sub_id}") 
         for sub_id, sub in SUBSCRIPTIONS.items()]
    ] + [[InlineKeyboardButton(text=localize("cancel_button", language), callback_data="cancel")]])
    return keyboard

def get_cancel_keyboard(language: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=localize("cancel_button", language), callback_data="cancel")]
    ])

def get_confirm_keyboard(language: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=localize("confirm_button", language), callback_data="confirm"),
            InlineKeyboardButton(text=localize("cancel_button", language), callback_data="cancel")
        ]
    ])

def get_payment_keyboard(language: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=localize("check_payment_button", language), callback_data="check_payment"),
            InlineKeyboardButton(text=localize("cancel_button", language), callback_data="cancel")
        ]
    ])

def get_language_keyboard(current_language: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Switch to {lang.upper()}", callback_data=f"lang_{lang}") 
         for lang in SUPPORTED_LANGUAGES]
    ])
    return keyboard

def localize(key: str, language: str):
    return translations.get(language, translations[DEFAULT_LANGUAGE]).get(key, key)