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
    oanda-cli spread [--debug|--info] [--file=<yaml>] [--csv=<path>] [--quiet]
                     [<instrument>...]
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
    --pl-graph=<path>   Visualize PL in a graphics file such as PDF or PNG

Commands:
    init                Create a YAML template for configuration
    info                Print information about <info_target>
    track               Fetch past rates
    stream              Stream market prices or authorized account events
    transaction         Fetch the latest transactions
    plotpl              Visualize cumulative PL in a file
    spread              Print the ratios of spread to price
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
    <graph_path>        Path to an output graphics file such as PDF or PNG
"""

import logging
import os
from pathlib import Path

import v20
from docopt import docopt

from .. import __version__
from ..call.candle import track_rate
from ..call.info import print_info, print_spread_ratios
from ..call.order import close_positions
from ..call.plot import read_and_plot_pl
from ..call.streamer import invoke_streamer
from ..call.transaction import track_transaction
from ..util.config import fetch_config_yml_path, read_yml, write_config_yml
from ..util.logger import set_log_config


def main():
    args = docopt(__doc__, version=f'oandacli {__version__}')
    set_log_config(debug=args['--debug'], info=args['--info'])
    logger = logging.getLogger(__name__)
    logger.debug(f'args:{os.linesep}{args}')
    config_yml_path = fetch_config_yml_path(path=args['--file'])
    execute_command(args=args, config_yml_path=config_yml_path)


def execute_command(args, config_yml_path):
    if args.get('init'):
        write_config_yml(
            dest_path=config_yml_path,
            template_path=str(
                Path(__file__).parent.parent.joinpath(
                    'static/default_oanda.yml'
                )
            )
        )
    else:
        config = read_yml(path=config_yml_path)
        api = v20.Context(
            hostname='{0}-fx{1}.oanda.com'.format(
                ('stream' if args.get('stream') else 'api'),
                config['oanda']['environment']
            ),
            token=config['oanda']['token']
        )
        account_id = config['oanda'].get('account_id')
        instruments = (
            args.get('<instrument>') or config.get('instruments') or list()
        )
        if args.get('info'):
            print_info(
                api=api, account_id=account_id, instruments=instruments,
                target=args['<info_target>'], print_json=args['--json']
            )
        elif args.get('spread'):
            print_spread_ratios(
                api=api, account_id=account_id, instruments=instruments,
                csv_path=args['--csv'], quiet=args['--quiet']
            )
        elif args.get('track'):
            track_rate(
                api=api, instruments=instruments,
                granularity=args['--granularity'], count=args['--count'],
                csv_dir_path=args['--csv-dir'], sqlite_path=args['--sqlite'],
                print_json=args['--json'], quiet=args['--quiet']
            )
        elif args.get('stream'):
            rd = config.get('redis') or dict()
            invoke_streamer(
                api=api, account_id=account_id, instruments=instruments,
                target=args['--target'], timeout_sec=args['--timeout'],
                csv_path=args['--csv'], sqlite_path=args['--sqlite'],
                use_redis=args['--use-redis'],
                redis_host=(args['--redis-host'] or rd.get('host')),
                redis_port=(args['--redis-port'] or rd.get('port')),
                redis_db=(args['--redis-db'] or rd.get('db')),
                redis_max_llen=args['--redis-max-llen'],
                ignore_api_error=args['--ignore-api-error'],
                quiet=args['--quiet']
            )
        elif args.get('transaction'):
            track_transaction(
                api=api, account_id=account_id, from_time=args['--from'],
                to_time=args['--to'], csv_path=args['--csv'],
                sqlite_path=args['--sqlite'], pl_graph_path=args['--pl-graph'],
                print_json=args['--json'], quiet=args['--quiet']
            )
        elif args.get('plotpl'):
            read_and_plot_pl(
                data_path=args['<data_path>'], graph_path=args['<graph_path>']
            )
        elif args.get('close'):
            close_positions(
                api=api, account_id=account_id, instruments=instruments
            )
