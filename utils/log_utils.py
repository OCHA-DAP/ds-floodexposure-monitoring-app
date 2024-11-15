import logging


def setup_logging():
    """Initialize basic logging configuration"""
    logger = logging.getLogger("dash")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


def get_logger(module_name):
    """Get a logger for a specific module"""
    return logging.getLogger(f"dash.{module_name}")
