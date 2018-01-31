from db import ticker
from .status import *
import pandas
import numpy as np


def get_ticker_data():
    """
    Get a list of all tickers' data
    :return: List of tickers along with price data list
    """
    raw_data = list(ticker.get_all_tickers())

    # convert price data into float
    def convert_prices_to_float(price):
        for k, v in price.items():
            if k != 'id' and v is not None:
                price[k] = float(v)
        return price

    for d in raw_data:
        d['price_list'] = list(map(convert_prices_to_float, d['price_list']))

    return raw_data


def get_symbol_id_map(data):
    """
    Get a dict which maps a symbol to a list of full id names
    :param data: The return value from get_ticker_data
    :return:
    """
    result = {}
    for t in data:
        symbol = t['symbol']
        if symbol in result:
            result[symbol].append(t['id'])
        else:
            result[symbol] = [t['id']]

    return result


def all_ticker_id(data):
    return list(map(lambda t: t['id'], data))


def build_df(data, feature):
    """
    Build a time-based data frame based on give feature
    :param feature: The name of feature to build on
    :return:
    """

    def fill_feature_list(feature_data, timestamps):
        # TODO allign data points with timestamps
        if len(feature_data) == len(timestamps):
            return feature_data
        else:
            return [None] * len(timestamps)

    timestamps = list(map(lambda ts: pandas.Timestamp(ts_input=ts * 1000000000), sorted(all_timestamp())))
    ticker_ids = all_ticker_id(data)

    df = pandas.DataFrame(columns=timestamps, index=ticker_ids)

    for t in data:
        sorted_price_list = sorted(t['price_list'],
                                   key=lambda p_list: 0 if p_list['last_updated'] is None else p_list['last_updated'])
        feature_data_list = list(map(lambda p_list: p_list[feature], sorted_price_list))
        feature_data_list = fill_feature_list(feature_data_list, timestamps)

        new_row_series = pandas.Series(data=feature_data_list, index=timestamps)

        df.loc[t['id']] = new_row_series

    return df
