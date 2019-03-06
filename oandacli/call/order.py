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
    insts = {
        p['instrument'] for p in positions
        if p['instrument'] in instruments or not instruments
    }
    if insts:
        logger.debug('insts: {}'.format(insts))
        for i in insts:
            res = api.position.close(accountID=account_id, instrument=i)
            body = ujson.loads(res.raw_body)
            if res.status == 200:
                logger.debug(body)
            else:
                logger.error(body)
                sys.exit(1)
        print('All the positions closed.')
    else:
        print('No positions to close.')
