import pymongo
from mongo import db


def get_latest_status():
    return db.status.find().sort('timestamp', pymongo.DESCENDING).limit(1)[0]

