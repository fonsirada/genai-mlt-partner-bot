from cik_module.cik_module import SecEdgar
import json

def lambda_handler(event, context):
    request_type = event['request_type']
    company = event['company']
    year = event['year']

    sec = SecEdgar('alfonso-rada-bucket', 'company_tickers.json')
    cik = sec.ticker_to_cik(company)[0]
    
    if request_type == 'Annual':
        # process annual request
        document = sec.annual_filing(cik, year)
    elif request_type == 'Quarter':
        quarter = event['quarter']
        # process quarterly request
        document = sec.quarterly_filing(cik, year, quarter)
    else:
        return "Invalid request."
    
    return {
        'statusCode': 200,
        'body': json.dumps(document)
    }

test_lambda_2 = {
    "request_type": "Quarter",
    "company": "NVDA",
    "year": 2021,
    "quarter": 1
}

print(lambda_handler(test_lambda_2, ''))