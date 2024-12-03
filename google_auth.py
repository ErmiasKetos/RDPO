import streamlit as st
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.send']

def get_google_creds():
    creds = None
    if 'google_client_secret' in st.secrets:
        client_config = st.secrets['google_client_secret']
        creds = service_account.Credentials.from_service_account_info(
            client_config, scopes=SCOPES)
    if not creds or not creds.valid:
        st.error("Google credentials are not valid. Please set up the Google client secret in Streamlit secrets.")
        st.stop()
    return creds

def get_drive_service():
    creds = get_google_creds()
    return build('drive', 'v3', credentials=creds)

def get_gmail_service():
    creds = get_google_creds()
    return build('gmail', 'v1', credentials=creds)



