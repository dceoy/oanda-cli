#!/usr/bin/env python

import logging
import os
import sqlite3
from itertools import chain

import pandas as pd
import pandas.io.sql as pdsql
import ujson

from ..util.config import create_api, log_response, read_yml


def track_rate(config_yml, instruments, granularity, count, csv_dir_path=None,
               sqlite_path=None, print_json=False, quiet=False):
    logger = logging.getLogger(__name__)
    logger.info('Rate tracking')
    cf = read_yml(path=config_yml)
    api = create_api(config=cf)
    candles = dict()
    for i in (instruments or cf['instruments']):
        res = api.instrument.candles(
            instrument=i, price='BA', granularity=granularity, count=int(count)
        )
        log_response(res, logger=logger)
        candles[i] = [
            _candlestick2dict(c) for c in res.body['candles'] if c.complete
        ]
    keys = ['instrument', 'time']
    df_all = pd.concat([
        pd.DataFrame(c).assign(instrument=i) for i, c in candles.items()
    ]).drop(columns=['complete']).set_index(keys)
    if csv_dir_path:
        csv_dir_abspath = os.path.abspath(
            os.path.expanduser(os.path.expandvars(csv_dir_path))
        )
        os.makedirs(csv_dir_abspath, exist_ok=True)
        df_all_day = df_all.reset_index().assign(
            datetime=lambda d: pd.to_datetime(d['time'])
        ).assign(
            date=lambda d: d['datetime'].dt.date
        )
        for t in df_all_day['date'].unique():
            for i in df_all_day['instrument'].unique():
                df_csv = df_all_day.pipe(
                    lambda d: d[(d['date'] == t) & (d['instrument'] == i)]
                ).drop(columns=['date', 'instrument'])
                csv_path = os.path.join(
                    csv_dir_abspath,
                    'candle.{0}.{1}.{2}.csv'.format(granularity, i, t)
                )
                if os.path.isfile(csv_path):
                    df_csv_new = df_csv.append(
                        pd.read_csv(csv_path).assign(
                            datetime=lambda d: pd.to_datetime(d['time'])
                        )
                    ).sort_values('datetime').drop(
                        columns='datetime'
                    ).drop_duplicates(
                        subset=['time'], keep='last'
                    ).set_index('time')
                else:
                    df_csv_new = df_csv.sort_values('datetime').drop(
                        columns='datetime'
                    ).set_index('time')
                df_csv_new.to_csv(csv_path, mode='w', header=True, sep=',')
    if sqlite_path:
        logger.debug('df_all.shape: {}'.format(df_all.shape))
        sqlite_abspath = os.path.abspath(
            os.path.expanduser(os.path.expandvars(sqlite_path))
        )
        if os.path.isfile(sqlite_abspath):
            with sqlite3.connect(sqlite_abspath) as con:
                df_db_diff = df_all.join(
                    pdsql.read_sql(
                        'SELECT instrument, time FROM candle;', con
                    ).assign(
                        in_db=True
                    ).set_index(keys),
                    on=keys, how='left'
                ).pipe(
                    lambda d: d[d['in_db'].isnull()].drop(columns=['in_db'])
                )
                logger.debug(
                    'df_db_diff:{0}{1}'.format(os.linesep, df_db_diff)
                )
                pdsql.to_sql(df_db_diff, 'candle', con, if_exists='append')
        else:
            schema_sql_path = os.path.join(
                os.path.dirname(__file__), '../static/create_tables.sql'
            )
            with open(schema_sql_path, 'r') as f:
                schema_sql = f.read()
            with sqlite3.connect(sqlite_abspath) as con:
                con.executescript(schema_sql)
                logger.debug('df_all:{0}{1}'.format(os.linesep, df_all))
                pdsql.to_sql(df_all, 'candle', con, if_exists='append')
    if not quiet:
        if print_json:
            print(ujson.dumps(candles, indent=2))
        else:
            with pd.option_context('display.max_rows', None):
                print(df_all)


def _candlestick2dict(candlestick):
    data_keys = ['bid', 'ask', 'mid']
    abbr = {'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close'}
    cs_dict = vars(candlestick)
    return {
        **{k: v for k, v in cs_dict.items() if k not in data_keys},
        **dict(chain.from_iterable([
            [(abbr[k] + dk.capitalize(), float(v)) for k, v in vars(d).items()]
            for dk, d in cs_dict.items() if dk in data_keys and d
        ]))
    }
