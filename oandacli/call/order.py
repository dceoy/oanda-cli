#!/usr/bin/env python

import logging
import sys
import ujson
from ..util.config import create_api, read_yml


def close_positions(config_yml, instruments=[]):
    logger = logging.getLogger(__name__)
    logger.info('Position closing')
    cf = read_yml(path=config_yml)
    account_id = cf['oanda']['account_id']
    api = create_api(config=cf)
    positions = ujson.loads(
        api.position.list_open(accountID=account_id).raw_body
    )['positions']
    logger.debug('positions: {}'.format(positions))
    pos_dict = {
        p['instrument']: {
            '{}Units'.format(k): ('NONE' if int(p[k]['units']) == 0 else 'ALL')
            for k in ['long', 'short']
        } for p in positions
        if p['instrument'] in instruments or not instruments
    }
    if pos_dict:
        logger.debug('pos_dict: {}'.format(pos_dict))
        for i, a in pos_dict.items():
            res = api.position.close(
                accountID=account_id, instrument=i, **a
            )
            body = ujson.loads(res.raw_body)
            if res.status == 200:
                logger.debug(body)
            else:
                logger.error(body)
                sys.exit(1)
        print('All the positions closed.')
    else:
        print('No positions to close.')
