import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from pathlib import Path
from config import Config, logger

class PurchaseData:
    def __init__(self):
        self.csv_file = Config.CSV_FILE
        self.columns = [
            'Requester', 
            'Request_DateTime', 
            'Link', 
            'Quantity',
            'Address', 
            'Attention_To', 
            'Department',
            'Description', 
            'Classification',
            'Urgency'
        ]
    
    @st.cache_data
    def load_data(self):
        """Load purchase data from CSV file"""
        try:
            if self.csv_file.exists():
                return pd.read_csv(self.csv_file)
            return pd.DataFrame(columns=self.columns)
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return pd.DataFrame(columns=self.columns)
    
    def save_data(self, data):
        """Save purchase data to CSV file"""
        try:
            df = pd.DataFrame(data)
            df.to_csv(self.csv_file, index=False)
            return True
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return False
    
    def add_purchase_request(self, form_data):
        """Add new purchase request to the dataset"""
        try:
            # Load existing data
            df = self.load_data()
            
            # Create new entry
            new_entry = pd.DataFrame([form_data])
            
            # Append new entry
            df = pd.concat([df, new_entry], ignore_index=True)
            
            # Save updated data
            return self.save_data(df)
            
        except Exception as e:
            logger.error(f"Error adding purchase request: {str(e)}")
            return False

class FormData:
    def __init__(self):
        self.pst_timezone = pytz.timezone('America/Los_Angeles')
    
    def validate_form(self, form_data):
        """Validate form input data"""
        required_fields = ['Requester', 'Link', 'Attention_To', 'Description']
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, None
    
    def process_form_data(self, form_inputs):
        """Process and format form data"""
        try:
            # Get current timestamp in PST
            current_time = datetime.now(self.pst_timezone)
            
            # Format form data
            form_data = {
                'Requester': form_inputs.get('requester', '').strip(),
                'Request_DateTime': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'Link': form_inputs.get('link', '').strip(),
                'Quantity': int(form_inputs.get('quantity', 1)),
                'Address': form_inputs.get('address', Config.DEFAULT_ADDRESS).strip(),
                'Attention_To': form_inputs.get('attention', '').strip(),
                'Department': Config.DEFAULT_DEPARTMENT,
                'Description': form_inputs.get('description', '').strip(),
                'Classification': form_inputs.get('classification', Config.CLASSIFICATION_CODES[0]),
                'Urgency': form_inputs.get('urgency', 'Normal')
            }
            
            # Validate form data
            is_valid, error_message = self.validate_form(form_data)
            if not is_valid:
                raise ValueError(error_message)
            
            return form_data
            
        except Exception as e:
            logger.error(f"Error processing form data: {str(e)}")
            raise
    
    def generate_email_body(self, form_data):
        """Generate email body from form data"""
        try:
            email_template = f"""
            Dear Ordering,

            R&D would like to order the following:

            - Requester: {form_data['Requester']}
            - Request Date and Time: {form_data['Request_DateTime']}
            - Link to Item(s): {form_data['Link']}
            - Quantity of Item(s): {form_data['Quantity']}
            - Shipment Address: {form_data['Address']}
            - Attention To: {form_data['Attention_To']}
            - Department: {form_data['Department']}
            - Description of Use: {form_data['Description']}
            - Classification Code: {form_data['Classification']}
            - Urgency: {form_data['Urgency']}

            Regards,
            {form_data['Requester']}
            """
            
            return email_template.strip()
            
        except Exception as e:
            logger.error(f"Error generating email body: {str(e)}")
            raise

class DataManager:
    def __init__(self):
        self.purchase_data = PurchaseData()
        self.form_data = FormData()
    
    def handle_form_submission(self, form_inputs):
        """Handle form submission and data processing"""
        try:
            # Process form data
            processed_data = self.form_data.process_form_data(form_inputs)
            
            # Add purchase request
            if not self.purchase_data.add_purchase_request(processed_data):
                raise ValueError("Failed to save purchase request")
            
            # Generate email body
            email_body = self.form_data.generate_email_body(processed_data)
            
            return True, email_body, None
            
        except Exception as e:
            logger.error(f"Form submission error: {str(e)}")
            return False, None, str(e)
    
    def get_purchase_summary(self):
        """Get purchase summary data"""
        try:
            df = self.purchase_data.load_data()
            return df.sort_values('Request_DateTime', ascending=False)
            
        except Exception as e:
            logger.error(f"Error getting purchase summary: {str(e)}")
            return pd.DataFrame()
