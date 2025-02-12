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

    # Check if OAuth credentials exist in session state
    if "google_auth_creds" in st.session_state:
        creds = pickle.loads(st.session_state["google_auth_creds"])

    # If token is expired or missing, request authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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

                # Display the correct login link
                st.markdown(f"[Click here to log in with Google]({auth_url})")

                # Stop execution until user logs in
                st.stop()

                # Handle the callback and fetch user credentials
                query_params = st.query_params
                if "code" in query_params:
                    flow.fetch_token(code=query_params["code"][0])
                    creds = flow.credentials

                    # Store credentials in session state
                    st.session_state["google_auth_creds"] = pickle.dumps(creds)
                    st.rerun()

    # Fetch user email after authentication
    user_info_service = build("oauth2", "v2", credentials=creds)
    user_info = user_info_service.userinfo().get().execute()

    return user_info.get("email")

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    if "google_auth_creds" in st.session_state:
        creds = pickle.loads(st.session_state["google_auth_creds"])
        return build("gmail", "v1", credentials=creds)
    return None

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
