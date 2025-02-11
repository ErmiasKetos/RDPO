import streamlit as st
from google_sheets import update_google_sheet
from datetime import datetime
from email.mime.text import MIMEText
from google_auth import get_gmail_service
import base64

# Constants
RECIPIENT_EMAIL = 'ermias@ketos.co'

# Function to generate PO number
def generate_po_number():
    """Generate a unique PO number."""
    current_date = datetime.now().strftime("%y%m%d-%H%M%S")
    return f"RD-PO-{current_date}"

# Function to send email
def send_email(sender_email, subject, email_body):
    """Send an email notification to the PO approver."""
    try:
        gmail_service = get_gmail_service()
        message = MIMEText(email_body, 'html')
        message['to'] = RECIPIENT_EMAIL
        message['from'] = sender_email
        message['subject'] = subject
        
        raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        gmail_service.users().messages().send(userId='me', body=raw_message).execute()
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

# Streamlit UI
st.title("R&D Purchase Request Application")

with st.form("po_request_form"):
    st.subheader("Purchase Request Form")
    requester = st.text_input("Requester Full Name")
    requester_email = st.text_input("Your Email Address")  # Removed Google Auth, user inputs their email
    link = st.text_input("Link to Item(s)")
    quantity = st.number_input("Quantity", min_value=1, value=1)
    shipment_address = st.text_input("Shipment Address", value="420 S Hillview Dr, Milpitas, CA 95035")
    attention_to = st.text_input("Attention To")
    department = "R&D"
    description = st.text_area("Brief Description of Use")
    classification = st.selectbox("Classification Code", ["Lab Supplies", "Testing", "Parts & Tools", "Prototype", "Other"])
    urgency = st.selectbox("Urgency", ["Normal", "Urgent"])

    submitted = st.form_submit_button("Submit Request")

if submitted:
    if requester and requester_email and link and description and attention_to:
        po_number = generate_po_number()
        request_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        form_data = {
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

        # Update Google Sheets
        if update_google_sheet(form_data):
            st.success("Request submitted and updated in Google Sheets!")

            # Email notification to the approver
            email_body = f"""
            <html>
            <body>
            <h2>New Purchase Request</h2>
            <p>Dear Approver,</p>
            <p>A new purchase request has been submitted:</p>
            <table border="1">
                <tr><th>PO Number</th><td>{po_number}</td></tr>
                <tr><th>Requester</th><td>{requester}</td></tr>
                <tr><th>Requester Email</th><td>{requester_email}</td></tr>
                <tr><th>Request Date</th><td>{request_datetime}</td></tr>
                <tr><th>Link</th><td>{link}</td></tr>
                <tr><th>Quantity</th><td>{quantity}</td></tr>
                <tr><th>Shipment Address</th><td>{shipment_address}</td></tr>
                <tr><th>Attention To</th><td>{attention_to}</td></tr>
                <tr><th>Description</th><td>{description}</td></tr>
                <tr><th>Classification</th><td>{classification}</td></tr>
                <tr><th>Urgency</th><td>{urgency}</td></tr>
            </table>
            <p>Regards,<br>{requester}</p>
            </body>
            </html>
            """

            if send_email(requester_email, f"Purchase Request: {po_number}", email_body):
                st.success("Email notification sent to the approver!")
            else:
                st.error("Email failed to send.")
        else:
            st.error("Failed to update Google Sheets.")
    else:
        st.error("Please fill in all required fields.")

if st.button("Test Google Sheets Connection"):
    test_google_sheet_connection()

