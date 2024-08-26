""" Application that provides functionality for the Telegram bot. """
import os
import yaml
import telebot
import logging.config

from omegaconf import OmegaConf


# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(OmegaConf.load("./src/telegram_bot/conf/logging_config.yaml"), resolve=True)

# Apply the logging configuration
logging.config.dictConfig(logging_config)

# Configure logging
logger = logging.getLogger(__name__)

class App:
    def __init__(self, parameter: str):
        self.parameter = parameter

    def run(self, message_text: str):
        logger.info(f"Received message: {message_text}")
        return f"Message text: {message_text}\nApp's parameter: {self.parameter}"
