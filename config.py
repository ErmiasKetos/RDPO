import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class Config:
    APP_NAME = "R&D Purchase Order System"
    APP_ICON = "🛒"
    DEFAULT_ADDRESS = "420 S Hillview Dr, Milpitas, CA 95035"
    DEFAULT_DEPARTMENT = "R&D"
    CLASSIFICATION_CODES = [
        "6051 - Lab Supplies (including Chemicals)",
        "6052 - Testing (Outside Lab Validation)",
        "6055 - Parts & Tools",
        "6054 - Prototype",
        "6053 - Other"
    ]
    URGENCY_LEVELS = ["Normal", "Urgent"]
    
    # File paths
    BASE_DIR = Path(__file__).resolve().parent
    CSV_FILE = BASE_DIR / "data" / "purchase_summary.csv"
    LOG_FILE = BASE_DIR / "logs" / "app.log"
    
    # Google API configuration
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    CLIENT_CONFIG = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8501/"]
        }
    }
    DRIVE_FOLDER_ID = "1VIbo7oRi7WcAMhzS55Ka1j9w7HqNY2EJ"

# Setup logging
logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom styles
CUSTOM_STYLES = """
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .instruction-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .form-section {
        background-color: #ffffff;
        border-radius: 5px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .required-field {
        color: red;
        margin-left: 5px;
    }
    .email-preview {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
    }
</style>
"""
