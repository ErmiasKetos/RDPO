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
DRIVE_FILE_NAME = 'purchase_summary.csv'
DRIVE_FOLDER_ID = '12lcXSmD_gbItepTW8FuR5mEd_iAKQ_HK'
RECIPIENT_EMAIL = 'ermias@ketos.co'

# Page configuration
st.set_page_config(page_title="R&D Purchase Request Application", layout="wide")

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
    .instructions {
        background-color: #e1e4e8;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .summary-table {
        margin-top: 2rem;
    }
    .card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .sidebar .stButton > button {
        background-color: #3498db;
    }
    .debug-info {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 10px;
        margin-top: 20px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

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
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = []
    st.session_state.debug_info.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def verify_file_exists_and_accessible(file_id):
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

def find_or_create_csv():
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
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            log_debug_info(f"Attempting to read CSV file with ID: {file_id} (Attempt {attempt + 1})")
            request = drive_service.files().get_media(fileId=file_id)
            file_content = request.execute()
            df = pd.read_csv(io.BytesIO(file_content))
            log_debug_info(f"CSV file successfully loaded with {len(df)} records")
            log_debug_info(f"CSV file content preview:\n{df.head().to_string()}")
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

def generate_po_number(df):
    current_date = datetime.now()
    year_month = current_date.strftime("%y%m")
    
    if df.empty:
        sequence_number = 1
    else:
        last_po_number = df['PO Number'].iloc[-1]
        last_year_month = last_po_number.split('-')[2]
        last_sequence_number = int(last_po_number.split('-')[-1])
        
        if last_year_month == year_month:
            sequence_number = last_sequence_number + 1
        else:
            sequence_number = 1
    
    return f"RD-PO-{year_month}-{sequence_number:04d}"

def send_email(sender_email, subject, email_body):
    try:
        message = MIMEMultipart()
        message['to'] = RECIPIENT_EMAIL
        message['from'] = sender_email
        message['subject'] = subject
        message.attach(MIMEText(email_body, 'html'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        sent_message = gmail_service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        
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

def force_refresh():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# Sidebar
st.sidebar.title("Instructions")
st.sidebar.markdown("""
1. Click the 'Update Records' button to manually refresh the data from Google Drive.
2. Fill in the Purchase Request Form in the main area.
3. Submit the form to create a new PO request.
4. Mention your project in the "Brief Description of Use" filed.
""")

# Force Refresh button
if st.sidebar.button("Force Refresh"):
    force_refresh()

# Find or create CSV file
if 'drive_file_id' not in st.session_state or not verify_file_exists_and_accessible(st.session_state.get('drive_file_id')):
    st.session_state.drive_file_id = find_or_create_csv()

if st.session_state.get('drive_file_id'):
    if verify_file_exists_and_accessible(st.session_state.drive_file_id):
        if st.sidebar.button("Update Records") or 'df' not in st.session_state:
            df = read_csv_from_drive(st.session_state.drive_file_id)
            if df is not None:
                st.session_state.df = df
                st.sidebar.success(f"CSV file successfully loaded with {len(df)} existing records.")
            else:
                st.sidebar.error("Failed to update records. Please try again.")
                st.session_state.drive_file_id = find_or_create_csv()
    else:
        st.error("The CSV file is not accessible. Attempting to create a new one.")
        st.session_state.drive_file_id = find_or_create_csv()
else:
    st.error("Unable to find or create the CSV file. Please check your Google Drive permissions and try again.")
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
        shipment_address = st.text_input("Shipment Address", value="420 S Hillview Dr, Milpitas, CA 95035")
    
    with col2:
        attention_to = st.text_input("Attention To")
        department = st.text_input("Department", value="R&D", disabled=True)
        description = st.text_area("Brief Description of Use")
        classification = st.selectbox("Classification Code", [
            "6051 - Lab Supplies (including Chemicals)",
            "6052 - Testing (Outside Lab Validation)",
            "6055 - Parts & Tools",
            "6054 - Prototype",
            "6053 - Other"
        ])
        urgency = st.selectbox("Urgency", ["Normal", "Urgent"])
    
    submitted = st.form_submit_button("Submit Request")

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if requester and requester_email and link and description and attention_to:
        po_number = generate_po_number(st.session_state.df)
        request_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        
        # Append to DataFrame
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
        
        # Update CSV in Google Drive
        if update_csv_in_drive(st.session_state.df, st.session_state.drive_file_id):
            st.success("Request submitted and synced to Google Drive!")
        else:
            st.error("Failed to sync request to Google Drive. Please try again.")
        
        # Email body
        email_body = f"""
        <html>
        <body>
        <p><b>RE: New Purchase Request</b></p2>
        <p>Dear Ordering,</p>
        <p>R&D would like to order the following:</p>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr><th align="left"><b>PO Number</b></th><td>{po_number}</td></tr>
            <tr><th align="left"><b>Requester</b></th><td>{requester}</td></tr>
            <tr><th align="left"><b>Request Date and Time</b></th><td>{request_datetime}</td></tr>
            <tr><th align="left"><b>Link to Item(s)</b></th><td>{link}</td></tr>
            <tr><th align="left"><b>Quantity of Item(s)</b></th><td>{quantity}</td></tr>
            <tr><th align="left"><b>Shipment Address</b></th><td>{shipment_address}</td></tr>
            <tr><th align="left"><b>Attention To</b></th><td>{attention_to}</td></tr>
            <tr><th align="left"><b>Department</b></th><td>{department}</td></tr>
            <tr><th align="left"><b>Description of Use</b></th><td>{description}</td></tr>
            <tr><th align="left"><b>Classification Code</b></th><td>{classification}</td></tr>
            <tr><th align="left"><b>Urgency</b></th><td>{urgency}</td></tr>
        </table>
        <p>Regards,<br>{requester}</p>
        </body>
        </html>
        """
        
        # Send email
        if send_email(requester_email, f"Purchase request: {po_number}", email_body):
            st.success("Email sent successfully!")
        else:
            st.error("Failed to send email. Please contact the IT department.")
        
        st.subheader("Email Preview")
        st.markdown(email_body, unsafe_allow_html=True)
    else:
        st.error("Please fill in all required fields.")



# Footer
st.markdown("---")
st.markdown("© 2023 R&D Purchase Request Application.")

