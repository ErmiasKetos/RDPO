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
    email_html = f"""
    <html>
        <body>
            <h2 style='color: #2a3f5f;'>New Purchase Request: {po_data['PO Number']}</h2>
            <div style='padding: 20px; background: #f8f9fa; border-radius: 10px;'>
                {pd.DataFrame.from_dict(po_data, orient='index').to_html()}
            </div>
            <p style='margin-top: 20px;'>Submitted by: {user_email}</p>
        </body>
    </html>
    """
    send_email(user_email, f"New PO Request: {po_data['PO Number']}", email_html)

if __name__ == "__main__":
    main()
