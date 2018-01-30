from .mongo import db


def get_all_tickers():
    return db.coins.find()
