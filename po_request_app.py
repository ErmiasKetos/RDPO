import streamlit as st
import pandas as pd
from datetime import datetime
from google_sheets import update_google_sheet
from google_auth import authenticate_user, send_email

# Modern UI Setup
st.set_page_config(page_title="R&D Purchase Request", layout="wide")

# Authenticate User
user_email = authenticate_user()
if not user_email:
    st.warning("You must log in with your Ketos email (@ketos.co) to submit a request.")
    st.stop()

# Restrict access to only Ketos employees
if not user_email.endswith("@ketos.co"):
    st.error("Access Denied: You must use a Ketos email to proceed.")
    st.stop()

st.success(f"✅ Logged in as: {user_email}")

# Main Page Header
st.title("📦 R&D Purchase Order Request")

# Form Layout
with st.form("po_request_form"):
    st.subheader("📝 Purchase Request Form")

    col1, col2 = st.columns(2)

    with col1:
        requester = st.text_input("Requester Full Name", placeholder="Enter your full name")
        link = st.text_input("Link to Item(s)", placeholder="Paste the item link")
        quantity = st.number_input("Quantity", min_value=1, value=1)

    with col2:
        shipment_address = st.text_input("Shipment Address", value="420 S Hillview Dr, Milpitas, CA 95035")
        attention_to = st.text_input("Attention To", placeholder="Person receiving the items")
        department = "R&D"
        description = st.text_area("Brief Description of Use", placeholder="Explain the purpose of this purchase")
        classification = st.selectbox("Classification Code", ["Lab Supplies", "Testing", "Parts & Tools", "Prototype", "Other"])
        urgency = st.selectbox("Urgency", ["Normal", "Urgent"])

    submitted = st.form_submit_button("📤 Submit Request")

# Processing the Form Submission
if submitted:
    if requester and link and description and attention_to:
        po_number = f"RD-PO-{datetime.now().strftime('%y%m%d-%H%M%S')}"
        request_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        form_data = {
            "PO Number": po_number,
            "Requester": requester,
            "Requester Email": user_email,  # Use authenticated email
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
            st.success("✅ Request submitted and updated in Google Sheets!")

            # Email content
            email_body = f"""
            <html>
            <body>
            <h2>New Purchase Request</h2>
            <p>Dear Approver,</p>
            <p>A new purchase request has been submitted:</p>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><th>PO Number</th><td>{po_number}</td></tr>
                <tr><th>Requester</th><td>{requester}</td></tr>
                <tr><th>Requester Email</th><td>{user_email}</td></tr>
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

            # Send Email Notification
            if send_email(user_email, f"Purchase Request: {po_number}", email_body):
                st.success("✅ Email notification sent successfully!")
            else:
                st.error("⚠️ Email failed to send.")
        else:
            st.error("⚠️ Failed to update Google Sheets.")
    else:
        st.error("⚠️ Please fill in all required fields.")
