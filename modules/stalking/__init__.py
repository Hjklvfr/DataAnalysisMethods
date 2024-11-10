import asyncio
import os
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, UTC
from logging.config import fileConfig
from typing import Any, Dict

import pymongo

from modules.stalking.relations import RelationsFetcher
from modules.vkapi import VkApi

current_dir = os.path.realpath(__file__)
current_dir = os.path.dirname(current_dir)
logging_config_path = os.path.join(current_dir, "../../config/logging_config.ini")
fileConfig(logging_config_path, disable_existing_loggers=False)


def _convert_response_to_entry(data: Any) -> Dict[str, Any]:
    return {'data': data, 'timestamp': datetime.now(UTC)}

#
# Group process
# First step:
# get group
# get members ids
# N step:
# get users subscriptions (users groups)
# get members friends
#
# User process
# get user
#
# Thread 1(relations extractor) - get users and groups from existed ids
# Thread 2(group entity extractor) - process groups
# Thread 3(users entity extractor) - process users
#
#

class Stalking(object):
    def __init__(
            self,
            mongo_url: str,
            mongo_db: str,
            vk_api_url: str,
            vk_api_access_token: str
    ):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db
        self.vk_api_url = vk_api_url
        self.vk_api_access_token = vk_api_access_token

        self.mongo = pymongo.MongoClient(mongo_url)
        self.responses_db = self.mongo[mongo_db]
        self.vkapi = VkApi(vk_api_url, vk_api_access_token)

    async def build_graph(self, group_id: int):
        # if db not contains this group -> run process group
        # continue fetch relations and entities (run processes)

        group = self.responses_db['groups'].find_one({'data.id': group_id})
        if not group:
            groups = await self.vkapi.get_groups([group_id], [
                'activity',
                'city',
                'contacts',
                'counters',
                'country',
                'description',
                'finish_date',
                'fixed_post',
                'links',
                'members_count',
                'place',
                'site',
                'start_date',
                'status',
                'verified',
                'wiki_page'
            ])
            self.responses_db['groups'].insert_many(map(_convert_response_to_entry, groups))
            members_subscriptions = await self.vkapi.get_members_with_subscriptions(group_id,  False)
            members_subscriptions = filter(lambda x: x.get('error') is None, members_subscriptions)
            members_subscriptions = map(lambda x: {'groups': x['response']['groups']['items'], 'users': x['response']['users']['items'], 'user_id': x['user_id']}, members_subscriptions)
            self.responses_db['subscriptions'].insert_many(map(_convert_response_to_entry, members_subscriptions))

        fetcher = RelationsFetcher(self.mongo_url, self.mongo_db, self.vk_api_url, self.vk_api_access_token)
        while True:
            await fetcher.fetch()

        print("Done")

    async def _fetch_relations(self):
        fetcher = RelationsFetcher(self.mongo_url, self.mongo_db, self.vk_api_url, self.vk_api_access_token)
        while True:
            await fetcher.fetch()
