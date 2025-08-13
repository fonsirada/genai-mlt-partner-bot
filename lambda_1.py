# Author: Alfonso Rada
# Date: 08/12/2025
# File Name: lambda_1.py
# Description:  Uploads the SEC's JSON on company ticker information to an S3 bucket daily
# for use by CIK lookup module.

import boto3
import requests

def lambda_handler(event, context):
    try:
        s3 = boto3.client('s3')
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {'user-agent': 'MLT arada@hamilton.edu'}

        response = requests.get(url, headers=headers)

        s3.put_object(Bucket='alfonso-rada-bucket', Key='company_tickers.json', Body=response.content)
        return "Upload complete!"
    except Exception as e:
        print(f"Error occurred: {e}")