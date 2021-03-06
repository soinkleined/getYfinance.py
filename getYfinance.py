#!/usr/bin/env python

########################################
#
# Author:
#    David Klein
#
# Contact:
#    david@soinkleined.com 
# 
# Version:
#    0.8 - 2020-05-08 - David Klein <david@soinkleined.com>
#    * changed tabs to spaces
#    * added date timestamp to summary output
#    * fixed json output by date for summary
#    * removed index labels from STDOUT
#    * changed by-date arg to transpose as not all data has date cols
#    * moved dat var inside get_page to have appropriate timestamp
#    0.7 - 2020-04-20 - David Klein <david@soinkleined.com>
#    * added summary option
#    0.6 - 2020-04-17 - David Klein <david@soinkleined.com>
#    * reformatted help
#    * used correct positional arguments 
#    0.5 - 2020-04-15 - David Klein <david@soinkleined.com>
#    * removed redundant code
#    * added symbol and type to json
#    0.4 - 2020-04-15 - David Klein <david@soinkleined.com>
#    * added json output
#    0.3 - 2020-04-14 - David Klein <david@soinkleined.com>
#    * added record print
#    * added record validation
#    0.2 - 2020-04-09 - David Klein <david@soinkleined.com>
#    * added parse options and sort by date
#    * added excel output
#    * added help descriptions
#    0.1 - 2020-04-08 - David Klein <david@soinkleined.com>
#    * initial release
# 
# To do:
#    * validate ticker args 
#    * validate http request
#    * fix or remove record query for summary
# 
# References:
#    https://www.mattbutton.com/2019/01/24/how-to-scrape-yahoo-finance-and-extract-fundamental-stock-market-data-using-python-lxml-and-pandas/
#    https://www.scrapehero.com/scrape-yahoo-finance-stock-market-data/
#    https://stackoverflow.com/questions/33752819/pandas-dataframe-from-dict-not-preserving-order-using-ordereddict
#    https://stackoverflow.com/questions/17839973/constructing-pandas-dataframe-from-values-in-variables-gives-valueerror-if-usi
#    https://stackoverflow.com/questions/50615824/xpath-copied-from-inspector-returns-wrong-results
#
########################################
version='0.8'
from datetime import datetime
import lxml
from lxml import html
import requests
import numpy as np
import pandas as pd
import argparse 
import json
from collections import OrderedDict
########################################
# ARGS
########################################
# make help output neater
formatter = lambda prog: argparse.HelpFormatter(prog,max_help_position=52)
parser = argparse.ArgumentParser(formatter_class=formatter, description='General purpose Yahoo! Finance scraper')
parser.add_argument('symbols', nargs='+', metavar='symbol', action='store', help='ticker symbol(s)')
parser.add_argument('--version', action='version', version='%(prog)s ' + version)
parser.add_argument('-t', '--transpose', action='store_true', help='transpose rows and columns')
parser.add_argument('-r', '--record', metavar='N', action='store', type=int, help='specify record N to print')
group_output = parser.add_mutually_exclusive_group(required=False)
group_output.add_argument('-x', '--excel', action='store_true', help='print to excel instead of STDOUT')
group_output.add_argument('-j', '--json', action='store_true', help='print JSON to STDOUT')
group_type = parser.add_mutually_exclusive_group(required=True)
group_type.add_argument('-i', '--income-statement', action='store_true', help='parse income statement')
group_type.add_argument('-b', '--balance-sheet', action='store_true', help='parse balance sheet')
group_type.add_argument('-c', '--cash-flow', action='store_true', help='parse cash flow')
group_type.add_argument('-s', '--summary', action='store_true', help='parse summary')
args = parser.parse_args()
args.symbols = [x.upper() for x in args.symbols]
########################################
# VARS
########################################

########################################
# METHODS
########################################

def get_page(url):
    # Set up the request headers that we're going to use, to simulate
    # a request by the Chrome browser. Simulating a request from a browser
    # is generally good practice when building a scraper
    date = datetime.today().strftime('%Y%m%d%H%M%S')
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache',
        'Referrer': 'https://google.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
    }
    return requests.get(url, headers), date

def parse_rows(table_rows):
    parsed_rows = []

    for table_row in table_rows:
        parsed_row = []
        el = table_row.xpath("./div")

        none_count = 0

        for rs in el:
           try:
              (text,) = rs.xpath('.//span/text()[1]')
              parsed_row.append(text)
           except ValueError:
              parsed_row.append(np.NaN)
              none_count += 1

        if (none_count < 4):
           parsed_rows.append(parsed_row)
    
    return pd.DataFrame(parsed_rows)

def clean_data_summary(df):
    df = df.transpose()
    cols = list(df.columns)
    df = df.set_axis(cols, axis='columns', inplace=False)
    df = df.transpose()
    return df

def clean_data(df):
    df = df.set_index(0) # Set the index to the first column: 'Period Ending'.
    df = df.transpose() # Transpose the DataFrame, so that our header contains the account names
    # Rename the "Breakdown" column to "Date"
    cols = list(df.columns)
    cols[0] = 'Date'
    df = df.set_axis(cols, axis='columns', inplace=False)
    
    # https://stackoverflow.com/questions/44833051/how-to-add-numbers-above-a-pandas-dataframes-column-names/44833717
    # transpose leaves non-unique column headers, so the below is required to create unique column names
    df.columns = pd.MultiIndex.from_tuples(list(enumerate(df)))
    
    numeric_columns = list(df.columns)[1::] # Take all columns, except the first (which is the 'Date' column)

    if args.excel or args.json:
        for column_name in numeric_columns:
           df[column_name] = df[column_name].str.replace(',', '') # Remove the thousands separator
           df[column_name] = df[column_name].astype(np.float64) # Convert the column to
    
    df = df.set_axis(cols, axis='columns', inplace=False)
    return df

def scrape_table(url):
    # Fetch the page that we're going to parse
    page, date = get_page(url);

    # Parse the page with LXML, so that we can start doing some XPATH queries
    # to extract the data that we want
    tree = html.fromstring(page.content)
    title = tree.xpath("//h1/text()")
    if not args.excel or args.json:
        print(title)

    if args.summary:
        # Xpath needs to be updated if format changes
        price = tree.xpath('//*[@id="quote-header-info"]/div[3]/div/span/text()')  
        change = tree.xpath('//*[@id="quote-header-info"]/div[3]/div/div/span//text()')  
        market_notice = tree.xpath('//*[@id="quote-header-info"]/div[3]/div/div/div/span//text()')  
        table_rows = tree.xpath('//div[contains(@data-test,"summary-table")]//tr')
        # validate the table formatting and scraping is accurate
        assert len(table_rows) > 0
        summary_data = OrderedDict()
        summary_data.update({'Current Price':price})
        summary_data.update({'Query Timestamp':date})
        summary_data.update({'Market Notice':market_notice})
        summary_data.update({'Change':change})
        for table_data in table_rows:
           raw_table_key = table_data.xpath('.//td[contains(@class,"C($primaryColor)")]//text()')
           raw_table_value = table_data.xpath('.//td[contains(@class,"Ta(end)")]//text()')
           table_key = ''.join(raw_table_key).strip()
           table_value = ''.join(raw_table_value).strip()
           summary_data.update({table_key:table_value})
        df = pd.DataFrame(summary_data, columns=summary_data.keys(), index=[0])
        df = clean_data_summary(df)
    else:
        # Fetch all div elements which have class 'D(tbr)'
        table_rows = tree.xpath("//div[contains(@class, 'D(tbr)')]")
        # validate the table formatting and scraping is accurate
        assert len(table_rows) > 0
        df = parse_rows(table_rows)
        df = clean_data(df)

    return df


for symbol in args.symbols:

    if args.income_statement:
        url = "https://finance.yahoo.com/quote/%s/financials?p=%s"%(symbol,symbol)
        type = 'Income Statement'
    elif args.balance_sheet:
        url = "https://finance.yahoo.com/quote/%s/balance-sheet?p=%s"%(symbol,symbol)
        type = 'Balance Sheet'
    elif args.cash_flow:
        url = "https://finance.yahoo.com/quote/%s/cash-flow?p=%s"%(symbol,symbol)
        type = 'Cash Flow'
    elif args.summary:
        url = "https://finance.yahoo.com/quote/%s?p=%s"%(symbol,symbol)
        type = 'Summary'

    df_result = scrape_table(url)
    if args.record:
        assert args.record <= len(df_result)

    if args.excel:
        file = symbol + '-' + type.replace(' ','_') + '-' + date + '.xlsx'
        writer = pd.ExcelWriter(file)
    if args.transpose :
        if args.record:
           df_result = df_result.loc[:, [args.record]]
    elif args.summary:
        if args.record:
           df_result = df_result.loc[[args.record], :]
        df_result = df_result.transpose()
    else:
        df_result = df_result.transpose()
        if args.record:
           df_result = df_result.loc[:, [args.record]]
    if args.excel:
        df_result.to_excel(writer,type)
        print('Writing ' + file)
        writer.save()
    elif args.json:
        json_object={}
        json_object['COMPANY'] = symbol
        json_object['TYPE'] = type
        json_object_result = json.loads(df_result.to_json(orient='table'))
        json_object.update(json_object_result)
        json_formatted_str = json.dumps(json_object, indent=2)
        print(json_formatted_str)
    elif args.transpose:
        # Don't print row numbers
        print(df_result.to_string(index=False))
    else:
        # Don't print column numbers
        print(df_result.to_string(header=False))

exit(0)
