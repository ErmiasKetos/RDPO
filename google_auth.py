import streamlit as st
import os
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText

SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/userinfo.email", "openid"]
TOKEN_PATH = "token.pickle"

def authenticate_user():
    """Authenticate user via Google OAuth and return their email."""
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
            flow = Flow.from_client_secrets_file("client_secret.json", SCOPES)
            flow.redirect_uri = "https://ntsmv7uynenkazkeftozjx.streamlit.app/_stcore/authorize"

            auth_url, _ = flow.authorization_url(prompt="consent")
            st.markdown(f"[Click here to log in with Google]({auth_url})")
            return None  # Stop execution until user logs in

    # Fetch user email after authentication
    user_info_service = build("oauth2", "v2", credentials=creds)
    user_info = user_info_service.userinfo().get().execute()

    return user_info.get("email")

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        return None

    return build("gmail", "v1", credentials=creds)

def send_email(sender_email, subject, email_body):
    """Send an email notification using the logged-in user's Gmail account."""
    try:
        gmail_service = get_gmail_service()
        if not gmail_service:
            st.warning("Please log in with Google to send emails.")
            return False

        recipient_email = "ermias@ketos.co"  # PO approver email

        message = MIMEText(email_body, 'html')
        message['to'] = recipient_email
        message['from'] = sender_email
        message['subject'] = subject

        raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        gmail_service.users().messages().send(userId="me", body=raw_message).execute()
        
        st.success("✅ Email successfully sent to the PO approver!")
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False
