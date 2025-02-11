import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

# Define required scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_credentials():
    """Authenticate using the service account stored in Streamlit secrets."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        return credentials
    except Exception as e:
        st.error(f"Error getting credentials: {str(e)}")
        return None

def get_drive_service():
    """Initialize Google Drive API service."""
    creds = get_credentials()
    if creds:
        return build("drive", "v3", credentials=creds)
    return None

def get_sheets_service():
    """Initialize Google Sheets API service."""
    creds = get_credentials()
    if creds:
        return build("sheets", "v4", credentials=creds)
    return None

def get_gmail_service():
    """Initialize Gmail API service."""
    creds = get_credentials()
    if creds:
        return build("gmail", "v1", credentials=creds)
    return None

def send_email(subject, email_body):
    """Send an email notification using the service account."""
    try:
        gmail_service = get_gmail_service()
        if not gmail_service:
            st.error("Failed to initialize Gmail service.")
            return False

        sender_email = st.secrets["gcp_service_account"]["client_email"]
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
