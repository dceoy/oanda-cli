#!/usr/bin/env python

import json
import logging
import os
import sqlite3
import time
from pathlib import Path

import pandas as pd
import pandas.io.sql as pdsql
import yaml

from ..util.config import create_api, log_response, read_yml
from .plot import plot_pl


def track_transaction(config_yml, from_time=None, to_time=None, csv_path=None,
                      sqlite_path=None, pl_graph_path=None, print_json=False,
                      quiet=False):
    logger = logging.getLogger(__name__)
    logger.info('Transaction tracking')
    transactions = _fetch_transactions(
        config_yml=config_yml, from_time=from_time, to_time=to_time
    )
    if transactions:
        df_txn = pd.DataFrame([
            {'id': int(t['id']), 'time': t['time'], 'json': json.dumps(t)}
            for t in transactions
        ]).set_index('id')
        logger.debug(f'df_txn:{os.linesep}{df_txn}')
        if csv_path:
            if Path(csv_path).is_file():
                old_ids = set(
                    pd.read_csv(csv_path, usecols=['id'], dtype=int)['id']
                )
                df_txn.pipe(
                    lambda d: d[~d.index.isin(old_ids)]
                ).to_csv(csv_path, mode='a', header=False)
            else:
                df_txn.to_csv(csv_path)
        if sqlite_path:
            tbl = 'transaction_history'
            if Path(sqlite_path).is_file():
                with sqlite3.connect(sqlite_path) as con:
                    old_ids = set(
                        pdsql.read_sql(f'SELECT id FROM {tbl};', con=con)['id']
                    )
                    df_txn_new = df_txn.pipe(
                        lambda d: d[~d.index.isin(old_ids)]
                    )
                    logger.debug(f'df_txn_new:{os.linesep}{df_txn_new}')
                    if df_txn_new.size > 0:
                        pdsql.to_sql(
                            df_txn_new, name=tbl, con=con, if_exists='append'
                        )
            else:
                schema_sql = Path(__file__).parent.parent.joinpath(
                    'static/create_tables.sql'
                )
                with sqlite3.connect(sqlite_path) as con:
                    with open(schema_sql, 'r') as f:
                        con.executescript(f.read())
                    pdsql.to_sql(df_txn, name=tbl, con=con, if_exists='append')
        if pl_graph_path:
            plot_pl(df_txn=df_txn, path=pl_graph_path)
    if not quiet:
        print(
            json.dumps(transactions, indent=2) if print_json
            else yaml.dump(transactions, default_flow_style=False).strip()
        )


def _fetch_transactions(config_yml, from_time=None, to_time=None):
    logger = logging.getLogger(__name__)
    cf = read_yml(path=config_yml)
    api = create_api(config=cf)
    account_id = cf['oanda']['account_id']
    res = api.transaction.list(
        accountID=account_id,
        **{
            k: v for k, v
            in {'fromTime': from_time, 'toTime': to_time}.items() if v
        }
    )
    log_response(res, logger=logger)
    transactions = list()
    for page in (res.body.get('pages') or list()):
        time.sleep(0.5)
        r = api.transaction.range(
            accountID=account_id, **_parse_idrange(page=page)
        )
        log_response(r, logger=logger)
        transactions.extend(
            json.loads(r.raw_body).get('transactions') or list()
        )
    return transactions


def _parse_idrange(page):
    return dict([
        s.split('=') for s in page.split('?')[1].replace('=', 'ID=').split('&')
    ])
