#!/usr/bin/env python

import json
import logging

import pandas as pd
import yaml

from ..util.logger import log_response


def print_info(api, account_id=None, instruments=None, target='accounts',
               print_json=False):
    logger = logging.getLogger(__name__)
    available_targets = [
        'instruments', 'account', 'accounts', 'orders', 'trades', 'positions',
        'transactions', 'prices', 'position', 'order_book', 'position_book'
    ]
    if target not in available_targets:
        raise ValueError(f'invalid info target:\t{target}')
    logger.info('Information')
    arg_insts = {'instruments': ','.join(instruments)} if instruments else {}
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
    elif not instruments:
        raise ValueError(f'{target}:\tinstruments required')
    elif target == 'prices':
        res = api.pricing.get(accountID=account_id, **arg_insts)
    elif target == 'position':
        res = api.position.get(accountID=account_id, instrument=instruments[0])
    elif target == 'order_book':
        res = api.instrument.order_book(instrument=instruments[0])
    elif target == 'position_book':
        res = api.instrument.position_book(instrument=instruments[0])
    log_response(res, logger=logger)
    data = json.loads(res.raw_body)
    print(
        json.dumps(data, indent=2) if print_json
        else yaml.dump(data, default_flow_style=False).strip()
    )


def print_spread_ratios(api, account_id, instruments=None, csv_path=None,
                        quiet=False):
    assert account_id, 'account ID required'
    logger = logging.getLogger(__name__)
    logger.info('Prices and Spread Ratios')
    if instruments:
        insts = instruments
    else:
        res0 = api.account.instruments(accountID=account_id)
        log_response(res0, logger=logger)
        insts = [o['name'] for o in json.loads(res0.raw_body)['instruments']]
    res1 = api.pricing.get(accountID=account_id, instruments=','.join(insts))
    log_response(res1, logger=logger)
    df_spr = pd.DataFrame([
        {k: o[k] for k in ['instrument', 'closeoutBid', 'closeoutAsk']}
        for o in json.loads(res1.raw_body)['prices']
    ]).rename(
        columns={'closeoutBid': 'bid', 'closeoutAsk': 'ask'}
    ).astype(
        dtype={'bid': float, 'ask': float}
    ).assign(
        mid=lambda d: d[['bid', 'ask']].mean(axis=1),
        spread=lambda d: (d['ask'] - d['bid'])
    ).assign(
        ratio_of_spread_to_mid=lambda d: (d['spread'] / d['mid'])
    ).set_index('instrument').sort_values('ratio_of_spread_to_mid')
    if csv_path:
        df_spr.to_csv(csv_path)
    if not quiet:
        with pd.option_context('display.max_rows', None):
            print(df_spr)
