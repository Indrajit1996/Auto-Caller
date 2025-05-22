import os
import sys

from loguru import logger

from app.core.config import config


def configure_logger():
    # Remove default Loguru handlers to prevent duplicate logs
    logger.remove()

    # Define log directory
    log_directory = "/app/logs"
    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
            print(f"Log directory created at: {log_directory}")
        except OSError as e:
            print(f"Warning: Could not create log directory: {e}")

    # Define Loguru format for stderr (console)
    console_format = (
        "<level>{time:YYYY-MM-DD HH:mm:ss}</level> | "
        "<level>{level}</level> | "
        "<level>{extra[request_ip]}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Add stderr handler
    try:
        logger.add(
            sys.stderr,
            level=config.LOG_LEVEL,
            backtrace=True,
            colorize=True,
            format=console_format,
            enqueue=True,  # Thread-safe logging
            diagnose=True,  # Extended traceback formatting
        )
    except Exception as e:
        print(f"Error configuring stderr logger: {e}")

    # Configure file logging based on environment
    if config.ENABLE_FILE_LOGGING:
        # Define Loguru format for file logging
        file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[request_ip]} | {name}:{function}:{line} - {message}"

        # Add file handler with proper error handling
        try:
            logger.add(
                os.path.join(log_directory, "{time:YYYY-MM-DD}.log"),
                level=config.LOG_LEVEL,
                rotation="1 day",
                retention="7 days",
                compression="zip",  # Compress old logs
                backtrace=True,
                format=file_format,
                enqueue=True,  # Thread-safe logging
                catch=True,  # Catch exceptions that occur during logging
            )
        except Exception as e:
            print(f"Error configuring file logger: {e}")
            logger.add(
                sys.stderr,
                level="WARNING",
                format="File logging failed: {message}",
            )

    # Set default extra fields for all loggers
    logger.configure(extra={"request_ip": "N/A"})
