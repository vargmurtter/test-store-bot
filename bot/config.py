import os
from dotenv import load_dotenv
from typing import cast


load_dotenv(override=True)


# Bot config
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_LINK = os.getenv("BOT_LINK")

BOT_ALIVE = os.getenv("BOT_ALIVE")
BOT_ALIVE = True if BOT_ALIVE == "1" else False

DEBUG_MODE = os.getenv("DEBUG_MODE")
DEBUG_MODE = True if DEBUG_MODE == "1" else False

# redis config
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_DB = os.getenv("REDIS_DB")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PREFIX = os.getenv("REDIS_PREFIX")

# postgres config
POSTGRES_CONN = os.getenv("POSTGRES_CONN")
TORTOISE_ORM = {
    "connections": {"default": POSTGRES_CONN},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

UKASSA_TOKEN = os.getenv("UKASSA_TOKEN")

ADMIN_IMAGES_URL = os.getenv("ADMIN_IMAGES_URL")

CHANNEL_ID = -1002003721015
CHANNEL_URL = "https://t.me/murtter_test_channel"

GROUP_ID = -1002117878359
GROUP_URL = "https://t.me/murtter_test_group"

POSTERS_DIR = "../admin/store/media"

XLS_FILE_PATH = "data/orders.xlsx"


QUESTIONS = [
    {
        "q": "Почему цены такие низкие?",
        "a": "Потому что вбивались они от балды!",
    },
    {
        "q": "Как долго доставляется заказ?",
        "a": "Вечность! Ведь это тестовый бот.",
    },
    {"q": "В какие города есть доставка?", "a": "Спросите что полегче..."},
    {
        "q": "Почему доставка бесплатная?",
        "a": "Потому что программисту было лень :3",
    },
    {
        "q": "Как отменить заказ?",
        "a": "Напишите администратору. А его почту угадайте сами :)",
    },
]
