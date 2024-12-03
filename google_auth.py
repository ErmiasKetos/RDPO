import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.send', 'openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

def get_google_auth_flow():
    if 'google_client_secret' in st.secrets:
        try:
            client_config = json.loads(st.secrets['google_client_secret'])
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri='http://localhost:8501/'  # Update this with your Streamlit app's URL
            )
            return flow
        except json.JSONDecodeError as e:
            st.error(f"Error parsing google_client_secret: {str(e)}")
            st.error("Please check the formatting of your google_client_secret in Streamlit secrets.")
            return None
    else:
        st.error("Google client secret is not set in Streamlit secrets.")
        return None

def get_google_creds():
    flow = get_google_auth_flow()
    if not flow:
        return None

    if 'google_auth_state' not in st.session_state:
        authorization_url, state = flow.authorization_url(prompt='consent')
        st.session_state.google_auth_state = state
        st.markdown(f"[Click here to log in with Google]({authorization_url})")
        return None

    if 'code' not in st.experimental_get_query_params():
        st.warning("Please log in with Google to continue.")
        return None

    code = st.experimental_get_query_params()['code'][0]
    flow.fetch_token(code=code)
    creds = flow.credentials
    return creds

def get_drive_service():
    creds = get_google_creds()
    if creds:
        return build('drive', 'v3', credentials=creds)
    return None

def get_gmail_service():
    creds = get_google_creds()
    if creds:
        return build('gmail', 'v1', credentials=creds)
    return None

def get_user_info(creds):
    if creds:
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        return user_info
    return None

