import requests

class SecEdgar:
    def __init__(self, fileurl):
        self.fileurl = fileurl

        headers = {'user-agent': 'MLT arada@hamilton.edu'}
        r = requests.get(self.fileurl, headers=headers)
        self.filejson = r.json()

        self.cik_json_to_dict()

    def cik_json_to_dict(self):
        self.name_dict = {}
        self.ticker_dict = {}

        for value in self.filejson.values():
            cik = value["cik_str"]
            name = value["title"]
            ticker = value["ticker"]
            self.name_dict[name] = cik
            self.ticker_dict[ticker] = cik

    def name_to_cik(self, name):
        try:
            cik = self.name_dict[name]
            return (f"Name: {name}, CIK: {cik}")
        except KeyError:
            print(f"Name: {name}, does not exist.")
    
    def ticker_to_cik(self, ticker):
        try:
            cik = self.ticker_dict[ticker]
            return (f"Ticker: {ticker}, CIK: {cik}")
        except KeyError:
            print(f"Ticker: {ticker}, does not exist.")

sec = SecEdgar("https://www.sec.gov/files/company_tickers.json")
print(sec.ticker_to_cik("NVDA"))