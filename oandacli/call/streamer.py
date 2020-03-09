#!/usr/bin/env python

import logging
import signal
import sqlite3
from abc import ABCMeta, abstractmethod
from datetime import datetime
from pathlib import Path

import pandas as pd
import redis
from v20 import V20ConnectionError, V20Timeout

from ..util.config import create_api, log_response, read_yml


class StreamDriver(object, metaclass=ABCMeta):
    def __init__(self, api, account_id, target='pricing', instruments=None,
                 timeout_sec=0, snapshot=True, ignore_api_error=False):
        if target not in ['pricing', 'transaction']:
            raise ValueError('invalid target: {}'.format(target))
        elif target == 'pricing' and not instruments:
            raise ValueError('pricing: instruments required')
        else:
            self.__logger = logging.getLogger(__name__)
            self.__api = api
            self.__account_id = account_id
            self.__target = target
            self.__instruments = instruments
            self.__timeout_sec = float(timeout_sec) if timeout_sec else None
            self.__snapshot = snapshot
            self.__ignore_api_error = ignore_api_error
            self.__latest_update_time = None

    def invoke(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            res = self._call_stream_api()
            for msg_type, msg in res.parts():
                self.act(msg_type, msg)
                self.__latest_update_time = datetime.now()
        except (V20ConnectionError, V20Timeout) as e:
            if not self.__ignore_api_error:
                self.shutdown()
                raise e
            else:
                self.__logger.error(e)
                if self.__timeout_sec and self.__latest_update_time:
                    td = datetime.now() - self.__latest_update_time
                    if td.total_seconds() > self.__timeout_sec:
                        self.__logger.warning(
                            'Timeout: {} sec'.format(self.__timeout_sec)
                        )
                        self.shutdown()
                        raise e
        else:
            log_response(res, logger=self.__logger)

    def _call_stream_api(self):
        if self.__target == 'pricing':
            self.__logger.info('Start to stream market prices')
            return self.__api.pricing.stream(
                accountID=self.__account_id, snapshot=self.__snapshot,
                instruments=','.join(self.__instruments)
            )
        elif self.__target == 'transaction':
            self.__logger.info('Start to stream transactions for the account')
            return self.__api.transaction.stream(accountID=self.__account_id)

    @abstractmethod
    def act(self, msg_type, msg):
        pass

    @abstractmethod
    def shutdown(self):
        pass


class StreamRecorder(StreamDriver):
    def __init__(self, api, account_id, target='pricing', instruments=None,
                 timeout_sec=0, snapshot=True, ignore_api_error=False,
                 skip_heartbeats=True, use_redis=False, redis_host='127.0.0.1',
                 redis_port=6379, redis_db=0, redis_max_llen=None,
                 sqlite_path=None, csv_path=None, quiet=False):
        super().__init__(
            api=api, account_id=account_id, target=target,
            instruments=instruments, timeout_sec=timeout_sec,
            snapshot=snapshot, ignore_api_error=ignore_api_error
        )
        self.__logger = logging.getLogger(__name__)
        self.__instruments = instruments
        self.__skip_heartbeats = skip_heartbeats
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
            sqlite_file = Path(sqlite_path).resolve()
            if sqlite_file.is_file():
                self.__sqlite = sqlite3.connect(str(sqlite_file))
            else:
                schema_sql_path = str(
                    Path(__file__).parent.parent.joinpath(
                        'static/create_tables.sql'
                    )
                )
                with open(schema_sql_path, 'r') as f:
                    sql = f.read()
                self.__sqlite = sqlite3.connect(str(sqlite_file))
                self.__sqlite.executescript(sql)
        else:
            self.__sqlite = None
        if csv_path:
            self.__csv_path = str(Path(csv_path).resolve())
        else:
            self.__csv_path = None

    def act(self, msg_type, msg):
        if msg_type.endswith('Heartbeat') and self.__skip_heartbeats:
            self.__logger.debug(msg)
        elif (msg_type.startswith('transaction.') or
              (msg_type.startswith('pricing.') and msg.instrument)):
            self.__logger.debug(msg)
            self._print_and_write_msg(msg_type=msg_type, msg=msg)
        else:
            self.__logger.warning('Save skipped: {}'.format(msg))

    def _print_and_write_msg(self, msg_type, msg):
        msg_json_str = str(msg.json())
        if not self.__quiet:
            print(msg_json_str, flush=True)
        inst = msg.instrument or ''
        if self.__redis_pool:
            data_key = inst or 'transactions'
            redis_c = redis.StrictRedis(connection_pool=self.__redis_pool)
            redis_c.rpush(data_key, msg_json_str)
            if self.__redis_max_llen:
                if redis_c.llen(data_key) > self.__redis_max_llen:
                    redis_c.lpop(data_key)
        if self.__sqlite:
            c = self.__sqlite.cursor()
            table_name = msg_type.split('.')[0] + '_stream'
            c.execute(
                'INSERT INTO {} VALUES (?,?,?)'.format(table_name),
                [msg.time, inst, msg_json_str]
            )
            self.__sqlite.commit()
        if self.__csv_path:
            pd.DataFrame(
                [{'time': msg.time, 'instrument': inst, 'json': msg_json_str}]
            ).set_index(
                ['time', 'instrument']
            ).to_csv(
                self.__csv_path, mode='a',
                sep=(',' if self.__csv_path.endswith('.csv') else '\t'),
                header=(not Path(self.__csv_path).is_file())
            )

    def shutdown(self):
        if self.__redis_pool:
            self.__redis_pool.disconnect()
        if self.__sqlite:
            self.__sqlite.close()


def invoke_streamer(config_yml, target='pricing', instruments=None,
                    timeout_sec=0, csv_path=None, sqlite_path=None,
                    use_redis=False, redis_host='127.0.0.1', redis_port=6379,
                    redis_db=0, redis_max_llen=None, ignore_api_error=False,
                    quiet=False, skip_heartbeats=True):
    logger = logging.getLogger(__name__)
    logger.info('Streaming')
    cf = read_yml(path=config_yml)
    rd = cf.get('redis') or dict()
    streamer = StreamRecorder(
        api=create_api(config=cf, stream=True),
        account_id=cf['oanda']['account_id'], target=target,
        instruments=(instruments or cf['instruments']),
        timeout_sec=timeout_sec, snapshot=True,
        ignore_api_error=ignore_api_error, skip_heartbeats=skip_heartbeats,
        use_redis=use_redis, redis_host=(redis_host or rd.get('host')),
        redis_port=(redis_port or rd.get('port')),
        redis_db=(redis_db if redis_db is not None else rd.get('db')),
        redis_max_llen=redis_max_llen, sqlite_path=sqlite_path,
        csv_path=csv_path, quiet=quiet
    )
    streamer.invoke()
