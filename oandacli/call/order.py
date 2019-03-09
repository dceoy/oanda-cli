#!/usr/bin/env python

import logging
import sys
from ..util.config import create_api, log_response, read_yml


def close_positions(config_yml, instruments=[]):
    logger = logging.getLogger(__name__)
    logger.info('Position closing')
    cf = read_yml(path=config_yml)
    account_id = cf['oanda']['account_id']
    api = create_api(config=cf)
    pos_res = api.position.list_open(accountID=account_id)
    log_response(pos_res, logger=logger)
    positions = pos_res.body['positions']
    if positions:
        for p in positions:
            pos = {
                'instrument': p.instrument,
                **{
                    '{}Units'.format(k):
                    ('NONE' if int(getattr(p, k).units) == 0 else 'ALL')
                    for k in ['long', 'short']
                }
            }
            logger.debug('pos: {}'.format(pos))
            res = api.position.close(accountID=account_id, **pos)
            log_response(res, logger=logger)
            if res.status == 200:
                logger.debug(res.body)
            else:
                logger.error(res.body)
                sys.exit(1)
        print('All the positions closed.')
    else:
        print('No positions to close.')
