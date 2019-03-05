#!/usr/bin/env python

import logging
import os
from ..util.config import create_api, read_yml


def close_positions(config_yml, instruments=[]):
    logger = logging.getLogger(__name__)
    logger.info('Position closing')
    cf = read_yml(path=config_yml)
    account_id = cf['oanda']['active_account']
    api = create_api(config=cf)
    insts = {
        p['instrument']
        for p in api.position.list_open(accountID=account_id)['positions']
        if not instruments or p['instrument'] in instruments
    }
    if insts:
        logger.debug('insts: {}'.format(insts))
        closed = [
            api.position.close(accountID=account_id, instrument=i)
            for i in insts
        ]
        logger.debug('closed:{0}{1}'.format(os.linesep, closed))
        print('All the positions closed.')
    else:
        print('No positions to close.')
