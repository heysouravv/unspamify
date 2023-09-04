import os
import json
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import msal
import boto3
from boto3.dynamodb.conditions import Key
import requests
from cryptography.fernet import Fernet
import base64
from dynomodb import init_user
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

CLIENT_ID = '5df87552-f119-4d3a-ac0f-e70bcb829e7d'
CLIENT_SECRET = '878e1418-0301-4875-8ec0-b497347835ab'
AUTHORITY = 'https://login.microsoftonline.com/common'
SCOPE = ['User.Read'] 
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
load_dotenv()
key = os.getenv('SECRET_KEY_FOR_APP')
app.add_middleware(SessionMiddleware, secret_key=key)
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/userinfo.profile']
session = boto3.Session(
            aws_access_key_id=os.getenv('ACCESS_KEY'),
            aws_secret_access_key=os.getenv('ACCESS_KEY_PRIVATE'),
            region_name=os.getenv('REGION')
        )
dynamodb = session.resource('dynamodb')
table = dynamodb.Table('UserScans')

def get_scans_for_user(user_email):
    response = table.query(
        KeyConditionExpression=Key('user_email').eq(user_email),
        ScanIndexForward=False  # This ensures descending order by sort key
    )
    return response['Items']

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
    if 'user_registered' in session:
        session = request.session
        decrypted_data = json.loads(session["user_data"])
        user_email = decrypted_data['user_email']
        display_name = decrypted_data['display_name']
        profile_picture_url = decrypted_data['profile_picture_url']
        data = get_scans_for_user(user_email )
        return templates.TemplateResponse("dashboard.html",  {"request": request, "email":user_email, "display_name": display_name, "profile_picture_url": profile_picture_url , "scans": data})
    else:
        return templates.TemplateResponse("login.html", {"request": request})
    
@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user_registered", None)
    request.session.pop("access_token", None)
    request.session.pop("user_email", None)
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/"})

@app.get("/oauth2/login")
async def login():
    # Redirect the user to Google's OAuth 2.0 authorization page
    flow.redirect_uri = 'http://localhost:8000/callback'
    flow.include_granted_scopes = 'true'
    flow.prompt = 'consent'
    authorization_url, state = flow.authorization_url(access_type='offline')
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": authorization_url})

@app.get("/callback",response_class=HTMLResponse)
async def callback(code: str, background_tasks: BackgroundTasks, request: Request,response: Response):
    response.set_cookie(key='user_registered', value='true', httponly=True)
    # Handle the OAuth 2.0 callback from Google
    flow.fetch_token(code=code)
    # Store only the access token in the session
    cipher_suite = Fernet(key)
    refresh_token = flow.credentials.refresh_token
    access_token = flow.credentials.token
    session = request.session
    session["user_registered"] = True
    session["access_token"] = access_token
    service = build('gmail', 'v1', credentials=Credentials(token=access_token))
    profile = service.users().getProfile(userId='me').execute()
    user_email = profile['emailAddress']
    service_for_details = build('people', 'v1', credentials=Credentials(token=access_token))
    results = service_for_details.people().get(resourceName='people/me', personFields='names,photos').execute()
    if 'names' in results and len(results['names']) > 0:
        display_name = results['names'][0]['displayName']
    else:
        display_name = user_email
    profile_picture_url = None
    if 'photos' in results and len(results['photos']) > 0:
        profile_picture_url = results['photos'][0].get('url')
    data_to_encrypt = {'user_email': user_email, 'display_name': display_name, 'profile_picture_url': profile_picture_url}
    session["user_data"] = json.dumps(data_to_encrypt)
    if refresh_token is not None:
        init_user(user_email=user_email, mailbox='gmail',refresh_token=refresh_token)
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/dashboard"})

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


@app.get("/dashboard")
async def dashboard(request: Request,credentials: Credentials = Depends(get_user_credentials)):
    session = request.session
    decrypted_data = json.loads(session["user_data"])
    user_email = decrypted_data['user_email']
    display_name = decrypted_data['display_name']
    profile_picture_url = decrypted_data['profile_picture_url']
    data = get_scans_for_user(user_email )
    return templates.TemplateResponse("dashboard.html",  {"request": request, "email":user_email, "display_name": display_name, "profile_picture_url": profile_picture_url , "scans": data})


# Add other endpoints as needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run('__main__:app', port=8000, reload=True, workers=2)
