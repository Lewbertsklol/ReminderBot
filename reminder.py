import asyncio
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from file_worker import get_users
from utils import get_price_changed


async def main():
    session = AiohttpSession()
    bot = Bot(token="6435449527:AAHct2buVqzgzZu8bRA0M3SF-PC2b5ou6Nw", session=session)

    # while True:
    #     for user in get_users().keys():
    #         diffs = get_price_changed
    #         await bot.send_message(int(user), f'{"\n".join(diffs)}')

    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
