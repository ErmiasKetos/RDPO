import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if available
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Using environment variables directly.")

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
    
    # Get environment variables with fallback to empty string
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Client configuration
    CLIENT_CONFIG = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8501/"],
            "javascript_origins": ["http://localhost:8501"]
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
            error_message = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please set these environment variables either:\n"
                "1. In your environment directly using export/set\n"
                "2. In a .env file in the project root\n"
                "3. In the Streamlit Cloud secrets management\n"
            )
            logger.error(error_message)
            raise EnvironmentError(error_message)

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
