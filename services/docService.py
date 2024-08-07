from typing import Optional, Union
from docx import Document
import re
from .epicorService import EpicorService


def extract_section(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_unit_test(text: str) -> Optional[str]:
    return extract_section(text,
                           r"An acceptable solution will pass all of the tests below.\n([\s\S]*?)\nTerms\n\nDesign and Engineering Approach")


def extract_solution(text: str) -> Optional[str]:
    return extract_section(text,
                           r"This is the solution Six S is proposing\.([\s\S]*?)Components These are the individual items that makeup the proposed solution\.")


def extract_problem(text: str) -> Optional[str]:
    return extract_section(text,
                           r"We will develop your solution based on this summary\.([\s\S]*?)Solution \(how we plan to solve your need\)")


def extract_need(text: str) -> Optional[str]:
    return extract_section(text,
                           r"There should be a way for a supervisor to override this logic for exceptional packs\.”([\s\S]*?)Do you have technical requirements\?")


class DocService:
    def __init__(self):
        self.epicor_service = EpicorService()

    def extract_all_sections_from_design_doc(self, x_file_ref_num_or_path: Union[int, str]):
        if isinstance(x_file_ref_num_or_path, int):
            file_path = self.epicor_service.download_file_by_xRefNum(x_file_ref_num_or_path)
            if not file_path:
                raise Exception('File could not be downloaded')
        else:
            file_path = x_file_ref_num_or_path

        # Load the document
        doc = Document(file_path)
        text = ' '.join([p.text for p in doc.paragraphs])

        # Extract sections
        need = extract_need(text)
        problem = extract_problem(text)
        solution = extract_solution(text)

        return {
            "Need": need,
            "Problem": problem,
            "Solution": solution,
        }
