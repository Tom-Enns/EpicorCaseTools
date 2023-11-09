# caseService.py

from typing import List, Dict, Optional, Iterable
from services.epicorService import EpicorService, CaseNotFoundError
from services.embeddingsService import EmbeddingsGeneratorService
from services.loggingService import LoggingService

logger = LoggingService.get_logger(__name__)


class CaseDetails:
    def __init__(self, case_number: int, epicor_service: EpicorService):
        self.case_number = case_number
        self.epicor_service = epicor_service
        self.case_info = None
        self.design_components = None
        self.tests = None

    def retrieve_case_info(self):
        try:
            self.case_info = self.epicor_service.get_case_info(self.case_number)
        except CaseNotFoundError as e:
            logger.warning(f"Case {self.case_number} not found: {e}")
            return  # Return from the function instead of re-throwing the exception
        except Exception as e:
            logger.error(f"Failed to retrieve case info for case {self.case_number}: {e}")
            raise Exception(f"Error retrieving case info for case {self.case_number}: {e}")

    def retrieve_design_components(self):
        try:
            self.design_components = self.epicor_service.get_design_components(self.case_number)
        except Exception as e:
            raise Exception(f"Failed to retrieve design components for case {self.case_number}: {str(e)}")

    def retrieve_tests(self):
        # Add your implementation here
        pass

    def retrieve_all(self):
        try:
            self.retrieve_case_info()
        except CaseNotFoundError:
            return
        self.retrieve_design_components()
        self.retrieve_tests()



class CaseService:
    def __init__(self):
        self.epicor_service = EpicorService()
        self.embeddings_service = EmbeddingsGeneratorService()

    def embed_cases(self, case_numbers: Iterable[int]):
        logger.info(f"Embedding cases {case_numbers}...")
        for case_number in case_numbers:
            try:
                self.embed_case(case_number)
            except CaseNotFoundError as e:
                logger.warning(f"Skipping case {case_number}: {e}")
                continue  # Proceed to the next case
            except Exception as e:
                logger.error(f"Error in embedding case {case_number}: {e}")
                continue  # This line will continue to the next case

    def embed_case(self, case_number: int):
        logger.info(f"Embedding case {case_number}...")
        try:
            case_details = CaseDetails(case_number, self.epicor_service)
            case_details.retrieve_all()

            if case_details.case_info is None:
                return  # Skip if no case info is found

            # List to store texts and their corresponding metadata
            texts_to_embed_with_metadata = []

            # Mapping texts to their component types
            texts_and_types = {
                "Need": case_details.case_info.get('DesignNeed'),
                "Problem": case_details.case_info.get('DesignProblem'),
                "Solution": case_details.case_info.get('DesignSolution'),
                "Components": ', '.join([f"{component.get('ComponentName', '')}, {component.get('ComponentType', '')}, {component.get('ComponentPurpose', '')}" for component in case_details.design_components])
            }

            for component_type, text in texts_and_types.items():
                if text:
                    metadata = {"ItemType": "Case", "CaseNum": case_number, "ComponentType": component_type}
                    texts_to_embed_with_metadata.append((text, metadata))

            # Pass the list of texts and metadata to the embeddings service
            if texts_to_embed_with_metadata:
                self.embeddings_service.generate_and_store_embeddings(texts_to_embed_with_metadata)
                logger.info(f"Successfully embedded texts for case {case_number}")

        except CaseNotFoundError as e:
            logger.warning(f"Case {case_number} not found: {e}")
            return
        except Exception as e:
            logger.error(f"Failed to embed case {case_number}: {e}")
            raise Exception(f"Failed to embed case {case_number}: {e}")


    def embed_case_components(self, case_number: int, design_components: List[Dict]):
        logger.info(f"Embedding components for case {case_number}...")
        for component in design_components:
            component_type = component.get('ComponentType')
            text_to_embed = component.get('Description', '')
            if text_to_embed:
                metadata = {"ItemType": "Case", "CaseNum": case_number, "Component": component_type}
                self.embeddings_service.generate_and_store_embeddings([(text_to_embed, metadata)])
                logger.info(f"Successfully embedded component {component_type} for case {case_number}")