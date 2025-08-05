# Author: Alfonso Rada
# Date: 08/04/2025
# File Name: cik_module.py
# Description:  A module that can be used to lookup the CIK number of companys registered with the SEC, 
# and grab its 10K and/or 10Q forms by year and/or quarter

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
    Returns the content to a company's 10-K form given the company's 
    CIK number and the year
    '''
    def annual_filing(self, cik, year):
        # retreiving a company's submission data from submissions API
        cik_for_submissions = self.adjust_cik_for_submissions(cik)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_for_submissions}.json"
        response = requests.get(submissions_url, headers=self.headers)
        response_json = response.json()

        url_10K = self.find_10K_file(cik, year, response_json)
        if url_10K:
            response = requests.get(url_10K, headers=self.headers)
            return response.text

        return f"10-K form for the year {year} could not be found."
        
    '''
    Returns the url to a company's 10K by searching for a matching year
    '''
    def find_10K_file(self, cik, year, response_json):
        # looking for the 10-K that corresponds to the year we're looking for
        forms = response_json['filings']['recent']['form']
        for index, desc in enumerate(forms):
            if desc == '10-K':
                date = response_json['filings']['recent']['reportDate'][index]
                yr = int(date[:4])
                if yr == year:
                    accessionNumber = response_json['filings']['recent']['accessionNumber'][index]
                    accn_for_fileurl = self.adjust_accn_for_fileurl(accessionNumber)
                    primaryDocument = response_json['filings']['recent']['primaryDocument'][index]

                    file = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn_for_fileurl}/{primaryDocument}"
                    return file
                
        return None

    '''
    Returns the content to a company's 10-Q form given the company's CIK number, the year, and the quarter
    '''
    def quarterly_filing(self, cik, year, quarter):
        # retreiving a company's submission data from submissions API
        cik_for_submissions = self.adjust_cik_for_submissions(cik)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_for_submissions}.json"
        response = requests.get(submissions_url, headers=self.headers)
        response_json = response.json()

        url_10Q = self.find_10Q_file(cik, year, quarter, response_json)
        if url_10Q:
            response = requests.get(url_10Q, headers=self.headers)
            return response.text
        
        return f"10-Q form for the year {year} and quarter {quarter} could not be found."
    
    '''
    Returns the url to a company's 10Q after determining the fiscal year end and the quarter date
    '''
    def find_10Q_file(self, cik, year, quarter, response_json):
        # finding the report month and year that corresponds to the quarter we're looking for
        target_month, target_year = self.find_quarter_date(year, quarter, response_json)

        # looking for the 10-Q that corresponds to the report date we're looking for
        forms = response_json['filings']['recent']['form']
        for index, desc in enumerate(forms):
            if desc == '10-Q':
                date = response_json['filings']['recent']['reportDate'][index]
                yr = int(date[:4])
                mth = int(date[5:7])
                if mth == target_month and yr == target_year:
                    accessionNumber = response_json['filings']['recent']['accessionNumber'][index]
                    accn_for_fileurl = self.adjust_accn_for_fileurl(accessionNumber)
                    primaryDocument = response_json['filings']['recent']['primaryDocument'][index]

                    file = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn_for_fileurl}/{primaryDocument}"
                    return file
                
        return None
    
    '''
    Returns the report date of a company's 10-K form given the year (determines the end of a fiscal year)
    '''
    def get_date_10K(self, year_target, response_json):
        forms = response_json['filings']['recent']['form']
        for index, desc in enumerate(forms):
            if desc == '10-K':
                date = response_json['filings']['recent']['reportDate'][index]
                year = int(date[:4])
                if year == year_target:
                    return date
    
    '''
    Finds, what should be, the report month and year of a company's 10-Q form given the year and the quarter
    '''
    def find_quarter_date(self, year, quarter, response_json):
        # find the date of the given year's 10K to know the fiscal year end to determine quarter dates
        fy_end = self.get_date_10K(year, response_json)
        fy_end_month = int(fy_end[5:7])

        # mapping the quarter we're looking for to the month that it's supposed to report on
        quarter_month = {
            1 : fy_end_month - 9,
            2 : fy_end_month - 6,
            3 : fy_end_month - 3
        }

        # adjusting for possible negative values in calculating the month
        target_month, target_year = quarter_month[quarter], year
        if target_month < 1:
            target_month += 12
            target_year -= 1

        return target_month, target_year

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
nvda_cik = return_tuple[0]
nvda_2021_10K = sec.annual_filing(nvda_cik, 2021)
print(nvda_2021_10K)
nvda_2021_10Q = sec.quarterly_filing(nvda_cik, 2021, 1)
#print(nvda_2021_10Q)