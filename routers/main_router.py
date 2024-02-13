from aiogram import types, Router, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_dialog import DialogManager, StartMode

from keyboards import MAIN_KB, WB_KB
from file_worker import load_wb_cookies
from commands import MainCommands

main_router = Router()


@main_router.message(Command(f"{MainCommands.START.value}"))
async def cmd_start(message: types.Message):
    text = "Привет! Я Second Memory Bot - твоя вторая память.\n" \
        "Я умею запоминать необходимые тебе вещи и напоминать тебе о них в нужную минуту.\n"\
        "Я могу создавать не только простые напоминания, "\
        "но также уведомлять тебя об изменении цен товаров на различных маркетплейсах и их наличии на складах!\n"\
        "Основные команды:\n"\
        f"<b>{MainCommands.REMIND.value}</b> - создать простое напоминание.\n"\
        f"<b>{MainCommands.WB_REMIND.value}</b> - отслеживание товаров на маркетплейсе Wildberries.\n"\
        "Просто нажми на нужную кнопку и следуй моим инструкциям."
    await message.answer(text, reply_markup=MAIN_KB, parse_mode=ParseMode.HTML)


@main_router.message(F.text == MainCommands.REMIND.value)
async def remind(message: types.Message, dialog_manager: DialogManager):
    pass


@main_router.message(F.text == MainCommands.WB_REMIND.value)
async def wb_remind(message: types.Message):
    user_id = str(message.chat.id)
    print(f"user {user_id} | /Напоминание WB")  # ! лог
    if load_wb_cookies(user_id):
        print(f"user {user_id} | Вошёл в WB панель")  # ! лог
        text = "Выберите действие..."
        await message.answer(text, reply_markup=WB_KB)
    else:
        print(f"user {user_id} | Первый вход в WB панель, прохождение регистрации")  # ! лог
        text = "Для работы с площадкой Wildberries мне необходим ваш профиль. "\
            "Пройдите простую авторизацию для начала работы!"
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="Авторизоваться",
            callback_data="logging")
        )
        await message.answer(text, reply_markup=builder.as_markup())


@main_router.message(F.text == MainCommands.CANCEL.value)
async def cancel_deleting(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    print(f"user {user_id} | /Отмена")  # ! лог
    await state.clear()
    text = "Выберите действие: \n"\
        f"{MainCommands.REMIND.value}\n"\
        f"{MainCommands.WB_REMIND.value}"
    await message.answer(text, reply_markup=MAIN_KB)
