from item import Item
from wb_parser import parse_basket
from file_worker import get_user


def get_price_changed(user_id: str) -> list[str]:

    items_from_file = [Item.from_dict(item) for item in get_user(user_id)["wb_basket"]]
    basket = parse_basket(user_id)

    diffs = []
    for item_from_file, item_from_basket in zip(items_from_file, basket):

        item_from_file.price = int(item_from_file.price.replace('₽', ''))
        item_from_basket.price = int(item_from_basket.price.replace('₽', ''))

        if item_from_file.price > item_from_basket.price:
            diff = item_from_file.price - item_from_basket.price
            diffs.append(f'↓ Цена товара {item_from_file.name}, {item_from_file.maker}: -{diff} ₽')
        if item_from_file.price < item_from_basket.price:
            diff = item_from_basket.price - item_from_file.price
            diffs.append(f'↑ Цена товара {item_from_file.name}, {item_from_file.maker}: +{diff} ₽')

    if diffs:
        diffs.insert(0, "↓↑ Цены изменились:")
    else:
        diffs.append("↓↑ Цены пока без изменений")

    return diffs
