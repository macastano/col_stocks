import csv
import datetime
import os
from webbrowser import get

import pandas as pd
from dateutil import parser


# TODO: FIX recur_day falling on a weekend, skipped
def today_or_next_working_day(dt, recur_day):
    recur_date = datetime.date(dt.year, dt.month, recur_day)
    recur_day_name = recur_date.weekday()

    add_day = 0
    if recur_day_name == 5:
        add_day += 2
    if recur_day_name == 6:
        add_day += 1

    return recur_date + datetime.timedelta(days=add_day)


def get_board_Lot(stock_price):
    match stock_price:
        case stock_price if stock_price < 0.01:
            return 1e+6
        case stock_price if 0.01 <= stock_price < 0.05:
            return 1e+5
        case stock_price if 0.05 <= stock_price < 0.5:
            return 1e+4
        case stock_price if 0.05 <= stock_price < 5.0:
            return 1e+3
        case stock_price if 5.0 <= stock_price < 50.0:
            return 1e+2
        case stock_price if 50.0 <= stock_price < 1000.0:
            return 1e+1
        case stock_price if stock_price >= 1000.0:
            return 5.0


def is_first_workday(dt):
    weekday = dt.weekday()
    day = dt.day

    if (weekday == 0 and day in (1, 2, 3)) or (weekday in (1, 2, 3, 4) and day == 1):
        return True
    else:
        return False


def compute_buy_price(price, lot):
    COMMISSION_RATE = 0.0025
    VAT = 1.12
    PSE_TRANS_FEE = 0.00005
    SCCP_FEE = 0.0001

    total_price = float(price) * lot
    commission = total_price * COMMISSION_RATE
    commission_with_VAT = 22.4 if commission < 20 else (commission * VAT)

    return total_price + commission_with_VAT + (total_price * (SCCP_FEE + PSE_TRANS_FEE))


def compute_sell_price(price, lot):
    COMMISSION_RATE = 0.0025
    VAT = 1.12
    PSE_TRANS_FEE = 0.00005
    SCCP_FEE = 0.0001
    SALES_TAX = 0.006

    total_price = float(price) * lot
    commission = total_price * COMMISSION_RATE
    commission_with_VAT = 22.4 if commission < 20 else (commission * VAT)

    return total_price - commission_with_VAT - (total_price * (SCCP_FEE + PSE_TRANS_FEE + SALES_TAX))


def compute_sell_price(price, lot):
    COMMISSION_RATE = 0.0025
    VAT = 1.12
    PSE_TRANS_FEE = 0.00005
    SCCP_FEE = 0.0001
    SALES_TAX = 0.006

    total_price = float(price) * lot
    commission = total_price * COMMISSION_RATE
    commission_with_VAT = 22.4 if commission < 20 else (commission * VAT)

    return total_price + commission_with_VAT + (total_price * (SCCP_FEE + PSE_TRANS_FEE + SALES_TAX))


def compute_lot_alloc(price, lot, budget):
    i = 1
    buy_amount = 0
    while buy_amount < float(budget):
        buy_amount = compute_buy_price(price, lot * i)
        i += 1
    return (lot * (i - 2))


def remove_csv(fname):
    os.remove(fname) if os.path.exists(
        fname) and os.path.isfile(fname) else True


def write_csv(fname, data):
    with open(fname, 'a', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(data)


def main(symbol, current_budget, recur_day, start_date, end_date):
    #current_budget = 10000
    #recur_day = 14
    #symbol = 'JFC'
    start_date = parser.parse(start_date).date()
    end_date = parser.parse(end_date).date()

    fname_read = f'./data/{symbol}_stockdata.csv'
    with open(fname_read) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        rem_budget = 0
        grand_total_buy_price = 0
        grand_total_lots = 0
        max_price = 0
        min_price = 9e+9

        fname_write = f'./data/{symbol}_analysed_stockdata.csv'
        remove_csv(fname_write)
        write_csv(fname_write, ['stock', 'date', 'stock price', 'min board lot',
                  'reco', 'total buy price', 'total lots', 'change'])

        for row in csv_reader:
            if line_count == 0:
                # print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                min_board_lot = get_board_Lot(float(row[4]))
                stock_date = parser.parse(row[0])
                trans_date = today_or_next_working_day(stock_date, recur_day)
                stock_price = float(row[4])

                # TODO: FIX problem with dates passing end of month on recur days
                if stock_date.date() == trans_date and (start_date < stock_date.date() < end_date):
                    recommendation = 'BUY'
                    lots = compute_lot_alloc(
                        float(row[4]), min_board_lot, current_budget)
                    total_buy_price = compute_buy_price(float(row[4]), lots)
                    change = current_budget - total_buy_price

                    grand_total_buy_price += total_buy_price
                    grand_total_lots += lots
                    rem_budget = rem_budget + change

                    min_price = float(row[4]) if float(
                        row[4]) < min_price else min_price
                    max_price = float(row[4]) if float(
                        row[4]) > max_price else max_price

                else:
                    recommendation = 'HOLD'
                    lots = 0
                    total_buy_price = 0
                    change = 0

                # print(
                #     f'\t{symbol} ({row[0]}): PHP {float(row[4]):,.2f}. Recommend: {recommendation}. {lots} lots for total of PHP {total_buy_price:,.2f}')
                write_csv(fname_write, [
                          symbol, row[0], f'{stock_price:,.2f}', min_board_lot, recommendation, f'{total_buy_price:,.2f}', lots, f'{change:,.2f}'])

                line_count += 1

        total_sell_price = compute_sell_price(float(row[4]), grand_total_lots)
        portfolio_gain_or_loss = total_sell_price - grand_total_buy_price
        portfolio_percentage = (
            (total_sell_price/grand_total_buy_price) - 1) * 100

        print('\n')
        print(
            f'Running total for budget change: PHP {rem_budget:,.2f}.', end=" ")
        print(
            f'Grand total for bought stocks: PHP {grand_total_buy_price:,.2f}.', end=" ")
        print(f'Grand total lots: {grand_total_lots:,.0f}')

        print('\n')
        print(f'Latest stock price: PHP {float(row[4]):,.2f}.', end=" ")
        print(f'Highest stock price: PHP {max_price:,.2f}.', end=" ")
        print(f'Lowest stock price: PHP {min_price:,.2f}.')

        print('\n')
        print(
            f'Sell price ({grand_total_lots:,.0f} lots): PHP {total_sell_price:,.2f}.', end=" ")
        print(
            f'Portfolio gain/loss: PHP {portfolio_gain_or_loss:,.2f}.', end=" ")
        print(
            f'Portfolio Percentage: {portfolio_percentage:.2f} %')

        print('\n')
        print(f'Processed {line_count} lines.')

        print('\n')


if __name__ == "__main__":

    main(symbol='JFC', current_budget=10000, recur_day=15,
         start_date='5/3/2012', end_date='4/11/2019')
