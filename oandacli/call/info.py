#!/usr/bin/env python

import logging

import yaml

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
    elif target == 'transactions':
        res = api.transaction.list(accountID=account_id)
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
    print(
        res.raw_body if print_json
        else yaml.dump(res.body, default_flow_style=False).strip()
    )
