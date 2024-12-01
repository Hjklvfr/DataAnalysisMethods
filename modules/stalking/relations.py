import asyncio
import json
import logging

import pymongo

from modules.stalking import convert_response_to_entry
from modules.vkapi import VkApi


class Relation:
    def __init__(self, from_id: str, to_id: str, from_type: str, to_type: str, relation_type: str, directed: bool):
        self.from_id = from_id
        self.to_id = to_id
        self.from_type = from_type
        self.to_type = to_type
        self.relation_type = relation_type
        self.directed = directed

    def __dict__(self):
        return {
            'from_id': self.from_id,
            'to_id': self.to_id,
            'from_type': self.from_type,
            'to_type': self.to_type,
            'relation_type': self.relation_type,
            'directed': self.directed
        }


class Unprocessed:
    def __init__(self, obj_id: str, obj_type: str):
        self.obj_id = obj_id
        self.obj_type = obj_type

    def __dict__(self):
        return {
            'obj_id': self.obj_id,
            'obj_type': self.obj_type
        }


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
            if unprocessed['obj_type'] == 'group':
                groups.add(unprocessed['obj_id'])
            elif unprocessed['obj_type'] == 'user':
                users.add(unprocessed['obj_id'])
            else:
                logging.warning('Unprocessed object type not supported. Object: %s', json.dumps(unprocessed))

        logging.info("Found %s groups, %s users", len(groups), len(users))
        tasks = [
            self.process_groups(groups),
            self.process_users(users)
        ]
        await asyncio.gather(*tasks)
        logging.info("Finished fetching relations")

    async def process_users(self, users):
        logging.info("Start processing users. Count %s", len(users))
        for user in users:
            user_data = await self.vkapi.get_users(user_ids=[user], fields=['activities','about','blacklisted','blacklisted_by_me','books','bdate','can_be_invited_group','can_post','can_see_all_posts','can_see_audio','can_send_friend_request','can_write_private_message','career','common_count','connections','contacts','city','crop_photo','domain','education','exports','followers_count','friend_status','has_photo','has_mobile','home_town','photo_100','photo_200','photo_200_orig','photo_400_orig','photo_50','sex','site','schools','screen_name','status','verified','games','interests','is_favorite','is_friend','is_hidden_from_feed','last_seen','maiden_name','military','movies','music','nickname','occupation','online','personal','photo_id','photo_max','photo_max_orig','quotes','relation','relatives','timezone','tv','universities','is_verified'])
            logging.info("Start processing user %s", user)
            tasks_res = await asyncio.gather(
                self.vkapi.get_friends(user),
                self.vkapi.get_followers(user, []),
                self.vkapi.get_subscriptions(user)
            )
            friends = tasks_res[0]
            followers = tasks_res[1]
            subs = tasks_res[2]
            relations = []
            rel_groups = []
            rel_users = []
            usrs = friends + followers + subs['response']['response']['users']['items'] if subs else []
            grps = subs['response']['response']['groups']['items'] if subs else []

            if friends:
                friends = map(lambda x: Relation(user, x, 'user', 'user', 'friend', False).__dict__(), friends)
                relations.extend(friends)
            if followers:
                followers = map(lambda x: Relation(x, user, 'user', 'user', 'follower', True).__dict__(), followers)
                relations.extend(followers)
            if subs and not subs['response'].get('error') and not subs['response']['response'].get('error') and (subs['response']['response'].get('groups') or subs['response']['response'].get('users')):
                rel_groups = subs['response']['response']['groups']['items']
                rel_users = subs['response']['response']['users']['items']
                if rel_groups:
                    rel_groups = list(map(lambda x: Relation(user, x, 'user', 'group', 'member', True).__dict__(), rel_groups))
                    relations.extend(rel_groups)
                if rel_users:
                    rel_users = list(map(lambda x: Relation(user, x, 'user', 'user', 'follower', True).__dict__(), users))
                    relations.extend(rel_users)

            async with self.mongo.start_session() as session:
                async with await session.start_transaction():
                    results = await asyncio.gather(
                        self.get_processed_users(usrs),
                        self.get_processed_groups(grps))
                    existed_users = results[0]
                    existed_groups = results[1]
                    new_unprocessed = []
                    new_unprocessed.extend(map(lambda x: Unprocessed(obj_id=x['from_id'], obj_type='user').__dict__(), filter(lambda x: x not in existed_users, rel_users)))
                    new_unprocessed.extend(map(lambda x: Unprocessed(obj_id=x['to_id'], obj_type='group').__dict__(), filter(lambda x: x not in existed_groups, rel_groups)))
                    if new_unprocessed:
                        await self.responses_db['unprocessed'].insert_many(new_unprocessed, session=session)
                    if relations:
                        await self.responses_db['relations'].insert_many(relations, session=session)
                    await self.responses_db['unprocessed'].delete_one({'obj_id': {'$eq': user}, 'obj_type': {'$eq': 'user'}}, session=session)
                    if user_data:
                        await self.responses_db['users'].insert_many(map(convert_response_to_entry, user_data), session=session)
            logging.info("Finished processing user %s", user)
        logging.info("Finished processing users")

    async def get_processed_users(self, user_ids: list[int]) -> list[int]:
        task_with_user_id = map(lambda u: (self.responses_db['users'].find_one({'data.id': {'$eq': u}}), u), user_ids)
        async def mapp(t):
            return await t[0], t[1]
        task_with_user_id = map(mapp, task_with_user_id)
        results = await asyncio.gather(*task_with_user_id)
        existed = filter(lambda u: u[0], results)
        return list(map(lambda u: u[1], existed))

    async def get_processed_groups(self, group_ids: list[int]) -> list[int]:
        task_with_group_id = map(lambda u: (self.responses_db['groups'].find_one({'data.id': {'$eq': u}}), u), group_ids)
        async def mapp(t):
            return await t[0], t[1]
        task_with_group_id = map(mapp, task_with_group_id)
        results = await asyncio.gather(*task_with_group_id)
        existed = filter(lambda u: u[0], results)
        return list(map(lambda u: u[1], existed))

    async def process_groups(self, groups):
        logging.info("Start processing groups. Count %s", len(groups))
        for group in groups:
            logging.info("Start processing group %s", group)
            group_data = await self.vkapi.get_groups(group_ids=[group], fields=['activity','city','contacts','counters','country','description','finish_date','fixed_post','links','members_count','place','site','start_date','status','verified','wiki_page'])
            members = await self.vkapi.get_members(group, [])
            usrs = members
            relations = []
            if members:
                members = map(lambda x: Relation(x, group, 'user', 'group', 'member', True), members)
                members = list(members)
                relations.extend(members)
            async with self.mongo.start_session() as session:
                async with await session.start_transaction():
                    try:
                        existed_users = await self.get_processed_users(usrs)
                        new_unprocessed = []
                        new_unprocessed.extend(map(lambda x: Unprocessed(obj_id=x.from_id, obj_type='user').__dict__(), filter(lambda x: x not in existed_users, members)))
                        if new_unprocessed:
                            await self.responses_db['unprocessed'].insert_many(new_unprocessed, session=session)
                        await self.responses_db['relation'].insert_many(map(lambda x: x.__dict__(), relations), session=session)
                        await self.responses_db['unprocessed'].delete_one({'obj_id': {'$eq': group}, 'obj_type': {'$eq': 'user'}}, session=session)
                        await self.responses_db['groups'].insert_many(map(convert_response_to_entry, group_data), session=session)
                        await session.commit_transaction()
                    except Exception as e:
                        logging.exception(e)
                        await session.abort_transaction()
            logging.info("Finished processing group %s", group)
        logging.info("Finished processing groups")

