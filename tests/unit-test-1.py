import logging
import sys
from calendar import isleap, monthrange
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import yfinance
from dateutil import parser, rrule
from plotly.subplots import make_subplots


def is_first_weekday_of_month(dt):
    weekday = dt.weekday()
    day = dt.day

    return (weekday == 0 and day in (1, 2, 3)) or (weekday in (1, 2, 3, 4) and day == 1)


def date_range(start_date, end_date, recur_day, skip=False):
    df_store = pd.DataFrame(columns=['date'])

    start_date = parser.parse(start_date)
    end_date = parser.parse(end_date)
    recur_flag = False
    for dt in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
        try:
            recur_date = datetime(dt.year, dt.month, recur_day)
        except:
            recur_date = datetime(dt.year, dt.month, monthrange(
                dt.year, dt.month)[1]) + timedelta(days=1)
            #recur_flag = True

        if len(df_store.index) > 0 and not skip:
            latest_recur_date = parser.parse(df_store.iloc[-1]['date'])
            delta = dt.month - latest_recur_date.month
            # if dt > recur_date and delta == 0:
            #     delta = 2
        else:
            delta = 0

        # TODO: Case March 29, 2015 (Sunday) it should be March 30 but is skipped and flags Apr 30 instead
        if (dt == recur_date and dt.strftime("%m/%d/%Y") in df['date'].unique()) or delta > 1:
            if delta > 1:
                while not dt.strftime("%m/%d/%Y") in df['date'].unique():
                    dt += timedelta(days=1)
            padding = ' ' * (9 - len(dt.strftime("%A")))
            # print(
            #     f'date: {dt.strftime("%Y-%m-%d")} | {dt.strftime("%A")}{padding} | {is_first_weekday_of_month(dt)}')
            df_dt = pd.DataFrame([dt.strftime("%m/%d/%Y")], columns=['date'])
            df_store = pd.concat([df_store, df_dt], ignore_index=True)
            recur_flag = False

    return df_store


def plot_range(range_df):
    range_df['diff'] = range_df['close'] - range_df['open']
    range_df.loc[range_df['diff'] >= 0, 'color'] = 'green'
    range_df.loc[range_df['diff'] < 0, 'color'] = 'red'

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Candlestick(x=range_df['date'],
                                 open=range_df['open'],
                                 high=range_df['high'],
                                 low=range_df['low'],
                                 close=range_df['close'],
                                 ))
    fig.add_trace(go.Scatter(x=range_df['date'], y=range_df['close'].rolling(
        window=1).mean(), marker_color='blue', opacity=0.1, name='MA'))
    fig.add_trace(go.Bar(
        x=range_df['date'], y=range_df['volume'], name='Volume', marker={'color': range_df['color']}, opacity=0.1), secondary_y=True)
    fig.update_yaxes(range=[0, 70000000], secondary_y=True)
    fig.update_yaxes(visible=False, secondary_y=True)
    fig.update_layout(xaxis_rangeslider_visible=False)

    return fig


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

df = pd.read_csv('./data/JFC_stockdata.csv')
# start_date = "05/03/2012"
start_date = "01/01/2015"
end_date = "12/31/2015"
recur_day = 15

logging.debug(
    f'\nstart_date: {start_date} | end_date: {end_date} | recur_day: {recur_day}')

df_dt = date_range(start_date, end_date, recur_day, skip=False)
logging.debug(f'\n{df_dt}')

merge_df = pd.merge(df, df_dt, how='inner', on=['date'])
logging.debug(f'\n{merge_df}')

# plot_range(merge_df).show()
