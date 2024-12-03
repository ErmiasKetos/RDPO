import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.send']

def get_google_creds():
    creds = None
    if 'google_token' in st.secrets:
        creds = Credentials.from_authorized_user_info(st.secrets['google_token'], SCOPES)
    if not creds or not creds.valid:
        st.error("Google credentials are not valid. Please set up the Google token in Streamlit secrets.")
        st.stop()
    return creds

def get_drive_service():
    creds = get_google_creds()
    return build('drive', 'v3', credentials=creds)

def get_gmail_service():
    creds = get_google_creds()
    return build('gmail', 'v1', credentials=creds)

