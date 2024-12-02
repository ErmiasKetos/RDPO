import os
import logging
from pathlib import Path

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
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["https://pybhayw4ybcvgk78gheuna.streamlit.app/"],
            "javascript_origins": ["https://pybhayw4ybcvgk78gheuna.streamlit.app/"]
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
    
    # Verify required environment variables
    @classmethod
    def verify_env(cls):
        required_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

# CSS styles for the app
CUSTOM_STYLES = """
<style>
    .main {
        padding: 2rem;
        border-radius: 10px;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.75rem;
        border-radius: 5px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .success-message {
        padding: 1rem;
        background-color: #dff0d8;
        border: 1px solid #d6e9c6;
        border-radius: 4px;
        color: #3c763d;
        margin-bottom: 1rem;
    }
    .error-message {
        padding: 1rem;
        background-color: #f2dede;
        border: 1px solid #ebccd1;
        border-radius: 4px;
        color: #a94442;
        margin-bottom: 1rem;
    }
    .instruction-box {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 4px;
    }
    .required-field {
        color: red;
        margin-left: 4px;
    }
    .form-section {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .email-preview {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .data-table {
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-indicator.success {
        background-color: #4CAF50;
    }
    .status-indicator.warning {
        background-color: #ff9800;
    }
    .status-indicator.error {
        background-color: #f44336;
    }
</style>
"""

# Helper functions
def setup_logging():
    """Configure logging settings"""
    log_file = Config.LOG_DIR / "app.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger
