from aiogram import types

from commands import MainCommands, WBCommands

MAIN_KB = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text=f"{MainCommands.REMIND.value}"),
            types.KeyboardButton(text=f"{MainCommands.WB_REMIND.value}"),
        ],
    ],
    resize_keyboard=True,
)


CANCEL_KB = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text=f"{MainCommands.CANCEL.value}")
        ]
    ],
    resize_keyboard=True
)

WB_KB = types.ReplyKeyboardMarkup(
    keyboard=[
        [

            types.KeyboardButton(text=WBCommands.ADD.value),
            types.KeyboardButton(text=WBCommands.DELETE.value),

        ],
        [
            types.KeyboardButton(text=WBCommands.BASKET.value),
            types.KeyboardButton(text=WBCommands.CHECK.value),
            types.KeyboardButton(text=WBCommands.CANCEL.value),
        ]

    ],
    resize_keyboard=True,
)
