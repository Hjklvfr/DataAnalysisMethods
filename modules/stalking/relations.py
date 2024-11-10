import asyncio
import json
import logging

import pymongo

from modules.vkapi import VkApi


class Relation:
    def __init__(self, from_id: str, to_id: str, from_type: str, to_type: str, relation_type: str, directed: bool):
        self.from_id = from_id
        self.to_id = to_id
        self.from_type = from_type
        self.to_type = to_type
        self.relation_type = relation_type
        self.directed = directed


class Unprocessed:
    def __init__(self, obj_id: str, obj_type: str):
        self.obj_id = obj_id
        self.obj_type = obj_type


class RelationsFetcher(object):
    def __init__(
            self,
            mongo_url: str,
            mongo_db: str,
            vk_api_url: str,
            vk_api_access_token: str,
    ):
        self.mongo = pymongo.AsyncMongoClient(mongo_url)
        self.responses_db = self.mongo[mongo_db]
        self.vkapi = VkApi(vk_api_url, vk_api_access_token)

    async def fetch(self):
        logging.info("Start fetching relations")
        unprocessed_cursor = self.responses_db['unprocessed'].find(limit=10)
        groups = set()
        users = set()
        async for unprocessed in unprocessed_cursor:
            if unprocessed['data']['obj_type'] == 'group':
                groups.add(unprocessed['data']['obj_id'])
            elif unprocessed['data']['obj_type'] == 'user':
                users.add(unprocessed['data']['obj_id'])
            else:
                logging.warning('Unprocessed object type not supported. Object: %s', json.dumps(unprocessed))


        subscriptionss_cursor = self.responses_db['subscriptions'].find({'processed': {'$exists': False}}, limit=10)
        groups = set()
        users = set()
        subscriptionss = []
        async for subscriptions in subscriptionss_cursor:
            groups.update(subscriptions['data']['groups'])
            users.update(subscriptions['data']['users'])
            subscriptionss.append(subscriptions)

        logging.info("Found %s groups, %s users", len(groups), len(users))
        # await loop.run_in_executor(executor, self.process_groups, groups)
        tasks = [
            self.process_groups(groups),
            self.process_users(users)
        ]
        await asyncio.gather(*tasks)
        ids = list(map(lambda x: x['_id'], subscriptionss))
        logging.info("Finished fetching relations. New %s subs", len(ids))
        await self.responses_db['subscriptions'].update_many({'_id': {'$in': ids}}, {'$set': {'processed': True}})
        logging.info("Finished fetching relations")

    async def process_users(self, users):
        logging.info("Start processing users. Count %s", len(users))
        for user in users:
            logging.info("Start processing user %s", user)
            # friends get
            friends = await self.vkapi.get_friends(user)
            friends = list(map(lambda x: {'user_id': user, 'friend': x}, friends))
            if friends:
                await self.responses_db['friends'].insert_many(friends)
            # followers get
            followers = await self.vkapi.get_followers(user, [])
            followers = list(map(lambda x: {'user_id': user, 'followed_by': x}, followers))
            if followers:
                await self.responses_db['followers'].insert_many(followers)
            # get subs
            subs = await self.vkapi.get_subscriptions(user)
            if subs['response'].get('error') is None and (subs['response'].get('groups') or subs['response'].get('users')):
                subs = {'groups': subs['response']['response']['groups']['items'], 'users': subs['response']['response']['users']['items'], 'user_id': subs['user_id']}
                await self.responses_db['subscriptions'].insert_one(subs)
            await asyncio.sleep(5)
            logging.info("Finished processing user %s", user)
        logging.info("Finished processing users")

    async def process_groups(self, groups):
        logging.info("Start processing groups. Count %s", len(groups))
        for group in groups:
            logging.info("Start processing group %s", group)
            subs = await self.vkapi.get_members_with_subscriptions(group, False)
            subs = filter(lambda x: x.get('error') is None, subs)
            subs = list(map(lambda x: {'groups': x['response']['groups']['items'], 'users': x['response']['users']['items'], 'user_id': x['user_id']}, subs))
            if subs:
                await self.responses_db['subscriptions'].insert_many(subs)
            await asyncio.sleep(5)
            logging.info("Finished processing group %s", group)
        logging.info("Finished processing groups")

