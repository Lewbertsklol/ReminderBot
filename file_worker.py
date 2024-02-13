import json

from typing import Any

from item import Item


def get_users() -> dict[str, Any]:
    with open("users.json", "r") as file:
        return json.load(file)


def get_user(user_id: str) -> dict[str, Any]:
    users = get_users()
    return users.get(user_id, None)


def write_users(users: dict[str, Any]) -> None:
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)


def add_user(user_id: str, phone: str) -> None:
    users = get_users()
    if user_id in users:
        return
    users[user_id] = {
        "phone": phone,
        "wb_basket": [],
        "wb_cookies": None
    }
    write_users(users)


def add_wb_cookies(user_id: str, cookies: Any) -> None:
    users = get_users()
    users[user_id]["wb_cookies"] = cookies
    write_users(users)


def load_wb_cookies(user_id: str) -> Any | None:
    user = get_user(user_id)
    if user:
        return user["wb_cookies"]


def add_wbfile_basket(user_id: str, item: Item) -> None:
    users = get_users()
    item = item.to_dict()
    users[user_id]["wb_basket"].append(item)
    write_users(users)


def remove_wbfile_basket(user_id: str, item: Item) -> None:
    users = get_users()
    item = item.to_dict()
    users[user_id]["wb_basket"].remove(item)
    write_users(users)
