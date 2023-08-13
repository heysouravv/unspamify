from google.auth.transport import requests as google_auth_requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleService:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self):
        self.flow = InstalledAppFlow.from_client_secrets_file('secret.json', scopes=self.SCOPES)

    def get_auth_url(self, redirect_uri):
        self.flow.redirect_uri = redirect_uri
        self.flow.include_granted_scopes = 'true'
        self.flow.prompt = 'consent'
        authorization_url, _ = self.flow.authorization_url(access_type='offline')
        return authorization_url

    def fetch_token(self, code):
        return self.flow.fetch_token(code=code)

    def get_gmail_service(self, credentials):
        return build('gmail', 'v1', credentials=credentials)
