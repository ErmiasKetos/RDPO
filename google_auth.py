import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.send']

def get_google_creds():
    creds = None
    # Debug output
    if 'google_client_secret' not in st.secrets:
        st.error("Missing google_client_secret in secrets")
        st.write("Available secret keys:", list(st.secrets.keys()))
        st.stop()
    
    try:
        client_config = json.loads(st.secrets['google_client_secret'])
        st.write("Successfully parsed client config")  # Debug output
    except json.JSONDecodeError as e:
        st.error(f"Error parsing client config: {str(e)}")
        st.write("Raw client secret:", st.secrets['google_client_secret'])
        st.stop()

    flow = Flow.from_client_config(client_config, SCOPES)
    flow.redirect_uri = client_config['web']['redirect_uris'][0]
    
    if 'google_token' in st.secrets:
        try:
            token_info = json.loads(st.secrets['google_token'])
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except json.JSONDecodeError as e:
            st.error(f"Error parsing token: {str(e)}")
            st.stop()
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(f"[Click here to authorize]({auth_url})")
            
            code = st.text_input("Enter the authorization code:")
            if code:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.success("Authorization successful! Please add this token to your secrets:")
                st.code(json.dumps(json.loads(creds.to_json()), indent=2))
                st.stop()
            else:
                st.stop()
    
    return creds

def get_drive_service():
    creds = get_google_creds()
    return build('drive', 'v3', credentials=creds)

def get_gmail_service():
    creds = get_google_creds()
    return build('gmail', 'v1', credentials=creds)
