import msal
import requests

class MicrosoftService:
    AUTHORITY = 'https://login.microsoftonline.com/common'
    SCOPE = ['User.Read']

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.app = msal.PublicClientApplication(client_id, authority=self.AUTHORITY)

    def get_auth_url(self, redirect_uri):
        return self.app.get_authorization_request_url(self.SCOPE, redirect_uri=redirect_uri)

    def fetch_token(self, code, redirect_uri):
        return self.app.acquire_token_by_authorization_code(code, self.SCOPE, redirect_uri=redirect_uri, client_secret=self.client_secret)

    @staticmethod
    def get_user_data(access_token):
        graph_endpoint = 'https://graph.microsoft.com/v1.0/me'
        headers = {'Authorization': 'Bearer ' + access_token}
        response = requests.get(graph_endpoint, headers=headers)
        return response.json() if response.status_code == 200 else None
