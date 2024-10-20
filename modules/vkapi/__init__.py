import itertools
import logging
import os
import time
from logging.config import fileConfig
from typing import Dict, List, Any

import grequests
import requests
import copy

from tqdm import tqdm

current_dir = os.path.realpath(__file__)
current_dir = os.path.dirname(current_dir)
logging_config_path = os.path.join(current_dir, "../../config/logging_config.ini")
fileConfig(logging_config_path, disable_existing_loggers=False)


class VkApi(object):
    def __init__(
            self,
            url: str = None,
            access_token: str = None,
    ):
        self.url = url
        self.access_token = access_token
        self.session = requests.Session()

    def get_members(self, group_id: int, fields: List[str]):
        endpoint = 'method/groups.getMembers'
        payload = {
            'group_id': group_id,
            'fields': ','.join(fields),
            'access_token': self.access_token,
            'v': '5.199'
        }

        response = self._prepare_and_make_request(endpoint, 'POST', payload)
        members = response.get('response').get('items')
        while next_from := response.get('response').get('next_from'):
            payload['start_from'] = next_from
            response = self._prepare_and_make_request(endpoint, 'POST', payload)
            members += response.get('response').get('items')

        return members

    def get_members_with_subscriptions(self, group_id: int):
        endpoint = 'method/users.getSubscriptions'
        payload = {
            'access_token': self.access_token,
            'extended': 1,
            'v': '5.199'
        }

        members = self.get_members(group_id, [])
        member_requests = []
        for member in members:
            req_payload = copy.copy(payload)
            req_payload['user_id'] = member
            member_requests.append(self._prepare_async_request(endpoint, 'POST', req_payload))

        responses = self._make_requests(member_requests)
        return responses


    def _prepare_request(self, endpoint: str, method: str, payload: dict[str, str | None | int]) -> requests.PreparedRequest:
        url = self.url + endpoint
        req = requests.Request(method, url, data=payload)
        return self.session.prepare_request(req)

    def _prepare_async_request(self, endpoint: str, method: str, payload: dict[str, str | None | int]) -> grequests.AsyncRequest:
        url = self.url + endpoint
        req = grequests.AsyncRequest(method, url, data=payload)
        return req

    def _make_request(self, prepared_request: requests.PreparedRequest) -> dict[str, Any]:
        response = self.session.send(prepared_request)

        if response.status_code == requests.codes.ok:
            try:
                resp = response.json()
                logging.debug(resp)
                return resp
            except ValueError:
                return response.text
        else:
            response.raise_for_status()

    def _make_requests(self, prepared_requests: List[grequests.AsyncRequest]) -> List[dict[str, Any]]:
        def exception_handler(request, exception):
            logging.error('Error on request {} |||| Exception: {}', request, exception)

        N = 100
        chunks = [prepared_requests[i:i + N] for i in range(0, len(prepared_requests), N)]
        all_responses = []
        for chunk in chunks:
            responses: List[requests.Response] = grequests.map(chunk, exception_handler=exception_handler)
            time.sleep(1)
            all_responses += responses


        return [{'user_id': r.request.body.split('user_id=')[1], 'response': r.json()} for r in all_responses]

    def _prepare_and_make_request(self, endpoint: str, method: str, payload: dict[str, str | None | int]) -> dict[str, Any]:
        prepared_request = self._prepare_request(endpoint, method, payload)

        return self._make_request(prepared_request)


