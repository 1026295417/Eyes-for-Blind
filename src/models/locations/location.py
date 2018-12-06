# @Author      : 'Savvy'
# @Created_date: 2018/12/5 4:40 PM

from src.database import Database
import datetime
import pytz
import uuid


class Location(object):
    def __init__(self, coord, time=None, _id=None):
        self.coord = coord
        self.time = datetime.datetime.now(pytz.timezone('US/Eastern')) if time is None else time
        self._id = uuid.uuid4().hex if _id is None else _id

    def __repr__(self):
        return "<Location with time {}>".format(self.time)

    @classmethod
    def find_latest_before_time(cls, time):
        return cls(**Database.find_latest_one_before_time('locations', time))

    def save_to_db(self):
        Database.insert("locations", self.json())

    def json(self):
        return {
            'coord': self.coord,
            'time': self.time,
            '_id': self._id
        }
