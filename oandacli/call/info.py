#!/usr/bin/env python

import os
import logging
from pprint import pformat
import ujson
import yaml
from ..util.error import OandaCliRuntimeError
from ..util.config import create_api, read_yml


def print_info(config_yml, instruments=[], type='accounts', print_json=False):
    logger = logging.getLogger(__name__)
    available_types = [
        'instruments', 'account', 'accounts', 'orders', 'trades', 'positions',
        'transactions', 'prices', 'position', 'order_book', 'position_book'
    ]
    if type not in available_types:
        raise OandaCliRuntimeError('invalid info type: {}'.format(type))
    logger.info('Information')
    cf = read_yml(path=config_yml)
    api = create_api(config=cf)
    account_id = cf['oanda']['account_id']
    insts = cf.get('instruments') or instruments
    arg_insts = {'instruments': ','.join(insts)} if insts else {}
    logger.debug('information type: {}'.format(type))
    if type == 'instruments':
        res = api.account.instruments(accountID=account_id, **arg_insts)
    elif type == 'account':
        res = api.account.get(accountID=account_id)
    elif type == 'accounts':
        res = api.account.list()
    elif type == 'orders':
        res = api.order.list_pending(accountID=account_id)
    elif type == 'trades':
        res = api.trade.list_open(accountID=account_id)
    elif type == 'positions':
        res = api.position.list_open(accountID=account_id)
    elif type == 'transactions':
        res = api.transaction.list(accountID=account_id)
    elif type == 'prices':
        res = api.pricing.get(accountID=account_id, **arg_insts)
    elif not insts:
        raise OandaCliRuntimeError('{}: instruments required'.format(type))
    elif type == 'position':
        res = api.position.get(accountID=account_id, instrument=insts[0])
    elif type == 'order_book':
        res = api.instrument.order_book(instrument=insts[0])
    elif type == 'position_book':
        res = api.instrument.position_book(instrument=insts[0])
    logger.debug('res:{0}{1}'.format(os.linesep, pformat(vars(res))))
    data = ujson.loads(res.raw_body)
    print(
        ujson.dumps(data) if print_json
        else yaml.dump(data, default_flow_style=False).strip()
    )
