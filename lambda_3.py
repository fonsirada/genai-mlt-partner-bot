# Author: Alfonso Rada
# Date: 08/12/2025
# File Name: lambda_3.py
# Description: Using Claude Sonnet 4, answers user-inputted questions using 
# a filing (10-K or 10-Q) of the user's choice as context.

from lambda_2 import get_filing
import boto3
import json

client = boto3.client("bedrock-runtime", "us-east-2")

'''
Asks Claude the user-inputted prompt, returns a response in text format.
'''
def ask(prompt):
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    response = client.invoke_model(
        modelId="us.anthropic.claude-sonnet-4-20250514-v1:0",
        body=json.dumps(body)
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

'''
Returns the latest filing for a company given their ticker symbol.
'''
def get_latest_filing(ticker):
    # As of today, latest filings can either be 2026 10-Q Q2/Q1, 2025 10-K, or 2025 10-Q Q3/Q2
    search_order = [
        ("Quarter", 2026, 2),
        ("Quarter", 2026, 1),
        ("Annual", 2025, None),
        ("Quarter", 2025, 3),
        ("Quarter", 2025, 2)
    ]
    
    for doc_type, year, quarter in search_order:
        filing = get_filing(doc_type, ticker, year, quarter)
        if filing:
            return filing

'''
Creates prompt for Claude with the user question and the user's chosen
company's latest filing.
'''
def create_prompt(question, ticker):
    context = get_latest_filing(ticker)
    return f"Using the information below. {question}\n\n{context}"

def lambda_handler(event, context):
    try:
        prompt = create_prompt(event['question'], event['ticker'])
        response = ask(prompt)
        return {
            'statusCode': 200,
            'response': response
        }
    except Exception as e:
        print(f"Error occurred: {e}")

## testing
test_lambda_3 = {
    "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
    "ticker": "AMZN",
    "year": "2024",
}

print(lambda_handler(test_lambda_3, '')['response'])