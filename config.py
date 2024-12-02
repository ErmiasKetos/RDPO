import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base configuration
class Config:
    # App settings
    APP_NAME = "Purchase Order Request System"
    APP_ICON = "🛍️"
    
    # File paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"
    
    # Create necessary directories
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    # CSV file path
    CSV_FILE = DATA_DIR / "purchase_summary.csv"
    
    # Google Drive settings
    DRIVE_FOLDER_ID = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"
    
    # OAuth 2.0 configuration
    SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    # Client configuration
    CLIENT_CONFIG = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8501/"],  # Add your Streamlit Cloud URL here as well
            "javascript_origins": ["http://localhost:8501"]  # Add your Streamlit Cloud URL here as well
        }
    }
    
    # Form fields configuration
    CLASSIFICATION_CODES = [
        "6051 - Lab Supplies (including Chemicals)",
        "6052 - Testing (Outside Lab Validation)",
        "6055 - Parts & Tools",
        "6054 - Prototype",
        "6053 - Other"
    ]
    
    URGENCY_LEVELS = ["Normal", "Urgent"]
    
    DEFAULT_ADDRESS = "420 S Hillview Dr, Milpitas, CA 95035"
    DEFAULT_DEPARTMENT = "R&D"
    
    @classmethod
    def verify_env(cls):
        """Verify required environment variables"""
        required_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please create a .env file with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
            )
