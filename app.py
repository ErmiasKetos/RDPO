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
import io
from email.mime.text import MIMEText
import base64


# Important: This allows OAuth to work in development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
APP_URL = "https://ztzvz35xfwxabgmvk6vp6i.streamlit.app"
DRIVE_FOLDER_ID = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"

# Simplified scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]

def get_google_auth_flow():
    """Create and configure OAuth flow"""
    client_config = {
        "web": {
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{APP_URL}/"],
            "javascript_origins": [APP_URL]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=f"{APP_URL}/"
    )
    return flow

def init_google_services():
    """Initialize Google Drive and Gmail API services"""
    try:
        # Check if already authenticated
        if 'google_auth_credentials' in st.session_state:
            try:
                creds = Credentials.from_authorized_user_info(
                    st.session_state.google_auth_credentials,
                    SCOPES
                )
                drive_service = build('drive', 'v3', credentials=creds)
                gmail_service = build('gmail', 'v1', credentials=creds)
                return drive_service, gmail_service
            except Exception:
                # Clear invalid credentials
                del st.session_state.google_auth_credentials
        
        # Start new authentication flow
        flow = get_google_auth_flow()
        
        # Handle OAuth callback
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
                
                # Build services with new credentials
                drive_service = build('drive', 'v3', credentials=credentials)
                gmail_service = build('gmail', 'v1', credentials=credentials)
                return drive_service, gmail_service
            
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                return None, None
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Display login button
        st.markdown(
            """
            <div style='padding: 20px; border-radius: 5px; border: 1px solid #ccc; background-color: #f8f9fa;'>
                <h3 style='color: #1a73e8;'>🔐 Authentication Required</h3>
                <p>Please sign in with your Google account to continue.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🔑 Sign in with Google",
                key="google_auth",
                use_container_width=True,
            ):
                st.markdown(
                    f"""
                    <meta http-equiv="refresh" content="0; url={auth_url}">
                    <p>Redirecting to Google login...</p>
                    """,
                    unsafe_allow_html=True
                )
                st.stop()
        
        return None, None
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        st.error("An error occurred during authentication. Please try again.")
        return None, None

def check_google_services():
    """Test Google services connection"""
    drive_service, gmail_service = init_google_services()
    
    if not drive_service or not gmail_service:
        st.warning("⚠️ Not authenticated. Please sign in.")
        return False
    
    try:
        # Test Drive API
        drive_service.files().list(pageSize=1).execute()
        # Test Gmail API
        gmail_service.users().getProfile(userId='me').execute()
        return True
    except Exception as e:
        logger.error(f"Service check failed: {str(e)}")
        return False

# Add this at the start of your main app code
def main():
    st.set_page_config(
        page_title="Purchase Order Request Form",
        page_icon="🛍️",
        layout="wide"
    )
    
    # Check authentication
    if not check_google_services():
        return
    
    # Rest of your app code here...

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

def load_purchase_summary(service):
    """Load purchase summary from Google Drive"""
    try:
        # Search for the file
        results = service.files().list(
            q=f"name='{PURCHASE_SUMMARY_FILE_NAME}' and '{DRIVE_FOLDER_ID}' in parents",
            fields="files(id, name)"
        ).execute()

        if not results['files']:
            # Create new DataFrame if file doesn't exist
            return pd.DataFrame(columns=[
                'Requester', 'Request_DateTime', 'Link', 'Quantity', 'Address',
                'Attention_To', 'Department', 'Description', 'Classification',
                'Urgency'
            ])

        # Download existing file
        file_id = results['files'][0]['id']
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        return pd.read_csv(io.StringIO(content.decode('utf-8')))

    except Exception as e:
        logger.error(f"Error loading purchase summary: {str(e)}")
        raise

def save_to_drive(service, df):
    """Save DataFrame to Google Drive"""
    try:
        # Convert DataFrame to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        # Prepare the file metadata and media
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
            # Update existing file
            file_id = results['files'][0]['id']
            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
        else:
            # Create new file
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

        return True

    except Exception as e:
        logger.error(f"Error saving to Drive: {str(e)}")
        return False

def main():
    st.set_page_config(
        page_title="Purchase Order Request Form",
        page_icon="🛍️",
        layout="wide"
    )

    # Initialize Google services
    drive_service, gmail_service = init_google_services()

    if not drive_service or not gmail_service:
        st.error("⚠️ Unable to access Google services. Please log in to continue.")
        return

    # Get user email
    user_email = get_user_email(gmail_service)
    if not user_email:
        st.error("⚠️ Unable to get user email. Please try again.")
        return

    # Try to load existing purchase summary
    try:
        purchase_df = load_purchase_summary(drive_service)
    except Exception as e:
        st.error(f"⚠️ Unable to access purchase summary: {str(e)}")
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

            # Update DataFrame and save to Drive
            purchase_df = pd.concat([purchase_df, pd.DataFrame([new_data])], ignore_index=True)
            if save_to_drive(drive_service, purchase_df):
                # Send email
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
