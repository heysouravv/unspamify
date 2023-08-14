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
import msal
import requests

CLIENT_ID = '5df87552-f119-4d3a-ac0f-e70bcb829e7d'
CLIENT_SECRET = '878e1418-0301-4875-8ec0-b497347835ab'
AUTHORITY = 'https://login.microsoftonline.com/common'
SCOPE = ['User.Read'] 
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
    

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session = request.session
    if 'access_token' in session:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        return templates.TemplateResponse("login.html", {"request": request})
    
@app.get("/logout")
async def logout(request: Request):
    request.session.pop("access_token", None)
    return {"message": "Logged out"}

@app.get("/oauth2/login")
async def login():
    # Redirect the user to Google's OAuth 2.0 authorization page
    flow.redirect_uri = 'https://app.unspamify.com/callback'
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
    session["refresh_token"] = refresh_token
    print("Refresh Token", refresh_token)
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/thank-you"})

@app.get("/login-with-microsoft/")
async def login_with_microsoft(request: Request):
    # Create a PublicClientApplication instance
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

    # Get the sign-in URL
    login_url = app.get_authorization_request_url(SCOPE, redirect_uri=request.url_for('microsoft_callback'))

    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": login_url})


def get_microsoft_user_data(access_token: str):
    # Fetch user info using the access token (Microsoft Graph API)
    graph_endpoint = 'https://graph.microsoft.com/v1.0/me'
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(graph_endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error fetching Microsoft user data.")


@app.get("/microsoft-callback/")
async def microsoft_callback(request: Request):
    code = request.query_params.get('code')
    if code:
        # Create a PublicClientApplication instance
        app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

        # Acquire a token using the authorization code
        result = app.acquire_token_by_authorization_code(code, SCOPE, redirect_uri=request.url_for('microsoft_callback'), client_secret=CLIENT_SECRET)

        if 'access_token' in result:
            # Successfully authenticated with Microsoft
            graph_data = get_microsoft_user_data(result['access_token'])
            email = graph_data.get('userPrincipalName') or graph_data.get('mail')
            if email:
                # ... [authentication logic here]
                return {"message": "Logged in successfully", "email": email}
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found in Microsoft user data.")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token received from Microsoft.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No code received from Microsoft.")


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



# ACCESS_key = AKIAZE666E7SG2JMSPSF
# ACCESS_Password = ZpvstVtRorOx9KiBTPj9G1yzyrvTUrUMIGkNEwgm


# Add other endpoints as needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
