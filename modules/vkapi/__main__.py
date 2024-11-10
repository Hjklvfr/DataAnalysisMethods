import os

import asyncio
from datetime import datetime

from tqdm import tqdm

from modules.vkapi import VkApi
from dotenv import load_dotenv


load_dotenv()
async def main():
       print(datetime.now())
       api = await (VkApi(os.getenv('VK_API_URL'), os.getenv('VK_ACCESS_TOKEN'))
              .get_members_with_subscriptions(73332691, False))
       print(datetime.now())
       print(api)



asyncio.run(main())