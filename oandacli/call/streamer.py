#!/usr/bin/env python

import json
import logging
import os
import signal
import sqlite3
import oandapy
import pandas as pd
import redis
import yaml
from ..util.config import read_yml
from ..util.error import OandaCliRuntimeError


class StreamDriver(oandapy.Streamer):
    def __init__(self, config_dict, target='rate', instruments=None,
                 ignore_heartbeat=True, print_json=False, use_redis=False,
                 redis_host='127.0.0.1', redis_port=6379, redis_db=0,
                 redis_max_llen=None, sqlite_path=None, csv_path=None,
                 quiet=False):
        self.__logger = logging.getLogger(__name__)
        super().__init__(
            environment=config_dict['oanda']['environment'],
            access_token=config_dict['oanda']['access_token']
        )
        self.__account_id = config_dict['oanda']['account_id'],
        if target in ['rate', 'event']:
            self.__data_key = {'rate': 'tick', 'event': 'transaction'}[target]
        else:
            raise OandaCliRuntimeError(
                'invalid stream target: {}'.format(target)
            )
        self.__instruments = (
            instruments if instruments else config_dict['instruments']
        )
        self.__ignore_heartbeat = ignore_heartbeat
        self.__print_json = print_json
        self.__quiet = quiet
        if use_redis:
            self.__logger.info('Set a streamer with Redis')
            self.__redis_pool = redis.ConnectionPool(
                host=redis_host, port=int(redis_port), db=int(redis_db)
            )
            self.__redis_max_llen = (
                int(redis_max_llen) if redis_max_llen else None
            )
            redis_c = redis.StrictRedis(connection_pool=self.__redis_pool)
            redis_c.flushdb()
        else:
            self.__redis_pool = None
            self.__redis_max_llen = None
        if sqlite_path:
            self.__logger.info('Set a streamer with SQLite')
            sqlite_abspath = os.path.abspath(
                os.path.expanduser(os.path.expandvars(sqlite_path))
            )
            if os.path.isfile(sqlite_abspath):
                self.__sqlite = sqlite3.connect(sqlite_abspath)
            else:
                schema_sql_path = os.path.join(
                    os.path.dirname(__file__), '../static/create_tables.sql'
                )
                with open(schema_sql_path, 'r') as f:
                    sql = f.read()
                self.__sqlite = sqlite3.connect(sqlite_abspath)
                self.__sqlite.executescript(sql)
        else:
            self.__sqlite = None
        if csv_path:
            self.__csv_path = os.path.abspath(
                os.path.expanduser(os.path.expandvars(csv_path))
            )
        else:
            self.__csv_path = None

    def on_success(self, data):
        data_json_str = json.dumps(data)
        if self.__quiet:
            self.__logger.debug(data)
        elif self.__print_json:
            print(data_json_str, flush=True)
        else:
            print(yaml.dump(data).strip(), flush=True)
        if 'disconnect' in data:
            self.__logger.warning('Streaming disconnected: {}'.format(data))
            self.shutdown()
        elif self.__data_key in data:
            self.__logger.debug(data)
            if self.__redis_pool:
                instrument = data[self.__data_key]['instrument']
                redis_c = redis.StrictRedis(connection_pool=self.__redis_pool)
                redis_c.rpush(instrument, data_json_str)
                if self.__redis_max_llen:
                    if redis_c.llen(instrument) > self.__redis_max_llen:
                        redis_c.lpop(instrument)
            if self.__sqlite:
                c = self.__sqlite.cursor()
                if self.__data_key == 'tick':
                    c.execute(
                        'INSERT INTO tick VALUES (?,?,?,?)',
                        [
                            data['tick']['instrument'], data['tick']['time'],
                            data['tick']['bid'], data['tick']['ask']
                        ]
                    )
                    self.__sqlite.commit()
                elif self.__data_key == 'transaction':
                    c.execute(
                        'INSERT INTO transaction VALUES (?,?,?)',
                        [
                            data['transaction']['instrument'],
                            data['transaction']['time'],
                            json.dumps(data['transaction'])
                        ]
                    )
                    self.__sqlite.commit()
            if self.__csv_path:
                pd.DataFrame([data[self.__data_key]]).set_index(
                    'time', drop=True
                ).to_csv(
                    self.__csv_path, mode='a',
                    sep=(',' if self.__csv_path.endswith('.csv') else '\t'),
                    header=(not os.path.isfile(self.__csv_path))
                )
        else:
            self.__logger.warning('Save skipped: {}'.format(data))

    def on_error(self, data):
        self.__logger.error(data)
        self.shutdown()

    def invoke(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if self.__data_key == 'tick':
            self.__logger.info('Start to stream market prices')
            self.rates(
                account_id=self.__account_id,
                ignore_heartbeat=self.__ignore_heartbeat,
                instruments=','.join(self.__instruments)
            )
        elif self.__data_key == 'transaction':
            self.__logger.info('Start to stream events for the account')
            self.events(
                account_id=self.__account_id,
                ignore_heartbeat=self.__ignore_heartbeat
            )

    def shutdown(self):
        self.disconnect()
        if self.__redis_pool:
            self.__redis_pool.disconnect()
        if self.__sqlite:
            self.__sqlite.close()


def invoke_streamer(config_yml, target='rate', instruments=None, csv_path=None,
                    sqlite_path=None, use_redis=False, redis_host='127.0.0.1',
                    redis_port=6379, redis_db=0, redis_max_llen=None,
                    print_json=False, quiet=False):
    logger = logging.getLogger(__name__)
    logger.info('Streaming')
    cf = read_yml(path=config_yml)
    rd = cf['redis'] if 'redis' in cf else {}
    streamer = StreamDriver(
        config_dict=cf, target=target, instruments=instruments,
        print_json=print_json, use_redis=use_redis,
        redis_host=(redis_host or rd.get('host')),
        redis_port=(redis_port or rd.get('port')),
        redis_db=(redis_db if redis_db is not None else rd.get('db')),
        redis_max_llen=redis_max_llen, sqlite_path=sqlite_path,
        csv_path=csv_path, quiet=quiet
    )
    streamer.invoke()
