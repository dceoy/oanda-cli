#!/usr/bin/env python

import logging
import os
from pprint import pformat

from ..util.config import create_api, log_response, read_yml


def close_positions(config_yml, instruments=None):
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
            if not instruments or p.instrument in instruments:
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
                if 100 <= res.status <= 399:
                    logger.debug(res.body)
                else:
                    raise RuntimeError(
                        'unexpected response:' + os.linesep + pformat(res.body)
                    )
        print('All the positions closed.')
    else:
        print('No positions to close.')
