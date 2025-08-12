from cik_module.cik_module import SecEdgar
import json

def get_filing(request_type, ticker, year, quarter = None):
    sec = SecEdgar('alfonso-rada-bucket', 'company_tickers.json')
    cik = sec.ticker_to_cik(ticker)[0]
    
    # process annual request
    if request_type == 'Annual':
        return sec.annual_filing(cik, year)
    # process quarterly request
    elif request_type == 'Quarter' and quarter:
        return sec.quarterly_filing(cik, year, quarter)
    else:
        return "Invalid request."

def lambda_handler(event, context):
    try:
        quarter = event['quarter']
        document = get_filing(event['request_type'], event['ticker'], event['year'], quarter)
        return {
            'statusCode': 200,
            'body': json.dumps(document)
        }
    except Exception as e:
        print(f"Error occurred: {e}")

# test_lambda_2 = {
#     "request_type": "Quarter",
#     "ticker": "NVDA",
#     "year": 2025,
#     "quarter": 1
# }

# print(json.loads(lambda_handler(test_lambda_2, '')['body']))