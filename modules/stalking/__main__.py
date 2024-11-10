import os

import asyncio
from logging.config import fileConfig

from tqdm import tqdm

from modules.stalking import Stalking
from modules.vkapi import VkApi
from dotenv import load_dotenv

load_dotenv()


current_dir = os.path.realpath(__file__)
current_dir = os.path.dirname(current_dir)
logging_config_path = os.path.join(current_dir, "../../config/logging_config.ini")
fileConfig(logging_config_path, disable_existing_loggers=False)

async def main():
    await Stalking(os.getenv('MONGO_URL'), os.getenv('MONGO_DB'), os.getenv('VK_API_URL'), os.getenv('VK_ACCESS_TOKEN')).build_graph(73332691)

asyncio.run(main())