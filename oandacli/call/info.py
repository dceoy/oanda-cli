#!/usr/bin/env python

import json
import logging
import time

import pandas as pd
import seaborn as sns
import yaml
from matplotlib.pylab import rcParams

from ..util.config import create_api, log_response, read_yml


def print_info(config_yml, instruments=None, target='accounts',
               print_json=False):
    logger = logging.getLogger(__name__)
    available_targets = [
        'instruments', 'account', 'accounts', 'orders', 'trades', 'positions',
        'transactions', 'prices', 'position', 'order_book', 'position_book'
    ]
    if target not in available_targets:
        raise ValueError('invalid info target: {}'.format(target))
    logger.info('Information')
    cf = read_yml(path=config_yml)
    api = create_api(config=cf)
    account_id = cf['oanda']['account_id']
    insts = cf.get('instruments') or instruments or list()
    arg_insts = {'instruments': ','.join(insts)} if insts else {}
    logger.debug('information target: {}'.format(target))
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
        raise ValueError('{}: instruments required'.format(target))
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
                      pl_graph_path=None, print_json=False, quiet=False):
    logger = logging.getLogger(__name__)
    logger.info('Transaction tracking')
    transactions = _fetch_transactions(
        config_yml=config_yml, from_time=from_time, to_time=to_time
    )
    df_txn = (
        pd.DataFrame(transactions).set_index('time')
        if transactions else pd.DataFrame()
    )
    logger.debug('df_txn.shape: {}'.format(df_txn.shape))
    if transactions:
        if csv_path:
            df_txn.to_csv(csv_path)
        if pl_graph_path:
            _plot_pl(transactions=transactions, path=pl_graph_path)
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


def _plot_pl(transactions, path):
    rcParams['figure.figsize'] = (11.88, 8.40)  # A4 aspect: (297x210)
    sns.set(style='ticks', color_codes=True)
    sns.set_context('paper')
    df_pl = _extract_df_pl(transactions=transactions).set_index(
        ['instrument', 'time']
    )['pl'].unstack(
        level=0, fill_value=0
    ).cumsum().stack().to_frame('PL').reset_index()
    logging.info(df_pl)
    sns.set_palette(palette='colorblind')
    ax = sns.lineplot(
        x='time', y='PL', hue='instrument', data=df_pl, alpha=0.8,
        legend='full'
    )
    ax.set_title('Cumulative PL')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), ncol=1)
    ax.figure.savefig(path)


def _extract_df_pl(transactions):
    cols = ['time', 'accountBalance', 'instrument', 'units', 'price', 'pl']
    return pd.DataFrame([
        {k: v for k, v in t.items() if k in cols}
        for t in transactions if t.get('accountBalance')
    ]).assign(
        time=lambda d: pd.to_datetime(d['time']),
        pl=lambda d: d['pl'].astype(float).fillna(0)
    ).pipe(
        lambda d: d[d['instrument'].notna()]
    )
