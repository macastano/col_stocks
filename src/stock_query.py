import argparse
import csv
import json
import os
import sys
from datetime import datetime

# CREDITS: https://github.com/alvarobartt/investpy
import investpy as stock


def write_csv(fname, data):
    with open(fname, 'a', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(data)


def query_stock(in_stock, in_country):
    fname = f'./data/{in_stock}_stockdata.csv'
    os.remove(fname) if os.path.exists(
        fname) and os.path.isfile(fname) else True

    data = json.loads(stock.get_stock_historical_data(
        stock=in_stock, country=in_country, from_date='01/01/2000', to_date=datetime.today().strftime("%d/%m/%Y"), as_json=True))

    stockdata = data['historical']

    count = 0
    for stockdetail in stockdata:
        if count == 0:
            header = stockdetail.keys()
            write_csv(fname, header)
            count += 1

        reformat_date = datetime.strptime(
            stockdetail['date'], "%d/%m/%Y").strftime("%m/%d/%Y")
        stockdetail['date'] = reformat_date
        write_csv(fname, stockdetail.values())
        count += 1

    return count


def main(arg_stock):
    try:
        search_result = stock.search_quotes(text=arg_stock, n_results=1)
        print(
            f'Symbol: {search_result.symbol}. Country: {search_result.country}')
        lines = query_stock(search_result.symbol, search_result.country)
        print(
            f'Historical stock data stored in: {arg_stock}_stockdata.csv. Count: {lines - 1} lines.')

    except RuntimeError as re:
        print(
            f'ERROR: Symbol {arg_stock} is not found. Enter a valid stock symbol.')


if __name__ == "__main__":

    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print('ERROR: Missing argument. Please pass the stock code.')
