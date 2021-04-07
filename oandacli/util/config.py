#!/usr/bin/env python

import logging
import os
import shutil
from pathlib import Path

import yaml


def read_yml(path):
    with open(path, 'r') as f:
        d = yaml.load(f, Loader=yaml.FullLoader)
    return d


def write_config_yml(dest_path, template_path):
    logger = logging.getLogger(__name__)
    if Path(dest_path).exists():
        print(f'A file already exists:\t{dest_path}')
    else:
        logger.info(f'Write a config:\t{dest_path}')
        shutil.copyfile(template_path, dest_path)
        print(f'A YAML template was generated:\t{dest_path}')


def fetch_config_yml_path(path=None, env='OANDA_YML', default='oanda.yml'):
    logger = logging.getLogger(__name__)
    p = [
        str(Path(p).resolve()) for p in [path, os.getenv(env), default]
        if p is not None
    ][0]
    logger.debug(f'abspath to a config:\t{p}')
    return p
