#!/usr/bin/env python

import logging
import os
from pprint import pformat


def set_log_config(debug=None, info=None):
    if debug:
        lv = logging.DEBUG
    elif info:
        lv = logging.INFO
    else:
        lv = logging.WARNING
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S', level=lv
    )


def log_response(response, logger=None, expected_status_range=(100, 399)):
    logger = logger or logging.getLogger(__name__)
    res_str = 'response =>' + os.linesep + pformat(vars(response))
    esr = sorted(expected_status_range)
    if esr[0] <= response.status <= esr[-1]:
        logger.debug(res_str)
    else:
        logger.error(res_str)
