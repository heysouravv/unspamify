import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def lambda_handler(event, context):
    # Get refresh token from the event
    refresh_token = event['refresh_token']
    if not refresh_token:
        return {
            'statusCode': 400,
            'body': json.dumps('Refresh token not provided.')
        }

    # Step 1: Use the refresh token to get a new access token
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id='922083715728-rtoi9jjjv9fjtefttd14t0p9us415f84.apps.googleusercontent.com',    # replace with your client_id
        client_secret='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'     # replace with your client_secret
    )

    # Refresh the credentials
    creds.refresh(Request())

    # Step 2: Use the access token to check for emails using Gmail API
    service = build('gmail', 'v1', credentials=creds)
    domains= ['unspamify.com']
    query = ' OR '.join([f'from:{domain}' for domain in domains])
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query,maxResults=10).execute()  # Fetching top 10 emails for demonstration
    messages = results.get('messages', [])
    print(messages)

    return {
        'statusCode': 200,
        'body': json.dumps(messages)  # Return the emails
    }