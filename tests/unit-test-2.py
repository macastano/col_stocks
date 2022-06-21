from calendar import isleap, monthrange
from datetime import datetime, timedelta
from email.policy import default

import pandas as pd
import plotly.graph_objects as go
from dateutil import parser, rrule
from plotly.subplots import make_subplots


def check_in_stock_data(df_stock, instance_date):

    if not isinstance(instance_date, datetime):
        instance_date = parser.parse(instance_date)

    return instance_date.strftime("%m/%d/%Y") in df_stock['date'].unique()


def today_or_next_working_day(dt):

    if not isinstance(dt, datetime):
        dt = parser.parse(dt)
    recur_day_name = dt.weekday()
    add_day = 0
    if recur_day_name == 5:
        add_day += 2
    if recur_day_name == 6:
        add_day += 1

    return dt + timedelta(days=add_day)


def date_range(start_date, end_date, recurrence='MONTHLY', interval=1):
    df_store = pd.DataFrame(columns=['date'])

    start_date = today_or_next_working_day(start_date)
    end_date = parser.parse(end_date)

    match (recurrence):
        case 'WEEKLY':
            for dt in rrule.rrule(freq=rrule.WEEKLY, interval=interval, dtstart=start_date, until=end_date):
                dt = today_or_next_working_day(dt)
                df_dt = pd.DataFrame(
                    [dt.strftime("%m/%d/%Y")], columns=['date'])
                df_store = pd.concat([df_store, df_dt], ignore_index=True)
        case 'MONTHLY':
            for dt in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
                recur_date = datetime(dt.year, dt.month, start_date.day)
                in_range = dt == recur_date and (
                    dt.month - start_date.month) % interval == 0
                if (in_range):
                    dt = today_or_next_working_day(dt)
                    df_dt = pd.DataFrame(
                        [dt.strftime("%m/%d/%Y")], columns=['date'])
                    df_store = pd.concat([df_store, df_dt], ignore_index=True)
        case 'YEARLY':
            for dt in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
                recur_date = datetime(
                    dt.year, start_date.month, start_date.day)
                in_range = dt == recur_date and (
                    dt.year - start_date.year) % interval == 0
                if (in_range):
                    df_dt = pd.DataFrame(
                        [dt.strftime("%m/%d/%Y")], columns=['date'])
                    df_store = pd.concat([df_store, df_dt], ignore_index=True)

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


def generate_EIP_range(df_stock, df_data_range):

    df_stocks = pd.DataFrame(
        columns=['date', 'open', 'high', 'low', 'close', 'volume', 'currency'])
    for dt in df_data_range['date']:
        if check_in_stock_data(df_stock, dt):
            df_stocks = pd.concat(
                [df_stocks, df_stock.loc[df['date'] == dt]], ignore_index=True)
        else:
            while not check_in_stock_data(df_stock, dt):
                dt = parser.parse(dt) + timedelta(days=1)

    return df_stocks


start_date = "01/3/2015"
end_date = "12/31/2015"

df = pd.read_csv('./data/JFC_stockdata.csv')
# print(check_in_stock_data(df, start_date))

df_range = date_range(start_date, end_date, 'MONTHLY', 1)
# print(df_range)

# flag = False
# weekday = today_or_next_working_day(start_date).weekday()
# for dt in df_range['date']:
#     dt = parser.parse(dt)
#     if dt.weekday() == 5 or dt.weekday() == 6:
#         flag = True
#     if dt.weekday() != weekday:
#         flag = True
# message = f'Fail.' if flag else f'Pass. Date is every {dt.strftime("%A")}'
# print(f'Weekend Checks: {message}')

df_stocks = generate_EIP_range(df, df_range)
print(df_stocks)
# plot_range(df_stocks).show()
