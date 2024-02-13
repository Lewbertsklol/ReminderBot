from enum import Enum


class MainCommands(Enum):
    START = "start"
    REMIND = "/Напоминание"
    WB_REMIND = "/Напоминание WB"
    CANCEL = "/Назад"


class WBCommands(Enum):
    BASKET = "/Корзина"
    ADD = "/Добавить товар"
    DELETE = "/Удалить товар"
    CHECK = "/Сравнить цены"
    CANCEL = "/Назад"
