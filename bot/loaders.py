import config

from redis.asyncio.client import Redis

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

from app.extras import Localizer

redis_client = Redis(
    db=config.REDIS_DB,
    host=config.REDIS_HOST,
    port=int(config.REDIS_PORT),
)

storage_key = DefaultKeyBuilder(prefix=config.REDIS_PREFIX)

storage = RedisStorage(redis=redis_client, key_builder=storage_key)

dp = Dispatcher(storage=storage)

bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")

loc = Localizer("data/texts.csv")
loc.set_language("RU")
