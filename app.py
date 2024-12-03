import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth import get_drive_service, get_gmail_service
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError

# Constants
DRIVE_FILE_ID = '1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ'
DRIVE_FILE_NAME = 'purchase_summary.csv'
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

# Function to create a new CSV file in Google Drive
def create_csv_in_drive():
    try:
        file_metadata = {
            'name': DRIVE_FILE_NAME,
            'mimeType': 'text/csv'
        }
        media = drive_service.files().create(
            body=file_metadata,
            media_body=io.BytesIO(b'Requester,Requester Email,Request Date and Time,Link,Quantity,Shipment Address,Attention To,Department,Description,Classification,Urgency\n'),
            fields='id'
        ).execute()
        return media.get('id')
    except Exception as e:
        st.error(f"Error creating CSV in Google Drive: {str(e)}")
        return None

# Function to read CSV from Google Drive
def read_csv_from_drive():
    try:
        file = drive_service.files().get_media(fileId=DRIVE_FILE_ID).execute()
        return pd.read_csv(io.StringIO(file.decode('utf-8')))
    except HttpError as e:
        if e.resp.status == 404:
            st.warning("CSV file not found in Google Drive. Creating a new one...")
            new_file_id = create_csv_in_drive()
            if new_file_id:
                st.success(f"New CSV file created with ID: {new_file_id}")
                global DRIVE_FILE_ID
                DRIVE_FILE_ID = new_file_id
                return pd.DataFrame(columns=['Requester', 'Requester Email', 'Request Date and Time', 'Link', 'Quantity', 'Shipment Address', 'Attention To', 'Department', 'Description', 'Classification', 'Urgency'])
            else:
                st.error("Failed to create a new CSV file. Please check your Google Drive permissions.")
                return None
        else:
            st.error(f"Error reading CSV from Google Drive: {str(e)}")
            return None
    except Exception as e:
        st.error(f"Unexpected error reading CSV from Google Drive: {str(e)}")
        return None

# Function to update CSV in Google Drive
def update_csv_in_drive(df):
    try:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        media = drive_service.files().update(
            fileId=DRIVE_FILE_ID,
            media_body=io.BytesIO(csv_buffer.getvalue().encode()),
            fields='id'
        ).execute()
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
    st.error("Unable to load or create the purchase summary. Please check your Google Drive permissions and try again later.")
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

