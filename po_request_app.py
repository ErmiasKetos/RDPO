import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth import get_drive_service
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import smtplib
import ssl

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

# Custom CSS
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

# Initialize Google services
try:
    drive_service = get_drive_service()
    gmail_service = get_gmail_service()
    sheet_service = build('sheets', 'v4', credentials=get_google_creds())
    if not sheet_service:
        st.error("Failed to initialize Google Sheets service.")
        st.stop()
except GoogleAuthError as e:
    st.error(f"Google authentication error: {str(e)}")
    st.error("Please follow the authorization process to resolve this issue.")
    st.stop()
except Exception as e:
    st.error(f"Error initializing Google services: {str(e)}")
    st.error("Please make sure you have set up the Google APIs correctly.")
    st.stop()
    
def log_debug_info(message):
    """Log debug information to session state"""
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = []
    st.session_state.debug_info.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def append_to_sheet(values):
    """Append new row to Google Sheet"""
    try:
        range_name = f"{WORKSHEET_NAME}!A:L"
        body = {
            'values': [list(values.values())]
        }
        result = sheet_service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        log_debug_info(f"Data appended to sheet: {result.get('updates').get('updatedRange')}")
        return True
    except Exception as e:
        log_debug_info(f"Error appending to sheet: {str(e)}")
        return False

def read_from_sheet():
    """Read all data from Google Sheet"""
    try:
        range_name = f"{WORKSHEET_NAME}!A:L"
        result = sheet_service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=range_name
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame(columns=[
                'PO Number', 'Requester', 'Requester Email', 'Request Date and Time',
                'Link', 'Quantity', 'Shipment Address', 'Attention To', 'Department',
                'Description', 'Classification', 'Urgency'
            ])
            
        df = pd.DataFrame(values[1:], columns=values[0])
        log_debug_info(f"Read {len(df)} rows from sheet")
        return df
    except Exception as e:
        log_debug_info(f"Error reading from sheet: {str(e)}")
        return None

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
            log_debug_info(f"File found - Name: {file['name']}, ID: {file_id}")
            return file_id
        else:
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
        return file.get('id')
    except Exception as e:
        log_debug_info(f"Error creating new CSV file: {str(e)}")
        return None

def update_csv_in_drive(df, file_id):
    """Update CSV file in Google Drive"""
    try:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        media = MediaIoBaseUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype='text/csv', resumable=True)
        drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        return True
    except Exception as e:
        log_debug_info(f"Error updating CSV in Google Drive: {str(e)}")
        return False

# Updated send_email function
def send_email(sender_email, receiver_email, subject, email_body):
    """Send email using sender's email account (no authorization required)"""
    try:
        message = MIMEMultipart()
        message['to'] = receiver_email
        message['from'] = sender_email
        message['subject'] = subject
        message.attach(MIMEText(email_body, 'html'))

        # Create a secure SSL context
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            #server.login(sender_email, sender_password)  # No login required
            server.sendmail(sender_email, receiver_email, message.as_string())

        log_debug_info(f"Email sent successfully from {sender_email} to {receiver_email}")
        return True
    except Exception as e:
        log_debug_info(f"Error sending email: {str(e)}")
        return False

# Initialize or get file ID for CSV backup
#if 'drive_file_id' not in st.session_state:
    #st.session_state.drive_file_id = find_or_create_csv()

# Initialize DataFrame from Google Sheets
#if 'df' not in st.session_state:
    #df = read_from_sheet()
    #if df is not None:
        #st.session_state.df = df
    #else:
        #st.error("Failed to read data from Google Sheets.")
        #st.stop()

# Sidebar
st.sidebar.title("Instructions")
st.sidebar.markdown("""
1. Fill in all required fields in the form.
2. Review your information before submitting.
3. Make sure to include your project in the Description.
4. You will receive an email confirmation.
""")

# Force Refresh button
if st.sidebar.button("Force Refresh"):
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# Main content
st.title("R&D Purchase Request (PO) Application")

# Input form
st.markdown("<div class='card'>", unsafe_allow_html=True)
with st.form("po_request_form", clear_on_submit=True):
    st.markdown("### Purchase Request Form")
    
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
        description = st.text_area("Brief Description of Use", help="Include your project name/number")
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

if submitted:
    if all([requester, requester_email, link, attention_to, description]):
        # First read latest data from sheet
        #latest_df = read_from_sheet()
        #if latest_df is not None:
            #st.session_state.df = latest_df
            #po_number = generate_po_number(latest_df)
        #else:
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
        
        # Save to Google Sheet
        #if append_to_sheet(new_data):
            #st.success("Request submitted to Google Sheet!")
            
            # Update local DataFrame and CSV backup
            #st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
            #update_csv_in_drive(st.session_state.df, st.session_state.drive_file_id)
            
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
                    <p>Thank you for your prompt attention to this request.</p>
                    <p>Sincerely,</p>
                    <p>R&D Team</p>
                </div>
            </body>
            </html>
        """

        #if send_email(requester_email, RECIPIENT_EMAIL, 'PO Request', email_body):  # Use requester's email
            #st.success("Request submitted successfully!")
        #else:
            #st.error("Failed to send email notification.")
    else:
        st.warning("Please fill in all required fields.")

# Display debug info if enabled
if st.sidebar.checkbox("Show Debug Info"):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Debug Information")
    if 'debug_info' in st.session_state:
        for message in st.session_state.debug_info:
            st.write(message)
    else:
        st.write("No debug information available.")
    st.markdown("</div>", unsafe_allow_html=True)
