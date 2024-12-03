import streamlit as st
import pandas as pd
from datetime import datetime
import os
import logging
import pytz
from google_auth_oauthlib.flow import Flow  # Correct import
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
APP_URL = "https://ztzvz35xfwxabgmvk6vp6i.streamlit.app/"
DRIVE_FOLDER_ID = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"
PURCHASE_SUMMARY_FILE_NAME = "purchase_summary.csv"

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

def init_google_services():
    """Initialize Google Drive and Gmail API services"""
    try:
        if 'google_auth_credentials' not in st.session_state:
            flow = create_flow()
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Provide authentication link
            st.markdown(
                f'''
                <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6;">
                    <h2 style="color: #1a73e8;">Google Authentication Required</h2>
                    <p>Please authenticate with your Google account to continue.</p>
                    <a href="{auth_url}" target="_blank">
                        <button style="
                            background-color: #1a73e8;
                            color: white;
                            padding: 12px 24px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 16px;
                            font-weight: 500;
                        ">
                            Sign in with Google
                        </button>
                    </a>
                </div>
                ''',
                unsafe_allow_html=True
            )
            
            # Check for authorization code
            query_params = st.experimental_get_query_params()
            if 'code' in query_params:
                try:
                    flow.fetch_token(code=query_params['code'][0])
                    st.session_state.google_auth_credentials = {
                        'token': flow.credentials.token,
                        'refresh_token': flow.credentials.refresh_token,
                        'token_uri': flow.credentials.token_uri,
                        'client_id': flow.credentials.client_id,
                        'client_secret': flow.credentials.client_secret,
                        'scopes': flow.credentials.scopes
                    }
                    st.experimental_set_query_params()
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error fetching token: {str(e)}")
                    st.error("Failed to complete authentication. Please try again.")
                    return None, None
            
            return None, None

        # Use existing credentials
        try:
            creds = Credentials.from_authorized_user_info(
                st.session_state.google_auth_credentials,
                SCOPES
            )
            
            drive_service = build('drive', 'v3', credentials=creds)
            gmail_service = build('gmail', 'v1', credentials=creds)
            
            # Verify services
            drive_service.files().list(pageSize=1).execute()
            gmail_service.users().getProfile(userId='me').execute()
            
            return drive_service, gmail_service
            
        except Exception as e:
            logger.error(f"Error with existing credentials: {str(e)}")
            del st.session_state.google_auth_credentials
            st.error("Session expired. Please authenticate again.")
            st.rerun()
            return None, None

    except Exception as e:
        logger.error(f"Error in authentication flow: {str(e)}")
        st.error(f"Authentication error. Please try again. Details: {str(e)}")
        return None, None

def send_email(service, sender_email, po_data):
    """Send email using Gmail API"""
    try:
        email_body = f"""
Dear Ordering,

R&D would like to order the following:

- Requester: {po_data['Requester']}
- Request Date and Time: {po_data['Request_DateTime']}
- Link to Item(s): {po_data['Link']}
- Quantity of Item(s): {po_data['Quantity']}
- Shipment Address: {po_data['Address']}
- Attention To: {po_data['Attention_To']}
- Department: {po_data['Department']}
- Description of Use: {po_data['Description']}
- Classification Code: {po_data['Classification']}
- Urgency: {po_data['Urgency']}

Regards,
{po_data['Requester']}
        """

        message = MIMEText(email_body)
        message['to'] = "ermias@ketos.co"
        message['from'] = sender_email
        message['subject'] = f"Purchase Order Request - {po_data['Requester']}"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def update_drive_file(service, df):
    """Update or create file in Google Drive"""
    try:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        file_metadata = {
            'name': PURCHASE_SUMMARY_FILE_NAME,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        media = MediaFileUpload(
            io.BytesIO(csv_content.encode()),
            mimetype='text/csv',
            resumable=True
        )

        # Check if file exists
        results = service.files().list(
            q=f"name='{PURCHASE_SUMMARY_FILE_NAME}' and '{DRIVE_FOLDER_ID}' in parents",
            fields="files(id)"
        ).execute()

        if results['files']:
            file_id = results['files'][0]['id']
            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
        else:
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
        return True
    except Exception as e:
        logger.error(f"Error updating Drive file: {str(e)}")
        return False

def load_purchase_summary(service):
    """Load existing purchase summary from Drive"""
    try:
        results = service.files().list(
            q=f"name='{PURCHASE_SUMMARY_FILE_NAME}' and '{DRIVE_FOLDER_ID}' in parents",
            fields="files(id)"
        ).execute()

        if not results['files']:
            return pd.DataFrame(columns=[
                'Requester', 'Request_DateTime', 'Link', 'Quantity', 'Address',
                'Attention_To', 'Department', 'Description', 'Classification',
                'Urgency'
            ])

        file_id = results['files'][0]['id']
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        return pd.read_csv(io.StringIO(content.decode('utf-8')))

    except Exception as e:
        logger.error(f"Error loading purchase summary: {str(e)}")
        raise

def main():
    st.set_page_config(
        page_title="Purchase Order Request Form",
        page_icon="🛍️",
        layout="wide"
    )

    # Initialize Google services
    drive_service, gmail_service = init_google_services()

    if not drive_service or not gmail_service:
        return

    # Main form
    st.title("Purchase Order Request Form")

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
            [
                "6051 - Lab Supplies (including Chemicals)",
                "6052 - Testing (Outside Lab Validation)",
                "6055 - Parts & Tools",
                "6054 - Prototype",
                "6053 - Other"
            ]
        )
        
        urgency = st.selectbox("Urgency", ["Normal", "Urgent"])
        
        submitted = st.form_submit_button("Submit Request")

    if submitted:
        if not all([requester, link, attention, description]):
            st.error("Please fill in all required fields marked with *")
            return

        try:
            # Prepare new entry
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

            # Update Drive file
            purchase_df = load_purchase_summary(drive_service)
            purchase_df = pd.concat([purchase_df, pd.DataFrame([new_data])], ignore_index=True)
            if update_drive_file(drive_service, purchase_df):
                # Send email
                user_email = "your_email@example.com"  # Replace with Gmail API-authenticated user email
                if send_email(gmail_service, user_email, new_data):
                    st.success("✅ Purchase request submitted and email sent successfully!")
                else:
                    st.warning("✅ Purchase request submitted but email sending failed.")
            else:
                st.error("❌ Error saving purchase request.")

        except Exception as e:
            st.error(f"❌ Error processing request: {str(e)}")

if __name__ == "__main__":
    main()
