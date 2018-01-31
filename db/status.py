import pymongo
from .mongo import db


def get_latest_status():
    return db.status.find().sort('timestamp', pymongo.DESCENDING).limit(1)[0]


def get_all_status():
    return list(db.status.find())
