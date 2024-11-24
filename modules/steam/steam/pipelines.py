import logging

import pymongo
from pymongo import MongoClient
from pymongo.synchronous.database import Database


class MongoDBPipeline:
    collection_name = 'products'

    def __init__(self, mongo_uri: str, mongo_db: str):
        self.db: Database = None
        self.client: MongoClient = None
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_URL'),
            mongo_db=crawler.settings.get('MONGODB_DB'),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        logging.debug('Write item to collection')
        self.db[self.collection_name].replace_one({'_id': item['_id']}, dict(item), upsert=True)
        return item
