#!/usr/bin/env python

import logging
import os
import sqlite3
from itertools import product

import matplotlib.pyplot as plt
import pandas as pd
import pandas.io.sql as pdsql
import seaborn as sns
from matplotlib.lines import Line2D


def read_and_plot_pl(data_path, graph_path):
    exts = {
        'csv': tuple([f'.csv{s}' for s in ['', '.gz', '.bz2']]),
        'tsv': tuple([
            (a + b) for a, b in product(['.tsv', '.txt'], ['', '.gz', '.bz2'])
        ]),
        'sqlite': ('.sqlite3', '.sqlite', '.db')
    }
    col_dtypes = {
        'id': int, 'time': str, 'accountBalance': float, 'instrument': str,
        'pl': float, 'tradeOpened': str
    }
    if data_path.endswith(exts['csv']):
        df_txn = pd.read_csv(
            data_path, sep=',', usecols=col_dtypes.keys(), dtype=col_dtypes
        )
    elif data_path.endswith(exts['tsv']):
        df_txn = pd.read_csv(
            data_path, sep='\t', usecols=col_dtypes.keys(), dtype=col_dtypes
        )
    elif data_path.endswith(exts['sqlite']):
        sql = (
            'SELECT id, time, accountBalance, instrument, pl, tradeOpened'
            ' FROM transaction_history'
            ' WHERE accountBalance IS NOT NULL AND instrument IS NOT NULL;'
        )
        with sqlite3.connect(data_path) as con:
            df_txn = pdsql.read_sql(sql, con=con).astype(col_dtypes).assign(
                tradeOpened=lambda d:
                d['tradeOpened'].mask(d['tradeOpened'] == 'nan')
            )
    else:
        raise ValueError(f'unsupported file type:\t{data_path}')
    plot_pl(df_txn=df_txn.set_index('id'), path=graph_path)


def plot_pl(df_txn, path):
    logger = logging.getLogger(__name__)
    df_pl = df_txn[[
        'time', 'accountBalance', 'instrument', 'pl', 'tradeOpened'
    ]].pipe(
        lambda d: d[d['accountBalance'].notna() & d['instrument'].notna()]
    ).astype(
        dtype={'accountBalance': float, 'pl': float, 'tradeOpened': object}
    ).assign(
        time=lambda d: pd.to_datetime(d['time']),
        pl=lambda d: d['pl'].fillna(0)
    )
    logger.debug(f'df_pl:{os.linesep}{df_pl}')
    df_cumpl = df_pl.set_index(['instrument', 'time'])['pl'].unstack(
        level=0, fill_value=0
    ).cumsum().stack().to_frame('pl').reset_index()
    logger.debug(f'df_cumpl:{os.linesep}{df_cumpl}')
    df_margin = df_pl.pipe(lambda d: d[d['tradeOpened'].notna()]).assign(
        initialMarginRequired=lambda d: d['tradeOpened'].astype(str).apply(
            lambda s: eval(s).get('initialMarginRequired')
        ).astype(float)
    )
    logger.debug(f'df_margin:{os.linesep}{df_margin}')

    plt.rcParams['figure.figsize'] = (11.88, 8.40)  # A4 aspect: (297x210)
    sns.set(style='ticks', color_codes=True)
    sns.set_context('paper')
    fig, axes = plt.subplots(nrows=3)
    plt.subplots_adjust(hspace=0.6)
    instruments = set(df_pl['instrument'])
    colors = {
        k: v for k, v in zip(
            sorted(instruments),
            sns.color_palette('deep', n_colors=len(instruments)).as_hex()
        )
    }
    alpha = 0.7
    time_range = (df_pl['time'].min(), df_pl['time'].max())
    ylim_ratio = 1.2

    for i, d in df_cumpl.groupby('instrument'):
        axes[0].plot(
            'time', 'pl', label=i, color=colors[i], data=d, alpha=alpha
        )
    axes[0].set(
        title='Cumulative Profit and Loss', ylabel='pl', xlim=time_range,
        ylim=(pd.Series([-1, 1]) * df_cumpl['pl'].abs().max() * ylim_ratio)
    )

    for i, d in df_margin.groupby('instrument'):
        axes[1].bar(
            x='time', height='initialMarginRequired', label=i, color=colors[i],
            data=d, alpha=alpha, width=0.02
        )
    axes[1].set(
        title='Initial Margins of Trades',
        ylabel='initialMarginRequired', xlim=time_range,
        ylim=(0, df_margin['initialMarginRequired'].max() * ylim_ratio)
    )

    axes[2].fill_between(
        x='time', y1='accountBalance', color='lightsteelblue', data=df_pl
    )
    axes[2].set(
        title='Account Balance', xlabel='time', ylabel='accountBalance',
        xlim=time_range, ylim=(0, df_pl['accountBalance'].max() * ylim_ratio)
    )

    sns.despine()
    fig.legend(
        handles=[
            Line2D([0], [0], color=v, label=k, alpha=alpha)
            for k, v in colors.items()
        ],
        loc='upper left', bbox_to_anchor=(0.91, 0.91), ncol=1,
        title='instrument'
    )
    fig.savefig(path, bbox_inches='tight')
