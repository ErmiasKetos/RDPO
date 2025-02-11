import streamlit as st
import pandas as pd
from datetime import datetime
from google_sheets import update_google_sheet
from google_auth import authenticate_user, send_email

# Modern UI Configuration
st.set_page_config(
    page_title="Ketos PO System",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling
st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        h1 {color: #2a3f5f;}
        .stForm {border: 1px solid #e1e4e8; border-radius: 10px; padding: 2rem;}
        .stButton>button {background-color: #4CAF50; color: white; border-radius: 5px;}
        .required:after {content: " *"; color: red;}
        .success-box {padding: 1.5rem; border-radius: 10px; background-color: #e6f4ea;}
    </style>
""", unsafe_allow_html=True)

# Authentication
def main():
    user_email = authenticate_user()
    
    if not user_email or not user_email.endswith("@ketos.co"):
        st.error("🔒 Please login with your @ketos.co email")
        st.stop()

    st.sidebar.success(f"Logged in as: {user_email}")
    app_interface(user_email)

# Main Application Interface
def app_interface(user_email):
    st.title("📦 R&D Purchase Request System")
    
    with st.expander("➕ New Purchase Request", expanded=True):
        with st.form("po_form"):
            # Form Layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<p class="required">Requester Name</p>', unsafe_allow_html=True)
                requester = st.text_input("Requester Name", placeholder="John Doe", label_visibility="collapsed")
                link = st.text_input("🔗 Item URL", placeholder="https://example.com/item")
                quantity = st.number_input("🔢 Quantity", min_value=1, value=1)
                
            with col2:
                attention = st.text_input("👤 Attention To", placeholder="Recipient Name")
                urgency = st.selectbox("🚨 Urgency Level", ["Normal", "Urgent"], index=0)
                category = st.selectbox("📦 Category", ["Lab Supplies", "Testing", "Parts & Tools", "Prototype", "Other"])
            
            description = st.text_area("📝 Purpose Description", placeholder="Explain why this purchase is needed...", height=100)
            submitted = st.form_submit_button("🚀 Submit Request", use_container_width=True)

    if submitted:
        handle_submission(user_email, requester, link, quantity, attention, urgency, category, description)

def handle_submission(user_email, requester, link, quantity, attention, urgency, category, description):
    # Validation
    required_fields = {
        "Requester Name": requester,
        "Item URL": link,
        "Attention To": attention,
        "Description": description
    }
    
    missing = [field for field, value in required_fields.items() if not value]
    if missing:
        st.error(f"❌ Missing required fields: {', '.join(missing)}")
        return

    # Generate PO Data
    po_data = {
        "PO Number": f"RD-PO-{datetime.now().strftime('%y%m%d-%H%M%S')}",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Requester": requester,
        "Email": user_email,
        "Item URL": link,
        "Quantity": quantity,
        "Attention": attention,
        "Urgency": urgency,
        "Category": category,
        "Description": description,
        "Status": "Pending"
    }

    # Process Submission
    with st.spinner("🚀 Submitting your request..."):
        try:
            if update_google_sheet(po_data):
                send_confirmation(user_email, po_data)
                st.balloons()
                st.success("""
                ## ✅ Success!
                Your purchase request has been submitted!
                - PO Number: **{po_number}**
                - Approval email sent to: **ermias@ketos.co**
                """.format(po_number=po_data["PO Number"]))
        except Exception as e:
            st.error(f"❌ Submission failed: {str(e)}")


def send_confirmation(user_email, po_data):
    """Recreate the original email body with modern styling"""
    email_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #2a3f5f; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">
            New Purchase Request: {po_data['PO Number']}
        </h2>
        
        <div style="margin: 20px 0;">
            <p>Dear Approver,</p>
            <p>A new purchase request has been submitted:</p>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Field</th>
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: left;">Value</td>
                </tr>
                <tr><th>PO Number</th><td>{po_data['PO Number']}</td></tr>
                <tr><th>Requester</th><td>{po_data['Requester']}</td></tr>
                <tr><th>Requester Email</th><td>{user_email}</td></tr>
                <tr><th>Request Date</th><td>{po_data['Timestamp']}</td></tr>
                <tr><th>Item URL</th><td><a href="{po_data['Item URL']}">{po_data['Item URL']}</a></td></tr>
                <tr><th>Quantity</th><td>{po_data['Quantity']}</td></tr>
                <tr><th>Attention To</th><td>{po_data['Attention']}</td></tr>
                <tr><th>Category</th><td>{po_data['Category']}</td></tr>
                <tr><th>Urgency</th><td>{po_data['Urgency']}</td></tr>
                <tr><th>Description</th><td>{po_data['Description']}</td></tr>
            </table>
            
            <p style="margin-top: 20px;">
                Regards,<br>
                <strong>{po_data['Requester']}</strong><br>
                <em>R&D Team</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send using the original email logic
    send_email(user_email, f"Purchase Request: {po_data['PO Number']}", email_html)

if __name__ == "__main__":
    main()
