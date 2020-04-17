# getYfinance.py
A general purpose Yahoo! Finance scraper.

    usage: getYfinance.py [-h] [--version] [-d] [-r N] [-x | -j] (-i | -b | -c)
                          symbol [symbol ...]
    
    General purpose Yahoo! Finance scraper
    
    positional arguments:
      symbol                  ticker symbol
    
    optional arguments:
      -h, --help              show this help message and exit
      --version               show program's version number and exit
      -d, --by-date           print by date
      -r N, --record N        specify record N to print
      -x, --excel             print to excel instead of STDOUT
      -j, --json              print JSON to STDOUT
      -i, --income-statement  parse income statement
      -b, --balance-sheet     parse balance sheet
      -c, --cash-flow         parse cash flow
    

## Acknowledgments

* most of the original code came from https://www.mattbutton.com/2019/01/24/how-to-scrape-yahoo-finance-and-extract-fundamental-stock-market-data-using-python-lxml-and-pandas/

