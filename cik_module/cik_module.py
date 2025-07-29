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

        self.headers = {'user-agent': 'MLT arada@hamilton.edu'}
        r = requests.get(self.fileurl, headers=self.headers)
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
            self.name_dict[name] = (cik, name, ticker)
            self.ticker_dict[ticker] = (cik, name, ticker)

    '''
    Given a company's name, return the corresponding CIK number, if it exists.
    '''
    def name_to_cik(self, name):
        try:
            return self.name_dict[name]
        except KeyError:
            print(f"Name: {name}, does not exist.")

    '''
    Given a company's ticker symbol, return the corresponding CIK number, if it exists.
    '''
    def ticker_to_cik(self, ticker):
        try:
            return self.ticker_dict[ticker]
        except KeyError:
            print(f"Ticker: {ticker}, does not exist.")

    '''
    Returns the url to a company's 10-K form given the year and
    the company's CIK number
    '''
    def annual_filing(self, cik, year):
        # retreiving a company's submission data from submissions API
        cik_for_submissions = self.adjust_cik_for_submissions(cik)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_for_submissions}.json"
        response = requests.get(submissions_url, headers=self.headers)
        response_json = response.json()

        years = self.get_years_of_10Ks(cik, response_json)
        
        if year in years:
            return years[year]
        return f"10-K form for the year {year} could not be found."
    
    '''
    Returns a dictionary with the years of filed 10-K forms as keys and
    the corresponding urls to the forms as values
    '''
    def get_years_of_10Ks(self, cik, response_json):
        # grabbing the indices that correspond to 10-K forms
        doc_descriptions = response_json['filings']['recent']['primaryDocDescription']
        indices_10K = []
        for index, desc in enumerate(doc_descriptions):
            if desc == '10-K':
                indices_10K.append(index)

        # gets the years for all the 10-K's and stores them in a dictionary with its file
        years = {}
        for index in indices_10K:
            date = response_json['filings']['recent']['filingDate'][index]
            year = int(date[:4])

            accessionNumber = response_json['filings']['recent']['accessionNumber'][index]
            accn_for_fileurl = self.adjust_accn_for_fileurl(accessionNumber)
            primaryDocument = response_json['filings']['recent']['primaryDocument'][index]
            file = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn_for_fileurl}/{primaryDocument}"

            years[year] = file

        return years

    '''
    CIK number needs to be 10 digits in submissions url, this function returns
    the CIK number with leading zeros (if nec.)
    '''
    def adjust_cik_for_submissions(self, cik):
        str_cik = str(cik)
        while len(str_cik) != 10:
            str_cik = '0' + str_cik
        return str_cik
    
    '''
    Accession number cannot include '-' in fileurl, this function returns the 
    inputted accession number as one long consecutive string.
    '''
    def adjust_accn_for_fileurl(self, accn):
        new_accn = ""
        for char in accn:
            if char != '-':
                new_accn += char
        return new_accn

sec = SecEdgar("https://www.sec.gov/files/company_tickers.json")
return_tuple = sec.ticker_to_cik('NVDA')
print(return_tuple)
print(sec.annual_filing(return_tuple[0], 2023))
