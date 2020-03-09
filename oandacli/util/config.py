#!/usr/bin/env python

import logging
import os
import shutil
from pathlib import Path
from pprint import pformat

import v20
import yaml


def read_yml(path):
    with open(path, 'r') as f:
        d = yaml.load(f, Loader=yaml.FullLoader)
    return d


def write_config_yml(dest_path, template_path):
    logger = logging.getLogger(__name__)
    if Path(dest_path).exists():
        print('A file already exists: {}'.format(dest_path))
    else:
        logger.info('Write a config: {}'.format(dest_path))
        shutil.copyfile(template_path, dest_path)
        print('A YAML template was generated: {}'.format(dest_path))


def fetch_config_yml_path(path=None, env='OANDA_YML', default='oanda.yml'):
    logger = logging.getLogger(__name__)
    p = [
        str(Path(p).resolve()) for p in [path, os.getenv(env), default]
        if p is not None
    ][0]
    logger.debug('abspath to a config: {}'.format(p))
    return p


def create_api(config, stream=False, **kwargs):
    return v20.Context(
        hostname='{0}-fx{1}.oanda.com'.format(
            ('stream' if stream else 'api'), config['oanda']['environment']
        ),
        token=config['oanda']['token'], **kwargs
    )


def log_response(response, logger=None, expected_status_range=(100, 399)):
    logger = logger or logging.getLogger(__name__)
    res_str = 'response =>{0}{1}'.format(os.linesep, pformat(vars(response)))
    esr = sorted(expected_status_range)
    if esr[0] <= response.status <= esr[-1]:
        logger.debug(res_str)
    else:
        logger.error(res_str)
