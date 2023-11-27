import requests
import os
from configparser import ConfigParser
from services.loggingService import LoggingService
import logging

logger = LoggingService.get_logger(__name__)
logger.setLevel(logging.DEBUG)

def ask_question(endpoint, question):
    # Load configuration
    config = ConfigParser()
    config.read(os.path.expanduser('~/.myapp.cfg'))

    base_url = "https://omnai.p.rapidapi.com/ask/"
    url = base_url + ("" if endpoint == "ask" else endpoint.lower())

    payload = {
        "openai_api_key": config.get('DEFAULT', 'OPENAI_APIKEY', fallback=''),
        "user_question": question,
        "openai_model": "gpt-4-1106-preview",
        "prompt": "",
        "dataset_size": 20,
        "openai_model_temp": 0.3
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "6eacc9132bmsh1ebe50d8cdb12f5p1b360bjsn576be198ebda",
        "X-RapidAPI-Host": "omnai.p.rapidapi.com"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises a HTTPError if the response was unsuccessful
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

    logger.debug(f"Response: {response.json()}")
    return response.json()