import logging
import os


class LoggingService:
    @staticmethod
    def setup_logging():
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(level=logging.INFO, format=log_format)

        # Example for File Handler, if you want to log to a file
        log_directory = "logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        file_handler = logging.FileHandler(f"{log_directory}/app.log")
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    @staticmethod
    def get_logger(name):
        return logging.getLogger(name)
