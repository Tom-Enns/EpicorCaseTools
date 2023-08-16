import requests
import os
import base64
from configparser import ConfigParser

config = ConfigParser()
config.read(os.path.expanduser('~/.myapp.cfg'))

BASE_URL = config.get('DEFAULT', 'BASE_URL', fallback=None)
sixs_api_key = config.get('DEFAULT', 'SIXS_API_KEY', fallback=None)
sixs_basic_auth = config.get('DEFAULT', 'SIXS_BASIC_AUTH', fallback=None)
DOC_PATH = config.get('DEFAULT', 'DOC_PATH', fallback=None)

ODATA_PATH = "/api/v2/odata/100" 
EFX_PATH = "/api/v2/efx/100"  

BASE_ODATA_URL = BASE_URL + ODATA_PATH if BASE_URL else None
BASE_EFX_URL = BASE_URL + EFX_PATH if BASE_URL else None

def get_case_by_id(case_number: int) -> dict:
    print(f"API Key: {sixs_api_key}")
    headers = {'api-key': sixs_api_key}
    print(f"Headers: {headers}")

    try:
        response = requests.get(
            url=BASE_ODATA_URL + "/Erp.BO.HelpDeskSvc/GetByID",
            headers={
                "X-API-Key": sixs_api_key,
                "Authorization": sixs_basic_auth,
                "Content-Type": "application/json; charset=utf-8",
            },
            params={"hdCaseNum": case_number}
        )

        # Print the status code
        print(f"Status code: {response.status_code}")
        print(f"Status message: {response.text}")
        print(f"URL: {BASE_ODATA_URL}")

        if response.json():
            if 'returnObj' in response.json():
                return response.json()['returnObj']['HDCaseAttch']
            else:
                print(f"'returnObj' not found in the response for case number: {case_number}")
                return None
        else:
            print(f'No case found for case number: {case_number}')
            return None
    except Exception as e:
        print(f"Error retrieving case: {str(e)}")
        return None

def download_file(xFileRefNum: int) -> str:
    try:
        response = requests.post(
            url=BASE_ODATA_URL + "/Ice.BO.AttachmentSvc/DownloadFile",
            headers={
                "X-API-Key": sixs_api_key,
                "Authorization": sixs_basic_auth,
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"xFileRefNum": xFileRefNum}  # Send xFileRefNum in the request body
        )

        if 'returnObj' in response.json():
            return response.json()['returnObj']
        else:
            print(f'No file found for xFileRefNum: {xFileRefNum}')
            return None
    except Exception as e:
        print(f"Error retrieving file: {str(e)}")
        return None

def save_attachment(case_number: int, filename: str, content: str):
    try:
        dir_path = os.path.join(DOC_PATH, str(case_number))
        os.makedirs(dir_path, exist_ok=True)
        full_path = os.path.join(dir_path, filename) 

        with open(full_path, 'wb') as f:
            f.write(base64.b64decode(content))

        print(f"Attachment saved at: {full_path}")  # Print the file path
        return full_path
    except Exception as e:
        print(f"Error saving attachment: {str(e)}")
        return None

def upload_document_logic(case_num, file_name, doc_type, encoded_content):
    try:
        response = requests.post(
            url=BASE_EFX_URL + "/CaseTools/UploadCaseAttachment",
            headers={
                "X-API-Key": sixs_api_key,
                "Authorization": sixs_basic_auth,
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "CaseNum": int(case_num),
                "Attachments": {
                    "Files": [
                        {
                            "DocType": doc_type,
                            "FileBytes": encoded_content,
                            "FileName": file_name
                        }
                    ]
                }
            }
        )
        return response
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed:', e)
        return None