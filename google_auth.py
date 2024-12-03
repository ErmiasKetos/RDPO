import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.send']

def get_google_creds():
    creds = None
    if 'google_client_secret' in st.secrets:
        try:
            client_config = json.loads(st.secrets['google_client_secret'])
        except json.JSONDecodeError as e:
            st.error(f"Error parsing google_client_secret: {str(e)}")
            st.error("Please check the formatting of your google_client_secret in Streamlit secrets.")
            st.stop()

        flow = Flow.from_client_config(client_config, SCOPES)
        flow.redirect_uri = client_config['web']['redirect_uris'][0]
        
        if 'google_token' in st.secrets:
            try:
                token_info = json.loads(st.secrets['google_token'])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except json.JSONDecodeError as e:
                st.error(f"Error parsing google_token: {str(e)}")
                st.error("Please check the formatting of your google_token in Streamlit secrets.")
                st.stop()
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                st.error("Google token is missing or invalid. Please reauthorize the application.")
                auth_url, _ = flow.authorization_url(prompt='consent')
                st.markdown(f"[Click here to authorize]({auth_url})")
                
                code = st.text_input("Enter the authorization code:")
                if code:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    st.success("Authorization successful! Please add the following token to your Streamlit secrets:")
                    st.code(json.dumps(json.loads(creds.to_json()), indent=2))
                    st.stop()
                else:
                    st.stop()
    else:
        st.error("Google client secret is not set in Streamlit secrets.")
        st.stop()
    
    return creds

def get_drive_service():
    creds = get_google_creds()
    return build('drive', 'v3', credentials=creds)

def get_gmail_service():
    creds = get_google_creds()
    return build('gmail', 'v1', credentials=creds)

