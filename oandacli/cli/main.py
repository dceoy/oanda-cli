#!/usr/bin/env python
"""
Command Line Interface for Oanda API

Usage:
    oanda-cli -h|--help
    oanda-cli --version
    oanda-cli init [--debug|--info] [--file=<yaml>]
    oanda-cli info [--debug|--info] [--file=<yaml>] [--json] <info_target>
                   [<instrument>...]
    oanda-cli track [--debug|--info] [--file=<yaml>] [--csv-dir=<path>]
                    [--sqlite=<path>] [--granularity=<code>] [--count=<int>]
                    [--json] [--quiet] [<instrument>...]
    oanda-cli stream [--debug|--info] [--file=<yaml>] [--target=<str>]
                     [--timeout=<sec>] [--csv=<path>] [--sqlite=<path>]
                     [--use-redis] [--redis-host=<ip>] [--redis-port=<int>]
                     [--redis-db=<int>] [--redis-max-llen=<int>]
                     [--ignore-api-error] [--quiet] [<instrument>...]
    oanda-cli transaction [--debug|--info] [--file=<yaml>] [--from=<date>]
                          [--to=<date>] [--csv=<path>] [--sqlite=<path>]
                          [--pl-graph=<path>] [--json] [--quiet]
    oanda-cli plotpl [--debug|--info] <data_path> <graph_path>
    oanda-cli close [--debug|--info] [--file=<yaml>] [<instrument>...]

Options:
    -h, --help          Print help and exit
    --version           Print version and exit
    --debug, --info     Execute a command with debug|info messages
    --file=<yaml>       Set a path to a YAML for configurations [$OANDA_YML]
    --quiet             Suppress messages
    --csv-dir=<path>    Write data with daily CSV in a directory
    --sqlite=<path>     Save data in an SQLite3 database
    --granularity=<code>
                        Set a granularity for rate tracking [default: S5]
    --count=<int>       Set a size for rate tracking (max: 5000) [default: 60]
    --json              Print data with JSON
    --target=<str>      Set a streaming target [default: pricing]
                        { pricing, transaction }
    --timeout=<sec>     Set senconds for response timeout
    --csv=<path>        Write data with CSV into a file
    --use-redis         Use Redis for data store
    --redis-host=<ip>   Set a Redis server host (override YAML configurations)
    --redis-port=<int>  Set a Redis server port (override YAML configurations)
    --redis-db=<int>    Set a Redis database (override YAML configurations)
    --redis-max-llen=<int>
                        Limit Redis list length (override YAML configurations)
    --ignore-api-error  Ignore Oanda API connection errors
    --from=<date>       Specify the starting time
    --to=<date>         Specify the ending time
    --pl-graph=<path>   Visualize cumulative PL in a file

Commands:
    init                Create a YAML template for configuration
    info                Print information about <info_target>
    track               Fetch past rates
    stream              Stream market prices or authorized account events
    transaction         Fetch the latest transactions
    plotpl              Visualize cumulative PL in a file
    close               Close positions (if not <instrument>, close all)

Arguments:
    <info_target>       { instruments, prices, account, accounts, orders,
                          trades, positions, position, order_book,
                          position_book }
    <instrument>        { AUD_CAD, AUD_CHF, AUD_HKD, AUD_JPY, AUD_NZD, AUD_SGD,
                          AUD_USD, CAD_CHF, CAD_HKD, CAD_JPY, CAD_SGD, CHF_HKD,
                          CHF_JPY, CHF_ZAR, EUR_AUD, EUR_CAD, EUR_CHF, EUR_CZK,
                          EUR_DKK, EUR_GBP, EUR_HKD, EUR_HUF, EUR_JPY, EUR_NOK,
                          EUR_NZD, EUR_PLN, EUR_SEK, EUR_SGD, EUR_TRY, EUR_USD,
                          EUR_ZAR, GBP_AUD, GBP_CAD, GBP_CHF, GBP_HKD, GBP_JPY,
                          GBP_NZD, GBP_PLN, GBP_SGD, GBP_USD, GBP_ZAR, HKD_JPY,
                          NZD_CAD, NZD_CHF, NZD_HKD, NZD_JPY, NZD_SGD, NZD_USD,
                          SGD_CHF, SGD_HKD, SGD_JPY, TRY_JPY, USD_CAD, USD_CHF,
                          USD_CNH, USD_CZK, USD_DKK, USD_HKD, USD_HUF, USD_INR,
                          USD_JPY, USD_MXN, USD_NOK, USD_PLN, USD_SAR, USD_SEK,
                          USD_SGD, USD_THB, USD_TRY, USD_ZAR, ZAR_JPY }
    <data_path>         Path to an input CSV or SQLite file
    <graph_path>        Path to an output graph file
"""

import logging
import os
from pathlib import Path

from docopt import docopt

from .. import __version__
from ..call.candle import track_rate
from ..call.info import print_info, track_transaction
from ..call.order import close_positions
from ..call.plot import read_and_plot_pl
from ..call.streamer import invoke_streamer
from ..util.config import fetch_config_yml_path, write_config_yml
from ..util.logger import set_log_config


def main():
    args = docopt(__doc__, version=f'oandacli {__version__}')
    set_log_config(debug=args['--debug'], info=args['--info'])
    logger = logging.getLogger(__name__)
    logger.debug(f'args:{os.linesep}{args}')
    config_yml_path = fetch_config_yml_path(path=args['--file'])
    execute_command(args=args, config_yml_path=config_yml_path)


def execute_command(args, config_yml_path):
    if args['init']:
        write_config_yml(
            dest_path=config_yml_path,
            template_path=str(
                Path(__file__).parent.parent.joinpath(
                    'static/default_oanda.yml'
                )
            )
        )
    elif args['info']:
        print_info(
            config_yml=config_yml_path, instruments=args['<instrument>'],
            target=args['<info_target>'], print_json=args['--json']
        )
    elif args['track']:
        track_rate(
            config_yml=config_yml_path, instruments=args['<instrument>'],
            granularity=args['--granularity'], count=args['--count'],
            csv_dir_path=args['--csv-dir'], sqlite_path=args['--sqlite'],
            print_json=args['--json'], quiet=args['--quiet']
        )
    elif args['stream']:
        invoke_streamer(
            config_yml=config_yml_path, target=args['--target'],
            instruments=args['<instrument>'], timeout_sec=args['--timeout'],
            csv_path=args['--csv'], sqlite_path=args['--sqlite'],
            use_redis=args['--use-redis'], redis_host=args['--redis-host'],
            redis_port=args['--redis-port'], redis_db=args['--redis-db'],
            redis_max_llen=args['--redis-max-llen'],
            ignore_api_error=args['--ignore-api-error'], quiet=args['--quiet']
        )
    elif args['transaction']:
        track_transaction(
            config_yml=config_yml_path, from_time=args['--from'],
            to_time=args['--to'], csv_path=args['--csv'],
            sqlite_path=args['--sqlite'], pl_graph_path=args['--pl-graph'],
            print_json=args['--json'], quiet=args['--quiet']
        )
    elif args['plotpl']:
        read_and_plot_pl(
            data_path=args['<data_path>'], graph_path=args['<graph_path>']
        )
    elif args['close']:
        close_positions(
            config_yml=config_yml_path, instruments=args['<instrument>']
        )
