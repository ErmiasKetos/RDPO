import streamlit as st
import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

def authenticate_user():
    """Modernized authentication flow with better error handling"""
    if 'google_auth' not in st.session_state:
        st.session_state.google_auth = {
            'creds': None,
            'email': None
        }

    # Return cached credentials if valid
    if st.session_state.google_auth['creds'] and st.session_state.google_auth['creds'].valid:
        return st.session_state.google_auth['email']

    # Initialize OAuth flow
    client_config = st.secrets["google_oauth_client"]
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=client_config['web']['redirect_uris'][0]
    )

    # Handle OAuth callback
    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        with st.spinner("Authenticating..."):
            try:
                flow.fetch_token(code=query_params['code'][0])
                creds = flow.credentials
                
                # Get user info
                user_info_service = build("oauth2", "v2", credentials=creds)
                user_info = user_info_service.userinfo().get().execute()
                
                # Store in session state
                st.session_state.google_auth = {
                    'creds': creds,
                    'email': user_info['email']
                }
                st.experimental_set_query_params()  # Clear URL params
                st.rerun()
                
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                st.stop()

    # Show login button if not authenticated
    if not st.session_state.google_auth['creds']:
        st.markdown(f"""
        <div style='text-align: center; margin: 2rem;'>
            <h2>Welcome to Ketos PO System</h2>
            <p>Please log in with your Ketos email to continue.</p>
            <a href="{flow.authorization_url()[0]}" target="_self">
                <button style='
                    background: #4285F4;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background 0.3s;
                '>
                    <strong>🔑 Continue with Google</strong>
                </button>
            </a>
            <p style='margin-top: 1rem; color: #666;'>
                You must use your @ketos.co email to access this system
            </p>
        </div>
        """, unsafe_allow_html=True)
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

