from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    SELECT_SUBSCRIPTION = State()  # Выбор подписки
    ENTER_TARGET = State()         # Ввод юзернейма/канала
    CONFIRM_ORDER = State()       # Подтверждение заказа
    CHECK_PAYMENT = State()       # Проверка оплаты