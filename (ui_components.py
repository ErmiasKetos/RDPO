import streamlit as st
from config import Config, CUSTOM_STYLES

class UIComponents:
    @staticmethod
    def setup_page():
        """Setup page configuration"""
        st.set_page_config(
            page_title=Config.APP_NAME,
            page_icon=Config.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.markdown(CUSTOM_STYLES, unsafe_allow_html=True)
    
    @staticmethod
    def show_header():
        """Display page header"""
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"# {Config.APP_ICON}")
        with col2:
            st.title(Config.APP_NAME)
    
    @staticmethod
    def show_instructions():
        """Display instructions section"""
        with st.expander("📋 Instructions", expanded=True):
            st.markdown("""
            <div class="instruction-box">
            <h4>How to Submit a Purchase Request:</h4>
            <ol>
                <li>Fill in all required fields marked with *</li>
                <li>Provide accurate item links and quantities</li>
                <li>Double-check the shipping address</li>
                <li>Select appropriate classification and urgency</li>
                <li>Review the email preview before final submission</li>
            </ol>
            <p><strong>Note:</strong> All submissions are logged and stored securely.</p>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_form():
        """Render purchase order form"""
        with st.container():
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            with st.form("po_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    requester = st.text_input(
                        "Requester Full Name",
                        help="Enter your full name as it should appear on the PO",
                        key="requester"
                    )
                    st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
                    
                    link = st.text_input(
                        "Link to Item(s)",
                        help="Paste the URL(s) of the items you want to order",
                        key="link"
                    )
                    st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
                    
                    quantity = st.number_input(
                        "Quantity of Item(s)",
                        min_value=1,
                        value=1,
                        help="Enter the number of items needed",
                        key="quantity"
                    )
                
                with col2:
                    address = st.text_input(
                        "Shipment Address",
                        value=Config.DEFAULT_ADDRESS,
                        help="Default shipping address (can be modified if needed)",
                        key="address"
                    )
                    
                    attention = st.text_input(
                        "Attention To",
                        help="Person who will receive the items",
                        key="attention"
                    )
                    st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
                
                department = st.text_input(
                    "Department",
                    value=Config.DEFAULT_DEPARTMENT,
                    disabled=True,
                    key="department"
                )
                
                description = st.text_area(
                    "Brief Description of Use",
                    help="Explain how these items will be used",
                    key="description",
                    height=100
                )
                st.markdown('<span class="required-field">*</span>', unsafe_allow_html=True)
                
                col3, col4 = st.columns(2)
                
                with col3:
                    classification = st.selectbox(
                        "Classification Code",
                        Config.CLASSIFICATION_CODES,
                        help="Select the appropriate classification for your purchase",
                        key="classification"
                    )
                
                with col4:
                    urgency = st.selectbox(
                        "Urgency",
                        Config.URGENCY_LEVELS,
                        help="Select urgency level - use 'Urgent' only when necessary",
                        key="urgency"
                    )
                
                submitted = st.form_submit_button("📤 Submit Request")
            
            st.markdown('</div>', unsafe_allow_html=True)
            return submitted, {
                'requester': requester,
                'link': link,
                'quantity': quantity,
                'address': address,
                'attention': attention,
                'description': description,
                'classification': classification,
                'urgency': urgency
            }
    
    @staticmethod
    def show_email_preview(email_body):
        """Display email preview"""
        st.subheader("📧 Email Preview")
        st.markdown('<div class="email-preview">', unsafe_allow_html=True)
        st.text_area("", email_body, height=400)
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def show_summary_table(df):
        """Display purchase summary table"""
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("📋 Purchase Summary")
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def setup_sidebar():
        """Setup sidebar content"""
        st.sidebar.title("📊 Purchase Summary")
        st.sidebar.markdown("""
        <div class="instruction-box">
        Toggle the checkbox below to view all previous purchase requests.
        </div>
        """, unsafe_allow_html=True)
        
        return st.sidebar.checkbox("Show Purchase Summary")
