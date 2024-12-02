import streamlit as st
import csv
from datetime import datetime
import os
import pytz
from pathlib import Path

# Configure page settings
st.set_page_config(
    page_title="R&D Purchase Order System",
    page_icon="🛍️",
    layout="wide"
)

# Ensure data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CSV_FILE = DATA_DIR / "purchase_summary.csv"

# Custom styling
st.markdown("""
<style>
    .main { padding: 2rem; }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.75rem;
        border-radius: 5px;
        border: none;
        font-weight: bold;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        color: #721c24;
        margin: 1rem 0;
    }
    .instruction-box {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Load data from CSV file"""
    if not CSV_FILE.exists():
        return []
    
    with open(CSV_FILE, 'r', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)

def save_data(data):
    """Save data to CSV file"""
    fieldnames = [
        'Requester', 'Request_DateTime', 'Link', 'Quantity',
        'Address', 'Attention_To', 'Department', 'Description',
        'Classification', 'Urgency'
    ]
    
    mode = 'a' if CSV_FILE.exists() else 'w'
    with open(CSV_FILE, mode, newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        writer.writerow(data)

def main():
    st.title("🛍️ R&D Purchase Order System")
    
    # Instructions
    with st.expander("📋 Instructions", expanded=True):
        st.markdown("""
        <div class="instruction-box">
        <h4>How to Submit a Purchase Request:</h4>
        <ol>
            <li>Fill in all required fields marked with *</li>
            <li>Provide accurate item links and quantities</li>
            <li>Double-check the shipping address</li>
            <li>Select appropriate classification and urgency</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Form
    with st.form("po_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            requester = st.text_input("Requester Full Name*")
            link = st.text_input("Link to Item(s)*")
            quantity = st.number_input("Quantity of Item(s)", min_value=1, value=1)
        
        with col2:
            address = st.text_input(
                "Shipment Address",
                value="420 S Hillview Dr, Milpitas, CA 95035"
            )
            attention = st.text_input("Attention To*")
        
        department = st.text_input("Department", value="R&D", disabled=True)
        description = st.text_area("Brief Description of Use*")
        
        col3, col4 = st.columns(2)
        
        with col3:
            classification = st.selectbox(
                "Classification Code",
                [
                    "6051 - Lab Supplies (including Chemicals)",
                    "6052 - Testing (Outside Lab Validation)",
                    "6055 - Parts & Tools",
                    "6054 - Prototype",
                    "6053 - Other"
                ]
            )
        
        with col4:
            urgency = st.selectbox("Urgency", ["Normal", "Urgent"])
        
        submitted = st.form_submit_button("📤 Submit Request")
    
    if submitted:
        # Validate required fields
        if not all([requester, link, attention, description]):
            st.markdown(
                '<div class="error-message">Please fill in all required fields marked with *</div>',
                unsafe_allow_html=True
            )
            return
        
        try:
            # Get current time in PST
            pst = pytz.timezone('America/Los_Angeles')
            request_datetime = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S %Z')
            
            # Prepare data
            data = {
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
            
            # Save data
            save_data(data)
            
            st.markdown(
                '<div class="success-message">✅ Purchase request submitted successfully!</div>',
                unsafe_allow_html=True
            )
            
            # Show email preview
            st.subheader("📧 Email Preview")
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
            st.text_area("", email_body, height=400)
            
        except Exception as e:
            st.markdown(
                f'<div class="error-message">❌ Error: {str(e)}</div>',
                unsafe_allow_html=True
            )
    
    # Sidebar for summary
    st.sidebar.title("📊 Purchase Summary")
    show_summary = st.sidebar.checkbox("Show Purchase Summary")
    
    if show_summary:
        data = load_data()
        if data:
            st.write("Previous Purchase Requests:")
            for entry in data:
                with st.expander(f"Request by {entry['Requester']} - {entry['Request_DateTime']}"):
                    for key, value in entry.items():
                        st.write(f"**{key}:** {value}")
        else:
            st.info("No purchase requests submitted yet.")

if __name__ == "__main__":
    main()
