import os
import logging
import asyncio
from telethon.sync import TelegramClient

from config import CONFIG
from bot.events import add_event_handlers

os.makedirs('../logs/', exist_ok=True)

logging.getLogger('telethon').setLevel(logging.WARNING)
logging.basicConfig(
    format='%(levelname)-5s %(module)s:%(lineno)d# [%(asctime)s] %(message)s',
    level=logging.DEBUG,
    filename='../logs/bot.log'
)


async def main():
    client = await TelegramClient(
        'bot',
        CONFIG.telegram_bot.api_id,
        CONFIG.telegram_bot.api_hash,
    ).start(bot_token=CONFIG.telegram_bot.api_token)
    add_event_handlers(client)

    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())