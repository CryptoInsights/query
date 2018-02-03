from db import ticker
from .status import *
import pandas as pd
import copy
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

    timestamps = list(map(lambda ts: pd.Timestamp(ts_input=ts * 1000000000), sorted(all_timestamp())))
    ticker_ids = all_ticker_id(data)

    df = pd.DataFrame(columns=timestamps, index=ticker_ids)

    for t in data:
        sorted_price_list = sorted(t['price_list'],
                                   key=lambda p_list: 0 if p_list['last_updated'] is None else p_list['last_updated'])
        feature_data_list = list(map(lambda p_list: p_list[feature], sorted_price_list))
        feature_data_list = fill_feature_list(feature_data_list, timestamps)

        new_row_series = pd.Series(data=feature_data_list, index=timestamps)

        df.loc[t['id']] = new_row_series

    return df


def merge_latest_price(data_point):
    """
    For any record in get_ticker_data, flat map the latest price data into the object itself
    :param data_point:
    :return:
    """
    sorted_price_list = sorted(data_point['price_list'],
                               key=lambda l: 0 if l['last_updated'] is None else l['last_updated'],
                               reverse=True)
    latest_price = sorted_price_list[0]

    result = dict(data_point)
    del result['price_list']
    result.update(latest_price)

    return result


reason_functions = {
    'diff': lambda new, old: new - old,
    'diff-percent': lambda new, old: 1.0 * (new - old) / old
}


def cross_compare(data, interval=24, reason_func=reason_functions['diff']):
    """
    Horizontally compares data points (along time axis), and produces a new data frame
    with results.
    For example, we can compare the price of each ticker with that from 24 hours ago.
    :param data: Result from build_df
    :param interval: Time interval in hour
    :param reason_func: How to compare data points
    :return: A new data frame which holds the compared results of data
    """
    data = data.dropna(axis=0, how='all')  # remove rows that are all None
    timestamp_labels = list(data.columns.values)

    # find out which labels to keep based on interval, we ASSUME that the interval between
    # every two labels is constantly 1 hour
    # TODO remove the above assumption by looking at real timestamp data
    label_index_range = range(len(timestamp_labels) - 1, -1, -interval)
    data_required = data.iloc[:, list(label_index_range)]

    # calculate data with provided reasoning function
    data_matrix = data_required.as_matrix()
    for row in data_matrix:
        for i in range(len(row) - 1):
            row[i] = reason_func(row[i], row[i + 1])

    result = pd.DataFrame(data_matrix, index=list(data_required.index.values),
                          columns=list(data_required.columns.values))

    # drop the last column since there is no previous data to compare with
    # and reverse all columns
    result = result.iloc[:, :-1]
    result = result.iloc[:, ::-1]
    return result
