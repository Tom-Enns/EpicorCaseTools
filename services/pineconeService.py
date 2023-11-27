# pineconeService.py

import pinecone
from configparser import ConfigParser
import os
from services.loggingService import LoggingService

logger = LoggingService.get_logger(__name__)


class PineconeService:
    def __init__(self):
        try:
            # Load configuration
            self.config = ConfigParser()
            self.config.read(os.path.expanduser('~/.myapp.cfg'))

            self.api_key = self.config.get('DEFAULT', 'PINECONE_APIKEY', fallback='')
            self.environment = self.config.get('DEFAULT', 'PINECONE_ENVIRONMENT', fallback='')
            self.index_name = self.config.get('DEFAULT', 'PINECONE_DB', fallback='')
            
            pinecone.init(api_key=self.api_key, environment=self.environment)

            self._ensure_index_exists()
        except Exception as e:
            raise Exception(f"Failed to initialize PineconeService: {str(e)}")

    def _ensure_index_exists(self):
        logger.info(f"Ensuring index exists...")
        try:
            # Check if the index exists
            if self.index_name not in pinecone.list_indexes():
                # Create the index if it does not exist
                pinecone.create_index(name=self.index_name, dimension=1536, metric='cosine')
            self.index = pinecone.Index(self.index_name)
        except pinecone.PineconeException as e:
            raise Exception(f"An error occurred with Pinecone: {str(e)}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

    def upsert_embeddings(self, id_embedding_pairs):
        logger.info(f"Upserting {len(id_embedding_pairs)} embeddings...")
        try:
            self.index.upsert(vectors=id_embedding_pairs)
            # Log success
            logger.info(f"Successfully upserted {len(id_embedding_pairs)} embeddings.")
        except Exception as e:
            logger.error(f"Failed to upsert embeddings: {str(e)}")
            raise

    def query_similar_embeddings(self, query_embedding, top_k):
        logger.info(f"Querying similar embeddings...")
        try:
            results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
            logger.info(f"Successfully queried similar embeddings.")
            return results
        except Exception as e:
            logger.error(f"Failed to query similar embeddings: {str(e)}")
            raise