import os
import json
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
from google.auth.transport import requests as google_auth_requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token")

# Replace with your Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Load the OAuth 2.0 client configuration from the credentials file
flow = InstalledAppFlow.from_client_secrets_file('secret.json', scopes=SCOPES)

def get_user_credentials(request: Request):
    try:
        session = request.session
        access_token = session["access_token"]
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Create a new Credentials object using the access token
        credentials = Credentials(token=access_token)
        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/oauth2/login")
async def login():
    # Redirect the user to Google's OAuth 2.0 authorization page
    flow.redirect_uri = 'https://unspamify.x265.team/callback'
    flow.include_granted_scopes = 'true'
    flow.prompt = 'consent'
    authorization_url, state = flow.authorization_url(access_type='offline')
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": authorization_url})

@app.get("/callback")
async def callback(code: str, background_tasks: BackgroundTasks, request: Request):
    # Handle the OAuth 2.0 callback from Google
    flow.fetch_token(code=code)
    # Store only the access token in the session
    access_token = flow.credentials.token
    session = request.session
    session["access_token"] = access_token
    print(access_token)
    return {"message": "Authentication successful!"}

@app.get("/emails", tags=["Emails"])
async def get_emails(credentials: Credentials = Depends(get_user_credentials)):
    try:
        # Create a Gmail API service using the authenticated credentials
        service = build('gmail', 'v1', credentials=credentials)

        # Fetch 100 emails using the Gmail API
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='', maxResults=100).execute()
        messages = results.get('messages', [])

        if not messages:
            return {"message": "No emails found."}

        # Get the message IDs from the list of messages
        message_ids = [message['id'] for message in messages]

        return {"message_ids": message_ids}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Add other endpoints as needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
