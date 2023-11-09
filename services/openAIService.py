# openAIService.py

import openai
from configparser import ConfigParser
import os
import tiktoken
from services.loggingService import LoggingService

logger = LoggingService.get_logger(__name__)

class OpenAIService:
    def __init__(self):
        try:
            # Load configuration
            self.config = ConfigParser()
            self.config.read(os.path.expanduser('~/.myapp.cfg'))
            api_key = self.config.get('DEFAULT', 'OPENAI_APIKEY', fallback='')

            # Instantiate OpenAI client with API key
            self.openai_client = openai.OpenAI(api_key=api_key)

        except Exception as e:
            raise Exception(f"Failed to initialize OpenAIService: {str(e)}")

    def generate_embeddings(self, texts, model="text-embedding-ada-002"):
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        try:
            if not isinstance(texts, list):
                texts = [texts]

            #logger.info(f"DEBUG Generating embeddings for texts: {texts}")

            response = self.openai_client.embeddings.create(input=texts, model=model)

            #logger.info(f"DEBUG Embedding response object: {response}")

            embeddings = [embedding.embedding for embedding in response.data]

            # Log success
            logger.info(f"Successfully generated embeddings for {len(texts)} texts.")
            return embeddings

        except openai.APIError as e:
            logger.error(f"OpenAI API returned an API Error: {str(e)}")
            raise
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {str(e)}")
            raise
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API request exceeded rate limit: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    
    def calculate_token_count(self, text):
        logger.info("Calculating token count for text...")
        try:
            # Encode the text using tiktoken
            enc = tiktoken.encoding_for_model("gpt-4")
            tokens = enc.encode(text)
            token_count = len(tokens)
            logger.info(f"Calculated token count: {token_count} for text.")
            return token_count
        except Exception as e:
            logger.error(f"Error calculating token count: {str(e)}")
            raise
