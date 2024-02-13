import re

from aiogram import types, Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from keyboards import MAIN_KB, WB_KB, CANCEL_KB
from commands import WBCommands
from wb_parser import start_auth, end_auth, parse_basket, add_wb_basket, remove_wb_basket
from file_worker import add_wbfile_basket, remove_wbfile_basket, get_user
from item import Item
from exeptions import PageIsNotLoaded, ItemIsNotAvailable, ItemHasSizes
from utils import get_price_changed

wb_router = Router()


class States(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_app_pswrd = State()
    waiting_for_link = State()
    waiting_for_size = State()
    waiting_for_delete = State()


async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите действие...", reply_markup=WB_KB)


@wb_router.message(States.waiting_for_app_pswrd, F.text == WBCommands.CANCEL.value)
async def cancel_auth(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите действие...", reply_markup=MAIN_KB)


@wb_router.message(States.waiting_for_link, F.text == WBCommands.CANCEL.value)
async def cancel_add(message: types.Message, state: FSMContext):
    await cancel(message, state)


@wb_router.message(States.waiting_for_delete, F.text == WBCommands.CANCEL.value)
async def cancel_del(message: types.Message, state: FSMContext):
    await cancel(message, state)


@wb_router.callback_query(F.data == "logging")
async def start_logging(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.message.chat.id
    print(f"user {user_id} | /Авторизоваться")  # ! лог
    await callback.message.answer("Введите номер телефона в формате 7XXXXXXXXXX", reply_markup=CANCEL_KB)
    await state.set_state(States.waiting_for_phone_number)


@wb_router.message(States.waiting_for_phone_number, F.text.isdigit())
async def first_step(message: types.Message, state: FSMContext):
    await message.answer("Загрузка...")
    user_id = str(message.chat.id)
    phone = message.text
    print(f"user {user_id} | Пользователь ввёл телефон: {phone}")  # ! лог
    driver = start_auth(user_id, phone)
    await state.set_state(States.waiting_for_app_pswrd)
    await state.update_data(driver=driver)
    await message.answer(
        "Введите пароль из мобильного приложения WB или личного кабинета на сайте",
        reply_markup=CANCEL_KB
    )


@wb_router.message(States.waiting_for_app_pswrd)
async def second_step(message: types.Message, state: FSMContext):
    await message.answer("Загрузка...")
    user_id = str(message.chat.id)

    pswrd = message.text.replace(" ", "")
    print(f"user {user_id} | Пользователь ввёл код из приложения: {pswrd}")  # ! лог

    data = await state.get_data()
    driver = data["driver"]

    auth = end_auth(user_id, pswrd, driver)
    await message.answer(
        f"{auth}",
        reply_markup=WB_KB
    )
    await state.clear()


@wb_router.message(F.text == WBCommands.BASKET.value)
async def basket(message: types.Message):
    print(f"user {message.chat.id} | /Корзина")  # ! лог
    await message.answer(f"Подгружаем актуальные цены...")
    user_id = str(message.chat.id)

    try:
        basket = parse_basket(user_id)
    except PageIsNotLoaded:
        print(f"user {user_id} | Страница недоступна")  # ! лог
        await message.answer(f"Страница недоступна, попробуйте еще раз", reply_markup=WB_KB)
        return

    if not basket:
        await message.answer(f"Корзина пуста", reply_markup=WB_KB)
        return

    await message.answer(
        "\n".join([f"{item.name}, {item.maker}: {item.price}" for item in basket]),
        reply_markup=WB_KB
    )


@wb_router.message(F.text == WBCommands.ADD.value)
async def add(message: types.Message, state: FSMContext):
    print(f"user {message.chat.id} | /Добавить товар")  # ! лог
    await message.answer(
        "Добавьте ссылку на товар",
        reply_markup=CANCEL_KB
    )
    await state.set_state(States.waiting_for_link)


@wb_router.message(States.waiting_for_link)
async def item_added(message: types.Message, state: FSMContext):
    user_id = str(message.chat.id)

    url_pattern = r'https://[\S]+'
    url = re.findall(url_pattern, message.text)
    if not url:
        await message.answer(f"Вы ввели что-то непонятное", reply_markup=WB_KB)
        await state.clear()
        return
    else:
        url = url[0]

    await message.answer(f"Добавляем...")

    try:
        item = add_wb_basket(user_id, url)
    except PageIsNotLoaded:
        print(f"user {user_id} | Ссылка недоступна: {url}")  # ! лог
        await message.answer(f"Ссылка недоступна, попробуйте еще раз", reply_markup=WB_KB)
        await state.clear()
        return
    except ItemIsNotAvailable:
        print(f"user {user_id} | Товара нет в наличии: {url}")  # ! лог
        await message.answer(f"Товара нет в наличии", reply_markup=WB_KB)
        await state.clear()
        return
    except ItemHasSizes as sizes:
        sizes = [f"{index + 1}. {size}" for index, size in enumerate(sizes.sizes_list)]
        await message.answer(f"Выберите порядковый номер размера:\n{"\n".join(sizes)}", reply_markup=CANCEL_KB)
        await state.update_data(url=url)
        await state.set_state(States.waiting_for_size)
        return

    add_wbfile_basket(user_id, item)
    print(f"user {user_id} | Добавлен товар: {item} по ссылке: {url}")  # ! лог
    await message.answer(
        f"Товар добавлен\n{item.name}, {item.maker}: {item.price}", reply_markup=WB_KB
    )
    await state.clear()


@wb_router.message(States.waiting_for_size)
async def choose_size(message: types.Message, state: FSMContext):
    user_id = str(message.chat.id)

    if not message.text.isdigit():
        await message.answer(f"Выберите порядковый номер размера", reply_markup=WB_KB)
        return

    size = int(message.text) - 1
    print(f"user {user_id} | Выбран размер {size}")  # ! лог

    data = await state.get_data()
    url = data["url"]

    await message.answer(f"Добавляем...")

    try:
        item = add_wb_basket(user_id, url, size)
    except PageIsNotLoaded:
        print(f"user {user_id} | Ссылка недоступна: {url}")  # ! лог
        await message.answer(f"Ссылка недоступна, попробуйте еще раз", reply_markup=WB_KB)
        await state.clear()
        return
    except ItemIsNotAvailable:
        print(f"user {user_id} | Товара нет в наличии: {url}")  # ! лог
        await message.answer(f"Товара нет в наличии", reply_markup=WB_KB)
        await state.clear()
        return

    add_wbfile_basket(user_id, item)
    print(f"user {user_id} | Добавлен товар: {item} по ссылке: {url}")  # ! лог
    await message.answer(
        f"Товар добавлен\n{item.name}, {item.maker}: {item.price}"
        f"\nРазмер: {item.size}",
        reply_markup=WB_KB
    )
    await state.clear()


@wb_router.message(F.text == WBCommands.DELETE.value)
async def delete(message: types.Message, state: FSMContext):
    user_id = str(message.chat.id)
    print(f"user {user_id} | /Удалить товар")  # ! лог

    items_from_file = get_user(user_id)["wb_basket"]

    if not items_from_file:
        await message.answer(f"Корзина пуста", reply_markup=WB_KB)
        return

    await message.answer(
        f'{"\n".join(
            [f'{num + 1}. {item["name"]}, {item["maker"]}' for num, item in enumerate(items_from_file)]
        )}'
    )

    await message.answer("Введите номер товара", reply_markup=CANCEL_KB)
    await state.set_state(States.waiting_for_delete)


@wb_router.message(States.waiting_for_delete)
async def delete(message: types.Message, state: FSMContext):
    await message.answer(f"Удаляем...")
    user_id = str(message.chat.id)
    delete_num = int(message.text)

    item = Item.from_dict(get_user(user_id)["wb_basket"][delete_num - 1])

    remove_wb_basket(user_id, item)
    remove_wbfile_basket(user_id, item)

    await message.answer(
        "Товар удалён\n"
        f"{item.name}: {item.maker}",
        reply_markup=WB_KB
    )
    await state.clear()


@wb_router.message(F.text == WBCommands.CHECK.value)
async def chek_prices(message: types.Message):
    await message.answer(f"Сравниваем...")
    user_id = str(message.chat.id)
    print(f"user {user_id} | /Сравнить цены")  # ! лог

    diffs = get_price_changed(user_id)
    await message.answer(f'{"\n".join(diffs)}', reply_markup=WB_KB)
