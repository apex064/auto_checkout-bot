import logging
import os
from datetime import datetime

def setup_logger():
    # Ensure "logs" directory exists
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped log file inside logs/
    log_filename = os.path.join(log_dir, f'autobot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

