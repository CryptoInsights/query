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
        if 'price_list' in d:
            d['price_list'] = list(map(convert_prices_to_float, d['price_list']))
        else:
            d['price_list'] = []

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


def fill_feature_list(feature_data, timestamp_list, feature):
    timestamp_list = sorted(timestamp_list)
    feature_data = filter(lambda data: data['last_updated'] is not None and data[feature] is not None, feature_data)
    feature_data = sorted(feature_data, key=lambda d: d['last_updated'])
    result = [0] * len(timestamp_list)

    if len(feature_data) == 0:
        return result

    i = 0
    j = 0
    while j < len(feature_data) - 1 and feature_data[j]['last_updated'] == feature_data[j + 1]['last_updated']:
        j += 1
    if j < len(feature_data) - 1:
        j += 1

    for d in range(len(timestamp_list)):
        if feature_data[i]['last_updated'] <= timestamp_list[d] < feature_data[j]['last_updated']:
            result[d] = feature_data[i][feature]
        elif timestamp_list[d] >= feature_data[j]['last_updated']:
            while j < len(feature_data) - 1 and feature_data[j]['last_updated'] == feature_data[j + 1]['last_updated']:
                j += 1
            i = j
            result[d] = feature_data[i][feature]
            if j < len(feature_data) - 1:
                j += 1

    return result


def build_df(data, feature):
    """
    Build a time-based data frame based on give feature
    :param feature: The name of feature to build on
    :return:
    """

    timestamps = list(map(lambda ts: pd.Timestamp(ts_input=ts * 1000000000), sorted(all_timestamp())))
    ticker_ids = all_ticker_id(data)

    df = pd.DataFrame(columns=timestamps, index=ticker_ids)

    for t in data:
        sorted_price_list = sorted(t['price_list'],
                                   key=lambda p_list: 0 if p_list['last_updated'] is None else p_list['last_updated'])
        feature_data_list = [{'last_updated': p['last_updated'], feature: p[feature]} for p in sorted_price_list]
        feature_data_list = fill_feature_list(feature_data_list, all_timestamp(), feature)

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

    For example, given a data frame like:

    | SYM | 00:00 | 01:00 | 02:00 | 03:00 | 04:00 | 05:00 |
    -------------------------------------------------------
    | BTC |  100  |  200  |  300  |  400  |  500  |  600  |
    | ETH |   1   |   2   |   3   |   4   |   5   |   6   |
    | BTH |   2   |   2   |   1   |   1   |   2   |   4   |

    the result of cross_compare(data, 1) will be:

    | SYM | 01:00 | 02:00 | 03:00 | 04:00 | 05:00 |
    -----------------------------------------------
    | BTC |  100  |  100  |  100  |  100  |  100  |
    | ETH |   1   |   1   |   1   |   1   |   1   |
    | BTH |   0   |   -1  |   0   |   1   |   2   |

    the result of cross_compare(data, 2, reason_functions['diff-percent']) will be:

    | SYM | 03:00 | 05:00 |
    -----------------------
    | BTC |  2.0  |  0.5  |
    | ETH |  2.0  |  0.5  |
    | BTH |  -.5  |  3.0  |

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
