# epicorService.py

import os
import requests
import json
import base64

from typing import List, Dict, Union, Optional
from configparser import ConfigParser
from services.loggingService import LoggingService

logger = LoggingService.get_logger(__name__)

class CaseNotFoundError(Exception):
    pass

class EpicorService:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read(os.path.expanduser('~/.myapp.cfg'))

        self.BASE_URL = self.config.get('DEFAULT', 'BASE_URL', fallback=None)
        self.SIXS_API_KEY = self.config.get('DEFAULT', 'SIXS_API_KEY', fallback=None)
        self.SIXS_BASIC_AUTH = self.config.get('DEFAULT', 'SIXS_BASIC_AUTH', fallback=None)
        self.DOC_PATH = self.config.get('DEFAULT', 'DOC_PATH', fallback=None)

        self.ODATA_PATH = "/api/v2/odata/100" 
        self.EFX_PATH = "/api/v2/efx/100"  

        self.BASE_ODATA_URL = self.BASE_URL + self.ODATA_PATH if self.BASE_URL else None
        self.BASE_EFX_URL = self.BASE_URL + self.EFX_PATH if self.BASE_URL else None

        self.headers = {
            "X-API-Key": self.SIXS_API_KEY,
            "Authorization": self.SIXS_BASIC_AUTH,
            "Content-Type": "application/json; charset=utf-8",
        }

    def post_request(self, endpoint: str, data: Dict) -> Dict:
        response = requests.post(
            f"{self.BASE_URL}{endpoint}",
            headers=self.headers,
            data=json.dumps(data)
        )
        response_data = response.json()

        if response_data.get('Error'):
            raise Exception(response_data.get('Message'))

        return response_data

    def get_case_info(self, case_number: int) -> Dict:
        logger.info(f"Retrieving case info for case {case_number}...")
        try:
            response_data = self.post_request("/api/v2/efx/100/CaseDev/GetCaseStatus", {'CaseNum': case_number})
            logger.info(f"Case Info response is{len(response_data)} characters long")
            if response_data.get('Message') == 'Record not found':
                logger.warning(f"Case {case_number} not found.")
                raise CaseNotFoundError(f"No data found for case {case_number}")
            elif response_data.get('Error'):
                raise Exception(response_data.get('Message'))
            return response_data
        except requests.RequestException as e:
            logger.error(f"Request failed for get_case_info: {e}")
            raise
        except CaseNotFoundError as e:
            logger.warning(f"Case not found: {case_number}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_case_info for case {case_number}: {e}")
            raise

    def get_design_components(self, case_number: int) -> Dict:
        try:
            response_data = self.post_request("/api/v2/efx/100/CaseDev/GetCaseComponents", {'CaseNum': case_number})
            if response_data.get('Error'):
                raise Exception(response_data.get('Message'))
            design_components = response_data.get('CaseComponents', {}).get('DesignComponents', [])
            return design_components
        except Exception as error:
            print(f"Unable to retrieve components for case {case_number}: {str(error)}")
            return None

    def get_case_attachment_list(self, hd_case_num: int) -> Optional[List[Dict]]:
        try:
            response_data = self.post_request("/api/v2/odata/100/Erp.BO.HelpDeskSvc/GetByID", {'hdCaseNum': hd_case_num})
            if response_data.get('HDCaseAttch'):
                return [{'XFileRefNum': a['XFileRefNum'], 'FileName': a['FileName'], 'DocTypeID': a['DocTypeID']} for a in response_data['HDCaseAttch']]
            else:
                print(f"No attachments found for case {hd_case_num}")
                return None
        except Exception as error:
            raise Exception(f"Unable to retrieve attachments for case {hd_case_num}: {str(error)}")

    def update_design_components(self, case_number: int, design_components: List[Dict]) -> None:
        try:
            self.post_request("/api/v2/efx/100/CaseDev/AddDesignComponents", {'CaseNum': case_number, 'Components': {'ComponentData': design_components}})
        except Exception as error:
            raise Exception(f"Unable to update design components: {str(error)}")

    def update_case_design_info(self, case_design_data: Dict) -> None:
        try:
            self.post_request("/api/v2/efx/100/CaseDev/UpdateCaseDesign", case_design_data)
        except Exception as error:
            print(f"Unable to update case: {str(error)}")

    def download_file(self, x_file_ref_num: int) -> Optional[bytes]:
        try:
            response_data = self.post_request("/api/v2/efx/100/CaseDev/GetCaseAttachment", {'XFileRefNum': x_file_ref_num})
            if response_data.get('Attachment'):
                file_extension = response_data.get('FileExtension')
                base64_response = response_data.get('Attachment')
                byte_array = base64.b64decode(base64_response)
                return byte_array
            else:
                print(f"No file found for xFileRefNum: {x_file_ref_num}")
                return None
        except Exception as error:
            print(f"Error retrieving file: {str(error)}")
            return None

    def get_case_by_id(self, case_number: int) -> dict:

        try:
            response = requests.get(
                url=self.BASE_ODATA_URL + "/Erp.BO.HelpDeskSvc/GetByID",
                headers=self.headers,
                params={"hdCaseNum": case_number}
            )

            print(f"Status code: {response.status_code}")
            print(f"Status message: {response.text}")
            print(f"URL: {self.BASE_ODATA_URL}")

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

    def download_file(self, xFileRefNum: int) -> str:
        try:
            response = requests.post(
                url=self.BASE_ODATA_URL + "/Ice.BO.AttachmentSvc/DownloadFile",
                headers=self.headers,
                json={"xFileRefNum": xFileRefNum}
            )

            if 'returnObj' in response.json():
                return response.json()['returnObj']
            else:
                print(f'No file found for xFileRefNum: {xFileRefNum}')
                return None
        except Exception as e:
            print(f"Error retrieving file: {str(e)}")
            return None

    def save_attachment(self, case_number: int, filename: str, content: str):
        try:
            dir_path = os.path.join(self.DOC_PATH, str(case_number))
            os.makedirs(dir_path, exist_ok=True)
            full_path = os.path.join(dir_path, filename) 

            with open(full_path, 'wb') as f:
                f.write(base64.b64decode(content))

            print(f"Attachment saved at: {full_path}")
            return full_path
        except Exception as e:
            print(f"Error saving attachment: {str(e)}")
            return None

    def upload_document_logic(self, case_num, file_name, doc_type, encoded_content):
        try:
            response = requests.post(
                url=self.BASE_EFX_URL + "/CaseTools/UploadCaseAttachment",
                headers=self.headers, 
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
        




