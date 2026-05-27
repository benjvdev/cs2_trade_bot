import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Ensure logs directory exists relative to project root
    # We use a path that works regardless of where the script is run from
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(project_root, "logs")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("cs2_bot")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        # Console Handler
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

        # File Handler
        f_handler = RotatingFileHandler(
            os.path.join(log_dir, "bot.log"),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)

    return logger

bot_logger = setup_logger()
