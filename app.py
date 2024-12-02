import streamlit as st
import pandas as pd
from datetime import datetime
import os.path
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pytz

# Configure page settings
st.set_page_config(page_title="Purchase Order Request Form", layout="wide")

# Initialize Google Drive API
def init_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    # Load credentials from secrets
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    
    service = build('drive', 'v3', credentials=credentials)
    return service

# Function to save to Google Drive
def save_to_drive(service, file_path, folder_id):
    file_metadata = {
        'name': 'purchase_summary.csv',
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, mimetype='text/csv', resumable=True)
    
    # Check if file exists
    results = service.files().list(
        q=f"name='purchase_summary.csv' and '{folder_id}' in parents",
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

# Function to load existing data
@st.cache_data
def load_existing_data():
    try:
        return pd.read_csv('purchase_summary.csv')
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'Requester', 'Request_DateTime', 'Link', 'Quantity', 'Address',
            'Attention_To', 'Department', 'Description', 'Classification',
            'Urgency'
        ])

# Main app
def main():
    st.title("Purchase Order Request Form")
    
    # Initialize session state for form data
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    # Form inputs
    with st.form("po_form"):
        requester = st.text_input("Requester Full Name*", key="requester")
        link = st.text_input("Link to Item(s)*", key="link")
        quantity = st.number_input("Quantity of Item(s)", min_value=1, value=1, key="quantity")
        
        address = st.text_input(
            "Shipment Address",
            value="420 S Hillview Dr, Milpitas, CA 95035",
            key="address"
        )
        
        attention = st.text_input("Attention To*", key="attention")
        department = st.text_input("Department", value="R&D", disabled=True, key="department")
        description = st.text_area("Brief Description of Use*", key="description")
        
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
        
        urgency = st.selectbox(
            "Urgency",
            ["Normal", "Urgent"],
            key="urgency"
        )
        
        submitted = st.form_submit_button("Submit Request")
        
    if submitted:
        # Validate required fields
        if not all([requester, link, attention, description]):
            st.error("Please fill in all required fields marked with *")
            return
        
        # Get current time in PST
        pst = pytz.timezone('America/Los_Angeles')
        request_datetime = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Prepare data for saving
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
        
        # Load existing data and append new entry
        df = load_existing_data()
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        # Save locally first
        df.to_csv('purchase_summary.csv', index=False)
        
        # Save to Google Drive
        try:
            service = init_google_drive()
            folder_id = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"
            save_to_drive(service, 'purchase_summary.csv', folder_id)
            st.success("Purchase request submitted successfully!")
        except Exception as e:
            st.error(f"Error saving to Google Drive: {str(e)}")
            return
        
        # Generate email preview
        st.subheader("Email Preview")
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
        st.text_area("Email Content", email_body, height=400)
        
        st.session_state.form_submitted = True
    
    # Display summary table
    st.sidebar.title("Summary Options")
    show_summary = st.sidebar.checkbox("Show Purchase Summary")
    
    if show_summary:
        st.subheader("Purchase Summary")
        df = load_existing_data()
        st.dataframe(df)

if __name__ == "__main__":
    main()
