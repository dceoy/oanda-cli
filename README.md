oanda-cli
=========

Command Line Interface for Oanda V20 REST API

[![wercker status](https://app.wercker.com/status/f747d0ad7049ed7a12936e7e993ac627/s/master "wercker status")](https://app.wercker.com/project/byKey/f747d0ad7049ed7a12936e7e993ac627)

Installation
------------

```sh
$ pip install -U oanda-cli
```

Docker image
------------

The image is available at [Docker Hub](https://hub.docker.com/r/dceoy/oanda-cli/).

```sh
$ docker pull dceoy/oanda-cli
```

Getting started
---------------

1.  Create and edit a configuration YAML file.

    ```sh
    $ oanda-cli init
    $ vim oanda.yml     # => edit
    ```

    An account ID and an API token are required to be set in the configuration file.

2.  Execute commands.

    ```sh
    # Print information
    $ oanda-cli info account
    $ oanda-cli info instruments
    $ oanda-cli info positions

    # Fetch past rates
    $ oanda-cli track

    # Stream market prices or authorized account transactions
    $ oanda-cli stream                          # prices
    $ oanda-cli stream --target=transaction     # transactions

    # Close all positions
    $ oanda-cli close
    ```

Usage
-----

```sh
$ oanda-cli --help
Command Line Interface for Oanda API

Usage:
    oanda-cli -h|--help
    oanda-cli -v|--version
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
    oanda-cli close [--debug|--info] [--file=<yaml>] [<instrument>...]

Options:
    -h, --help          Print help and exit
    -v, --version       Print version and exit
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

Commands:
    init                Create a YAML template for configuration
    info                Print information about <info_target>
    track               Fetch past rates
    stream              Stream market prices or authorized account events
    close               Close positions (if not <instrument>, close all)

Arguments:
    <info_target>       { instruments, prices, account, accounts, orders,
                          trades, positions, position, transactions,
                          order_book, position_book }
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
```
