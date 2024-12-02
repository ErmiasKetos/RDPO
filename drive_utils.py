import streamlit as st
import logging
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import Config, logger

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
    
    def init_oauth_flow(self):
        """Initialize OAuth 2.0 flow"""
        try:
            flow = Flow.from_client_config(
                Config.CLIENT_CONFIG,
                scopes=Config.SCOPES,
                redirect_uri=Config.CLIENT_CONFIG['web']['redirect_uris'][0]
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return flow, auth_url
            
        except Exception as e:
            logger.error(f"OAuth flow initialization error: {str(e)}")
            raise
    
    def handle_auth_callback(self, flow, code):
        """Handle OAuth callback and token generation"""
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Store credentials in session state
            st.session_state.google_auth_credentials = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Auth callback error: {str(e)}")
            return False
    
    def initialize_service(self):
        """Initialize Google Drive API service"""
        try:
            if 'google_auth_credentials' not in st.session_state:
                return None
            
            credentials = Credentials.from_authorized_user_info(
                st.session_state.google_auth_credentials,
                Config.SCOPES
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            return self.service
            
        except Exception as e:
            logger.error(f"Service initialization error: {str(e)}")
            return None
    
    def check_file_exists(self, filename, folder_id=None):
        """Check if file exists in Google Drive"""
        try:
            if not self.service:
                return None
            
            query = f"name='{filename}'"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            logger.error(f"File check error: {str(e)}")
            return None
    
    def save_file(self, file_path, folder_id=None):
        """Save or update file in Google Drive"""
        try:
            if not self.service:
                raise ValueError("Drive service not initialized")
            
            folder_id = folder_id or Config.DRIVE_FOLDER_ID
            filename = file_path.name
            
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='text/csv',
                resumable=True
            )
            
            # Check if file exists
            existing_files = self.check_file_exists(filename, folder_id)
            
            if existing_files:
                # Update existing file
                file_id = existing_files[0]['id']
                file = self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                logger.info(f"Updated file: {filename} ({file.get('id')})")
            else:
                # Create new file
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"Created file: {filename} ({file.get('id')})")
            
            return True
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            return False
    
    def test_connection(self):
        """Test Google Drive API connection"""
        try:
            if not self.service:
                return False
            
            # Test API call
            self.service.files().list(pageSize=1).execute()
            return True
            
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            return False

class DriveManager:
    def __init__(self):
        self.drive_service = GoogleDriveService()
    
    def setup_authentication(self):
        """Setup Google Drive authentication"""
        try:
            # Check existing service
            if self.drive_service.initialize_service():
                return True
            
            # Initialize new OAuth flow
            flow, auth_url = self.drive_service.init_oauth_flow()
            
            # Display authentication UI
            st.markdown("""
                <div class="instruction-box">
                    <h3>Google Drive Authentication Required</h3>
                    <p>Please authenticate to enable Google Drive integration.</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Login with Google"):
                st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                st.stop()
            
            # Check for authorization code
            query_params = st.experimental_get_query_params()
            if 'code' in query_params:
                if self.drive_service.handle_auth_callback(flow, query_params['code'][0]):
                    st.success("✅ Authentication successful!")
                    # Clear query parameters
                    st.experimental_set_query_params()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication setup error: {str(e)}")
            st.error(f"Authentication error: {str(e)}")
            return False
    
    def save_purchase_data(self, file_path):
        """Save purchase data to Google Drive"""
        try:
            if not self.drive_service.test_connection():
                raise ValueError("Not connected to Google Drive")
            
            if self.drive_service.save_file(file_path):
                return True
            
            raise ValueError("Failed to save file to Google Drive")
            
        except Exception as e:
            logger.error(f"Save purchase data error: {str(e)}")
            st.error(f"Error saving data: {str(e)}")
            return False
