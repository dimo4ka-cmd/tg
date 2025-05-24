import requests
import json
import logging
from config import CRYPTO_BOT_TOKEN

def create_invoice(subscription_id: str, description: str):
    from config import SUBSCRIPTIONS
    payload = {
        "amount": SUBSCRIPTIONS[subscription_id]["price"],
        "currency": SUBSCRIPTIONS[subscription_id]["currency"],
        "description": description,
    }
    headers = {"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}
    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            headers=headers,
            data=json.dumps(payload)
        )
        if response.status_code == 200:
            invoice = response.json()["result"]
            return invoice["invoice_id"], invoice["pay_url"]
        else:
            logging.error(f"Ошибка CryptoBot API: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при создании счета: {e}")
        return None

def check_invoice_status(invoice_id: str):
    headers = {"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}
    try:
        response = requests.get(
            f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}",
            headers=headers
        )
        if response.status_code == 200:
            invoice = response.json()["result"]["items"][0]
            return invoice["status"], invoice["pay_url"]
        else:
            logging.error(f"Ошибка CryptoBot API: {response.text}")
            return None, None
    except Exception as e:
        logging.error(f"Ошибка при проверке оплаты: {e}")
        return None, None