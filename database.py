import sqlite3
from datetime import datetime, timedelta
from config import SUBSCRIPTIONS
import logging

logger = logging.getLogger(__name__)

def init_db():
    try:
        with sqlite3.connect("subscriptions.db") as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id TEXT PRIMARY KEY,
                    subscription_id TEXT,
                    end_date TEXT,
                    language TEXT DEFAULT 'ru'
                )
            """)
            conn.commit()
        logger.info("Database table 'subscriptions' created or verified")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise

def save_subscription(user_id: str, subscription_id: str, language: str = "ru"):
    try:
        with sqlite3.connect("subscriptions.db") as conn:
            c = conn.cursor()
            end_date = (datetime.now() + timedelta(days=SUBSCRIPTIONS[subscription_id]["duration_days"])).isoformat()
            c.execute("INSERT OR REPLACE INTO subscriptions (user_id, subscription_id, end_date, language) VALUES (?, ?, ?, ?)",
                      (user_id, subscription_id, end_date, language))
            conn.commit()
        logger.info(f"Subscription saved for user {user_id}: {subscription_id}, language: {language}")
    except sqlite3.Error as e:
        logger.error(f"Failed to save subscription for user {user_id}: {e}")
        raise

def get_subscription(user_id: str):
    try:
        with sqlite3.connect("subscriptions.db") as conn:
            c = conn.cursor()
            c.execute("SELECT subscription_id, end_date, language FROM subscriptions WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            if result:
                subscription_id, end_date, language = result
                if datetime.fromisoformat(end_date) > datetime.now():
                    days_left = (datetime.fromisoformat(end_date) - datetime.now()).days
                    if days_left <= 3:
                        return subscription_id, end_date, language, f"Ваша подписка истекает через {days_left} дней!"
                    return subscription_id, end_date, language, None
            return None, None, "ru", "Подписка отсутствует или истекла"
    except sqlite3.Error as e:
        logger.error(f"Failed to get subscription for user {user_id}: {e}")
        raise