import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_credentials():
    """Get credentials from service account"""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/gmail.send",
                "https://mail.google.com/"
            ]
        )
        return credentials
    except Exception as e:
        st.error(f"Error getting credentials: {str(e)}")
        return None

def get_drive_service():
    """Get Google Drive service"""
    credentials = get_credentials()
    if credentials:
        return build('drive', 'v3', credentials=credentials)
    return None

def get_gmail_service():
    """Get Gmail service"""
    credentials = get_credentials()
    if credentials:
        return build('gmail', 'v1', credentials=credentials)
    return None
