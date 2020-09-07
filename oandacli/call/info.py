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
from pandas.api.types import is_object_dtype

from ..util.config import create_api, log_response, read_yml
from .plot import plot_pl


def print_info(config_yml, instruments=None, target='accounts',
               print_json=False):
    logger = logging.getLogger(__name__)
    available_targets = [
        'instruments', 'account', 'accounts', 'orders', 'trades', 'positions',
        'transactions', 'prices', 'position', 'order_book', 'position_book'
    ]
    if target not in available_targets:
        raise ValueError(f'invalid info target:\t{target}')
    logger.info('Information')
    cf = read_yml(path=config_yml)
    api = create_api(config=cf)
    account_id = cf['oanda']['account_id']
    insts = cf.get('instruments') or instruments or list()
    arg_insts = {'instruments': ','.join(insts)} if insts else {}
    logger.debug(f'information target:\t{target}')
    if target == 'instruments':
        res = api.account.instruments(accountID=account_id, **arg_insts)
    elif target == 'account':
        res = api.account.get(accountID=account_id)
    elif target == 'accounts':
        res = api.account.list()
    elif target == 'orders':
        res = api.order.list_pending(accountID=account_id)
    elif target == 'trades':
        res = api.trade.list_open(accountID=account_id)
    elif target == 'positions':
        res = api.position.list_open(accountID=account_id)
    elif not insts:
        raise ValueError(f'{target}:\tinstruments required')
    elif target == 'prices':
        res = api.pricing.get(accountID=account_id, **arg_insts)
    elif target == 'position':
        res = api.position.get(accountID=account_id, instrument=insts[0])
    elif target == 'order_book':
        res = api.instrument.order_book(instrument=insts[0])
    elif target == 'position_book':
        res = api.instrument.position_book(instrument=insts[0])
    log_response(res, logger=logger)
    data = json.loads(res.raw_body)
    print(
        json.dumps(data, indent=2) if print_json
        else yaml.dump(data, default_flow_style=False).strip()
    )


def track_transaction(config_yml, from_time=None, to_time=None, csv_path=None,
                      sqlite_path=None, pl_graph_path=None, print_json=False,
                      quiet=False):
    logger = logging.getLogger(__name__)
    logger.info('Transaction tracking')
    transactions = _fetch_transactions(
        config_yml=config_yml, from_time=from_time, to_time=to_time
    )
    df_txn = (
        pd.DataFrame(transactions).astype(
            dtype=dict(
                [(k, int) for k in ['id', 'userID', 'batchID']] + [
                    (k, float) for k in [
                        'units', 'requestID', 'orderID', 'requestedUnits',
                        'price', 'pl', 'financing', 'commission',
                        'accountBalance', 'gainQuoteHomeConversionFactor',
                        'lossQuoteHomeConversionFactor',
                        'guaranteedExecutionFee', 'halfSpreadCost', 'fullVWAP',
                        'tradeID', 'distance', 'closedTradeID',
                        'tradeCloseTransactionID', 'amount'
                    ]
                ]
            )
        ).set_index('id')
        if transactions else pd.DataFrame()
    )
    logger.debug(f'df_txn:{os.linesep}{df_txn}')
    if transactions:
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
            db_exists = Path(sqlite_path).is_file()
            tbl = 'transaction_history'
            with sqlite3.connect(sqlite_path) as con:
                tbl_exists = (
                    db_exists
                    and tbl in pdsql.read_sql(
                        'SELECT name FROM sqlite_master WHERE type = "table";',
                        con=con
                    )['name'].to_list()
                )
                old_ids = set(
                    pdsql.read_sql(f'SELECT id FROM {tbl};', con=con)['id']
                    if tbl_exists else list()
                )
                df_new = df_txn.pipe(lambda d: d[~d.index.isin(old_ids)])
                logger.debug(f'df_new:{os.linesep}{df_new}')
                if df_new.size > 0:
                    pdsql.to_sql(
                        df_new.astype(
                            dtype={
                                k: str for k in df_new.dtypes.pipe(
                                    lambda a: a[a.apply(is_object_dtype)]
                                ).index
                            }
                        ),
                        name=tbl, con=con, if_exists='append'
                    )
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
