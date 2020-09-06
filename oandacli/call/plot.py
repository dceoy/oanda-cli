#!/usr/bin/env python

import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


def plot_pl(transactions, path):
    logger = logging.getLogger(__name__)
    df_pl = _extract_df_pl(transactions=transactions)
    logger.debug(f'df_pl:{os.linesep}{df_pl}')
    time_range = [df_pl['time'].min(), df_pl['time'].max()]
    df_cumpl = df_pl.set_index(['instrument', 'time'])['pl'].unstack(
        level=0, fill_value=0
    ).cumsum().stack().to_frame('pl').reset_index()
    logger.debug(f'df_cumpl:{os.linesep}{df_cumpl}')
    df_margin = df_pl.pipe(
        lambda d: d[d['tradeOpened'].notna()]
    ).assign(
        initialMarginRequired=lambda d: d['tradeOpened'].apply(
            lambda j: j.get('initialMarginRequired')
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

    for i, d in df_cumpl.groupby('instrument'):
        axes[0].plot(
            'time', 'pl', label=i, color=colors[i], data=d, alpha=alpha
        )
    axes[0].set(
        title='Cumulative PL', ylabel='pl', xlim=time_range
    )

    for i, d in df_margin.groupby('instrument'):
        axes[1].bar(
            x='time', height='initialMarginRequired', label=i, color=colors[i],
            data=d, alpha=alpha, width=0.02
        )
    axes[1].set(
        title='Initial Margins for Trades Opened',
        ylabel='initialMarginRequired', xlim=time_range
    )

    axes[2].fill_between(
        x='time', y1='accountBalance', color='lightsteelblue', data=df_pl
    )
    axes[2].set(
        title='Account Balance', xlabel='time', ylabel='accountBalance',
        xlim=time_range
    )

    sns.despine()
    fig.legend(
        handles=[
            Line2D([0], [0], color=v, label=k, alpha=alpha)
            for k, v in colors.items()
        ],
        loc='upper left', bbox_to_anchor=(0.95, 0.95), ncol=1,
        title='instrument'
    )
    fig.savefig(path, bbox_inches='tight')


def _extract_df_pl(transactions):
    cols = [
        'time', 'accountBalance', 'instrument', 'units', 'price', 'pl',
        'tradeOpened'
    ]
    return pd.DataFrame([
        {k: v for k, v in t.items() if k in cols}
        for t in transactions if t.get('accountBalance')
    ]).assign(
        time=lambda d: pd.to_datetime(d['time']),
        pl=lambda d: d['pl'].astype(float).fillna(0),
        accountBalance=lambda d: d['accountBalance'].astype(float)
    ).pipe(
        lambda d: d[d['instrument'].notna()]
    )
