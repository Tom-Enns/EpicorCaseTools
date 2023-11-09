from services.documentService import extract_all_sections
from pprint import pprint

def test_extract_all_sections():
    file_path = "/Users/tomenns/Library/CloudStorage/OneDrive-SixSPartners/Documents/Cases/2473/Design - Case 2473 V1.docx"
    result = extract_all_sections(file_path)
    pprint(result)

if __name__ == "__main__":
    test_extract_all_sections()