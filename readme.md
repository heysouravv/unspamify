## FastAPI Gmail OAuth2 Integration
This is a simple FastAPI app that demonstrates how to integrate Gmail OAuth2 authentication with the Google API using the google-auth and google-api-python-client libraries. It allows users to log in via Gmail, retrieve emails from their inbox, and display the message IDs.

### Prerequisites
- Python 3.x installed
- Gmail API client credentials (downloaded as secret.json)
- FastAPI and other required libraries *(fastapi, google-auth, google-auth-oauthlib, google-api-python-client, starlette, uvicorn)*

### Setting Up
Install the required libraries:

    pip install fastapi google-auth google-auth-oauthlib google-api-python-client starlette uvicorn

- Place your Gmail API client credentials (secret.json) in the same directory as the script.
- Update the redirect_uri in the /oauth2/login endpoint to match your application's callback URL.

### Endpoints
1. **/oauth2/login**
    - Redirects the user to Google's OAuth 2.0 authorization page.
    Requests access to the Gmail API with the necessary scopes (https://www.googleapis.com/auth/gmail.readonly).
    Prompts the user to grant access.
2. **/callback**
    - Receives the OAuth 2.0 callback from Google after the user grants access.
    - Fetches the access token and stores it in the session using *fastapi.middleware.sessions.SessionMiddleware*.
3. **/emails**
    - Requires OAuth2 authentication to access.
    - Retrieves the user's Gmail inbox messages using the Gmail API.
    - Returns a list of message IDs from the Gmail API response.

### Usage

Start the FastAPI app using Uvicorn:

    uvicorn main:app --reload

-   Access the app's documentation at http://127.0.0.1:8000/docs to test the endpoints using the Swagger UI.

-   Click on the /oauth2/login endpoint to initiate the Gmail OAuth2 login process.

-   Grant access to the Gmail API when prompted.

-   After successful authentication, access the /emails endpoint to retrieve the message IDs from your Gmail inbox.

### Note
-   This app uses fastapi.middleware.sessions.SessionMiddleware to store the access token in the session. It is recommended to use a more secure and persistent session storage mechanism in production.
-   The app fetches a maximum of 100 emails from the Gmail API. You can modify the maxResults parameter in the service.users().messages().list call to retrieve more or fewer emails as needed.
-   Remember to replace your_secret_key with a strong secret key for session management.
-   Ensure you handle errors and edge cases appropriately for production usage.

**Disclaimer**: This app is for educational purposes and may not be production-ready. Always follow security best practices when integrating with third-party APIs and handling user data.




