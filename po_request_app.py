import streamlit as st
import pandas as pd
from datetime import datetime
from google_sheets import update_google_sheet
from google_auth import send_email

# Modern UI Setup
st.set_page_config(
    page_title="R&D Purchase Request",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern look
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        .stButton>button {
            width: 100%;
            background-color: #007BFF;
            color: white;
            font-size: 18px;
            padding: 10px;
        }
        .stSelectbox, .stTextInput, .stTextArea, .stNumberInput {
            background-color: white;
            padding: 10px;
            border-radius: 5px;
        }
        .form-section {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .stSidebar .stButton>button {
            background-color: #28A745;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar Info
st.sidebar.title("📊 Purchase Summary")
st.sidebar.write("Track all purchase requests and view their status.")
st.sidebar.button("🔄 Refresh Data")

# Main Page Header
st.title("📦 R&D Purchase Order Request")

# Form Layout
st.markdown("<div class='form-section'>", unsafe_allow_html=True)

with st.form("po_request_form"):
    st.subheader("📝 Purchase Request Form")

    col1, col2 = st.columns(2)

    with col1:
        requester = st.text_input("Requester Full Name", placeholder="Enter your full name")
        requester_email = st.text_input("Your Email", placeholder="Enter your email")
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

st.markdown("</div>", unsafe_allow_html=True)

# Processing the Form Submission
if submitted:
    if requester and requester_email and link and description and attention_to:
        po_number = f"RD-PO-{datetime.now().strftime('%y%m%d-%H%M%S')}"
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

            # Send Email Notification
            if send_email(f"Purchase Request: {po_number}", email_body):
                st.success("✅ Email notification sent successfully!")
            else:
                st.error("⚠️ Email failed to send. Please contact support.")
        else:
            st.error("⚠️ Failed to update Google Sheets.")
    else:
        st.error("⚠️ Please fill in all required fields.")

# Summary Table
show_summary = st.checkbox("📜 Show Purchase Request Summary")

if show_summary:
    st.markdown("<div class='form-section'>", unsafe_allow_html=True)
    st.subheader("📋 Purchase Request Summary")

    # Fetch and display data from Google Sheets
    from google_sheets import get_google_sheets_client
    client = get_google_sheets_client()
    sheet = client.open_by_key("1Su8RA77O7kixU03jrm6DhDOAUYijW-JBBDZ7DK6ulrY").worksheet("Sheet1")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    st.dataframe(df)
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("© 2024 R&D Purchase Request Application")
