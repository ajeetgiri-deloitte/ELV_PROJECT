import base64
import json
import os
import subprocess
from datetime import datetime

from starlette.responses import RedirectResponse

from scripts.constants import app_configurations
from scripts.constants.app_configurations import emudra_api_path, certificate, jarPath, digital_signed_files, \
    ds_minio_path
from scripts.constants.app_constants import TableName, Routes, DigitalSignature
from scripts.core.digital_signature.handlers.updated_certificate import CERTIFICATE_GENERATION
from scripts.logging.logger import logger
from scripts.utils.db_utility import DBUtility
from scripts.utils.minio_utility import S3Utility


class DigitalSignatureHandler:
    def __init__(self):
        self.db_conn = DBUtility()

    def gate_way_response(self, return_value, return_status, reference_number):
        try:
            logger.info(f"Initiated saving digital signature")
            logger.debug(f"Return value : {return_value}")
            logger.debug(f"Return status : {return_status}")
            logger.debug(f"Reference number : {reference_number}")
            company_details = self.fetch_company_details(ref_no=reference_number)
            signed_by = company_details.get('created_by')
            signed_user_type = self.fetch_user_type(signed_user=signed_by)
            logger.debug(f"Singed user type : {signed_user_type}")
            directory_path = os.path.join(emudra_api_path, reference_number)
            # Call decrypt jar file
            arg1 = "Decrypt"
            arg2 = os.path.join(directory_path, "Encrypted_Signed_Data.txt")
            arg3 = os.path.join(directory_path, "session_key.txt")
            arg4 = os.path.join(directory_path, "Decrypted_Signed_Data.txt")
            digital_singed_file_path = os.path.join(digital_signed_files, f'{reference_number}_signed.pdf')
            minio_file_path = f"{ds_minio_path}/PIBO/{signed_by}/signed/{reference_number}_signed.pdf"

            if return_status.lower() == "success" and return_value != '':
                self.create_file(file_path=arg2, content=return_value)
                self.create_file(file_path=arg4, content="")

                logger.info("Executing jar to decrypt the certificate contents")
                subprocess.getoutput(f"java -jar {jarPath}" + (
                    ' '.join([arg1, arg2, arg3, arg4])))
                b64 = self.read_file_content(file_path=arg4)

                # Decode the Base64 string, making sure that it contains only valid characters
                decode_value = base64.b64decode(b64, validate=True)
                if decode_value[0:4] != b'%PDF':
                    raise ValueError('Missing the PDF file signature')

                with open(digital_singed_file_path, 'wb') as output_file:
                    output_file.write(decode_value)

                S3Utility().upload_file_to_s3(digital_singed_file_path, minio_file_path)
                self.update_application_details(ref_no=reference_number, cert_path=minio_file_path)
                if signed_user_type.lower() == 'cpcb':
                    url = f"{app_configurations.MODULE_BASE_URL}/#/epr/pibo-applications/bo/success"
                elif signed_user_type.lower() == 'spcb':
                    url = f"{app_configurations.MODULE_BASE_URL}/#/epr/spcb-applications/bo/success"
                else:
                    raise Exception("Invalid user type")
                logger.debug(f"Redirection URL after digital sign -----> {url}")
                return RedirectResponse(url,
                                        status_code=302)
            return {"status": "Failure", "message": "Unable to save digitally signed file"}
        except Exception as e:
            logger.info(f"Exception saving digitally signed file : {str(e)}")
            return {"status": "Failure", "message": "Unable to save digitally signed file"}

    def sign_digitally(self, request_json, user_info, request):
        try:
            request_domain = request.headers.get('Origin')
            user_id = user_info['user_id']
            result = self.fetch_logged_in_user_details(user_id=user_id)
            signed_by = result['user_fullname']
            designation = result['user_designation']
            logger.debug(f"Logged in user : {signed_by}")

            company_id = request_json.company_id
            application_id = request_json.application_id
            request_id = request_json.request_id
            logger.debug(f"Company id : {company_id}")
            logger.debug(f"Application id : {application_id}")
            logger.debug(f"Request id : {request_id}")
            reference_no = self.fetch_reference_number(company_id=company_id, application_id=application_id)

            logger.info("Fetching PDF content")
            response_json = CERTIFICATE_GENERATION().cpcb_certificate_generation(company_id=company_id,
                                                                                 user_id=user_id,
                                                                                 reference_no=reference_no,
                                                                                 designation=designation,
                                                                                 application_id=application_id,
                                                                                 request_id=request_id)

            logger.debug(f"Reference number generated: {reference_no}")
            file_data = ''
            if response_json:
                file_data = response_json['data']['fileData']
            data_dir = emudra_api_path + reference_no
            logger.debug(f"Data Dir for digital sign ----> {data_dir}")

            arg1 = "Encrypt"
            arg2 = os.path.normpath(os.path.join(data_dir, "Json_Data.txt"))
            arg3 = os.path.join(data_dir, "session_key.txt")
            arg4 = os.path.join(data_dir, "encrypted_session_key.txt")
            arg5 = os.path.join(data_dir, "encrypted_json_data.txt")
            arg6 = os.path.join(data_dir, "encrypted_hash_of_json_data.txt")

            arg7 = certificate

            logger.debug(f"Check if the directory exists : {data_dir}")
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=False)
            logger.debug("Data dir created successfully")

            empty_txt = ''
            # Creating the Files to store Encrypted Data
            self.create_file(file_path=arg3, content=empty_txt)
            self.create_file(file_path=arg4, content=empty_txt)
            self.create_file(file_path=arg5, content=empty_txt)
            self.create_file(file_path=arg6, content=empty_txt)

            json_input = {
                "Name": signed_by,
                "FileType": "PDF",
                "SignatureType": 1,
                "SelectPage": "ALL",
                "SignaturePosition": "Bottom-Right",
                "AuthToken": "b4a1180b-4001-446d-9f20-3e80d1f0f2ba",
                "File": file_data,
                "PageNumber": "",
                "No_of_pages": 0,
                "PreviewRequired": True,
                "SUrl": f"{request_domain}{Routes.digital_signature_base_url}{DigitalSignature.gateway_response}?ngsw-bypass=true",
                "FUrl": "/Error",
                "CUrl": "/Cancel",
                "ReferenceNumber": reference_no,
                "IsCompressed": False,
                "IsCosign": False,
                "IsCustomized": False
            }
            logger.debug(
                f"------->Url,{request_domain}{Routes.digital_signature_base_url}{DigitalSignature.gateway_response}")
            with open(arg2, "w") as outfile:
                json.dump(json_input, outfile)

            try:
                logger.info("Executing JAR now ..")
                command = f"java -jar {jarPath}" + (
                    ' '.join([arg1, arg2, arg3, arg4, arg5, arg6, arg7]))
                logger.debug(f"Digital Sign JAR Command being executed ---> {command}")
                subprocess.getoutput(command)
            except Exception as je:
                logger.error(f"DSign JAR Execution error : {str(je)}")
                raise Exception("DSign JAR Execution error")

            # call gateway and return response to api
            post_names = ["Parameter1", "Parameter2", "Parameter3"]
            encrypted_session_key = self.read_file_content(file_path=arg4)
            encrypted_json_data = self.read_file_content(file_path=arg5)
            encrypted_hash_of_json_data = self.read_file_content(file_path=arg6)
            post_values = [encrypted_session_key, encrypted_json_data, encrypted_hash_of_json_data]
            c = 0
            dup_dict = dict()
            for name in post_names:
                dup_dict[str(c)] = {"key": name, "value": post_values[c]}
                c += 1
            final_dict = {"data": dup_dict}
            self.update_digital_signature_status(company_id=company_id, application_id=application_id,
                                                 request_id=request_id,
                                                 ref_no=reference_no, signed_by=user_id,
                                                 application_type=0)
            return final_dict
        except Exception as e:
            logger.exception(f"Exception Due to {e}")
            return {"status": "Failed", "message": f"Exception  Due to {e}"}

    def fetch_logged_in_user_details(self, user_id):
        try:
            logger.info("Fetching logged in user details")
            select_query = f"""select user_fullname,user_designation from {TableName.admin} where user_id = {user_id}"""
            flag, user_info = self.db_conn.select_mysql_fetchone(select_query)
            return user_info
        except Exception as e:
            logger.error(f"Error occurred while fetching logged in user details : {str(e)}", exc_info=True)
            raise Exception("Failed to fetch logged in user details")

    @staticmethod
    def fetch_reference_number(company_id, application_id):
        try:
            logger.info("Generating reference number")
            ref_number_format = f"EPR-{company_id}-{application_id}-{int(datetime.now().timestamp())}"
            return ref_number_format
        except Exception as e:
            logger.error(f"Error occurred while generating reference number : {str(e)}", exc_info=True)
            raise Exception("Failed to generating reference number")

    @staticmethod
    def create_file(file_path, content):
        try:
            logger.info(f"Creating file : {file_path}")
            with open(file_path, 'w') as data_file:
                data_file.write(content)
        except Exception as e:
            logger.error(f"Error occurred while creating file : {str(e)}")
            raise Exception("Failed to create file ")

    @staticmethod
    def read_file_content(file_path):
        try:
            logger.info(f"Reading file : {file_path}")
            with open(file_path, 'rt') as data_file:
                data = data_file.read()
                return data
        except Exception as e:
            logger.error(f"Error occurred while creating file : {str(e)}")
            raise Exception("Failed to create file ")

    def update_digital_signature_status(self, company_id, application_id, request_id, ref_no, signed_by,
                                        application_type):
        try:
            logger.info("Update digital sign status")
            insert_query = f"INSERT INTO dsign_logs " \
                           f"(company_id, application_id, request_id, reference_no, created_by, created_at," \
                           f"application_type) " \
                           f"VALUES ('{company_id}', '{application_id}', '{request_id}', '{ref_no}', '{signed_by}', " \
                           f"'{datetime.now()}','{application_type}')"
            status = self.db_conn.insert_mysql_table(insert_query)
            logger.debug(f"Digital signature insert status : {status}")
            if not status:
                logger.debug("Failed to insert sign log to table")
                raise Exception("Failed to insert digital sign status to db")
        except Exception as e:
            logger.error(f"Error occurred while creating file : {str(e)}")
            raise Exception("Failed to create file ")

    def fetch_company_details(self, ref_no):
        try:
            logger.info("Fetch company details")
            select_query = f"select * from dsign_logs where reference_no = '{ref_no}'"
            status, company_details = self.db_conn.select_mysql_fetchone(select_query)
            if not status:
                logger.debug("Failed to fetch company details")
                raise Exception("Failed to fetch company details")
            return company_details
        except Exception as e:
            logger.error(f"Error occurred while fetching company details: {str(e)}")
            raise Exception("Error occurred while fetching company details")

    def update_application_details(self, ref_no, cert_path):
        try:
            logger.info("update application status for digital signature")
            company_details = self.fetch_company_details(ref_no=ref_no)
            company_id = company_details.get('company_id')
            application_id = company_details.get('application_id')
            signed_by = company_details.get('created_by')
            request_id = company_details.get('request_id')
            update_digital_signature = f"update {TableName.pibo_application_requests} " \
                                       f"set digital_sign_status = '1', " \
                                       f"cert_path = '{cert_path}', " \
                                       f"signed_by = {signed_by} " \
                                       f"where company_id = '{company_id}'and " \
                                       f"application_id = '{application_id}'and" \
                                       f" request_id = '{request_id}'"
            logger.debug(f"Update digital signature status query ---> {update_digital_signature}")
            status = self.db_conn.update_mysql_table(query=update_digital_signature)
            if not status:
                raise Exception('Failed to update digital signature status for the application')
            else:
                return {'status': "success"}
        except Exception as e:
            logger.error(f"Error occurred while updating application status after digital signature: {str(e)}")
            raise Exception("Error occurred while updating application status after digital signature")

    def fetch_user_type(self, signed_user):
        """
        This method is to identify if the user is a CPCB user or an SPCB user
        :param signed_user:
        :return:
        """
        try:
            logger.info(f"Signed user : {signed_user}")
            query_user_type = f"select user_id, user_fullname, user_state_id" \
                              f" from {TableName.admin} where user_id  = '{signed_user}'"
            logger.debug(f"Query user type --> {query_user_type}")
            status, resp = self.db_conn.select_mysql_fetchone(query=query_user_type)
            if status and resp:
                if resp.get('user_state_id') not in [None, 'None', 0, '0']:
                    return 'spcb'
                else:
                    return 'cpcb'
            else:
                raise Exception("Failed to fetch user details")
        except Exception as e:
            logger.error(f"Error occurred while identifying the digitally signed user type : {str(e)}", exc_info=True)
            raise Exception("Failed to fetch the digitally signed user type ")
