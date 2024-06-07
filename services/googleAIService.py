import google.generativeai as genai
from configparser import ConfigParser
import os
import json


def setup_genai():
    # Load configuration
    config = ConfigParser()
    config.read(os.path.expanduser('~/.myapp.cfg'))
    api_key = config.get('DEFAULT', 'GOOGLE_API_KEY', fallback=None)

    if not api_key:
        raise ValueError("Google API key is not set in the configuration file.")

    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

    return generation_config, safety_settings


def load_role(file_path):
    with open(file_path, 'r') as file:
        role = file.read().strip()
    return role


def load_examples(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        examples = json.load(file)
    return examples


def generate_google_ai_response(role, prompt):
    generation_config, safety_settings = setup_genai()

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=role,
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ],
            },
        ]
    )

    response = chat_session.send_message(prompt)
    return response.text


def get_solution_statement(examples, role, final_need):
    generation_config, safety_settings = setup_genai()

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=role,
    )

    prompt_parts = []

    for example in examples:
        prompt_parts.append(f"role: {role}")
        prompt_parts.append(f"need: {example['need']}")
        prompt_parts.append(f"solution: {example['solution']}")

    prompt_parts.append(f"role: {role}")
    prompt_parts.append(f"need: {final_need}")
    prompt_parts.append("solution: ")

    response = model.generate_content(prompt_parts)
    return response.text
