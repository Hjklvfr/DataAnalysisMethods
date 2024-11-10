import json
import logging
import asyncio
import copy
import logging
import os
from http.client import responses
from logging.config import fileConfig
from typing import List, Any

import aiohttp
from yarl import URL


class VkApi(object):
    def __init__(
            self,
            url: str = None,
            access_token: str = None,
    ):
        self.url = url
        self.access_token = access_token
        self.session = aiohttp.ClientSession(loop=asyncio.get_event_loop())
        self.semaphore = asyncio.Semaphore(2)

    async def get_members(self, group_id: int, fields: List[str]):
        endpoint = 'method/groups.getMembers'
        payload = {
            'group_id': group_id,
            'fields': ','.join(fields),
            'access_token': self.access_token,
            'v': '5.199'
        }

        response = await self._prepare_and_make_request(endpoint, 'POST', payload)
        if response.get('error'):
            logging.warning('Error for get_members. %s', json.dumps(response.get('error')))
            return []
        members = response.get('response').get('items')
        while next_from := response.get('response').get('next_from'):
            payload['start_from'] = next_from
            response = await self._prepare_and_make_request(endpoint, 'POST', payload)
            if response.get('error'):
                logging.warning('Error for get_members. %s', json.dumps(response.get('error')))
                return []
            members += response.get('response').get('items')

        return members

    async def get_groups(self, group_ids: List[int], fields: List[str]):
        endpoint = 'method/groups.getById'
        payload = {
            'group_ids': group_ids,
            'fields': ','.join(fields),
            'access_token': self.access_token,
            'v': '5.199'
        }

        response = await self._prepare_and_make_request(endpoint, 'POST', payload)
        if response.get('error'):
            logging.warning('Error for get_groups. %s', json.dumps(response.get('error')))
            return []
        groups = response.get('response').get('groups')
        return groups

    async def get_followers(self, user_id: int, fields: List[str]):
        endpoint = 'method/users.getFollowers'
        payload = {
            'user_id': user_id,
            'fields': ','.join(fields),
            'access_token': self.access_token,
            'v': '5.199'
        }

        response = await self._prepare_and_make_request(endpoint, 'POST', payload)
        if response.get('error'):
            logging.warning('Error for user %s. %s', user_id, json.dumps(response.get('error')))
            return []
        users = response.get('response').get('items')
        return users

    async def get_subscriptions(self, user_id: int):
        endpoint = 'method/users.getSubscriptions'
        payload = {
            'user_id': user_id,
            'access_token': self.access_token,
            'v': '5.199'
        }

        response = await self._prepare_and_make_request(endpoint, 'POST', payload)
        if response.get('error'):
            logging.warning('Error for get_subscriptions for user %s. %s', user_id, json.dumps(response.get('error')))
            return []
        subscriptions = {'user_id': user_id, 'response': response}
        return subscriptions

    async def get_friends(self, user_id: int):
        endpoint = 'method/friends.get'
        payload = {
            'user_id': user_id,
            'access_token': self.access_token,
            'v': '5.199'
        }

        response = await self._prepare_and_make_request(endpoint, 'POST', payload)
        if response.get('error'):
            logging.warning('Error for user %s. %s', user_id, json.dumps(response.get('error')))
            return []
        friends = response.get('response').get('items')
        return friends

    async def get_members_with_subscriptions(self, group_id: int, extended: bool = True):
        """ extended = False
        [{
            'response': {
                'response': {
                    'groups': {
                        'count': 63,
                        'items': [164999301]
                    },
                    'users': {
                        'count': 30,
                        'items': [783872438]
                    }
                }
            },
            'user_id': '2188417'
        }]
        """
        endpoint = 'method/users.getSubscriptions'
        payload = {
            'access_token': self.access_token,
            'extended': 1 if extended else 0,
            'v': '5.199'
        }

        members = await self.get_members(group_id, [])
        member_requests = []
        for member in members:
            req_payload = copy.copy(payload)
            req_payload['user_id'] = member
            member_requests.append((self._prepare_request(endpoint, 'POST', req_payload), member))
        async def map_to_make_requests(x):
            return await self._make_request(x[0]), x[1]
        tasks = map(map_to_make_requests, member_requests)
        response2s = await asyncio.gather(*tasks)
        def map_response(x):
            t = x[0]
            t['user_id']=x[1]
            return t

        response2s = map(map_response, response2s)
        return response2s


    def _prepare_request(self, endpoint: str, method: str, payload: dict[str, str | None | int]) -> aiohttp.ClientRequest:
        url = self.url + endpoint
        req = aiohttp.ClientRequest(method, URL(url), data=payload)
        return req

    async def _make_request(self, prepared_request: aiohttp.ClientRequest) -> dict[str, Any]:
        async with self.semaphore:
            method = None
            match prepared_request.method:
                case 'GET':
                    method = self.session.get
                case 'POST':
                    method = self.session.post
            if method is None:
                raise Exception('Method not supported')
            await asyncio.sleep(1)
            async with method(prepared_request.url, data=prepared_request.body, ssl=False) as response:
                if response.status == 200:
                    try:
                        resp = await response.json()
                        logging.debug(resp)
                        return resp
                    except ValueError:
                        raise
                else:
                    response.raise_for_status()

    async def _prepare_and_make_request(self, endpoint: str, method: str, payload: dict[str, str | None | int]) -> dict[str, Any]:
        prepared_request = self._prepare_request(endpoint, method, payload)

        return await self._make_request(prepared_request)


