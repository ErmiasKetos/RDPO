import streamlit as st
import os
import json
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = "token.pickle"

def get_gmail_service():
    """Authenticate using OAuth 2.0 and return Gmail API service."""
    creds = None

    # Load credentials from token.pickle if available
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # If credentials are invalid, request new authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use Streamlit Secrets to store OAuth credentials
            client_config = {
                "web": {
                    "client_id": st.secrets["google_oauth_client"]["client_id"],
                    "client_secret": st.secrets["google_oauth_client"]["client_secret"],
                    "redirect_uris": [st.secrets["google_oauth_client"]["redirect_uri"]],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }

            flow = Flow.from_client_config(client_config, SCOPES)
            flow.redirect_uri = st.secrets["google_oauth_client"]["redirect_uri"]

            auth_url, _ = flow.authorization_url(prompt="consent")
            st.markdown(f"[Click here to log in with Google]({auth_url})")
            return None  # Stop execution until user logs in

    return build("gmail", "v1", credentials=creds)
