import os

from tqdm import tqdm

from modules.vkapi import VkApi
from dotenv import load_dotenv


load_dotenv()
api = (VkApi(os.getenv('VK_API_URL'), os.getenv('VK_ACCESS_TOKEN'))
       .get_members(73332691, ['bdate', 'sex', 'country']))

print(api)