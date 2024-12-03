import streamlit as st
import pandas as pd
from datetime import datetime
import os
import logging
import pytz
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from email.mime.text import MIMEText
import base64
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
APP_URL = "https://<your-app-name>.streamlit.app"
DRIVE_FOLDER_ID = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"
PURCHASE_SUMMARY_FILE_NAME = "purchase_summary.csv"
AUTHORIZED_DOMAIN = "ketos.co"  # Only allow emails from this domain

# OAuth 2.0 configuration
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]

def create_flow():
    """Create OAuth flow with secure configuration"""
    client_config = {
        "web": {
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                f"{APP_URL}/",
                f"{APP_URL}/callback"
            ],
            "javascript_origins": [APP_URL]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=f"{APP_URL}/"
    )

def verify_email_domain(email):
    """Check if the email belongs to the authorized domain"""
    if not email.endswith(f"@{AUTHORIZED_DOMAIN}"):
        st.error(f"Access Denied: Only @{AUTHORIZED_DOMAIN} email addresses are allowed.")
        st.stop()

def init_google_services():
    """Initialize Google Drive and Gmail API services"""
    try:
        if 'google_auth_credentials' not in st.session_state:
            flow = create_flow()
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )

            st.markdown(f'''
                <div style="text-align: center; padding: 20px;">
                    <h2>Sign in with your @{AUTHORIZED_DOMAIN} email</h2>
                    <a href="{auth_url}" target="_blank">
                        <button style="
                            background-color: #1a73e8;
                            color: white;
                            padding: 12px 24px;
                            border: none;
                            border-radius: 4px;
                            font-size: 16px;
                        ">
                            Sign in with Google
                        </button>
                    </a>
                </div>
            ''', unsafe_allow_html=True)

            query_params = st.experimental_get_query_params()
            if 'code' in query_params:
                try:
                    flow.fetch_token(code=query_params['code'][0])
                    credentials = flow.credentials
                    st.session_state.google_auth_credentials = {
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        'token_uri': credentials.token_uri,
                        'client_id': credentials.client_id,
                        'client_secret': credentials.client_secret,
                        'scopes': credentials.scopes
                    }
                    st.experimental_set_query_params()
                    st.rerun()
                except Exception as e:
                    st.error("Failed to complete authentication. Please try again.")
                    logger.error(f"Error fetching token: {e}")
                    return None, None
            return None, None

        # Use existing credentials
        creds = Credentials.from_authorized_user_info(
            st.session_state.google_auth_credentials,
            SCOPES
        )
        drive_service = build('drive', 'v3', credentials=creds)
        gmail_service = build('gmail', 'v1', credentials=creds)

        # Get user email and verify
        user_info = gmail_service.users().getProfile(userId='me').execute()
        user_email = user_info.get('emailAddress', '')
        verify_email_domain(user_email)

        return drive_service, gmail_service

    except Exception as e:
        st.error(f"Authentication failed. Details: {e}")
        logger.error(f"Authentication error: {e}")
        return None, None

def main():
    st.set_page_config(page_title="Purchase Order Request Form", page_icon="🛍️")
    st.title("Purchase Order Request Form")

    # Initialize Google services
    drive_service, gmail_service = init_google_services()
    if not drive_service or not gmail_service:
        return

    # Form for purchase order
    with st.form("po_form"):
        requester = st.text_input("Requester Full Name*")
        link = st.text_input("Link to Item(s)*")
        quantity = st.number_input("Quantity of Item(s)", min_value=1, value=1)
        address = st.text_input("Shipment Address", value="420 S Hillview Dr, Milpitas, CA 95035")
        attention = st.text_input("Attention To*")
        department = st.text_input("Department", value="R&D", disabled=True)
        description = st.text_area("Brief Description of Use*")
        classification = st.selectbox(
            "Classification Code",
            ["6051 - Lab Supplies (including Chemicals)",
             "6052 - Testing (Outside Lab Validation)",
             "6055 - Parts & Tools",
             "6054 - Prototype",
             "6053 - Other"]
        )
        urgency = st.selectbox("Urgency", ["Normal", "Urgent"])
        submitted = st.form_submit_button("Submit Request")

    if submitted:
        if not all([requester, link, attention, description]):
            st.error("Please fill in all required fields marked with *")
            return

        try:
            pst = pytz.timezone('America/Los_Angeles')
            request_datetime = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S %Z')

            new_data = {
                'Requester': requester,
                'Request_DateTime': request_datetime,
                'Link': link,
                'Quantity': quantity,
                'Address': address,
                'Attention_To': attention,
                'Department': department,
                'Description': description,
                'Classification': classification,
                'Urgency': urgency
            }

            st.success("Request submitted successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
