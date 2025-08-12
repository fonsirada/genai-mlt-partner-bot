# Author: Alfonso Rada
# Date: 08/04/2025
# File Name: cik_module.py
# Description:  A module that can be used to lookup the CIK number of companys registered with the SEC, 
# and grab its 10K and/or 10Q forms by year and/or quarter

from bs4 import BeautifulSoup
import requests
import boto3
import json

'''
    Given a URL to an SEC public JSON file, extract its information and use it to
    lookup a company's CIK number by name or by ticker symbol.
'''
class SecEdgar:
    '''
    Grabbing the JSON from the SEC URL and filling dictionaries for lookup
    '''
    def __init__(self, bucket_name, key_name):
        self.headers = {'user-agent': 'MLT arada@hamilton.edu'}

        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name
        self.key_name = key_name

        obj =  self.s3.get_object(Bucket = self.bucket_name, Key = self.key_name)
        data = obj['Body'].read()

        self.filejson = json.loads(data)

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
        if year > 2025:
            return "Invalid year input."

        # retreiving a company's submission data from submissions API
        cik_for_submissions = self.adjust_cik_for_submissions(cik)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_for_submissions}.json"
        response = requests.get(submissions_url, headers=self.headers)
        response_json = response.json()

        url_10K = self.find_10K_file(cik, year, response_json)
        if url_10K:
            response = requests.get(url_10K, headers=self.headers)
            text = self.extract_text_from_html(response.text)
            return text

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
        # invalid year/quarter input
        if year > 2026 or quarter < 1 or quarter > 3:
            return "Invalid year or quarter input."

        # retreiving a company's submission data from submissions API
        cik_for_submissions = self.adjust_cik_for_submissions(cik)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_for_submissions}.json"
        response = requests.get(submissions_url, headers=self.headers)
        response_json = response.json()

        url_10Q = self.find_10Q_file(cik, year, quarter, response_json)
        if url_10Q:
            response = requests.get(url_10Q, headers=self.headers)
            text = self.extract_text_from_html(response.text)
            return text
        
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
    Returns the report date of a company's 10-K form given the year (determines the end of a fiscal year).
    For determining a company's 10-Q report date.
    '''
    def get_date_10K(self, year_target, response_json):
        # treat a 2026 10K like 2025 since it hasn't come out yet, and use for determining 2026 10Q report date
        if year_target == 2026:
            year_target = 2025

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

        target_month, target_year = self.determine_month(fy_end_month, quarter, year)

        return target_month, target_year
    
    '''
    Using the report month of a company's 10-K, works backwards to find, what should be, the report month of a company's 
    10-Q form
    '''
    def determine_month(self, fy_end_month, quarter, year):
        # handling determining the month for a 10-Q in a future calendar year
        if year == 2026:
            return self.handle_future_cal_year(fy_end_month, quarter, year)

        target_year = year
        # determining report month relative to that year's 10-K
        quarter_month = {
            1 : fy_end_month - 9,
            2 : fy_end_month - 6,
            3 : fy_end_month - 3
        }

        target_month = quarter_month[quarter]
        # adjusting for possible negative values in calculating the month
        if target_month < 1:
            target_month += 12
            target_year -= 1

        return target_month, target_year
    
    '''
    If looking for a 10-Q in a calendar that hasn't happened yet, the 10-K for that year will not exist
    (and likely the 10-Q unless it's well into the previous calendar year), so use the current year's 10-K
    and work forwards rather than backwards to find the report month. Should only work for the upcoming year.
    '''
    def handle_future_cal_year(self, fy_end_month, quarter, year):
        target_year = year - 1
        
        # handling 10-Qs in calendar years that haven't happened yet (since 10-K hasn't come out yet)
        quarter_month_future = {
            1 : fy_end_month + 3,
            2 : fy_end_month + 6,
            3 : fy_end_month + 9
        }

        target_month = quarter_month_future[quarter]
        # adjusting for months > 12 in calculating the month this shouldn't happen until the
        # calendar year happens, and at that point you can adjust this handling to the upcoming year
        if target_month > 12:
            target_month -= 12
            target_year += 1

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
    
    '''
    Cleans up the raw html from a file, leaving just the actual text from the document
    '''
    def extract_text_from_html(self, raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        text = soup.get_text(separator='\n')

        # Remove trailing whitespace but keep everything else, including empty lines
        lines = [line.strip() for line in text.split('\n')]

        clean_text = '\n'.join(lines)
        return clean_text

# sec = SecEdgar("alfonso-rada-bucket", "company_tickers.json")
# return_tuple = sec.ticker_to_cik('NVDA')
# nvda_cik = return_tuple[0]
# nvda_2025_10K = sec.annual_filing(nvda_cik, 2025)
# print(nvda_2025_10K)
# nvda_2026_10Q = sec.quarterly_filing(nvda_cik, 2026, 1)
# print(nvda_2026_10Q)