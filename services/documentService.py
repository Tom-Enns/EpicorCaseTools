import re

from typing import Optional, Union
from docx import Document
from .epicorService import EpicorService
import pypandoc
from services.loggingService import LoggingService

logger = LoggingService.get_logger(__name__)

epicor_service = EpicorService()


def convert_doc_to_text(file_path: str) -> str:
    # Convert the docx file to plain text with simple tables using pypandoc
    content = pypandoc.convert_file(file_path, "plain+simple_tables", format="docx")

    # Find the index of the specified text
    index = content.find('Terms\n\nDesign and Engineering Approach')

    # If the text is found, remove everything after it
    if index != -1:
        content = content[:index]

    print(content)
    return content


def extract_text_from_doc(file_path: str) -> str:
    doc = Document(file_path)
    return ' '.join([paragraph.text for paragraph in doc.paragraphs])


def extract_section(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1) if match else None


def extract_need(text: str) -> Optional[str]:
    return extract_section(text,
                           r"There should be a way for a supervisor to override this logic for exceptional packs\.”([\s\S]*?)Do you have technical requirements\?")


def extract_problem(text: str) -> Optional[str]:
    return extract_section(text,
                           r"We will develop your solution based\non this summary\.([\s\S]*?)Solution \(how we plan to solve your need\)")


def extract_solution(text: str) -> Optional[str]:
    return extract_section(text,
                           r"This is the solution Six S is proposing\.([\s\S]*?)Components These are the individual items that makeup the proposed solution\.")


def extract_unit_test(text: str) -> Optional[str]:
    return extract_section(text,
                           r"An acceptable solution will pass all of the tests below.\n([\s\S]*?)\nTerms\n\nDesign and Engineering Approach")


def extract_all_sections(file_path: str):
    text = extract_text_from_doc(file_path)
    need = extract_need(text)
    problem = extract_problem(text)
    solution = extract_solution(text)
    unit_test = extract_unit_test(text)
    return {'need': need, 'problem': problem, 'solution': solution, 'unit_test': unit_test}


def extract_sections_from_doc(x_file_ref_num_or_path: Union[int, str]):
    if isinstance(x_file_ref_num_or_path, int):
        file_path = epicor_service.download_file_by_xRefNum(x_file_ref_num_or_path)
        if not file_path:
            raise Exception('File could not be downloaded')
    else:
        file_path = x_file_ref_num_or_path

    return extract_all_sections(file_path)
