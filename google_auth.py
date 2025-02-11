import streamlit as st
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

    if st.secrets.get("google_oauth_client"):
        client_config = {
            "web": {
                "client_id": st.secrets["google_oauth_client"]["client_id"],
                "client_secret": st.secrets["google_oauth_client"]["client_secret"],
                "redirect_uris": [st.secrets["google_oauth_client"]["redirect_uri"]],
                "auth_uri": st.secrets["google_oauth_client"]["auth_uri"],
                "token_uri": st.secrets["google_oauth_client"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["google_oauth_client"]["auth_provider_x509_cert_url"]
            }
        }

        flow = Flow.from_client_config(client_config, SCOPES)
        flow.redirect_uri = st.secrets["google_oauth_client"]["redirect_uri"]

        auth_url, _ = flow.authorization_url(prompt="consent")
        st.markdown(f"[Click here to log in with Google]({auth_url})")
        return None  # Stop execution until user logs in

    else:
        st.error("Google OAuth credentials are missing. Please update your Streamlit secrets.")
        return None

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    if st.secrets.get("google_oauth_client"):
        if TOKEN_PATH and pickle.load(open(TOKEN_PATH, "rb")):
            creds = pickle.load(open(TOKEN_PATH, "rb"))

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
