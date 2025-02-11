import streamlit as st
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]

def get_google_login_url():
    """Generate Google OAuth login URL."""
    client_config = json.loads(st.secrets["google_oauth_client"])
    flow = Flow.from_client_config(client_config, SCOPES)
    flow.redirect_uri = client_config['web']['redirect_uris'][0]
    
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url

def authenticate_user():
    """Authenticate user via Google OAuth."""
    if "google_user" in st.session_state:
        return True  # User is already authenticated

    # Check for authorization code
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        client_config = json.loads(st.secrets["google_oauth_client"])
        flow = Flow.from_client_config(client_config, SCOPES)
        flow.redirect_uri = client_config['web']['redirect_uris'][0]
        flow.fetch_token(code=query_params["code"][0])

        creds = flow.credentials
        user_info = Credentials.from_authorized_user_info(creds).id_token

        email = user_info.get("email")
        if email.endswith("@ketos.co"):  # Restrict access to company emails
            st.session_state["google_user"] = user_info
            return True
        else:
            st.error("Access denied: Only @ketos.co emails are allowed.")
            return False
    return False
