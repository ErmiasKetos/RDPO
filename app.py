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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default Google Drive folder ID
DRIVE_FOLDER_ID = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"

# OAuth 2.0 configuration
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Client configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["https://pybhayw4ybcvgk78gheuna.streamlit.app/"],
        "javascript_origins": ["https://pybhayw4ybcvgk78gheuna.streamlit.app/"]
    }
}

# Configure page settings
st.set_page_config(
    page_title="Purchase Order Request Form",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        border-radius: 10px;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.75rem;
        border-radius: 5px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .success-message {
        padding: 1rem;
        background-color: #dff0d8;
        border: 1px solid #d6e9c6;
        border-radius: 4px;
        color: #3c763d;
        margin-bottom: 1rem;
    }
    .error-message {
        padding: 1rem;
        background-color: #f2dede;
        border: 1px solid #ebccd1;
        border-radius: 4px;
        color: #a94442;
        margin-bottom: 1rem;
    }
    .instruction-box {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 4px;
    }
    .required-field {
        color: red;
        margin-left: 4px;
    }
    .form-section {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .email-preview {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
    .google-auth-button {
        background-color: #4285f4;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        text-align: center;
        cursor: pointer;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def init_google_drive():
    """Initialize Google Drive API with OAuth 2.0"""
    try:
        if 'google_auth_credentials' not in st.session_state:
            flow = Flow.from_client_config(
                CLIENT_CONFIG,
                scopes=SCOPES,
                redirect_uri=CLIENT_CONFIG['web']['redirect_uris'][0]
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            st.markdown("""
                <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
                    <h3>Google Drive Authentication Required</h3>
                    <p>Please authenticate to enable Google Drive integration.</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Login with Google", key="google_auth"):
                st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                st.stop()

            query_params = st.experimental_get_query_params()
            if 'code' in query_params:
                code = query_params['code'][0]
                flow.fetch_token(code=code)
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

        if 'google_auth_credentials' in st.session_state:
            creds = Credentials.from_authorized_user_info(
                st.session_state.google_auth_credentials,
                SCOPES
            )
            service = build('drive', 'v3', credentials=creds)
            return service
        
        return None

    except Exception as e:
        logger.error(f"Error initializing Google Drive: {str(e)}")
        st.error(f"Error initializing Google Drive: {str(e)}")
        return None

def save_to_drive(service, file_path, folder_id=DRIVE_FOLDER_ID):
    """Save file to Google Drive"""
    try:
        if not service:
            raise ValueError("Google Drive service not initialized")

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, mimetype='text/csv', resumable=True)
        
        results = service.files().list(
            q=f"name='{os.path.basename(file_path)}' and '{folder_id}' in parents",
            fields="files(id)"
        ).execute()
        
        if results['files']:
            file_id = results['files'][0]['id']
            file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            logger.info(f"Updated file: {file.get('name')} ({file.get('id')})")
        else:
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            logger.info(f"Created file: {file.get('id')}")
        
        return True

    except Exception as e:
        logger.error(f"Error saving to Google Drive: {str(e)}")
        st.error(f"Error saving to Google Drive: {str(e)}")
        return False

@st.cache_data
def load_existing_data():
    """Load existing purchase order data"""
    try:
        return pd.read_csv('purchase_summary.csv')
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'Requester', 'Request_DateTime', 'Link', 'Quantity', 'Address',
            'Attention_To', 'Department', 'Description', 'Classification',
            'Urgency'
        ])

def main():
    # Initialize Google Drive
    drive_service = init_google_drive()

    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("# 🛍️")
    with col2:
        st.title("Purchase Order Request Form")
    
    # Instructions
    with st.expander("📋 Instructions", expanded=True):
        st.markdown("""
        <div class="instruction-box">
        <h4>How to Submit a Purchase Request:</h4>
        <ol>
            <li>Fill in all required fields marked with *</li>
            <li>Provide accurate item links and quantities</li>
            <li>Double-check the shipping address</li>
            <li>Select appropriate classification and urgency</li>
            <li>Review the email preview before final submission</li>
        </ol>
        <p><strong>Note:</strong> All submissions are logged and stored securely.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main form
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        with st.form("po_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                requester = st.text_input(
                    "Requester Full Name",
                    help="Enter your full name as it should appear on the PO"
                )
                st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
                
                link = st.text_input(
                    "Link to Item(s)",
                    help="Paste the URL(s) of the items you want to order"
                )
                st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
                
                quantity = st.number_input(
                    "Quantity of Item(s)",
                    min_value=1,
                    value=1,
                    help="Enter the number of items needed"
                )
            
            with col2:
                address = st.text_input(
                    "Shipment Address",
                    value="420 S Hillview Dr, Milpitas, CA 95035",
                    help="Default shipping address (can be modified if needed)"
                )
                
                attention = st.text_input(
                    "Attention To",
                    help="Person who will receive the items"
                )
                st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
            
            department = st.text_input(
                "Department",
                value="R&D",
                disabled=True
            )
            
            description = st.text_area(
                "Brief Description of Use",
                help="Explain how these items will be used",
                height=100
            )
            st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                classification = st.selectbox(
                    "Classification Code",
                    [
                        "6051 - Lab Supplies (including Chemicals)",
                        "6052 - Testing (Outside Lab Validation)",
                        "6055 - Parts & Tools",
                        "6054 - Prototype",
                        "6053 - Other"
                    ],
                    help="Select the appropriate classification for your purchase"
                )
            
            with col4:
                urgency = st.selectbox(
                    "Urgency",
                    ["Normal", "Urgent"],
                    help="Select urgency level - use 'Urgent' only when necessary"
                )
            
            submitted = st.form_submit_button("📤 Submit Request")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submitted:
            if not all([requester, link, attention, description]):
                st.markdown(
                    '<div class="error-message">Please fill in all required fields marked with *</div>',
                    unsafe_allow_html=True
                )
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
                
                df = load_existing_data()
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                df.to_csv('purchase_summary.csv', index=False)
                
                if drive_service:
                    if save_to_drive(drive_service, 'purchase_summary.csv'):
                        st.markdown(
                            '<div class="success-message">✅ Purchase request submitted and saved to Google Drive!</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            '<div class="error-message">❌ Error saving to Google Drive. Data saved locally.</div>',
                            unsafe_allow_html=True
                        )
                
                # Email Preview
                st.subheader("📧 Email Preview")
                email_body = f"""
                Dear Ordering,

                R&D would like to order the following:

                - Requester: {requester}
                - Request Date and Time: {request_datetime}
                - Link to Item(s): {link}
                - Quantity of Item(s): {quantity}
                - Shipment Address: {address}
                - Attention To: {attention}
                - Department: {department}
                - Description of Use: {description}
                - Classification Code: {classification}
                - Urgency: {urgency}

                Regards,
                {requester}
                """
                st.markdown('<div class="email-preview">', unsafe_allow_html=True)
                st.text_area("", email_body, height=400)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(
                    f'<div class="error-message">❌ Error: {str(e)}</div>',
                    unsafe_allow_html=True
                )
    
    # Sidebar
    st.sidebar.title("📊 Purchase Summary")
    st.sidebar.markdown("""
    <div class="instruction-box">
    Toggle the checkbox below to view all previous purchase requests.
    </div>
    """, unsafe_allow_html=True)
    
    show_summary = st.sidebar.checkbox("Show Purchase Summary")
    
    if show_summary:
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("📋 Purchase Summary")
        df = load_existing_data()
        st.dataframe(df, use_container_width=True, height=400)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
