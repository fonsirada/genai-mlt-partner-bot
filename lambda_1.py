import boto3
import requests

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {'user-agent': 'MLT arada@hamilton.edu'}

    response = requests.get(url, headers=headers)

    s3.put_object(Bucket='alfonso-rada-bucket', Key='company_tickers.json', Body=response.content)
    return "Upload complete!"

print(lambda_handler({},''))