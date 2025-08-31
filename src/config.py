import json
from dataclasses import dataclass
from typing import List


@dataclass
class Db:
    db_uri: str


@dataclass
class TelegramBot:
    api_id: int
    api_hash: str
    api_token: str
    phone_number: str
    bot_admins: List[str]


@dataclass
class ConfigData:
    db: Db
    telegram_bot: TelegramBot

    @classmethod
    def load_settings(cls):
        with open('/etc/app/config.json', 'r') as config_file:
            config_dict = json.load(config_file)
        return cls(
            db=Db(**config_dict['db']),
            telegram_bot=TelegramBot(**config_dict['bot'])
        )

CONFIG = ConfigData.load_settings()
