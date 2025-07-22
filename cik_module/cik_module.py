# Author: Alfonso Rada
# Date: 07/21/2025
# File Name: cik_module.py
# Description:  A module that can be used to lookup the CIK number of companys registered with the SEC

import requests

'''
    Given a URL to an SEC public JSON file, extract its information and use it to
    lookup a company's CIK number by name or by ticker symbol.
'''
class SecEdgar:
    '''
    Grabbing the JSON from the SEC URL and filling dictionaries for lookup
    '''
    def __init__(self, fileurl):
        self.fileurl = fileurl

        headers = {'user-agent': 'MLT arada@hamilton.edu'}
        r = requests.get(self.fileurl, headers=headers)
        self.filejson = r.json()

        self.cik_json_to_dict()

    '''
    Fills name_dict and ticker_dict dictionaries using data from 
    SEC JSON file with company information
    '''
    def cik_json_to_dict(self):
        self.name_dict = {}
        self.ticker_dict = {}

        for value in self.filejson.values():
            cik = value["cik_str"]
            name = value["title"]
            ticker = value["ticker"]
            self.name_dict[name] = cik
            self.ticker_dict[ticker] = cik

    '''
    Given a company's name, return the corresponding CIK number, if it exists.
    '''
    def name_to_cik(self, name):
        try:
            cik = self.name_dict[name]
            return (f"Name: {name}, CIK: {cik}")
        except KeyError:
            print(f"Name: {name}, does not exist.")

    '''
    Given a company's ticker symbol, return the corresponding CIK number, if it exists.
    '''
    def ticker_to_cik(self, ticker):
        try:
            cik = self.ticker_dict[ticker]
            return (f"Ticker: {ticker}, CIK: {cik}")
        except KeyError:
            print(f"Ticker: {ticker}, does not exist.")

sec = SecEdgar("https://www.sec.gov/files/company_tickers.json")