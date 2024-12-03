import streamlit as st
import pandas as pd
from datetime import datetime
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google Drive and Gmail setup
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.send']
creds = None
if 'google_token' in st.secrets:
    creds = Credentials.from_authorized_user_info(st.secrets['google_token'], SCOPES)

if not creds or not creds.valid:
    st.error("Google credentials are not valid. Please set up the Google Drive and Gmail APIs.")
    st.stop()

drive_service = build('drive', 'v3', credentials=creds)
gmail_service = build('gmail', 'v1', credentials=creds)

# Constants
DRIVE_FILE_ID = '1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ'
RECIPIENT_EMAIL = 'ermias@ketos.co'

# Page configuration
st.set_page_config(page_title="Purchase Request Application", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
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
</style>
""", unsafe_allow_html=True)

# Function to read CSV from Google Drive
def read_csv_from_drive():
    try:
        file = drive_service.files().get_media(fileId=DRIVE_FILE_ID).execute()
        return pd.read_csv(io.StringIO(file.decode('utf-8')))
    except Exception as e:
        st.error(f"Error reading CSV from Google Drive: {str(e)}")
        return None

# Function to update CSV in Google Drive
def update_csv_in_drive(df):
    try:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        media = MediaFileUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype='text/csv', resumable=True)
        drive_service.files().update(fileId=DRIVE_FILE_ID, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Error updating CSV in Google Drive: {str(e)}")
        return False

# Function to send email
def send_email(sender_email, email_body):
    try:
        message = MIMEMultipart()
        message['to'] = RECIPIENT_EMAIL
        message['from'] = sender_email
        message['subject'] = 'New Purchase Request'
        message.attach(MIMEText(email_body, 'plain'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        gmail_service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

# App title and instructions
st.title("Purchase Request (PO) Application")

with st.expander("Instructions", expanded=False):
    st.markdown("""
    <div class="instructions">
        <h4>How to use this application:</h4>
        <ol>
            <li>Fill in all required fields in the form below.</li>
            <li>Click the 'Submit Request' button to process your request.</li>
            <li>Your request will be saved and synced to Google Drive.</li>
            <li>An email will be sent to the purchasing department.</li>
            <li>Use the checkbox below the form to view all submitted requests.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Load existing purchase summary
df = read_csv_from_drive()
if df is None:
    st.error("Unable to load the purchase summary. Please try again later.")
    st.stop()

# Input form
with st.form("po_request_form"):
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

if submitted:
    if requester and requester_email and link and description and attention_to:
        request_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_data = {
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
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        # Update CSV in Google Drive
        if update_csv_in_drive(df):
            st.success("Request submitted and synced to Google Drive!")
        else:
            st.error("Failed to sync request to Google Drive. Please try again.")
        
        # Email body
        email_body = f"""
        Dear Ordering,

        R&D would like to order the following:

        - Requester: {requester}
        - Request Date and Time: {request_datetime}
        - Link to Item(s): {link}
        - Quantity of Item(s): {quantity}
        - Shipment Address: {shipment_address}
        - Attention To: {attention_to}
        - Department: {department}
        - Description of Use: {description}
        - Classification Code: {classification}
        - Urgency: {urgency}

        Regards,
        {requester}
        """
        
        # Send email
        if send_email(requester_email, email_body):
            st.success("Email sent successfully!")
        else:
            st.error("Failed to send email. Please contact the IT department.")
        
        st.subheader("Email Preview")
        st.text_area("", email_body, height=300)
    else:
        st.error("Please fill in all required fields.")

# Summary table
show_summary = st.checkbox("Show Purchase Request Summary")

if show_summary:
    st.subheader("Purchase Request Summary")
    st.dataframe(df.style.set_properties(**{'background-color': '#f0f2f6', 'color': 'black'}))

# Footer
st.markdown("---")
st.markdown("© 2023 Purchase Request Application. All rights reserved.")

