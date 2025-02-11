import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define Google Sheets API scope
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
        # Replace with your actual Google Sheet ID
        SHEET_ID = "1Su8RA77O7kixU03jrm6DhDOAUYijW-JBBDZ7DK6ulrY"
        sheet = client.open_by_key(SHEET_ID)

        sheet_names = [ws.title for ws in sheet.worksheets()]
        st.write(f"Available worksheets: {sheet_names}")

        worksheet = sheet.worksheet("Sheet1")

        # Append new row with form data
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

def test_google_sheet_connection():
    """Test if Google Sheets API can access the file."""
    client = get_google_sheets_client()
    if not client:
        st.error("Failed to connect to Google Sheets API.")
        return

    try:
        # Replace with your actual Google Sheet ID
        SHEET_ID = "1Su8RA77O7kixU03jrm6DhDOAUYijW-JBBDZ7DK6ulrY"
        sheet = client.open_by_key(SHEET_ID).worksheet("purchase_summary")

        # Append a test row to verify access
        sheet.append_row(["Test", "Connection"])
        st.success("✅ Google Sheets API connection successful!")
    except Exception as e:
        st.error(f"Google Sheets access error: {str(e)}")
