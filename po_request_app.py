# po_request.py

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2 import service_account
import io
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

# Configure Streamlit page
st.set_page_config(
    page_title="R&D Purchase Request Application",
    page_icon="🛍️",
    layout="wide"
)

# Constants
SHEET_ID = "1MTMTgGB6J6b_b_2wqHsaxxi5O_La1L34qMus5NC3K-E"
WORKSHEET_NAME = "Sheet1"
RECIPIENT_EMAIL = 'ermias@ketos.co, girma.seifu@ketos.co'

# Modern styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
        padding: 2rem;
    }
    
    /* Card styling */
    .card {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* Form styling */
    .stForm {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #0071ba, #00a6fb);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,113,186,0.2);
    }
    
    /* Header styling */
    h1 {
        color: #0071ba;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    h2, h3 {
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    /* Success/Error message styling */
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-success {
        background-color: #28a745;
    }
    
    .status-error {
        background-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Part 2: Google Sheets Integration and Core Functions

class InventoryManager:
    def __init__(self):
        """Initialize Google Sheets connection."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file",
                    "https://mail.google.com/",
                    "https://www.googleapis.com/auth/gmail.send"
                ]
            )
            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
        except Exception as e:
            st.error(f"Failed to initialize Google Sheets connection: {str(e)}")
            raise

    def get_all_records(self):
        """Get all PO records from the sheet."""
        try:
            return pd.DataFrame(self.sheet.get_all_records())
        except Exception as e:
            st.error(f"Error fetching records: {str(e)}")
            return pd.DataFrame()

    def add_new_po(self, po_data):
        """Add a new PO record to the sheet."""
        try:
            self.sheet.append_row([
                po_data["PO Number"],
                po_data["Requester"],
                po_data["Requester Email"],
                po_data["Request Date and Time"],
                po_data["Link"],
                po_data["Quantity"],
                po_data["Shipment Address"],
                po_data["Attention To"],
                po_data["Department"],
                po_data["Description"],
                po_data["Classification"],
                po_data["Urgency"]
            ])
            return True
        except Exception as e:
            st.error(f"Error adding new PO: {str(e)}")
            return False

def generate_po_number(df):
    """Generate unique PO number."""
    current_date = datetime.now()
    year_month = current_date.strftime("%y%m")
    
    if df.empty:
        sequence_number = 1
    else:
        try:
            last_po_number = df['PO Number'].iloc[-1]
            last_year_month = last_po_number.split('-')[2]
            last_sequence_number = int(last_po_number.split('-')[-1])
            
            if last_year_month == year_month:
                sequence_number = last_sequence_number + 1
            else:
                sequence_number = 1
        except:
            sequence_number = 1
    
    return f"RD-PO-{year_month}-{sequence_number:04d}"


def send_email_notification(po_data):
    """Send email notification with enhanced error handling."""
    try:
        # Explicitly specify all required scopes
        scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
        # Create credentials with all scopes
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        
        # Use the service account email as the sender
        sender_email = credentials.service_account_email
        
        from googleapiclient.discovery import build
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create Gmail service
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Construct email message
        message = MIMEMultipart()
        message['to'] = RECIPIENT_EMAIL
        message['from'] = sender_email  # Use service account email
        message['subject'] = f"Purchase request: {po_data['PO Number']}"

        
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p><b>RE: New Purchase Request</b></p>
                <p>Dear Ordering,</p>
                <p>R&D would like to order the following:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">PO Number</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['PO Number']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Requester</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Requester']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Request Date and Time</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Request Date and Time']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Link to Item(s)</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Link']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Quantity</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Quantity']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Shipment Address</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Shipment Address']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Attention To</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Attention To']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Department</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Department']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Description</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Description']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Classification</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Classification']}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Urgency</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_data['Urgency']}</td></tr>
                </table>
                <p>Regards,<br>{po_data['Requester']}</p>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(email_body, 'html'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
      
        try:
            # Specify service account email explicitly
            result = gmail_service.users().messages().send(
                userId=sender_email,  # Use service account email instead of 'me'
                body={'raw': raw_message}
            ).execute()
            
            st.success(f"Email sent successfully. Message ID: {result.get('id')}")
            return True
        
        except HttpError as http_err:
            # More detailed error logging
            st.error(f"Gmail API Error: {http_err}")
            st.error(f"Error Response: {http_err.resp.status}")
            st.error(f"Error Reason: {http_err.resp.reason}")
            st.error(f"Error Details: {http_err}")
            return False
    
        except Exception as e:
            # Catch-all error handling
            st.error(f"Comprehensive Email Sending Error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return False

# Part 3: Main Application UI and Form Handling

def main():
    # Initialize Inventory Manager
     if 'inventory_manager' not in st.session_state:
        try:
            st.session_state.inventory_manager = InventoryManager()
        except Exception as e:
            st.error("Failed to initialize application. Please check your connection and try again.")
            st.error(f"Error: {str(e)}")
            return

    # Application Header
    st.markdown('<h1>R&D Purchase Request (PO) Application</h1>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### Instructions")
        st.info("""
        1. Fill in all required fields in the form.
        2. Review your information before submitting.
        3. Make sure to include your project in the Description.
        4. You will receive an email confirmation.
        """)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Main Form
    st.markdown('<div class="card">', unsafe_allow_html=True)
    with st.form("po_request_form", clear_on_submit=True):
        st.markdown("### Purchase Request Form")
        
        col1, col2 = st.columns(2)
        
        with col1:
            requester = st.text_input("Requester Full Name", key="requester")
            requester_email = st.text_input("Requester Email", key="email")
            link = st.text_input("Link to Item(s)", key="link")
            quantity = st.number_input("Quantity of Item(s)", min_value=1, value=1, key="quantity")
            shipment_address = st.text_input("Shipment Address", 
                                           value="420 S Hillview Dr, Milpitas, CA 95035",
                                           key="address")

        with col2:
            attention_to = st.text_input("Attention To", key="attention")
            department = st.text_input("Department", value="R&D", disabled=True)
            description = st.text_area("Brief Description of Use", key="description",
                                     help="Include your project name/number")
            classification = st.selectbox(
                "Classification Code",
                [
                    "6051 - Lab Supplies (including Chemicals)",
                    "6052 - Testing (Outside Lab Validation)",
                    "6055 - Parts & Tools",
                    "6054 - Prototype",
                    "6053 - Other"
                ],
                key="classification"
            )
            urgency = st.selectbox("Urgency", ["Normal", "Urgent"], key="urgency")

        submit_button = st.form_submit_button("Submit Request", use_container_width=True)

    if submit_button:
        if all([requester, requester_email, link, attention_to, description]):
            with st.spinner("Processing your request..."):
                try:
                    # Get existing records
                    df = st.session_state.inventory_manager.get_all_records()
                    
                    # Generate PO number
                    po_number = generate_po_number(df)
                    
                    # Prepare PO data
                    po_data = {
                        "PO Number": po_number,
                        "Requester": requester,
                        "Requester Email": requester_email,
                        "Request Date and Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Link": link,
                        "Quantity": quantity,
                        "Shipment Address": shipment_address,
                        "Attention To": attention_to,
                        "Department": department,
                        "Description": description,
                        "Classification": classification,
                        "Urgency": urgency
                    }
                    
                    # Save to Google Sheets
                    if st.session_state.inventory_manager.add_new_po(po_data):
                        # Send email notification
                        if send_email_notification(po_data):
                            st.success("✅ Request submitted successfully!")
                            st.info(f"Your PO Number is: {po_number}")
                            
                            # Show confirmation details
                            with st.expander("View Request Details", expanded=True):
                                st.markdown(f"""
                                    ### Request Summary
                                    - **PO Number**: {po_number}
                                    - **Requester**: {requester}
                                    - **Email**: {requester_email}
                                    - **Item Link**: {link}
                                    - **Quantity**: {quantity}
                                    - **Urgency**: {urgency}
                                """)
                        else:
                            st.warning("Request saved but email notification failed. Please contact support.")
                    else:
                        st.error("Failed to submit request. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Please fill in all required fields.")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            © 2024 KETOS R&D Purchase Request Application
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
