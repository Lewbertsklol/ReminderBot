import time

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from file_worker import get_user, add_user, add_wb_cookies, load_wb_cookies
from item import Item
from exeptions import PageIsNotLoaded, ItemIsNotAvailable, ItemHasSizes


def launch_browser():
    options = Options()
    # options.add_experimental_option("detach", True)                  # !
    # options.add_argument(f"--user-data-dir={os.getcwd()}/profiles")  # !
    # options.add_argument("--profile-directory=Default")              # ! Dont close browser ever option
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )
    driver.maximize_window()
    return driver


def start_auth(user_id: str, phone: str) -> WebDriver:
    driver = launch_browser()
    driver.get("https://www.wildberries.ru/security/login?returnUrl=https%3A%2F%2Fwww.wildberries.ru%2F")
    phone_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div/div/form/div/div[1]/div/div[2]/input')))
    phone_field.clear()
    phone_field.send_keys(f'+{phone}')
    time.sleep(1)
    get_pass = driver.find_element(By.ID, 'requestCode')
    get_pass.click()
    add_user(user_id, phone)
    return driver


def end_auth(user_id: str, pswrd: str, driver: WebDriver) -> str:
    pass_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="spaAuthForm"]/div/div[4]/div/input[1]')
        )
    )
    pass_field.send_keys(pswrd)
    time.sleep(1)
    add_wb_cookies(user_id, driver.get_cookies())
    return "Вы успешно авторизованы, ваш профиль сохранён."


def parse_basket(user_id: str) -> list[Item]:
    user = get_user(user_id)
    if not user['wb_basket']:
        return []

    cookies = load_wb_cookies(user_id)
    driver = launch_browser()
    driver.get("https://www.wildberries.ru/lk/basket")
    [driver.add_cookie(cookie) for cookie in cookies]

    try:
        basket = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]/div[4]/div/div[1]/form/div[1]')
            )
        )
        basket = WebDriverWait(basket, 10).until(
            EC.presence_of_all_elements_located(  # находим все элементы в поле с корзиной (там не только товары)
                (By.XPATH, '//*[@id="app"]/div[4]/div/div[1]/form/div[1]/div[1]'))
        )
    except TimeoutException:
        raise PageIsNotLoaded()

    try:
        names = [
            name.text for name in [  # находим имена производителей в корзине
                element.find_elements(
                    By.XPATH,
                    '//*[@id="app"]/div[4]/div/div[1]/form/div[1]/div[1]/div[2]/div/div/div/div/div/div/div[1]/div/a/span[1]'
                ) for element in basket
            ][0]
        ]

        makers = [  # находим имена производителей в корзине
            maker.text.replace(', ', '') for maker in [
                element.find_elements(
                    By.XPATH,
                    '//*[@id="app"]/div[4]/div/div[1]/form/div[1]/div[1]/div[2]/div/div/div/div/div/div/div[1]/div/a/span[2]'
                ) for element in basket
            ][0]
        ]
        prices = [  # находим цены в корзине
            price.text for price in [
                element.find_elements(
                    By.CLASS_NAME, 'list-item__price-new'
                ) for element in basket
            ][0]
        ]
    except TimeoutException:
        return []

    basket_size = len(names)
    return [
        Item(
            name=names[index],
            maker=makers[index],
            price=prices[index]
        )
        for index in range(basket_size)
        if names[index] in [item["name"] for item in user["wb_basket"]]
        and makers[index] in [item["maker"] for item in user["wb_basket"]]
    ]


def add_wb_basket(user_id: str, url: str, size: int = None) -> Item:
    cookies = load_wb_cookies(user_id)
    driver = launch_browser()
    driver.get(url)
    [driver.add_cookie(cookie) for cookie in cookies]

    try:
        grid = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'product-page__grid')
            )
        )
    except TimeoutException:
        raise PageIsNotLoaded()

    if size is None:
        try:
            sizes_list = grid.find_element(By.CLASS_NAME, 'sizes-list')
            sizes_list = [
                size.text.replace('\n', ' ')
                for size in sizes_list.find_elements(By.CLASS_NAME, 'sizes-list__item')]
            raise ItemHasSizes(sizes_list)
        except NoSuchElementException:
            pass
    else:
        sizes_list = grid.find_element(By.CLASS_NAME, 'sizes-list')
        sizes = sizes_list.find_elements(By.CLASS_NAME, 'sizes-list__item')
        sizes[size].click()
        time.sleep(1)
        size = sizes[size].text.replace('\n', ' ')

    try:
        button_add_to_basket = WebDriverWait(grid, 10).until(
            EC.element_to_be_clickable([
                button for button in WebDriverWait(grid, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, 'hide-mobile')
                    )
                ) if button.text == "Добавить в корзину"
            ][0])
        )
        button_add_to_basket.click()
        time.sleep(1)
    except IndexError:
        raise ItemIsNotAvailable()

    maker, name = WebDriverWait(grid, 10).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, 'product-page__header')
        )
    ).text.split('\n')

    price = [line for line in WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, 'app')
        )
    ).text.split('\n') if line.endswith('₽')][0]

    return Item(name=name, maker=maker, price=price, size=size)


def remove_wb_basket(user_id: int, item: Item) -> None:
    cookies = load_wb_cookies(user_id)
    driver = launch_browser()
    driver.get("https://www.wildberries.ru/lk/basket")
    [driver.add_cookie(cookie) for cookie in cookies]

    try:
        basket = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(  # находим поле с корзиной
                (By.XPATH,
                 '//*[@id="app"]/div[4]/div/div[1]/form/div[1]')
            )
        )
        basket = WebDriverWait(basket, 10).until(
            EC.presence_of_all_elements_located(  # находим все элементы в поле с корзиной (там не только товары)
                (By.XPATH, '//*[@id="app"]/div[4]/div/div[1]/form/div[1]/div[1]')
            )
        )
    except TimeoutException:
        raise PageIsNotLoaded()

    names = [
        name.text for name in [  # находим имена товаров в корзине
            element.find_elements(
                By.XPATH,
                '//*[@id="app"]/div[4]/div/div[1]/form/div[1]/div[1]/div[2]/div/div/div/div/div/div/div[1]/div/a/span[1]'
            ) for element in basket
        ][0]
    ]

    makers = [  # находим имена продавцов в корзине
        maker.text.replace(', ', '') for maker in [
            element.find_elements(
                By.XPATH,
                '//*[@id="app"]/div[4]/div/div[1]/form/div[1]/div[1]/div[2]/div/div/div/div/div/div/div[1]/div/a/span[2]'
            ) for element in basket
        ][0]
    ]

    del_buttons = driver.find_elements(
        By.CLASS_NAME,
        'btn__del.j-basket-item-del'
    )

    items = [
        Item(name=names[index], maker=makers[index])
        for index in range(len(names))
    ]
    if item in items:
        del_buttons[items.index(item)].click()
        time.sleep(1)
