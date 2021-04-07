#!/usr/bin/env python

import json
import logging
import os
import sqlite3
from itertools import chain
from pathlib import Path

import pandas as pd
import pandas.io.sql as pdsql

from ..util.logger import log_response


def track_rate(api, instruments, granularity, count, csv_dir_path=None,
               sqlite_path=None, print_json=False, quiet=False):
    assert instruments, 'instruments required'
    logger = logging.getLogger(__name__)
    logger.info('Rate tracking')
    candles = dict()
    for i in instruments:
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
        csv_dir = Path(csv_dir_path).resolve()
        if not csv_dir.is_dir():
            csv_dir.mkdir()
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
                csv_path = str(
                    csv_dir.joinpath(f'candle.{granularity}.{i}.{t}.csv')
                )
                if Path(csv_path).is_file():
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
        logger.debug(f'df_all.shape:\t{df_all.shape}')
        sqlite_file = Path(sqlite_path).resolve()
        if sqlite_file.is_file():
            with sqlite3.connect(str(sqlite_file)) as con:
                df_db_diff = df_all.join(
                    pdsql.read_sql(
                        'SELECT instrument, time FROM candle;', con
                    ).assign(
                        in_db=True
                    ).set_index(keys),
                    on=keys, how='left'
                ).pipe(
                    lambda d: d[d['in_db'].isna()].drop(columns=['in_db'])
                )
                logger.debug(f'df_db_diff:{os.linesep}{df_db_diff}')
                pdsql.to_sql(
                    df_db_diff, name='candle', con=con, if_exists='append'
                )
        else:
            schema_sql = Path(__file__).parent.parent.joinpath(
                'static/create_tables.sql'
            )
            with sqlite3.connect(str(sqlite_file)) as con:
                with open(schema_sql, 'r') as f:
                    con.executescript(f.read())
                logger.debug(f'df_all:{os.linesep}{df_all}')
                pdsql.to_sql(
                    df_all, name='candle', con=con, if_exists='append'
                )
    if not quiet:
        if print_json:
            print(json.dumps(candles, indent=2))
        else:
            with pd.option_context('display.max_rows', None):
                print(df_all)


def _candlestick2dict(candlestick):
    data_keys = ['bid', 'ask', 'mid']
    abbr = {'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close'}
    cs_dict = candlestick.dict()
    return {
        **{k: v for k, v in cs_dict.items() if k not in data_keys},
        **dict(
            chain.from_iterable([
                [(abbr[k] + dk.capitalize(), float(v)) for k, v in d.items()]
                for dk, d in cs_dict.items() if dk in data_keys and d
            ])
        )
    }
