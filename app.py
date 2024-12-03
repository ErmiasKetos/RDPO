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



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App configuration
APP_URL = "https://ztzvz35xfwxabgmvk6vp6i.streamlit.app"
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]

def create_flow():
    """Create OAuth flow with secure configuration"""
    client_config = {
        "installed": {  # Changed from "web" to "installed"
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [APP_URL],
        }
    }
    
    flow = InstalledAppFlow.from_client_config(
        client_config,
        SCOPES,
        redirect_uri=APP_URL
    )
    return flow

def init_auth():
    """Initialize authentication"""
    try:
        if 'credentials' not in st.session_state:
            flow = create_flow()
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Display login button with secure redirect
            st.markdown(
                f'''
                <div style="text-align: center; padding: 20px;">
                    <h2>Google Authentication</h2>
                    <p>Click below to authenticate with your Ketos email</p>
                    <a href="{authorization_url}" target="_self">
                        <button style="
                            background-color: #4285f4;
                            color: white;
                            padding: 10px 20px;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                        ">
                            Sign in with Google
                        </button>
                    </a>
                </div>
                ''',
                unsafe_allow_html=True
            )
            return None

        # Use existing credentials
        credentials = Credentials.from_authorized_user_info(
            st.session_state.credentials,
            SCOPES
        )
        
        if credentials and credentials.valid:
            return credentials
        
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            st.session_state.credentials = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            return credentials
            
        return None

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        st.error("Authentication failed. Please try again.")
        return None

def build_services(credentials):
    """Build Google services with credentials"""
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        gmail_service = build('gmail', 'v1', credentials=credentials)
        return drive_service, gmail_service
    except Exception as e:
        logger.error(f"Error building services: {str(e)}")
        return None, None

def main():
    st.set_page_config(
        page_title="Purchase Order Request Form",
        page_icon="🛍️",
        layout="wide"
    )

    # Get authentication
    credentials = init_auth()
    
    if not credentials:
        return
    
    # Build services
    drive_service, gmail_service = build_services(credentials)
    
    if not drive_service or not gmail_service:
        st.error("Failed to initialize Google services. Please try again.")
        return

    # Your main app code goes here...

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
