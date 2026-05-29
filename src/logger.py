import logging
import os
from datetime import datetime

# log filename
LOG_FILE = f"{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}.log"

# logs directory
LOG_DIR = os.path.join(os.getcwd(), "logs")

# create logs directory
os.makedirs(LOG_DIR, exist_ok=True)

# full log path
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[%(asctime)s] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)