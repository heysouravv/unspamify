from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, BackgroundTasks
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.oauth2.credentials import Credentials
from services.google_service import GoogleService
from services.microsoft_service import MicrosoftService
from utils import get_user_credentials_from_session

CLIENT_ID = '5df87552-f119-4d3a-ac0f-e70bcb829e7d'
CLIENT_SECRET = '878e1418-0301-4875-8ec0-b497347835ab'

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

templates = Jinja2Templates(directory="templates")

# Instantiate service classes
google_service = GoogleService()
microsoft_service = MicrosoftService(CLIENT_ID, CLIENT_SECRET)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/oauth2/login")
async def login():
    authorization_url = google_service.get_auth_url('http://localhost:8000/callback')
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": authorization_url})

@app.get("/callback", response_class=HTMLResponse)
async def callback(code: str, request: Request):
    google_service.fetch_token(code)
    access_token = google_service.flow.credentials.token
    session = request.session
    session["access_token"] = access_token
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/thank-you"})

@app.get("/microsoft-login")
async def microsoft_login(request: Request):
    login_url = microsoft_service.get_auth_url(str(request.base_url) + "microsoft-callback/")
    return Response(content="", status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": login_url})

@app.get("/microsoft-callback")
async def microsoft_callback(code: str, request: Request):
    token_data = microsoft_service.fetch_token(code, redirect_uri=str(request.base_url) + "microsoft-callback/")
    if 'access_token' in token_data:
        graph_data = microsoft_service.get_user_data(token_data['access_token'])
        email = graph_data.get('userPrincipalName') or graph_data.get('mail')
        if email:
            return {"message": "Logged in successfully", "email": email}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found in Microsoft user data.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token received from Microsoft.")

@app.get("/thank-you")
async def thank_you(request: Request):
    return templates.TemplateResponse("thank-you.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    access_token = get_user_credentials_from_session(request)
    credentials = google_service.get_credentials(access_token)
    await get_emails(credentials)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/emails", tags=["Emails"])
async def get_emails(credentials: Credentials = Depends(get_user_credentials_from_session)):
    try:
        # Create a Gmail API service using the authenticated credentials
        service = google_service.get_gmail_service(credentials)
        
        # List of domains to watch for
        domains = ['tryapollo.io', 'apollo.io']

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
