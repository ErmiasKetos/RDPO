import streamlit as st
import pandas as pd
from datetime import datetime
import os.path
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pytz

import streamlit as st
from config import Config, logger, setup_logging
from drive_utils import DriveManager
from data_utils import DataManager
from ui_components import UIComponents

class PurchaseOrderApp:
    def __init__(self):
        self.ui = UIComponents()
        self.drive_manager = DriveManager()
        self.data_manager = DataManager()
    
    def run(self):
        """Run the Streamlit application"""
        try:
            # Setup logging
            setup_logging()
            
            # Verify environment variables
            Config.verify_env()
            
            # Setup page
            self.ui.setup_page()
            
            # Setup Google Drive authentication
            if not self.drive_manager.setup_authentication():
                return
            
            # Display header
            self.ui.show_header()
            
            # Show instructions
            self.ui.show_instructions()
            
            # Render form and get submission status
            submitted, form_inputs = self.ui.render_form()
            
            if submitted:
                self.handle_submission(form_inputs)
            
            # Setup sidebar and show summary if requested
            show_summary = self.ui.setup_sidebar()
            if show_summary:
                self.show_purchase_summary()
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"An error occurred: {str(e)}")
    
    def handle_submission(self, form_inputs):
        """Handle form submission"""
        try:
            # Process form submission
            success, email_body, error = self.data_manager.handle_form_submission(form_inputs)
            
            if success:
                # Save to Google Drive
                if self.drive_manager.save_purchase_data(Config.CSV_FILE):
                    st.markdown(
                        '<div class="success-message">✅ Purchase request submitted successfully!</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Show email preview
                    self.ui.show_email_preview(email_body)
                else:
                    raise Exception("Failed to save to Google Drive")
            else:
                raise Exception(error or "Failed to process form submission")
                
        except Exception as e:
            logger.error(f"Submission error: {str(e)}")
            st.markdown(
                f'<div class="error-message">❌ Error: {str(e)}</div>',
                unsafe_allow_html=True
            )
    
    def show_purchase_summary(self):
        """Display purchase summary"""
        try:
            df = self.data_manager.get_purchase_summary()
            self.ui.show_summary_table(df)
            
        except Exception as e:
            logger.error(f"Summary display error: {str(e)}")
            st.error(f"Error displaying summary: {str(e)}")

def main():
    app = PurchaseOrderApp()
    app.run()

if __name__ == "__main__":
    main()
