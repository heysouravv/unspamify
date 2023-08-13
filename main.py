import os
import json
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
from google.auth.transport import requests as google_auth_requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
templates = Jinja2Templates(directory="templates")

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
    
async def get_emails(credentials):
    try:
        # Create a Gmail API service using the authenticated credentials
        service = build('gmail', 'v1', credentials=credentials)
        # List of domains to watch for
        domains = ['tryapollo.io',
                    'apollo.io',
                    'apollo.design',
                    'tryapollo.io',
                    'useapollo.io',
                    'meetapollo.io',
                    'apollo-privacy.com',
                    'zoominfo.com',
                    'Zoominfo.org',
                    'Zoominformation.com',
                    'Zoominfotechnologies.com',
                    'Zoomprivacy.com',
                    'hunter.io',
                    'emailhunter.co',
                    'email-hunter.com',
                    'gethunter.io',
                    'm.onetrust.com',
                    'lusha.co',
                    'lusha.us',
                    'signalhire.com',
                    'Signalhire.net',
                    'clay.run',
                    'clay.com',
                    'clay.run',
                    'clay.company',
                    'accessclay.com',
                    'clayoutreach.com',
                    'claysheets.com',
                    'buildclay.com',
                    'clayaccess.com',
                    'runclay.com',
                    'uplead.com',
                    'upleadapp.com',
                    'Leadsgorilla.io',
                    'Leadsgorilla.com',
                    'leadsgorillareview.com',
                    'leadsgorilla.pk',
                    'leadsgorillabonus.com',
                    'leadsgorillabundle.com',
                    'skrapp.io',
                    'Findemails.com',
                    'anymailfinder.com',
                    'getprospect.com',
                    'getprospect.io',
                    'getprospect.org',
                    'getprospect.co',
                    'rocketreach.co',
                    'rocketsreach.com',
                    'rocketreach-privacy.com',
                    'rocketreach.com',
                    'voilanorbert.com',
                    'Vnbravos.com',
                    'leadgibbon.com',
                    'findymail.com',
                    'Bettercontact.rocks',
                    'FindThatLead.com',
                    'findthatlead.org',
                    'findthatlead.eu',
                    'Findthatlead.co',
                    'Findthatlead.us',
                    'datagma.com',
                    'Datarosa.com',
                    'snov.io',
                    'Getsnov.com',
                    'Snovio.com',
                    'cognism.com',
                    'cognism.ai',
                    'cognism-privacy.com',
                    'cognism.io',
                    '6sense.com',
                    'contactout.com',
                    'contactout.io',
                    'trycontactout.com',
                    'contactout.net',
                    'leadiq.com',
                    'leadiq-gdpr.com',
                    'leadiq-notices.com',
                    'leadiq-updates.com',
                    'leadiq-legal.com',
                    'leadiqapp.com',
                    'getleadiq.com',
                    'leadiq.io',
                    'leadiq-notifications.com',
                    'leadiq-privacy.com',
                    'KleanLeads.com',
                    'Persistiq.com',
                    'Dropcontact.com',
                    'Boardroominsiders.com',
                    'Getluna.dev',
                    'interseller.io',
                    'thecompaniesapi.com',
                    'clearbit.com',
                    'clearbitprivacy.com',
                    'clearbitforprivacy.com',
                    'tryclearbit.co',
                    'tryclearbit.com',
                    'Seamless.ai',
                    'fullcontact.com',
                    'Mattermark.com',
                    'peopledatalabs.com',
                    'Anyleads.com',
                    'anylead.com',
                    'anyleads.in',
                    'Leadfuze.com',
                    'Societeinfo.co',
                    'Getemail.io',
                    'Nomination.fr',
                    'Aeroleads.com',
                    'unspamify.com']

        # Create a query string to filter emails by sender
        query = ' OR '.join([f'from:{domain}' for domain in domains])

        # Fetch 100 emails using the Gmail API
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query, maxResults=100).execute()
        messages = results.get('messages', [])
        totalEmails = service.users().profiles().list(userId='me').execute()
        print(totalEmails)

        total_filtered = len(messages)

        if not messages:
            return {"message": "No emails found."}

        # Get the message IDs from the list of messages
        message_ids = [message['id'] for message in messages]

        return {"messages_filtered": total_filtered,}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/oauth2/login")
async def login():
    # Redirect the user to Google's OAuth 2.0 authorization page
    flow.redirect_uri = 'http://localhost:8000/callback'
    flow.include_granted_scopes = 'true'
    flow.prompt = 'consent'
    authorization_url, state = flow.authorization_url(access_type='offline')
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": authorization_url})

@app.get("/callback",response_class=HTMLResponse)
async def callback(code: str, background_tasks: BackgroundTasks, request: Request):
    # Handle the OAuth 2.0 callback from Google
    flow.fetch_token(code=code)
    # Store only the access token in the session
    refresh_token = flow.credentials.refresh_token
    access_token = flow.credentials.token
    session = request.session
    session["access_token"] = access_token
    session['refresh_token'] = refresh_token
    print("Refresh Token", refresh_token)
    print(access_token)
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/thank-you"})


@app.get("/thank-you")
async def thank_you(request: Request):
    return templates.TemplateResponse("thank-you.html", {"request": request})



@app.get("/dashboard")
async def dashboard(request: Request,credentials: Credentials = Depends(get_user_credentials)):
    await get_emails(credentials)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/emails", tags=["Emails"])
async def get_emails(credentials: Credentials = Depends(get_user_credentials)):
    try:
        # Create a Gmail API service using the authenticated credentials
        service = build('gmail', 'v1', credentials=credentials)
        # List of domains to watch for
        domains = ['tryapollo.io',
                    'apollo.io',
                    'apollo.design',
                    'tryapollo.io',
                    'useapollo.io',
                    'meetapollo.io',
                    'apollo-privacy.com',
                    'zoominfo.com',
                    'Zoominfo.org',
                    'Zoominformation.com',
                    'Zoominfotechnologies.com',
                    'Zoomprivacy.com',
                    'hunter.io',
                    'emailhunter.co',
                    'email-hunter.com',
                    'gethunter.io',
                    'm.onetrust.com',
                    'lusha.co',
                    'lusha.us',
                    'signalhire.com',
                    'Signalhire.net',
                    'clay.run',
                    'clay.com',
                    'clay.run',
                    'clay.company',
                    'accessclay.com',
                    'clayoutreach.com',
                    'claysheets.com',
                    'buildclay.com',
                    'clayaccess.com',
                    'runclay.com',
                    'uplead.com',
                    'upleadapp.com',
                    'Leadsgorilla.io',
                    'Leadsgorilla.com',
                    'leadsgorillareview.com',
                    'leadsgorilla.pk',
                    'leadsgorillabonus.com',
                    'leadsgorillabundle.com',
                    'skrapp.io',
                    'Findemails.com',
                    'anymailfinder.com',
                    'getprospect.com',
                    'getprospect.io',
                    'getprospect.org',
                    'getprospect.co',
                    'rocketreach.co',
                    'rocketsreach.com',
                    'rocketreach-privacy.com',
                    'rocketreach.com',
                    'voilanorbert.com',
                    'Vnbravos.com',
                    'leadgibbon.com',
                    'findymail.com',
                    'Bettercontact.rocks',
                    'FindThatLead.com',
                    'findthatlead.org',
                    'findthatlead.eu',
                    'Findthatlead.co',
                    'Findthatlead.us',
                    'datagma.com',
                    'Datarosa.com',
                    'snov.io',
                    'Getsnov.com',
                    'Snovio.com',
                    'cognism.com',
                    'cognism.ai',
                    'cognism-privacy.com',
                    'cognism.io',
                    '6sense.com',
                    'contactout.com',
                    'contactout.io',
                    'trycontactout.com',
                    'contactout.net',
                    'leadiq.com',
                    'leadiq-gdpr.com',
                    'leadiq-notices.com',
                    'leadiq-updates.com',
                    'leadiq-legal.com',
                    'leadiqapp.com',
                    'getleadiq.com',
                    'leadiq.io',
                    'leadiq-notifications.com',
                    'leadiq-privacy.com',
                    'KleanLeads.com',
                    'Persistiq.com',
                    'Dropcontact.com',
                    'Boardroominsiders.com',
                    'Getluna.dev',
                    'interseller.io',
                    'thecompaniesapi.com',
                    'clearbit.com',
                    'clearbitprivacy.com',
                    'clearbitforprivacy.com',
                    'tryclearbit.co',
                    'tryclearbit.com',
                    'Seamless.ai',
                    'fullcontact.com',
                    'Mattermark.com',
                    'peopledatalabs.com',
                    'Anyleads.com',
                    'anylead.com',
                    'anyleads.in',
                    'Leadfuze.com',
                    'Societeinfo.co',
                    'Getemail.io',
                    'Nomination.fr',
                    'Aeroleads.com',
                    'unspamify.com']

        # Create a query string to filter emails by sender
        query = ' OR '.join([f'from:{domain}' for domain in domains])

        # Fetch 100 emails using the Gmail API
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query, maxResults=100).execute()
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
