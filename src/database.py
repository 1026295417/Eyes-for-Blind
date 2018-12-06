# @Author      : 'Savvy'
# @Created_date: 2018/12/5 4:09 PM
import pymongo


class Database(object):
    URI = "mongodb://127.0.0.1:27017"
    DATABASE = None

    @staticmethod
    def initialize():
        client = pymongo.MongoClient(Database.URI)
        Database.DATABASE = client['IoTFinal']

    @staticmethod
    def insert(collection, data):
        Database.DATABASE[collection].insert(data)

    @staticmethod
    def find(collection, query):
        return Database.DATABASE[collection].find(query)

    @staticmethod
    def find_latest_one_before_time(collection, time):
        return Database.DATABASE[collection].find_one({'time': {'$lt': time}}, sort=[('time', pymongo.DESCENDING)])

    @staticmethod
    def update(collection, query, data):
        Database.DATABASE[collection].update(query, data, upsert=True)