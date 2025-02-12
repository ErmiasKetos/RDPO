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
        SHEET_ID = "1Su8RA77O7kixU03jrm6DhDOAUYijW-JBBDZ7DK6ulrY"  
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet("Sheet1")

        # Append the new row to the sheet
        worksheet.append_row([
            form_data['PO Number'],
            form_data['Requester'],
            form_data['Email'],
            form_data['Timestamp'],
            form_data['Item URL'],
            form_data['Quantity'],
            form_data['Attention'],
            form_data['Category'],
            form_data['Description'],
            form_data['Urgency'],
            form_data['Status']
        ])
        
        st.success("✅ Data successfully added to Google Sheets!")
        return True
    except Exception as e:
        st.error(f"Error updating Google Sheet: {str(e)}")
        return False

def get_user_requests(user_email):
    """Fetch user's past requests from Google Sheets."""
    client = get_google_sheets_client()
    if not client:
        return []

    try:
        SHEET_ID = "1Su8RA77O7kixU03jrm6DhDOAUYijW-JBBDZ7DK6ulrY"
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet("Sheet1")

        # Get all records
        records = worksheet.get_all_records()

        # Filter records for the current user
        user_requests = [record for record in records if record['Email'] == user_email]

        return user_requests
    except Exception as e:
        st.error(f"Error fetching user requests: {str(e)}")
        return []

