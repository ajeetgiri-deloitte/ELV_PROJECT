from datetime import datetime
import traceback
import os
import pdfkit
import base64

from scripts.constants.app_configurations import *
from scripts.constants.app_constants import TableName, PiboUserRolesJson, ResponseMessage, Message
from scripts.logging.logger import logger
from scripts.utils.db_utility import DBUtility
from scripts.utils.minio_utility import S3Utility


class CERTIFICATE_GENERATION:
    def __init__(self):
        self.db_util = DBUtility()
        self.folder_dir = "state_logos"
        self.minio_util = S3Utility()

    def certificate_generation(self, company_id,user_id):
        try:
            with open(os.path.join(dsign_html_template_dir, 'pdf.html')) as index:
                data = index.read()
            pibo_main_query = f"""select 
                                   company_id from {TableName.pibo_company_details} where number_of_os > 2 and
                                    company_id={company_id}
                                   """
            status, records = self.db_util.select_mysql_table(pibo_main_query)
            if status:
                if records:
                    logger.info('Generating user certificates')
                    cpcb_certificate_query = f"""
                                      select
                                          c.company_id ,
                                          c.created_on as date ,
                                          c.applicant_type as type,
                                          a.application_id as app_id,
                                          c.company_legal_name as legal_name,
                                          c.company_trade_name as trade_name,
                                          c.company_registered_address as address,
                                          a.year as application_year,
                                          p.cat_1,p.cat_2,p.cat_3,p.cat_4,
                                          app.additional_notes as conditions

                                      from 
                                           {TableName.pibo_company_details} as c left join {TableName.application} as a on a.company_id=c.company_id
                                           left join {TableName.pre_post_consumer_waste} as p on c.company_id=p.company_id
                                           left join {TableName.application_requests} as app on c.company_id=app.company_id
                                      where 
                                           c.company_id={company_id} and a.year=p.year  
                                      GROUP BY 
                                           c.company_id"""
                    state = "Central"
                    address_1 = "(Ministry Of Environment, Forest and Climate Change, Govt. of India), \
                                                            Parivesh Bhawan, East Arjun Nagar,Delhi-110032"
                    new_status, new_records = self.db_util.select_mysql_table(cpcb_certificate_query)
                    with open(f"state_logos/cpcb.png", "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                        final_encoded_string = "data:image/jpg;base64," + encoded_string
                        data = data.replace('$logo_name$', final_encoded_string)
                else:
                    logger.info('Generating user certificates that are under spcb')
                    spcb_certificate_query = f"""
                                                     select
                                                         c.company_id ,
                                                         c.created_on as date ,
                                                         c.applicant_type as type,
                                                         a.application_id as app_id,
                                                         c.company_legal_name as legal_name,
                                                         c.company_trade_name as trade_name,
                                                         c.company_registered_address as address,
                                                         a.year as application_year,
                                                         p.cat_1,p.cat_2,p.cat_3,p.cat_4,
                                                         app.additional_notes as conditions,
                                                         s.state_name as state,
                                                         s.address as state_address,
                                                         s.logo as logo_name

                                                     from 
                                                          {TableName.pibo_company_details} as c left join {TableName.application} as a on a.company_id=c.company_id
                                                          left join {TableName.pre_post_consumer_waste} as p on c.company_id=p.company_id
                                                          left join {TableName.application_requests} as app on c.company_id=app.company_id
                                                           LEFT JOIN {TableName.states} as s on s.id=c.company_state_id
                                                     where 
                                                          c.company_id={company_id} and a.year=p.year    
                                                     GROUP BY 
                                                          c.company_id"""
                    status, new_records = self.db_util.select_mysql_table(spcb_certificate_query)
                    logo_name = new_records[0].get('logo_name')
                    state = new_records[0].get('state')
                    address_1 = new_records[0].get('state_address')
                    with open(os.path.join(state_logs_dir, logo_name), "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                        final_encoded_string = "data:image/jpg;base64," + encoded_string
                        data = data.replace('$logo_name$', final_encoded_string)
                    # for images in os.listdir(self.folder_dir):
                    #     if images.endswith(".png"):
                    #         if logo_name == images:
                    #             with open(f"state_logos/{images}", "rb") as image_file:
                    #                 encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    #                 final_encoded_string = "data:image/jpg;base64," + encoded_string
                    #                 data = data.replace('$logo_name$', final_encoded_string)
                data = data.replace('$state$', state)
                data = data.replace('$address_line_1$', address_1)
                now = datetime.now()
                date = now.strftime("%d-%m-%Y %H:%M")
                data = data.replace('$DATE$', date)
                created_on = new_records[0].get('date').strftime("%d/%m/%Y")
                applicant_type = new_records[0].get('type')
                applicant_type_value = PiboUserRolesJson.roles_json.get(applicant_type)
                application_id = new_records[0].get('app_id')
                certificate_number = f'{created_on}-{applicant_type_value}-{application_id}'
                data = data.replace('$Certificate_Number$', certificate_number)
                data = data.replace('$USER_TYPE$', applicant_type_value)
                legal_name = new_records[0].get('legal_name')
                trade_name = new_records[0].get('trade_name')
                data = data.replace('$LEGAL_NAME$', legal_name)
                data = data.replace('$TRADE_NAME$', trade_name)
                company_address = new_records[0].get('address')
                data = data.replace('$ADDRESS$', company_address)
                data = data.replace('$APPLICATION_DATE$', created_on)
                data = data.replace('$USER_TYPE$', applicant_type_value)
                data = data.replace('$COMPANY_NAME$', legal_name)
                data = data.replace('$USER_TYPE$', applicant_type_value)
                financial_year = new_records[0].get('application_year')
                data = data.replace('$FinancialYear$', financial_year)
                cat1_target = new_records[0].get('cat_1')
                cat2_target = new_records[0].get('cat_2')
                cat3_target = new_records[0].get('cat_3')
                cat4_target = new_records[0].get('cat_4')
                data = data.replace('$CAT1_TARGET$', str(cat1_target))
                data = data.replace('$CAT2_TARGET$', str(cat2_target))
                data = data.replace('$CAT3_TARGET$', str(cat3_target))
                data = data.replace('$CAT4_TARGET$', str(cat4_target))
                data = data.replace('$TOTAL_CAT1_TARGET$', str(cat1_target))
                data = data.replace('$TOTAL_CAT2_TARGET$', str(cat2_target))
                data = data.replace('$TOTAL_CAT3_TARGET$', str(cat3_target))
                data = data.replace('$TOTAL_CAT4_TARGET$', str(cat4_target))
                total = cat1_target + cat2_target + cat3_target + cat4_target
                data = data.replace('$TOTAL_TARGET$', str(total))
                condition = new_records[0].get('conditions')
                data = data.replace('$TERMS_AND_CONDITIONS$', str(condition))
                data = data.replace('$logo_name$', final_encoded_string)
                new_date = datetime.now().strftime("%d-%m-%Y")
                pdf_name = f'{company_id}-{application_id}-{new_date}'
                if os.path.exists(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html')):
                    os.remove(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html'))
                with open(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html'), 'w') as w:
                    w.write(data)
                if os.path.exists(f'{digital_signature_files}/{pdf_name}.pdf'):
                    os.remove(f'{digital_signature_files}/{pdf_name}.pdf')
                pdfkit.from_file(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html'),
                                 f'{digital_signature_files}/{pdf_name}.pdf')
                file_path = rf'{digital_signature_files}/{company_id}-{application_id}-{new_date}.pdf'
                pdf_path = f"{ds_minio_path}/{user_id}/unsigned/{company_id}-{application_id}-{new_date}.pdf"
                self.minio_util.upload_file_to_s3(file_path, pdf_path)
                # file_path = 'scripts/core/digital_signature/digital_signature_files/3-1-16-08-2022.pdf'
                with open(file_path, "rb") as f:
                    encoded_string = base64.b64encode(f.read())
                    f.close()
                final_json = {
                    'status': "success",
                    "file": f"{pdf_name}_DS.pdf",
                    "fileData": encoded_string.decode('utf-8')
                }
                return ResponseMessage.final_json(status=Message.success, message="Get Summary List  Successful",
                                                  data=final_json)
            else:
                logger.error(f'error while trying to perform user type query')

        except Exception as e:
            logger.exception(f'error while trying to generate certificate{str(e)}')
            traceback.print_exc()
