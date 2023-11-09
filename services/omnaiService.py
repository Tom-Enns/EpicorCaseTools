import requests
from configparser import ConfigParser
import os

def ask_question(endpoint, question):
    # Load configuration
    config = ConfigParser()
    config.read(os.path.expanduser('~/.myapp.cfg'))

    base_url = "https://omnai.p.rapidapi.com/ask/"
    url = base_url + ("" if endpoint == "ask" else endpoint.lower())


    payload = {
        "openai_api_key": config.get('DEFAULT', 'OPENAI_APIKEY', fallback=''),
        "user_question": question,
        "openai_model": "gpt-4-1106-preview"
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "6eacc9132bmsh1ebe50d8cdb12f5p1b360bjsn576be198ebda",
        "X-RapidAPI-Host": "omnai.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
