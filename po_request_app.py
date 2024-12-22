import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth import get_drive_service, get_gmail_service
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

# Clear Streamlit cache
st.cache_data.clear()

# Constants
SHEET_ID = "1MTMTgGB6J6b_b_2wqHsaxxi5O_La1L34qMus5NC3K-E"
WORKSHEET_NAME = "PO2025"
RECIPIENT_EMAIL = 'ermias@ketos.co, girma.seifu@ketos.co'
DRIVE_FILE_NAME = 'purchase_summary.csv'
DRIVE_FOLDER_ID = '12lcXSmD_gbItepTW8FuR5mEd_iAKQ_HK'

# Page configuration
st.set_page_config(
    page_title="R&D Purchase Request Application",
    page_icon="🛍️",
    layout="wide"
)

# Initialize Google services
try:
    drive_service = get_drive_service()
    gmail_service = get_gmail_service()
except GoogleAuthError as e:
    st.error(f"Google authentication error: {str(e)}")
    st.error("Please follow the authorization process to resolve this issue.")
    st.stop()
except Exception as e:
    st.error(f"Error initializing Google services: {str(e)}")
    st.error("Please make sure you have set up the Google Drive and Gmail APIs correctly.")
    st.stop()

def log_debug_info(message):
    """Log debug information to session state"""
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = []
    st.session_state.debug_info.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def verify_file_exists_and_accessible(file_id):
    """Verify if file exists and is accessible in Google Drive"""
    try:
        file = drive_service.files().get(fileId=file_id, fields='id, name, modifiedTime, size, trashed').execute()
        if file.get('trashed', False):
            log_debug_info(f"File {file_id} exists but is in the trash.")
            return False
        log_debug_info(f"File verified: {file['name']} (ID: {file['id']}, Modified: {file['modifiedTime']}, Size: {file['size']} bytes)")
        return True
    except HttpError as error:
        if error.resp.status == 404:
            log_debug_info(f"File {file_id} not found.")
        else:
            log_debug_info(f"Error verifying file {file_id}: {str(error)}")
        return False

def verify_file_content(file_id):
    """Verify if file has valid content"""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()
        if file_content:
            df = pd.read_csv(io.BytesIO(file_content))
            log_debug_info(f"File content verified. Number of records: {len(df)}")
            return True
        else:
            log_debug_info("File exists but is empty.")
            return False
    except Exception as e:
        log_debug_info(f"Error verifying file content: {str(e)}")
        return False

def send_email(sender_email, subject, email_body):
    """Send email using Gmail API"""
    try:
        message = MIMEMultipart()
        message['to'] = RECIPIENT_EMAIL
        message['from'] = sender_email
        message['subject'] = subject
        message.attach(MIMEText(email_body, 'html'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        sent_message = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        if sent_message:
            log_debug_info(f"Email sent successfully. Message ID: {sent_message['id']}")
            return True
        else:
            log_debug_info("Failed to send email. No error was raised, but no message was returned.")
            return False
    except HttpError as error:
        if error.resp.status == 403 and "accessNotConfigured" in str(error):
            log_debug_info("Gmail API is not enabled. Please enable it in the Google Cloud Console.")
        else:
            log_debug_info(f"An error occurred while sending the email: {error}")
        return False
    except Exception as e:
        log_debug_info(f"An unexpected error occurred while sending the email: {str(e)}")
        return False

def generate_po_number(df):
    """Generate unique PO number"""
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

def find_or_create_csv():
    """Find existing CSV file or create a new one"""
    try:
        log_debug_info("Searching for existing CSV file")
        results = drive_service.files().list(
            q=f"name='{DRIVE_FILE_NAME}' and '{DRIVE_FOLDER_ID}' in parents and mimeType='text/csv' and trashed=false",
            spaces='drive',
            fields='files(id, name, modifiedTime, size)'
        ).execute()
        files = results.get('files', [])

        if files:
            file = files[0]
            file_id = file['id']
            log_debug_info(f"File found - Name: {file['name']}, ID: {file_id}, Modified: {file['modifiedTime']}, Size: {file['size']} bytes")
            
            if verify_file_exists_and_accessible(file_id) and verify_file_content(file_id):
                return file_id
            else:
                log_debug_info("File found but not accessible or empty. Creating a new one.")
                return create_new_csv()
        else:
            log_debug_info("No existing CSV file found. Creating a new one.")
            return create_new_csv()
    except Exception as e:
        log_debug_info(f"Error in find_or_create_csv: {str(e)}")
        return None

def create_new_csv():
    """Create a new CSV file in Google Drive"""
    try:
        file_metadata = {
            'name': DRIVE_FILE_NAME,
            'parents': [DRIVE_FOLDER_ID],
            'mimeType': 'text/csv'
        }
        content = 'PO Number,Requester,Requester Email,Request Date and Time,Link,Quantity,Shipment Address,Attention To,Department,Description,Classification,Urgency\n'
        media = MediaIoBaseUpload(io.BytesIO(content.encode()), mimetype='text/csv', resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        new_file_id = file.get('id')
        log_debug_info(f"New CSV file created with ID: {new_file_id}")
        return new_file_id
    except Exception as e:
        log_debug_info(f"Error creating new CSV file: {str(e)}")
        return None

def read_csv_from_drive(file_id):
    """Read CSV file from Google Drive"""
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            log_debug_info(f"Attempting to read CSV file with ID: {file_id} (Attempt {attempt + 1})")
            request = drive_service.files().get_media(fileId=file_id)
            file_content = request.execute()
            df = pd.read_csv(io.BytesIO(file_content))
            log_debug_info(f"CSV file successfully loaded with {len(df)} records")
            return df
        except HttpError as e:
            if e.resp.status in [404, 410]:
                log_debug_info(f"File not found or inaccessible. Error: {str(e)}")
                return None
            elif attempt < max_retries - 1:
                log_debug_info(f"Transient error, retrying in {retry_delay} seconds. Error: {str(e)}")
                time.sleep(retry_delay)
            else:
                log_debug_info(f"Max retries reached. Error reading CSV from Google Drive: {str(e)}")
                return None
        except Exception as e:
            log_debug_info(f"Unexpected error reading CSV from Google Drive: {str(e)}")
            return None

def update_csv_in_drive(df, file_id):
    """Update CSV file in Google Drive"""
    try:
        log_debug_info(f"Attempting to update CSV file with ID: {file_id}")
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        media = MediaIoBaseUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype='text/csv', resumable=True)
        updated_file = drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        
        if updated_file:
            log_debug_info(f"CSV file successfully updated. File ID: {updated_file['id']}")
            return True
        else:
            log_debug_info("Failed to update CSV file in Google Drive.")
            return False
    except Exception as e:
        log_debug_info(f"Error updating CSV in Google Drive: {str(e)}")
        return False

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f0f5ff;
        padding: 2rem;
        border-radius: 10px;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .stSelectbox, .stTextInput, .stTextArea {
        background-color: white;
    }
    .card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Instructions")
st.sidebar.markdown("""
1. Click the 'Update Records' button to manually refresh the data.
2. Fill in the Purchase Request Form in the main area.
3. Submit the form to create a new PO request.
4. Make sure to mention your project in the Description.
""")

# Force Refresh button
if st.sidebar.button("Force Refresh"):
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# Initialize or get file ID
if 'drive_file_id' not in st.session_state or not verify_file_exists_and_accessible(st.session_state.get('drive_file_id')):
    st.session_state.drive_file_id = find_or_create_csv()

if st.session_state.get('drive_file_id'):
    if verify_file_exists_and_accessible(st.session_state.drive_file_id):
        if st.sidebar.button("Update Records") or 'df' not in st.session_state:
            df = read_csv_from_drive(st.session_state.drive_file_id)
            if df is not None:
                st.session_state.df = df
                st.sidebar.success(f"Successfully loaded {len(df)} records.")
            else:
                st.sidebar.error("Failed to update records. Please try again.")
                st.session_state.drive_file_id = find_or_create_csv()
    else:
        st.error("CSV file not accessible. Creating new one...")
        st.session_state.drive_file_id = find_or_create_csv()
else:
    st.error("Unable to find or create CSV file. Check permissions.")
    st.stop()

# Main content
st.title("R&D Purchase Request (PO) Application")

# Input form
st.markdown("<div class='card'>", unsafe_allow_html=True)
with st.form("po_request_form"):
    st.subheader("Purchase Request Form")
    col1, col2 = st.columns(2)
    
    with col1:
        requester = st.text_input("Requester Full Name")
        requester_email = st.text_input("Requester Email")
        link = st.text_input("Link to Item(s)")
        quantity = st.number_input("Quantity of Item(s)", min_value=1, value=1)
        shipment_address = st.text_input("Shipment Address", 
                                       value="420 S Hillview Dr, Milpitas, CA 95035")

    with col2:
        attention_to = st.text_input("Attention To")
        department = st.text_input("Department", value="R&D", disabled=True)
        description = st.text_area("Brief Description of Use", 
                                 help="Include your project name/number")
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

    submitted = st.form_submit_button("Submit Request", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Form submission handling
if submitted:
    if all([requester, requester_email, link, attention_to, description]):
        po_number = generate_po_number(st.session_state.df)
        request_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare new data
        new_data = {
            "PO Number": po_number,
            "Requester": requester,
            "Requester Email": requester_email,
            "Request Date and Time": request_datetime,
            "Link": link,
            "Quantity": quantity,
            "Shipment Address": shipment_address,
            "Attention To": attention_to,
            "Department": department,
            "Description": description,
            "Classification": classification,
            "Urgency": urgency
        }
        
        # Update DataFrame and save to Drive
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
        if update_csv_in_drive(st.session_state.df, st.session_state.drive_file_id):
            st.success("Request submitted and synced to Google Drive!")
        else:
            st.error("Failed to sync request to Google Drive. Please try again.")
        
        # Prepare and send email
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p><b>RE: New Purchase Request</b></p>
                <p>Dear Ordering,</p>
                <p>R&D would like to order the following:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">PO Number</th><td style="padding: 8px; border: 1px solid #dee2e6;">{po_number}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Requester</th><td style="padding: 8px; border: 1px solid #dee2e6;">{requester}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Request Date and Time</th><td style="padding: 8px; border: 1px solid #dee2e6;">{request_datetime}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Link to Item(s)</th><td style="padding: 8px; border: 1px solid #dee2e6;">{link}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Quantity</th><td style="padding: 8px; border: 1px solid #dee2e6;">{quantity}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Shipment Address</th><td style="padding: 8px; border: 1px solid #dee2e6;">{shipment_address}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Attention To</th><td style="padding: 8px; border: 1px solid #dee2e6;">{attention_to}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Department</th><td style="padding: 8px; border: 1px solid #dee2e6;">{department}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Description</th><td style="padding: 8px; border: 1px solid #dee2e6;">{description}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Classification</th><td style="padding: 8px; border: 1px solid #dee2e6;">{classification}</td></tr>
                    <tr><th style="text-align: left; padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6;">Urgency</th><td style="padding: 8px; border: 1px solid #dee2e6;">{urgency}</td></tr>
                </table>
                <p>Regards,<br>{requester}</p>
            </div>
        </body>
        </html>
        """
        
        if send_email(requester_email, f"Purchase request: {po_number}", email_body):
            st.success("✅ Email sent successfully!")
            
            # Show confirmation details
            with st.expander("View Request Details", expanded=True):
                st.markdown(f"""
                    ### Request Summary
                    - **PO Number**: {po_number}
                    - **Requester**: {requester}
                    - **Email**: {requester_email}
                    - **Link**: {link}
                    - **Quantity**: {quantity}
                    - **Urgency**: {urgency}
                """)
        else:
            st.warning("Request saved but email notification failed. Please contact support.")
    else:
        st.error("Please fill in all required fields.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        © 2024 KETOS R&D Purchase Request Application
    </div>
""", unsafe_allow_html=True)

# Debug info (optional)
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.markdown("### Debug Information")
    if 'debug_info' in st.session_state:
        for msg in st.session_state.debug_info:
            st.sidebar.text(msg)

