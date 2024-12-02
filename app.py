import streamlit as st
from ui_components import UIComponents
from data_utils import DataManager
from drive_utils import DriveManager
from config import Config, logger

def main():
    # Setup page
    UIComponents.setup_page()
    UIComponents.show_header()
    UIComponents.show_instructions()

    # Initialize managers
    data_manager = DataManager()
    drive_manager = DriveManager()

    # Setup Google Drive authentication
    if not drive_manager.setup_authentication():
        st.warning("Google Drive integration is not available. Data will be stored locally.")

    # Render form
    submitted, form_inputs = UIComponents.render_form()

    if submitted:
        success, email_body, error = data_manager.handle_form_submission(form_inputs)
        if success:
            st.success("✅ Purchase request submitted successfully!")
            UIComponents.show_email_preview(email_body)
            
            # Save to Google Drive
            if drive_manager.save_purchase_data(Config.CSV_FILE):
                st.success("📁 Data saved to Google Drive")
            else:
                st.warning("⚠️ Failed to save data to Google Drive. Data stored locally.")
        else:
            st.error(f"❌ Error submitting request: {error}")

    # Show summary table
    if UIComponents.setup_sidebar():
        summary_data = data_manager.get_purchase_summary()
        UIComponents.show_summary_table(summary_data)

if __name__ == "__main__":
    main()
