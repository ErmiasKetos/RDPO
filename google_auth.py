import streamlit as st
import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
from urllib.parse import urlencode
import requests
from requests.exceptions import ConnectionError, SSLError

# Important: Set this environment variable
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

def check_google_connection():
    """Check if we can connect to Google's services"""
    try:
        requests.get('https://accounts.google.com', timeout=5)
        return True
    except (ConnectionError, SSLError) as e:
        st.error("Unable to connect to Google services. Please check your internet connection.")
        st.error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error checking connection: {str(e)}")
        return False

def authenticate_user():
    """Modernized authentication flow with connection checking and better error handling"""
    if 'google_auth' not in st.session_state:
        st.session_state.google_auth = {
            'creds': None,
            'email': None
        }

    # Return cached credentials if valid
    if st.session_state.google_auth['creds'] and st.session_state.google_auth['creds'].valid:
        return st.session_state.google_auth['email']

    # Check Google connection first
    if not check_google_connection():
        st.error("Please try again when you have a stable internet connection")
        st.stop()

    try:
        # Initialize OAuth flow with explicit redirect URI
        client_config = {
            "web": {
                "client_id": st.secrets["google_oauth_client"]["client_id"],
                "client_secret": st.secrets["google_oauth_client"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["google_oauth_client"]["redirect_uris"][0]]
            }
        }
        
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=SCOPES,
            redirect_uri=st.secrets["google_oauth_client"]["redirect_uris"][0]
        )

        # Handle OAuth callback using st.query_params
        if 'code' in st.query_params:
            with st.spinner("Authenticating..."):
                try:
                    flow.fetch_token(code=st.query_params['code'])
                    creds = flow.credentials
                    
                    # Get user info
                    user_info_service = build("oauth2", "v2", credentials=creds)
                    user_info = user_info_service.userinfo().get().execute()
                    
                    # Validate email domain
                    if not user_info['email'].endswith('@ketos.co'):
                        st.error("Please use your @ketos.co email address")
                        if 'google_auth' in st.session_state:
                            del st.session_state['google_auth']
                        st.stop()
                    
                    # Store in session state
                    st.session_state.google_auth = {
                        'creds': creds,
                        'email': user_info['email']
                    }
                    
                    # Clear query parameters and reload
                    st.query_params.clear()
                    st.rerun()
                    
                except ConnectionError as e:
                    st.error("Connection to Google failed. Please check your internet connection.")
                    st.error(f"Connection error: {str(e)}")
                    if 'google_auth' in st.session_state:
                        del st.session_state['google_auth']
                    st.stop()
                except Exception as e:
                    st.error("Authentication failed. Please try again.")
                    st.error(f"Error details: {str(e)}")
                    if 'google_auth' in st.session_state:
                        del st.session_state['google_auth']
                    st.stop()

        # Show login button if not authenticated
        if not st.session_state.google_auth['creds']:
            auth_params = {
                'access_type': 'offline',
                'include_granted_scopes': 'true',
                'prompt': 'consent',
                'hd': 'ketos.co'  # Restrict to ketos.co domain
            }
            
            try:
                auth_url, _ = flow.authorization_url(**auth_params)
                
                st.markdown(f"""
                <div style='text-align: center; margin: 2rem;'>
                    <h2 style='color: #1a73e8; margin-bottom: 1rem;'>Welcome to Ketos PO System</h2>
                    <p style='color: #5f6368; margin-bottom: 2rem;'>Please log in with your Ketos email to continue.</p>
                    <div style='margin-bottom: 1rem;'>
                        <a href="{auth_url}" target="_self" style='text-decoration: none;'>
                            <button style='
                                background: #4285F4;
                                color: white;
                                padding: 12px 24px;
                                border: none;
                                border-radius: 4px;
                                font-size: 16px;
                                cursor: pointer;
                                transition: all 0.3s;
                                display: inline-flex;
                                align-items: center;
                                gap: 12px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.25);
                            '>
                                <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                                    <path fill="#fff" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
                                    <path fill="#fff" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
                                    <path fill="#fff" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957C.347 6.155 0 7.54 0 9s.348 2.845.957 4.039l3.007-2.332z"/>
                                    <path fill="#fff" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z"/>
                                </svg>
                                <strong>Sign in with Google</strong>
                            </button>
                        </a>
                    </div>
                    <p style='margin-top: 1.5rem; color: #5f6368; font-size: 0.9rem;'>
                        You must use your @ketos.co email to access this system
                    </p>
                    <div style='margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 4px;'>
                        <p style='color: #5f6368; font-size: 0.9rem;'>
                            Having trouble connecting? Try these steps:
                            <ul style='text-align: left; margin-top: 0.5rem;'>
                                <li>Check your internet connection</li>
                                <li>Clear your browser cache and cookies</li>
                                <li>Try using a different browser</li>
                                <li>Contact IT support if issues persist</li>
                            </ul>
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.stop()
                
            except Exception as e:
                st.error("Failed to initialize Google Sign-In")
                st.error(f"Error details: {str(e)}")
                st.error("Please try again or contact your administrator")
                st.stop()

    except Exception as e:
        st.error("Failed to initialize authentication")
        st.error(f"Error details: {str(e)}")
        st.error("Please contact your administrator")
        st.stop()

    return st.session_state.google_auth['email']

def send_email(sender_email, subject, email_body):
    """Improved email sending with better error handling"""
    try:
        if 'google_auth' not in st.session_state or not st.session_state.google_auth['creds']:
            st.error("Authentication required to send emails")
            return False

        service = build('gmail', 'v1', credentials=st.session_state.google_auth['creds'])
        
        message = MIMEText(email_body, 'html')
        message['to'] = "ermias@ketos.co"
        message['from'] = f"Ketos PO System <{sender_email}>"
        message['subject'] = subject
        
        raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        
        with st.spinner("Sending notification..."):
            service.users().messages().send(
                userId="me",
                body=raw_message
            ).execute()
        
        st.toast("📧 Email sent successfully!", icon="✅")
        return True
        
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

