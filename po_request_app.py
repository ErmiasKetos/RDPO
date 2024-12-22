import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2 import service_account
import io
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# Configure Streamlit page
st.set_page_config(
    page_title="R&D Purchase Request Application",
    page_icon="🛍️",
    layout="wide"
)

# Constants
SHEET_ID = "1MTMTgGB6J6b_b_2wqHsaxxi5O_La1L34qMus5NC3K-E"
WORKSHEET_NAME = "PO2025"
RECIPIENT_EMAIL = 'ermias@ketos.co, girma.seifu@ketos.co'

class InventoryManager:
    def __init__(self):
        """Initialize Google Sheets connection."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file",
                ]
            )
            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
            self.credentials = credentials
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
    """Send email notification using SMTP."""
    try:
        # Prepare email message
        message = MIMEMultipart()
        message['To'] = RECIPIENT_EMAIL
        message['From'] = po_data['Requester Email']
        message['Cc'] = po_data['Requester Email']
        message['Subject'] = f"Purchase request: {po_data['PO Number']}"

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

        # Get all recipients (To and Cc)
        all_recipients = []
        all_recipients.extend(RECIPIENT_EMAIL.split(','))
        all_recipients.append(po_data['Requester Email'])
        
        # Get SMTP settings from secrets
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        smtp_username = st.secrets["email"]["smtp_username"]
        smtp_password = st.secrets["email"]["smtp_password"]

        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message, 
                              from_addr=smtp_username,
                              to_addrs=all_recipients)

        st.success("Email sent successfully!")
        return True

    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        st.error(traceback.format_exc())
        return False


def main():
    st.markdown('<h1>R&D Purchase Request (PO) Application</h1>', unsafe_allow_html=True)

    # Sidebar with instructions
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

    # Main form
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
                    # Initialize inventory manager
                    inventory_manager = InventoryManager()
                    
                    # Get existing records
                    df = inventory_manager.get_all_records()
                    
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
                    if inventory_manager.add_new_po(po_data):
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
                    st.error(traceback.format_exc())
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



