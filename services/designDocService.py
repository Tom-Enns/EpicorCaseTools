import docx
import shutil

def get_element_value(element, tag, attribute='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'):
    found = element.find(f'.//w:{tag}', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    return found.get(attribute) if found is not None else None

def get_text_from_element(element):
    text = ""
    for node in element.iter():
        if node.tag.endswith('}t') and node.text:
            text += node.text
    return text.strip()

def extract_table_data(table):
    table_data = []
    for row in table.findall('.//w:tr', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
        row_data = []
        for cell in row.findall('.//w:tc', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
            cell_text = ''
            for paragraph in cell.findall('.//w:p', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                for run in paragraph.findall('.//w:r', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                    for text in run.findall('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                        if text.text:
                            cell_text += text.text
            row_data.append(cell_text.strip())
        table_data.append(row_data)
    return table_data

def extract_content_control_data(element):
    title = get_element_value(element, 'alias')
    if title == "ComponentsGrid":
        table = element.find('.//w:tbl', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        return (title, extract_table_data(table)) if table is not None else (title, [])
    text_content = get_text_from_element(element)
    return (title, text_content if text_content is not None else "")

def extract_design_data(doc_path):
    doc = docx.Document(doc_path)
    data = {}
    for element in doc.element.findall('.//w:sdt', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
        title, content = extract_content_control_data(element)
        data[title] = content
    return data

def clear_existing_content(sdt_content):
    print("Clearing existing content.")
    for child in list(sdt_content):
        sdt_content.remove(child)

def update_rich_text(element, text, field_title):
    print(f"Updating rich text field '{field_title}' with: {text}")
    sdt_content = element.find('.//w:sdtContent', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    if sdt_content is not None:
        clear_existing_content(sdt_content)
        new_paragraph = docx.oxml.shared.OxmlElement('w:p')
        new_run = docx.oxml.shared.OxmlElement('w:r')
        new_text_element = docx.oxml.shared.OxmlElement('w:t')
        new_text_element.text = text
        new_run.append(new_text_element)
        new_paragraph.append(new_run)
        sdt_content.append(new_paragraph)

def update_plain_text(element, text):
    print(f"Updating plain text field with: {text}")
    sdt_content = element.find('.//w:sdtContent', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    if sdt_content is not None:
        text_element = sdt_content.find('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        if text_element is not None:
            text_element.text = text

def update_table(element, table_data):
    table = element.find('.//w:tbl', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    if table is not None:
        rows = table.findall('.//w:tr', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        for row_index, row in enumerate(rows):
            if row_index == 0:
                continue  # Skip the first row (headers)
            if row_index - 1 < len(table_data):
                for cell_index, cell in enumerate(row.findall('.//w:tc', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})):
                    if cell_index < len(table_data[row_index - 1]):
                        cell_text = table_data[row_index - 1][cell_index]
                        paragraph = cell.find('.//w:p', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                        if paragraph is None:
                            paragraph = docx.oxml.shared.OxmlElement('w:p')
                            cell.append(paragraph)
                        run = paragraph.find('.//w:r', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                        if run is None:
                            run = docx.oxml.shared.OxmlElement('w:r')
                            paragraph.append(run)
                        text_element = run.find('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                        if text_element is None:
                            text_element = docx.oxml.shared.OxmlElement('w:t')
                            run.append(text_element)
                        text_element.text = cell_text

def write_design_data(original_doc_path, updated_doc_path, data):
    try:
        # Copy the original document to create a working copy
        shutil.copyfile(original_doc_path, updated_doc_path)
        doc = docx.Document(updated_doc_path)
        for element in doc.element.findall('.//w:sdt', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
            title = get_element_value(element, 'alias')
            if title in data:
                if isinstance(data[title], list):
                    if title == "ComponentsGrid":
                        print(f"Updating {title} with {data[title]}")
                        update_table(element, data[title])
                else:
                    if title in ["SolutionStatement"]:
                        print(f"Updating {title} with {data[title]}")
                        update_rich_text(element, data[title], title)
                    else:
                        print(f"Updating {title} with {data[title]}")
                        update_plain_text(element, data[title])
        doc.save(updated_doc_path)
        print("Data written successfully to the document.")
    except PermissionError:
        print("Failed to write data. The document is currently open. Please close it and try again.")
    except Exception as e:
        print(f"An error occurred while writing data: {e}")

# Example usage
original_doc_path = '/Users/tomenns/Downloads/devDDtest.docx'
updated_doc_path = '/Users/tomenns/Downloads/updated_devDDtest.docx'

# Extract data from the document
design_data = extract_design_data(original_doc_path)
print("Extracted data:")
print(design_data)

# Modify the extracted data for testing only, to be removed in final version.
design_data['SolutionStatement'] = 'This is an updated solution summary.'
design_data['ComponentsGrid'] = [['Component 1', 'Type 1', 'Purpose 1'], ['Component 2', 'Type 2', 'Purpose 2']]
design_data['CaseNum'] = '126657745745745'
design_data['QuoteNum'] = 'ABC123'
design_data['Company'] = 'asdfasdfasdf'
design_data['Status'] = '99.99'
design_data['Title'] = 'TitleGOesHERERERERE'
design_data['Database'] = 'TestDB'
design_data['Author'] = 'John Doe'
design_data['Hosting'] = 'Cloud'
design_data['RefreshRequested'] = 'Yes'
design_data['UI'] = 'Web'
design_data['OtherUI'] = 'Mobile'
design_data['DesignNeed'] = 'Updated Need.'
design_data['ProblemSummary'] = 'Updated Problem Summary'

# Write the modified data back to the document (updating all fields)
write_design_data(original_doc_path, updated_doc_path, design_data)
