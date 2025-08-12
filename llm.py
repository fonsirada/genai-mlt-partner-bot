from lambda_2 import get_filing
import boto3
import json

client = boto3.client("bedrock-runtime", "us-east-2")

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

question = "When did the 1st quarterly period for Nvidia's 2026 fiscal year end?"
context = get_filing("Quarter", "NVDA", 2026, 1)
prompt = f"Using the information below. {question}\n\n{context}"

# if you ask about Nvidia's 2026 10-Q Q1, without context, it won't know exactly when it ended
# print(ask(question))
# if you ask the same question, with context (the 10-Q), it knows exactly when it ended
# print(ask(prompt))