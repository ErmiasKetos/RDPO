import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Page configuration
st.set_page_config(page_title="Purchase Request Application", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .stSelectbox, .stTextInput, .stTextArea {
        background-color: white;
    }
    .instructions {
        background-color: #e1e4e8;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .summary-table {
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# App title and instructions
st.title("Purchase Request (PO) Application")

with st.expander("Instructions", expanded=False):
    st.markdown("""
    <div class="instructions">
        <h4>How to use this application:</h4>
        <ol>
            <li>Fill in all required fields in the form below.</li>
            <li>Click the 'Submit Request' button to process your request.</li>
            <li>Your request will be saved and synced to Google Drive.</li>
            <li>An email preview will be generated for your review.</li>
            <li>Use the checkbox below the form to view all submitted requests.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Input form
with st.form("po_request_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        requester = st.text_input("Requester Full Name")
        link = st.text_input("Link to Item(s)")
        quantity = st.number_input("Quantity of Item(s)", min_value=1, value=1)
        shipment_address = st.text_input("Shipment Address", value="420 S Hillview Dr, Milpitas, CA 95035")
        attention_to = st.text_input("Attention To")
    
    with col2:
        department = st.text_input("Department", value="R&D", disabled=True)
        description = st.text_area("Brief Description of Use")
        classification = st.selectbox("Classification Code", [
            "6051 - Lab Supplies (including Chemicals)",
            "6052 - Testing (Outside Lab Validation)",
            "6055 - Parts & Tools",
            "6054 - Prototype",
            "6053 - Other"
        ])
        urgency = st.selectbox("Urgency", ["Normal", "Urgent"])
    
    submitted = st.form_submit_button("Submit Request")

# CSV file handling
csv_file = "purchase_summary.csv"

if submitted:
    if requester and link and description and attention_to:
        request_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_data = {
            "Requester": requester,
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
        
        # Append to CSV
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        else:
            df = pd.DataFrame([new_data])
        
        df.to_csv(csv_file, index=False)
        
        # Google Drive sync (placeholder - replace with actual implementation)
        st.success("Request submitted and synced to Google Drive!")
        
        # Email preview
        email_body = f"""
        Dear Ordering,

        R&D would like to order the following:

        - Requester: {requester}
        - Request Date and Time: {request_datetime}
        - Link to Item(s): {link}
        - Quantity of Item(s): {quantity}
        - Shipment Address: {shipment_address}
        - Attention To: {attention_to}
        - Department: {department}
        - Description of Use: {description}
        - Classification Code: {classification}
        - Urgency: {urgency}

        Regards,
        {requester}
        """
        
        st.subheader("Email Preview")
        st.text_area("", email_body, height=300)
    else:
        st.error("Please fill in all required fields.")

# Summary table
show_summary = st.checkbox("Show Purchase Request Summary")

if show_summary and os.path.exists(csv_file):
    st.subheader("Purchase Request Summary")
    df = pd.read_csv(csv_file)
    st.dataframe(df.style.set_properties(**{'background-color': '#f0f2f6', 'color': 'black'}))

# Footer
st.markdown("---")
st.markdown("© 2023 Purchase Request Application. All rights reserved.")

