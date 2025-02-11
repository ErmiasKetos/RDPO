import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define the Google Sheets scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_google_sheets_client():
    """Authenticate and return a Google Sheets client."""
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

def update_google_sheet(form_data):
    """Append a new purchase request to the Google Sheet."""
    client = get_google_sheets_client()
    if not client:
        return False

    try:
        sheet = client.open_by_key("Sheet1").worksheet("purchase_summary")
        sheet.append_row([
            form_data['PO Number'],
            form_data['Requester'],
            form_data['Requester Email'],
            form_data['Request Date and Time'],
            form_data['Link'],
            form_data['Quantity'],
            form_data['Shipment Address'],
            form_data['Attention To'],
            form_data['Department'],
            form_data['Description'],
            form_data['Classification'],
            form_data['Urgency']
        ])
        return True
    except Exception as e:
        st.error(f"Error updating Google Sheet: {str(e)}")
        return False
