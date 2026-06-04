import numpy as np

from scripts.constants.app_configurations import dsign_html_template_dir, state_logs_dir, digital_signature_files, \
    ds_minio_path
from scripts.constants.app_constants import TableName, StateDataCPCB, TextFiles, PiboUserRolesJsonCapital, \
    PiboUserRolesJsonSmall, RegnUser, ResponseMessage, Message
from scripts.core.PIBO.handlers.epr_target_updated import AnnualEPRTarget
from scripts.utils.common_utils import CommonUtils
from scripts.logging.logger import logger
from datetime import datetime
import traceback

import os
import pdfkit
import base64

from scripts.utils.db_utility import DBUtility
from scripts.utils.minio_utility import S3Utility
import n2w
import math 


class CERTIFICATE_GENERATION:
    def __init__(self):
        self.minio_util = S3Utility()
        self.db_util = DBUtility()
        self.options = {

            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'footer-line': None,
            'header-line': None,
            'outline': None,
            'page-offset': '0',
            'footer-left': '[page]',

        }
        self.factor = 10.0 ** 4

    def cpcb_certificate_generation(self, company_id, application_id, request_id, user_id, reference_no, designation):
        try:
            # Query for checking if it is under cpcb or spcb
            pibo_main_query = f"""select 
                                       company_id from {TableName.pibo_company_details} where number_of_os > 2 and
                                        company_id={company_id}
                                       """
            status, records = self.db_util.select_mysql_table(pibo_main_query)
            if status:
                if records:
                    cpcb_certificate_query = f"""select
                                                            c.company_id ,c.company_pan,
                                                            pd.addedon as date  ,
                                                            c.applicant_type as type,
                                                            a.application_id as app_id,
                                                            c.company_legal_name as legal_name,
                                                            c.company_trade_name as trade_name,
                                                            c.company_registered_address as address,
                                                            a.year as application_year,
                                                            p.cat_1,p.cat_2,p.cat_3,p.cat_4,
                                                            a.is_renewal as app_renewal,
                                                            cert.application_type as renewal,
                                                            cert.validity,
                                                            cert.modify_validity,
                                                            cert.modify_expiry,
                                                            cert.terms_and_conditions,
                                                            a.prev_cert_valid_till as app_cert_validity,
                                                            cert.previous_expiry_date as cert_exp

                                                        from 
                                                             {TableName.pibo_company_details} as c 
                                                             left join {TableName.application} as a on a.company_id=c.company_id
                                                             left join {TableName.pibo_epr_target} as p on a.application_id=p.application_id and c.company_id=p.company_id
                                                             left join {TableName.pibo_application_requests} as app on c.company_id=app.company_id and app.application_id=a.application_id
                                                             left join {TableName.pibo_cert_info} as cert on cert.application_id=a.application_id
                                                             left join {TableName.payment_details} as pd ON pd.company_id = c.company_id AND pd.`status`= 'success' 
                                                        where 
                                                             c.company_id={company_id} and a.application_id={application_id}
                                                             and app.status=5 
                                                        """
                    # Fetch EPR targets
                    fy = CommonUtils.get_current_fy_in_format()
                    fy_query = f"""select year from application where company_id = {company_id} and application_id = {application_id}"""
                    fy_query_exc = DBUtility().execute_query(fy_query,True)
                    if fy_query_exc:
                        fy = fy_query_exc[0]["year"]
                    logger.debug(f"&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& {fy}")
                    epr_targets = AnnualEPRTarget(company_id=company_id, year=fy).return_epr_targets()
                    logger.debug(f"-----------------------------> {epr_targets}")
                    epr_targets = epr_targets.get("tables", [{}])[0].get("tableData", {}).get("bodyContent", [{}])[0]
                    logger.debug(f"-----------------------------> {epr_targets}")
                    new_status, new_records = self.db_util.select_mysql_table(cpcb_certificate_query)
                    if new_status:
                        if new_records:
                            logger.info('Generating user certificates under cpcb')
                            if os.path.exists(os.path.join(dsign_html_template_dir, 'cpcb_main.html')):
                                # opening cpcb main html template
                                with open(os.path.join(dsign_html_template_dir, 'cpcb_main.html')) as index:
                                    data = index.read()
                                if os.path.exists(os.path.join(state_logs_dir, 'cpcb.png')):
                                    # opening cpcb main logo
                                    with open(os.path.join(state_logs_dir, 'cpcb.png'), "rb") as image_file:
                                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                        logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                        # cpcb logo at top left and center
                                        data = data.replace('$central_logo$', logo_encoded_string)
                                        data = data.replace('$logo_name$', logo_encoded_string)
                                    # This section is for displaying cpcb address in top right corner
                                    cpcb_state = StateDataCPCB.cpcb_state
                                    table_state = StateDataCPCB.table_state
                                    data = data.replace('$state$', cpcb_state)
                                    data = data.replace('$table_state$', table_state)
                                    address_1 = StateDataCPCB.address_1
                                    address_2 = StateDataCPCB.address_2
                                    address_3 = StateDataCPCB.address_3
                                    data = data.replace('$address_line_1$', address_1)
                                    data = data.replace('$address_line_2$', address_2)
                                    data = data.replace('$address_line_3$', address_3)
                                    # checking if the application is nenewed or not
                                    renewal = new_records[0].get('renewal')
                                    modify_validity = new_records[0].get('modify_validity')
                                    modify_expiry = new_records[0].get('modify_expiry')
                                    expiry_without_modification = new_records[0].get('app_cert_validity')
                                    expiry_with_modification = new_records[0].get('cert_exp')
                                    app_renewal = new_records[0].get('app_renewal')
                                    if app_renewal.lower() == 'no':
                                        Validity_Period = '<b>One Year</b> from the date of issue of the letter unless revoked, suspended or cancelled.'
                                        expiry = ''
                                    else:
                                        Validity_Period = '<b>Three Year</b>'
                                        expiry = f'from the expiry date of previous registration i.e. {expiry_without_modification} unless revoked, suspended or cancelled .'
                                    if renewal:
                                        if renewal.lower() == 'fresh':
                                            Validity_Period = '<b>One Year</b> from the date of issue of the letter unless revoked, suspended or cancelled.'
                                            expiry = ''
                                        elif renewal.lower() == 'renewal':
                                            if modify_validity.lower() == 'no' and modify_expiry.lower() == 'no':
                                                # Validity_Period = 'Three Year'
                                                # data = data.replace('$expiry_date$',
                                                #                     f'from the expiry date of previous registration i.e. {expiry_without_modification} unless revoked, suspended or cancelled .')
                                                Validity_Period = ' <b>Three Year</b>  from the date of issue of the letter unless revoked, suspended or cancelled. '
                                                expiry = ''

                                            elif modify_validity.lower() == 'no' and modify_expiry.lower() == 'yes':
                                                Validity_Period = '<b>Three Year</b>'
                                                expiry = f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .'
                                            elif modify_validity.lower() == 'yes' and modify_expiry.lower() == 'no':
                                                validity = new_records[0].get('validity')
                                                Validity_Period = n2w.convert(validity).capitalize()
                                                # Validity_Period = Validity_Period + " " + 'Year'
                                                # data = data.replace('$expiry_date$',
                                                #                     f'from the expiry date of previous registration i.e. {expiry_without_modification} unless revoked, suspended or cancelled .')
                                                Validity_Period = f' <b> {Validity_Period} Year</b>  from the date of issue of the letter unless revoked, suspended or cancelled. '
                                                expiry = ''
                                            else:
                                                validity = new_records[0].get('validity')
                                                Validity_Period = n2w.convert(validity).capitalize()
                                                Validity_Period = f' <b> {Validity_Period} Year</b> '
                                                expiry = f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .'
                                    data = data.replace('$Validity_Period$', Validity_Period)
                                    data = data.replace('$expiry_date$', expiry)
                                    # date displaying under address at top right corner
                                    now = datetime.now()
                                    date = now.strftime("%d-%m-%Y  %I:%M %p")
                                    data = data.replace('$DATE$', date)
                                    print("----------", new_records[0]['date'])  # current date
                                    created_on = new_records[0].get('date').strftime("%d-%m-%Y")
                                    # created_on = "19-08-2022"
                                    applicant_type = new_records[0].get('type')
                                    # taking corresponding text file for terms and condition
                                    file_name = TextFiles.files_json.get(applicant_type)
                                    with open(f'{file_name}') as f:
                                        lines = f.read()
                                    data = data.replace('$terms&conditions$', lines)
                                    # authority is under last line of terms and conditions
                                    data = data.replace('$authority$', StateDataCPCB.table_state)
                                    # user type in heading
                                    applicant_type_capital = PiboUserRolesJsonCapital.roles_json.get(applicant_type)
                                    data = data.replace('$USER_TYPE$', applicant_type_capital)
                                    # inside paragraph user_type
                                    applicant_type_small = PiboUserRolesJsonSmall.roles_json.get(applicant_type)
                                    data = data.replace('$user_type$', applicant_type_small)
                                    # for short form of user type in registration number
                                    regn_applicant = RegnUser.roles_json.get(applicant_type)
                                    application_id = new_records[0].get('app_id')
                                    # forming registration number for certificate
                                    l_3_4 = str(date)[0:2]
                                    l_8_9 = str(date)[3:5]
                                    l_10_19 = new_records[0].get('company_pan')
                                    l_20_22 = str(date)[8:10]
                                    certificate_number = f'{regn_applicant}-{l_3_4}-000-{l_8_9}-{l_10_19}-{l_20_22}'
                                    data = data.replace('$Certificate_Number$', certificate_number)
                                    legal_name = new_records[0].get('legal_name')
                                    legal_name_cap = legal_name.upper()
                                    data = data.replace('$LEGAL_NAME$', legal_name_cap)
                                    trade_name = new_records[0].get('trade_name').upper()
                                    data = data.replace('$TRADE_NAME$', trade_name)
                                    company_address = new_records[0].get('address')
                                    data = data.replace('$ADDRESS$', company_address)
                                    # for taking applied date
                                    data = data.replace('$APPLICATION_DATE$', created_on)
                                    data = data.replace('$COMPANY_NAME$', legal_name)
                                    financial_year = new_records[0].get('application_year')
                                    data = data.replace('$FinancialYear$', financial_year)
                                    # target displaying table
                                    # cat1_target = new_records[0].get('cat_1')
                                    # cat2_target = new_records[0].get('cat_2')
                                    # cat3_target = new_records[0].get('cat_3')
                                    # cat4_target = new_records[0].get('cat_4')

                                    # cat1_target = epr_targets.get('cat1', 0)
                                    # cat2_target = epr_targets.get('cat2', 0)
                                    # cat3_target = epr_targets.get('cat3', 0)
                                    # cat4_target = epr_targets.get('cat4', 0)

                                    # Updated target to be displayed in the table

                                    result = AnnualEPRTarget(company_id=company_id, year=financial_year).return_epr_targets()
                                    cat1_target = 0.0
                                    cat2_target = 0.0
                                    cat3_target = 0.0
                                    cat4_target = 0.0
                                    total_sum = 0.0

                                    for table in result["tables"]:
                                        for row in table.get("tableData", {}).get("bodyContent", []):
                                            # Sum totalEPRTarget
                                            value = row.get("totalEPRTarget")
                                            if isinstance(value, (int, float)):
                                                total_sum += value

                                            # Sum cat1
                                            value = row.get("cat1")
                                            if isinstance(value, (int, float)):
                                                cat1_target += value

                                            # Sum cat2
                                            value = row.get("cat2")
                                            if isinstance(value, (int, float)):
                                                cat2_target += value

                                            # Sum cat3
                                            value = row.get("cat3")
                                            if isinstance(value, (int, float)):
                                                cat3_target += value

                                            # Sum cat4
                                            value = row.get("cat4")
                                            if isinstance(value, (int, float)):
                                                cat4_target += value

                                    data = data.replace('$CAT1_TARGET$', str(cat1_target))
                                    data = data.replace('$CAT2_TARGET$', str(cat2_target))
                                    data = data.replace('$CAT3_TARGET$', str(cat3_target))
                                    data = data.replace('$CAT4_TARGET$', str(cat4_target))
                                    data = data.replace('$TOTAL_CAT1_TARGET$', str(cat1_target))
                                    data = data.replace('$TOTAL_CAT2_TARGET$', str(cat2_target))
                                    data = data.replace('$TOTAL_CAT3_TARGET$', str(cat3_target))
                                    data = data.replace('$TOTAL_CAT4_TARGET$', str(cat4_target))
                                    # total = cat1_target + cat2_target + cat3_target + cat4_target
                                    # try:
                                    #     total = math.trunc(
                                    #         (
                                    #                 cat1_target + cat2_target + cat3_target + cat4_target) * self.factor) / self.factor
                                    # except Exception as round_off_error:
                                    #     logger.error(f"Round off error : {str(round_off_error)}")
                                    #     pass
                                    data = data.replace('$TOTAL_TARGET$', str(total_sum))
                                    new_date = datetime.now().strftime("%d-%m-%Y")
                                    terms_con = new_records[0].get('terms_and_conditions')

                                    if terms_con:
                                        data = data.replace('$Terms and Conditions:-$', 'Terms and Conditions :-')
                                        data = data.replace('$terms$', terms_con)
                                    else:
                                        data = data.replace('$Terms and Conditions:-$', ' ')
                                        data = data.replace('$terms$', ' ')
                                    data = data.replace('$DESIGNATION$', str(designation))
                                    pdf_name = f'{reference_no}_unsigned'
                                    if os.path.exists(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html')):
                                        os.remove(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html'))
                                    with open(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html'), 'w') as w:
                                        w.write(data)

                                    if os.path.exists(f'{digital_signature_files}/{pdf_name}.pdf'):
                                        os.remove(f'{digital_signature_files}/{pdf_name}.pdf')

                                    pdfkit.from_file(os.path.join(dsign_html_template_dir, 'cpcb_certificate.html'),
                                                     f'{digital_signature_files}/{pdf_name}.pdf',
                                                     options=self.options)
                                    file_path = rf'{digital_signature_files}/{pdf_name}.pdf'
                                    pdf_path = f"{ds_minio_path}/PIBO/{user_id}/unsigned/{company_id}-{application_id}-{new_date}.pdf"
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
                                    logger.info('certificate generated successfully')
                                    return ResponseMessage.final_json(status=Message.success,
                                                                      message="Get Summary List  Successful",
                                                                      data=final_json)

                                else:
                                    logger.error('There is no path corresponding for cpcb logo')

                            else:
                                logger.error('There is no such file or directory for cpcb_main')

                        else:
                            logger.info('no data corresponding to cpcb certificate query')

                    else:
                        logger.error(f'error while trying to perform cpcb certificate query')

                else:
                    logger.info("user type is under spcb")
                    result = self.spcb_certificate_generation(company_id=company_id,
                                                              user_id=user_id,
                                                              reference_no=reference_no,
                                                              application_id=application_id,
                                                              designation=designation,
                                                              request_id=request_id)
                    print("result")

                    return result

            else:
                logger.error(f'error while trying to perform user type query')

        except Exception as e:
            logger.exception(f'error while trying to generate cpcb certificate{str(e)}')
            traceback.print_exc()

    def spcb_certificate_generation(self, company_id, application_id, user_id, reference_no, designation, request_id):
        try:
            # Query for spcb certificate generation
            logger.debug(f"Fetching selected state id for request : {request_id}")
            state_id = self.fetch_selected_state(request_id=request_id)
            logger.debug(f"State id for request : {state_id}")
            spcb_certificate_query = f"""   select
                                             c.company_id ,c.company_pan,
                                             pd.addedon as date  ,
                                             c.applicant_type as type,
                                             a.application_id as app_id,
                                             c.company_legal_name as legal_name,
                                             c.company_trade_name as trade_name,
                                             c.company_registered_address as address,
                                             a.year as application_year,
                                             p.cat_1,p.cat_2,p.cat_3,p.cat_4,
                                             s.state_name as state,
                                             s.address as state_address,
                                             s.logo as logo_name,
                                             a.is_renewal as app_renewal,
                                             cert.application_type as renewal,
                                             cert.validity,
                                             cert.modify_validity,
                                             cert.modify_expiry,
                                             cert.terms_and_conditions,
                                             a.prev_cert_valid_till as app_cert_validity,
                                             cert.previous_expiry_date as cert_exp


                                         from 
                                              {TableName.pibo_company_details} as c left join {TableName.application} as a on a.company_id=c.company_id
                                              left join {TableName.pibo_application_requests} as pr on a.application_id=pr.application_id
                                              left join {TableName.pibo_epr_target} as p on a.application_id=p.application_id and pr.state_id=p.state_id
                                              left join {TableName.pibo_cert_info} as cert on cert.application_id=a.application_id
                                              LEFT JOIN {TableName.states} as s on s.id = pr.state_id
                                              left join {TableName.payment_details} as pd ON pd.company_id = c.company_id AND pd.`status`= 'success'  
                                         where 
                                              c.company_id={company_id} and a.application_id={application_id}
                                              and pr.status=5 and pr.state_id = {state_id}
                                         GROUP BY 
                                              c.company_id"""
            logger.debug(spcb_certificate_query)
            fy = CommonUtils.get_current_fy_in_format()
            fy_query = f"""select year from application where company_id = {company_id} and application_id = {application_id}"""
            fy_query_exc = DBUtility().execute_query(fy_query, True)
            if fy_query_exc:
                fy = fy_query_exc[0]["year"]
            epr_targets = AnnualEPRTarget(company_id=company_id, year=fy).return_epr_targets()
            logger.debug(f"-----------------------------> {epr_targets}")
            epr_targets = epr_targets.get("tables", [{}])[0].get("tableData", {}).get("bodyContent", [{}])[0]
            logger.debug(f"-----------------------------> {epr_targets}")
            new_status, new_records = self.db_util.select_mysql_table(spcb_certificate_query)
            if new_status:
                if new_records:
                    logger.info('Generating user certificates under spcb')
                    if os.path.exists(os.path.join(dsign_html_template_dir, 'spcb_main.html')):
                        # opening spcb main html template
                        with open(os.path.join(dsign_html_template_dir, 'spcb_main.html')) as index:
                            data = index.read()
                        if os.path.exists(os.path.join(state_logs_dir, 'cpcb.png')):
                            # opening central logo
                            with open(os.path.join(state_logs_dir, 'cpcb.png'), "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                data = data.replace('$central_logo$', logo_encoded_string)
                            logo_name = new_records[0].get('logo_name')
                            if os.path.exists(os.path.join(state_logs_dir, f'{logo_name}')):
                                # opening spcb  logo
                                with open(os.path.join(state_logs_dir, f'{logo_name}'), "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                    logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                    data = data.replace('$logo_name$', logo_encoded_string)

                                # This section is for displaying spcb address in top right corner
                                state = new_records[0].get('state')
                                # this is for displaying first letter as capital
                                state_title = state.title()
                                if state not in ['ANDAMAN AND NICOBAR ISLANDS', 'DELHI', 'PONDICHERRY',
                                                 'CHANDIGARH', 'DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
                                                 'LAKSHADWEEP']:
                                    if state == 'CHHATTISGARH':
                                        state_title = state_title + ' ' + 'Environment Conservation Board'
                                    else:
                                        state_title = state_title + ' ' + 'Pollution Control Board'
                                else:
                                    state_title = state_title + ' ' + 'Pollution Control Committee'
                                # state address
                                address_1 = new_records[0].get('state_address')
                                data = data.replace('$state$', state_title)
                                # for state in target table
                                data = data.replace('$table_state$', state)
                                # display address at top right
                                data = data.replace('$address_line_1$', address_1)
                                now = datetime.now()
                                # display date at top right
                                date = now.strftime("%d-%m-%Y  %I:%M %p")
                                data = data.replace('$DATE$', date)
                                # for checking renewal status
                                renewal = new_records[0].get('renewal')
                                modify_validity = new_records[0].get('modify_validity')
                                modify_expiry = new_records[0].get('modify_expiry')
                                expiry_without_modification = new_records[0].get('app_cert_validity')
                                expiry_with_modification = new_records[0].get('cert_exp')
                                app_renewal = new_records[0].get('app_renewal')
                                if app_renewal.lower() == 'no':
                                    Validity_Period = '<b>One Year</b>from the date of issue of the letter unless revoked, suspended or cancelled.'
                                    expiry = ''
                                else:
                                    Validity_Period = '<b>Three Year</b>'
                                    expiry = f'from the expiry date of previous registration i.e. {expiry_without_modification} unless revoked, suspended or cancelled .'
                                if renewal:
                                    if renewal.lower() == 'fresh':
                                        Validity_Period = '<b>One Year </b>from the date of issue of the letter unless revoked, suspended or cancelled.'
                                        expiry = ''
                                    elif renewal.lower() == 'renewal':
                                        if modify_validity.lower() == 'no' and modify_expiry.lower() == 'no':
                                            # Validity_Period = '<b>Three Year</b>'
                                            # data = data.replace('$expiry_date$',
                                            #                     f'from the expiry date of previous registration i.e. {expiry_without_modification} unless revoked, suspended or cancelled .')
                                            Validity_Period = ' <b>Three Year</b>  from the date of issue of the letter unless revoked, suspended or cancelled. '
                                            expiry = ''

                                        elif modify_validity.lower() == 'no' and modify_expiry.lower() == 'yes':
                                            Validity_Period = '<b>Three Year</b>'
                                            expiry = f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .'
                                        elif modify_validity.lower() == 'yes' and modify_expiry.lower() == 'no':
                                            validity = new_records[0].get('validity')
                                            Validity_Period = n2w.convert(validity).capitalize()
                                            # Validity_Period =f'<b> {Validity_Period} </b>'+ " " + 'Year'
                                            # data = data.replace('$expiry_date$',
                                            #                     f'from the expiry date of previous registration i.e. {expiry_without_modification} unless revoked, suspended or cancelled .')
                                            Validity_Period = f' <b> {Validity_Period} Year</b>  from the date of issue of the letter unless revoked, suspended or cancelled. '
                                            expiry = ''
                                        else:
                                            validity = new_records[0].get('validity')
                                            Validity_Period = n2w.convert(validity).capitalize()
                                            Validity_Period = f'<b>{Validity_Period}</b>' + " " + 'Year'
                                            expiry = f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .'
                                data = data.replace('$Validity_Period$', Validity_Period)
                                data = data.replace('$expiry_date$', expiry)
                                created_on = new_records[0].get('date').strftime("%d-%m-%Y")
                                applicant_type = new_records[0].get('type')
                                # for taking rules and regulations from text file
                                file_name = TextFiles.files_json.get(applicant_type)
                                with open(f'{file_name}') as f:
                                    lines = f.read()
                                data = data.replace('$terms&conditions$', lines)
                                # adding authority at last rule
                                data = data.replace('$authority$',
                                                    state_title)
                                # display user type in title
                                applicant_type_capital = PiboUserRolesJsonCapital.roles_json.get(applicant_type)
                                # for displaying user type in body
                                applicant_type_small = PiboUserRolesJsonSmall.roles_json.get(applicant_type)
                                # small form of user type for forming registration number
                                regn_applicant = RegnUser.roles_json.get(applicant_type)
                                application_id = new_records[0].get('app_id')
                                # forming certificate number
                                l_3_4 = str(date)[0:2]
                                l_8_9 = str(date)[3:5]
                                l_10_19 = new_records[0].get('company_pan')
                                l_20_22 = str(date)[8:10]
                                state_key = (str(state)[0:3])
                                certificate_number = f'{regn_applicant}-{l_3_4}-{state_key}-{l_8_9}-{l_10_19}-{l_20_22}'
                                data = data.replace('$Certificate_Number$', certificate_number)
                                data = data.replace('$USER_TYPE$', applicant_type_capital)
                                data = data.replace('$user_type$', applicant_type_small)
                                legal_name = new_records[0].get('legal_name')
                                trade_name = new_records[0].get('trade_name')
                                data = data.replace('$LEGAL_NAME$', legal_name)
                                data = data.replace('$TRADE_NAME$', trade_name)
                                company_address = new_records[0].get('address')
                                data = data.replace('$ADDRESS$', company_address)
                                data = data.replace('$APPLICATION_DATE$', created_on)
                                data = data.replace('$COMPANY_NAME$', legal_name)
                                financial_year = new_records[0].get('application_year')
                                data = data.replace('$FinancialYear$', financial_year)
                                # target table part
                                # cat1_target = new_records[0].get('cat_1')
                                # cat2_target = new_records[0].get('cat_2')
                                # cat3_target = new_records[0].get('cat_3')
                                # cat4_target = new_records[0].get('cat_4')
                                # cat1_target = epr_targets.get('cat1', 0)
                                # cat2_target = epr_targets.get('cat2', 0)
                                # cat3_target = epr_targets.get('cat3', 0)
                                # cat4_target = epr_targets.get('cat4', 0)

                                result = AnnualEPRTarget(company_id=company_id, year=financial_year).return_epr_targets()
                                logger.info(f"AnnualEPRTarget: {result}")
                                cat1_target = 0.0
                                cat2_target = 0.0
                                cat3_target = 0.0
                                cat4_target = 0.0
                                total_sum = 0.0

                                for table in result["tables"]:
                                    for row in table.get("tableData", {}).get("bodyContent", []):
                                        # Sum totalEPRTarget
                                        value = row.get("totalEPRTarget")
                                        if isinstance(value, (int, float)):
                                            total_sum += value

                                        # Sum cat1
                                        value = row.get("cat1")
                                        if isinstance(value, (int, float)):
                                            cat1_target += value

                                        # Sum cat2
                                        value = row.get("cat2")
                                        if isinstance(value, (int, float)):
                                            cat2_target += value

                                        # Sum cat3
                                        value = row.get("cat3")
                                        if isinstance(value, (int, float)):
                                            cat3_target += value

                                        # Sum cat4
                                        value = row.get("cat4")
                                        if isinstance(value, (int, float)):
                                            cat4_target += value

                                data = data.replace('$CAT1_TARGET$', str(cat1_target))
                                data = data.replace('$CAT2_TARGET$', str(cat2_target))
                                data = data.replace('$CAT3_TARGET$', str(cat3_target))
                                data = data.replace('$CAT4_TARGET$', str(cat4_target))
                                data = data.replace('$TOTAL_CAT1_TARGET$', str(cat1_target))
                                data = data.replace('$TOTAL_CAT2_TARGET$', str(cat2_target))
                                data = data.replace('$TOTAL_CAT3_TARGET$', str(cat3_target))
                                data = data.replace('$TOTAL_CAT4_TARGET$', str(cat4_target))
                                # total = cat1_target + cat2_target + cat3_target + cat4_target
                                # total = cat1_target + cat2_target + cat3_target + cat4_target
                                # try:
                                #     total = math.trunc(
                                #         (
                                #                 cat1_target + cat2_target + cat3_target + cat4_target) * self.factor) / self.factor
                                # except Exception as round_off_error:
                                #     logger.error(f"Round off error : {str(round_off_error)}")
                                #     pass
                                data = data.replace('$TOTAL_TARGET$', str(total_sum))
                                new_date = datetime.now().strftime("%d-%m-%Y")
                                terms_con = new_records[0].get('terms_and_conditions')
                                if terms_con:
                                    data = data.replace('$Terms and Conditions:-$', 'Terms and Conditions :-')
                                    data = data.replace('$terms$', terms_con)
                                else:
                                    data = data.replace('$Terms and Conditions:-$', ' ')
                                    data = data.replace('$terms$', ' ')
                                data = data.replace('$DESIGNATION$', str(designation))
                                # pdf_name = f'{company_id}-{application_id}-{new_date}'
                                if os.path.exists(os.path.join(dsign_html_template_dir, 'spcb_certificate.html')):
                                    os.remove(os.path.join(dsign_html_template_dir, 'spcb_certificate.html'))
                                with open(os.path.join(dsign_html_template_dir, 'spcb_certificate.html'), 'w') as w:
                                    w.write(data)
                                pdf_name = f'{reference_no}_unsigned'
                                if os.path.exists(f'{digital_signature_files}{pdf_name}.pdf'):
                                    os.remove(f'{digital_signature_files}{pdf_name}.pdf')
                                pdfkit.from_file(os.path.join(dsign_html_template_dir, 'spcb_certificate.html'),
                                                 f'{digital_signature_files}/{pdf_name}.pdf', options=self.options)
                                logger.info('certificate generated successfully')
                                file_path = rf'{digital_signature_files}/{pdf_name}.pdf'
                                pdf_path = f"{ds_minio_path}/PIBO/{user_id}/unsigned/{company_id}-{application_id}-{new_date}.pdf"
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
                                logger.info('certificate generated successfully')
                                return ResponseMessage.final_json(status=Message.success,
                                                                  message="Get Summary List  Successful",
                                                                  data=final_json)
                        else:
                            logger.error('There is no path corresponding for spcb logo')

                    else:
                        logger.error('There is no such file or directory for spcb_main')

                else:
                    logger.info('no data corresponding to spcb certificate query')
            else:
                logger.error(f'error while trying to perform spcb certificate query')

        except Exception as e:
            logger.exception(f'error while trying to generate spcb certificate{str(e)}')
            traceback.print_exc()

    def pwp_certificate_generation(self, company_id, application_id, user_id, reference_no, designation):
        # Query for pwp certificate generation
        try:
            pwp_certificate_query = f"""
                                          select
                                                pd.addedon as date,
                                                u.company_name,u.company_address,
                                                u.company_pan as user_pan,
                                                u.district,u.pincode,
                                                s.state_name as state,
                                                s.address as state_address,s.logo as state_logo,
                                                a.id as app_id,p.addedon as payment_date,
                                                cert.application_type as renewal,
                                                cert.validity,
                                                cert.modify_validity,
                                                cert.modify_expiry,
                                                cert.terms_and_conditions,
                                                cert.previous_expiry_date as cert_exp
                                          from {TableName.pwp_company_details} as u
                                          left join {TableName.states} as s on s.id=u.state_id
                                          left join {TableName.pwp_application} as a on a.company_id=u.id
                                          left join {TableName.pwp_payment_details} as p on a.company_id=p.company_id
                                          left join {TableName.pwp_cert_info} as cert on cert.application_id=a.id 
                                          left join {TableName.pwp_payment_details} as pd on pd.company_id=u.id and 
                                          pd.status = 'success' 
                                          where u.id={company_id} and a.id ={application_id}
                                          and a.status=5
                                          group by a.id"""
            logger.debug(f"Query pwp company details ---> {pwp_certificate_query}")
            new_status, new_records = self.db_util.select_mysql_table(pwp_certificate_query)
            if new_status:

                if new_records:
                    logger.info('Generating user certificates under pwp')
                    if os.path.exists(os.path.join(dsign_html_template_dir, 'pwp_new.html')):
                        # opening pwp main html template
                        with open(os.path.join(dsign_html_template_dir, 'pwp_new.html')) as index:
                            data = index.read()
                        if os.path.exists(os.path.join(state_logs_dir, 'cpcb.png')):
                            # opening central logo
                            with open(os.path.join(state_logs_dir, 'cpcb.png'), "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                data = data.replace('$central_logo$', logo_encoded_string)
                            logo_name = new_records[0].get('state_logo')
                            if os.path.exists(os.path.join(state_logs_dir, f'{logo_name}')):
                                # opening pwp  logo
                                with open(os.path.join(state_logs_dir, f'{logo_name}'), "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                    logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                    data = data.replace('$logo_name$', logo_encoded_string)
                                # This section is for displaying pwp address in top right corner
                                state = new_records[0].get('state')
                                # this is for displaying first letter as capital
                                state_title_normal = state.title()
                                state_title = state.title()
                                if state not in ['ANDAMAN AND NICOBAR ISLANDS', 'DELHI', 'PONDICHERRY',
                                                 'CHANDIGARH', 'DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
                                                 'LAKSHADWEEP']:
                                    if state == 'CHHATTISGARH':
                                        state_title = state_title + ' ' + 'Environment Conservation Board'
                                    else:
                                        state_title = state_title + ' ' + 'Pollution Control Board'
                                else:
                                    state_title = state_title + ' ' + 'Pollution Control Committee'
                                # state address
                                address_1 = new_records[0].get('state_address')
                                data = data.replace('$STATE_NAME$', state_title)
                                # for state in target table
                                data = data.replace('$table_state$', state)
                                # display address at top right
                                data = data.replace('$STATE ADDRESS$', address_1)
                                now = datetime.now()
                                # display date at top right
                                date = now.strftime("%d-%m-%Y  %I:%M %p")
                                data = data.replace('$CURRENT_DATE$', date)
                                # for checking renewal status
                                renewal = new_records[0].get('renewal')
                                modify_validity = new_records[0].get('modify_validity')
                                modify_expiry = new_records[0].get('modify_expiry')
                                expiry_with_modification = new_records[0].get('cert_exp')
                                if renewal:
                                    if renewal.lower() == 'fresh':
                                        Validity_Period = f'<b> One Year </b> from the date of issue of the letter unless revoked, suspended or cancelled.'
                                        data = data.replace('$expiry_date$', ' ')
                                    elif renewal.lower() == 'renewal':
                                        if modify_validity.lower() == 'no' and modify_expiry.lower() == 'no':
                                            Validity_Period = ' <b>Three Year</b>  from the date of issue of the letter unless revoked, suspended or cancelled. '
                                            data = data.replace('$expiry_date$', '')
                                        elif modify_validity.lower() == 'no' and modify_expiry.lower() == 'yes':
                                            Validity_Period = '<b>Three Year </b>'
                                            data = data.replace('$expiry_date$',
                                                                f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .')
                                        elif modify_validity.lower() == 'yes' and modify_expiry.lower() == 'no':
                                            validity = new_records[0].get('validity')
                                            Validity_Period = n2w.convert(validity).capitalize()
                                            Validity_Period = f'<b>{Validity_Period}' + " " + 'Year </b> from the date of issue of the letter unless revoked, suspended or cancelled. '
                                            data = data.replace('$expiry_date$', '')
                                        else:
                                            validity = new_records[0].get('validity')
                                            Validity_Period = n2w.convert(validity).capitalize()
                                            Validity_Period = f'<b>{Validity_Period} </b>' + " " + 'Year'
                                            data = data.replace('$expiry_date$',
                                                                f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .')
                                data = data.replace('$VALIDITY$', Validity_Period)
                                # application_id = new_records[0].get('app_id')
                                # forming certificate number
                                l_3_4 = str(date)[0:2]
                                l_8_9 = str(date)[3:5]
                                l_10_19 = new_records[0].get('user_pan')
                                l_20_22 = str(date)[8:10]
                                state_key = (str(state)[0:3])
                                certificate_number = f'PR-{l_3_4}-{state_key}-{l_8_9}-{l_10_19}-{l_20_22}'
                                data = data.replace('$REGISTRATION_NUMBER$', certificate_number)
                                company_name = new_records[0].get('company_name')
                                data = data.replace('$COMPANY_NAME$', company_name)
                                company_address = new_records[0].get('company_address')
                                data = data.replace('$COMPANY_ADDRESS$', company_address)
                                company_district = new_records[0].get('district')
                                company_pincode = new_records[0].get('pincode')
                                data = data.replace('$COMPANY_DISTRICT$', company_district)
                                data = data.replace('$COMPANY_STATE$', state_title_normal)
                                data = data.replace('$COMPANY_PINCODE$', str(company_pincode))
                                payment_date = new_records[0].get('payment_date').strftime("%d-%m-%Y")

                                data = data.replace('$PAYMENT_DATE$', str(payment_date))
                                # processing capacity table part
                                processing_capacity_query = f"""  
                                        Select w.category,sum(w.processing_capacity) as processing_capacity,w.process_code
                                        from {TableName.waste_processing_capacity} as w
                                        where w.company_id = {company_id} and w.application_id={application_id}
                                        GROUP by  w.category,w.process_code"""
                                p_status, p_records = self.db_util.select_mysql_table(processing_capacity_query)
                                if p_status:
                                    if p_records:
                                        category_list = [1, 2, 3, 4]
                                        exist = []
                                        for each_value in p_records:
                                            exist.append(each_value.get('category'))
                                        main_list = np.setdiff1d(category_list, exist)
                                        cat_1, cat_2, cat_3, cat_4 = '', '', '', ''
                                        production_capacity = ''
                                        cat1_code, cat2_code, cat3_code, cat4_code = [], [], [], []
                                        cat1_process, cat2_process, cat3_process, cat4_process = [], [], [], []
                                        for new_value in p_records:
                                            if 1 not in main_list:
                                                if new_value.get('category') == 1:
                                                    cat1_process.append(new_value.get('processing_capacity'))
                                                    cat_1 = sum(cat1_process)
                                                    cat1_code.append(new_value.get('process_code'))
                                            else:
                                                cat_1 = '--'
                                            if 2 not in main_list:
                                                if new_value.get('category') == 2:
                                                    cat2_process.append(new_value.get('processing_capacity'))
                                                    cat_2 = sum(cat2_process)
                                                    cat2_code.append(new_value.get('process_code'))
                                            else:
                                                cat_2 = '--'
                                            if 3 not in main_list:
                                                if new_value.get('category') == 3:
                                                    cat3_process.append(new_value.get('processing_capacity'))
                                                    cat_3 = sum(cat3_process)
                                                    cat3_code.append(new_value.get('process_code'))
                                            else:
                                                cat_3 = '--'
                                            if 4 not in main_list:
                                                if new_value.get('category') == 4:
                                                    cat4_process.append(new_value.get('processing_capacity'))
                                                    cat_4 = sum(cat4_process)
                                                    cat4_code.append(new_value.get('process_code'))
                                            else:
                                                cat_4 = '--'
                                        production_capacity_query = f"""  
                                             Select sum(w.recycled_quality_tpa) as recycled_tpa, d.name,w.process_code
                                            from {TableName.waste_processing_capacity} as w
                                            left join {TableName.pwp_products} as d on d.id=w.product
                                            where w.company_id = {company_id} and w.application_id={application_id}
                                            GROUP by  w.product,w.process_code
                                            """
                                        prod_status, prod_response = self.db_util.select_mysql_table(
                                            production_capacity_query)
                                        if prod_response:
                                            for prod_value in prod_response:
                                                capacity_data = f"""
                                                        <tr><td>{prod_value.get('name')} {"    "}{"    "}  [{prod_value.get('process_code')}]</td> 
                                                    <td>{prod_value.get('recycled_tpa')}</td> 
                                                    </tr>"""
                                                print(capacity_data)
                                                production_capacity += capacity_data
                                        distict_list = set(cat1_code + cat2_code + cat3_code + cat4_code)
                                        joined_string = ",".join(sorted(distict_list))
                                        data = data.replace('$table_code$', joined_string)
                                        cat1_code = '[%s]' % ', '.join(map(str, cat1_code))
                                        cat2_code = '[%s]' % ', '.join(map(str, cat2_code))
                                        cat3_code = '[%s]' % ', '.join(map(str, cat3_code))
                                        cat4_code = '[%s]' % ', '.join(map(str, cat4_code))
                                        # data = data.replace('$Cat-I$', f'Cat-I {str(cat1_code)}')
                                        # data = data.replace('$Cat-II$', f'Cat-II {str(cat2_code)}')
                                        # data = data.replace('$Cat-III$', f'Cat-III {str(cat3_code)}')
                                        # data = data.replace('$Cat-IV$', f'Cat-IV {str(cat4_code)}')
                                        data = data.replace('$Cat-I$', 'Cat-I ')
                                        data = data.replace('$Cat-II$', 'Cat-II ')
                                        data = data.replace('$Cat-III$', 'Cat-III ')
                                        data = data.replace('$Cat-IV$', 'Cat-IV ')

                                        data = data.replace('$CAT1$', str(cat_1))
                                        data = data.replace('$CAT2$', str(cat_2))
                                        data = data.replace('$CAT3$', str(cat_3))
                                        data = data.replace('$CAT4$', str(cat_4))
                                        data = data.replace('$production_capacity$', production_capacity)
                                        # new_date = datetime.now().strftime("%d-%m-%Y")
                                        terms_con = new_records[0].get('terms_and_conditions')

                                        if terms_con:
                                            data = data.replace('$Terms and Conditions:-$', 'Terms and Conditions :-')
                                            data = data.replace('$terms$', terms_con)
                                        else:
                                            data = data.replace('$Terms and Conditions:-$', ' ')
                                            data = data.replace('$terms$', ' ')
                                        data = data.replace('$DESIGNATION$', str(designation))
                                        pdf_name = f'{reference_no}_unsigned'
                                        if os.path.exists(
                                                os.path.join(dsign_html_template_dir, 'pwp_certificate.html')):
                                            os.remove(os.path.join(dsign_html_template_dir, 'pwp_certificate.html'))
                                        with open(os.path.join(dsign_html_template_dir, 'pwp_certificate.html'),
                                                  'w') as w:
                                            w.write(data)
                                        if os.path.exists(f'{digital_signature_files}/{pdf_name}.pdf'):
                                            os.remove(f'{digital_signature_files}/{pdf_name}.pdf')
                                        pdfkit.from_file(os.path.join(dsign_html_template_dir, 'pwp_certificate.html'),
                                                         f'{digital_signature_files}/{pdf_name}.pdf',
                                                         options=self.options)
                                        logger.info('certificate generated successfully')
                                        file_path = rf'{digital_signature_files}/{pdf_name}.pdf'
                                        pdf_path = f"{ds_minio_path}/PWP/{user_id}/unsigned/{pdf_name}.pdf"
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
                                        logger.info('certificate generated successfully')
                                        return ResponseMessage.final_json(status=Message.success,
                                                                          message="Get Summary List  Successful",
                                                                          data=final_json)

                                    else:
                                        logger.info('no data corresponding to pwp waste processing capacity')
                                else:
                                    logger.error('error while trying to perform processing query')
                        else:
                            logger.error('There is no path corresponding for pwp logo')

                    else:
                        logger.error('There is no such file or directory for pwp_new')

                else:
                    logger.info('no data corresponding to pwp certificate query')
            else:
                logger.error(f'error while trying to perform pwp certificate query')

        except Exception as e:
            logger.exception(f'error while trying to generate pwp certificate{str(e)}')
            traceback.print_exc()

    def ulb_certificate_generation(self, company_id, application_id, user_id, reference_no, designation):
        # Query for ulb certificate generation
        try:
            pwp_certificate_query = f"""
                                          select
                                                pd.addedon as date,
                                                u.company_name,u.company_address,
                                                u.user_pan, u.company_pan,
                                                u.district,u.pincode,
                                                s.state_name as state,
                                                s.address as state_address,s.logo as state_logo,
                                                a.id as app_id,p.addedon as payment_date,
                                                cert.application_type as renewal,
                                                cert.validity,
                                                cert.modify_validity,
                                                cert.terms_and_conditions,
                                                cert.modify_expiry,
                                                cert.previous_expiry_date as cert_exp
                                          from {TableName.ulb_user_details_new} as u
                                          left join {TableName.states} as s on s.id=u.state_id
                                          left join {TableName.ulb_application} as a on a.company_id=u.id
                                          left join {TableName.ulb_payment_details} as p on a.company_id=p.company_id
                                          left join {TableName.ulb_cert_info} as cert on cert.application_id=a.id
                                          left join {TableName.pwp_payment_details} as pd on pd.company_id=u.id and 
                                          pd.status = 'success'
                                          where u.id={company_id} and a.id ={application_id}
                                          and a.status=5
                                          group by a.id"""
            logger.debug(f"Query ulb company details ---> {pwp_certificate_query}")
            new_status, new_records = self.db_util.select_mysql_table(pwp_certificate_query)
            if new_status:

                if new_records:
                    logger.info('Generating user certificates under ulb')
                    if os.path.exists(os.path.join(dsign_html_template_dir, 'ulb_new.html')):
                        # opening pwp main html template
                        with open(os.path.join(dsign_html_template_dir, 'ulb_new.html')) as index:
                            data = index.read()
                        if os.path.exists(os.path.join(state_logs_dir, 'cpcb.png')):
                            # opening central logo
                            with open(os.path.join(state_logs_dir, 'cpcb.png'), "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                data = data.replace('$central_logo$', logo_encoded_string)
                            logo_name = new_records[0].get('state_logo')
                            if os.path.exists(os.path.join(state_logs_dir, f'{logo_name}')):
                                # opening pwp  logo
                                with open(os.path.join(state_logs_dir, f'{logo_name}'), "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                    logo_encoded_string = "data:image/jpg;base64," + encoded_string
                                    data = data.replace('$logo_name$', logo_encoded_string)
                                # This section is for displaying pwp address in top right corner
                                state = new_records[0].get('state')
                                # this is for displaying first letter as capital
                                state_title_normal = state.title()
                                state_title = state.title()
                                if state not in ['ANDAMAN AND NICOBAR ISLANDS', 'DELHI', 'PONDICHERRY',
                                                 'CHANDIGARH', 'DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
                                                 'LAKSHADWEEP']:
                                    if state == 'CHHATTISGARH':
                                        state_title = state_title + ' ' + 'Environment Conservation Board'
                                    else:
                                        state_title = state_title + ' ' + 'Pollution Control Board'
                                else:
                                    state_title = state_title + ' ' + 'Pollution Control Committee'
                                # state address
                                address_1 = new_records[0].get('state_address')
                                data = data.replace('$STATE_NAME$', state_title)
                                # for state in target table
                                data = data.replace('$table_state$', state)
                                # display address at top right
                                data = data.replace('$STATE ADDRESS$', address_1)
                                now = datetime.now()
                                # display date at top right
                                date = now.strftime("%d-%m-%Y  %I:%M %p")
                                data = data.replace('$CURRENT_DATE$', date)
                                # for checking renewal status
                                renewal = new_records[0].get('renewal')
                                modify_validity = new_records[0].get('modify_validity')
                                modify_expiry = new_records[0].get('modify_expiry')
                                expiry_with_modification = new_records[0].get('cert_exp')
                                if renewal:
                                    if renewal.lower() == 'fresh':
                                        Validity_Period = f'<b> One Year </b> from the date of issue of the letter unless revoked, suspended or cancelled.'
                                        data = data.replace('$expiry_date$', ' ')
                                    elif renewal.lower() == 'renewal':
                                        if modify_validity.lower() == 'no' and modify_expiry.lower() == 'no':
                                            Validity_Period = ' <b>Three Year</b>  from the date of issue of the letter unless revoked, suspended or cancelled. '
                                            data = data.replace('$expiry_date$', '')
                                        elif modify_validity.lower() == 'no' and modify_expiry.lower() == 'yes':
                                            Validity_Period = '<b>Three Year </b>'
                                            data = data.replace('$expiry_date$',
                                                                f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .')
                                        elif modify_validity.lower() == 'yes' and modify_expiry.lower() == 'no':
                                            validity = new_records[0].get('validity')
                                            Validity_Period = n2w.convert(validity).capitalize()
                                            Validity_Period = f'<b>{Validity_Period}' + " " + 'Year </b> from the date of issue of the letter unless revoked, suspended or cancelled. '
                                            data = data.replace('$expiry_date$', '')
                                        else:
                                            validity = new_records[0].get('validity')
                                            Validity_Period = n2w.convert(validity).capitalize()
                                            Validity_Period = f'<b>{Validity_Period} </b>' + " " + 'Year'
                                            data = data.replace('$expiry_date$',
                                                                f'from the expiry date of previous registration i.e. {expiry_with_modification} unless revoked, suspended or cancelled .')
                                data = data.replace('$VALIDITY$', Validity_Period)
                                # application_id = new_records[0].get('app_id')
                                # forming certificate number
                                l_3_4 = str(date)[0:2]
                                l_8_9 = str(date)[3:5]
                                l_10_19 = new_records[0].get('user_pan')
                                l_20_22 = str(date)[8:10]
                                state_key = (str(state)[0:3])
                                certificate_number = f'PR-{l_3_4}-{state_key}-{l_8_9}-{l_10_19}-{l_20_22}'
                                data = data.replace('$REGISTRATION_NUMBER$', certificate_number)
                                company_name = new_records[0].get('company_name')
                                data = data.replace('$COMPANY_NAME$', company_name)
                                company_address = new_records[0].get('company_address')
                                data = data.replace('$COMPANY_ADDRESS$', company_address)
                                company_district = new_records[0].get('district')
                                company_pincode = new_records[0].get('pincode')
                                data = data.replace('$COMPANY_DISTRICT$', company_district)
                                data = data.replace('$COMPANY_STATE$', state_title_normal)
                                data = data.replace('$COMPANY_PINCODE$', str(company_pincode))
                                payment_date = new_records[0].get('payment_date').strftime("%d-%m-%Y")

                                data = data.replace('$PAYMENT_DATE$', str(payment_date))
                                # processing capacity table part
                                processing_capacity_query = f"""Select w.category,
                                sum(w.processing_capacity) as processing_capacity
                                from {TableName.ulb_waste_process} as w
                                where w.company_id = {company_id} and w.application_id={application_id}
                                GROUP by  w.category ,w.process_code"""
                                p_status, p_records = self.db_util.select_mysql_table(processing_capacity_query)
                                if p_status:
                                    if p_records:
                                        category_list = [1, 2, 3, 4]
                                        exist = []
                                        for each_value in p_records:
                                            exist.append(each_value.get('category'))
                                        main_list = np.setdiff1d(category_list, exist)
                                        cat_1, cat_2, cat_3, cat_4 = '', '', '', ''
                                        production_capacity = ''
                                        cat1_code, cat2_code, cat3_code, cat4_code = [], [], [], []
                                        cat1_process, cat2_process, cat3_process, cat4_process = [], [], [], []
                                        for new_value in p_records:
                                            if 1 not in main_list:
                                                if new_value.get('category') == 1:
                                                    # cat_1 = (new_value.get('processing_capacity'))
                                                    cat1_process.append(new_value.get('processing_capacity'))
                                                    cat_1 = sum(cat1_process)
                                                    cat1_code.append(new_value.get('process_code'))
                                            else:
                                                cat_1 = '--'
                                            if 2 not in main_list:
                                                if new_value.get('category') == 2:
                                                    # cat_2 = (new_value.get('processing_capacity'))
                                                    cat2_process.append(new_value.get('processing_capacity'))
                                                    cat_2 = sum(cat2_process)
                                                    cat2_code.append(new_value.get('process_code'))
                                            else:
                                                cat_2 = '--'
                                            if 3 not in main_list:
                                                if new_value.get('category') == 3:
                                                    # cat_3 = (new_value.get('processing_capacity'))
                                                    cat3_process.append(new_value.get('processing_capacity'))
                                                    cat_3 = sum(cat3_process)
                                                    cat3_code.append(new_value.get('process_code'))
                                            else:
                                                cat_3 = '--'
                                            if 4 not in main_list:
                                                if new_value.get('category') == 4:
                                                    # cat_4 = (new_value.get('processing_capacity'))
                                                    cat4_process.append(new_value.get('processing_capacity'))
                                                    cat_4 = sum(cat4_process)
                                                    cat4_code.append(new_value.get('process_code'))
                                            else:
                                                cat_4 = '--'
                                        production_capacity_query = f"""
                                        Select sum(w.recycled_quality_tpa) as recycled_tpa, d.name, w.process_code
                                        from {TableName.ulb_waste_process} as w
                                        left join {TableName.pwp_products} as d on d.id=w.product
                                        where w.company_id = {company_id} and w.application_id={application_id}
                                        GROUP by w.product, w.process_code
                                        """
                                        prod_status, prod_response = self.db_util.select_mysql_table(
                                            production_capacity_query)
                                        if prod_response:
                                            for prod_value in prod_response:
                                                capacity_data = f"""
                                                <tr><td>{prod_value.get('name')} {"    "}{"    "}  [{prod_value.get('process_code')}]</td> 
                                                <td>{prod_value.get('recycled_tpa')}</td>
                                                </tr>"""
                                                production_capacity += capacity_data
                                                distict_list = set(cat1_code + cat2_code + cat3_code + cat4_code)
                                                # joined_string = ",".join(sorted(distict_list))
                                                joined_string =''
                                                data = data.replace('$table_code$', joined_string)
                                                cat1_code = '[%s]' % ', '.join(map(str, cat1_code))
                                                cat2_code = '[%s]' % ', '.join(map(str, cat2_code))
                                                cat3_code = '[%s]' % ', '.join(map(str, cat3_code))
                                                cat4_code = '[%s]' % ', '.join(map(str, cat4_code))
                                                # data = data.replace('$Cat-I$', f'Cat-I {str(cat1_code)}')
                                                # data = data.replace('$Cat-II$', f'Cat-II {str(cat2_code)}')
                                                # data = data.replace('$Cat-III$', f'Cat-III {str(cat3_code)}')
                                                # data = data.replace('$Cat-IV$', f'Cat-IV {str(cat4_code)}')
                                                data = data.replace('$Cat-I$', 'Cat-I ')
                                                data = data.replace('$Cat-II$', 'Cat-II ')
                                                data = data.replace('$Cat-III$', 'Cat-III ')
                                                data = data.replace('$Cat-IV$', 'Cat-IV ')
                                        data = data.replace('$CAT1$', str(cat_1))
                                        data = data.replace('$CAT2$', str(cat_2))
                                        data = data.replace('$CAT3$', str(cat_3))
                                        data = data.replace('$CAT4$', str(cat_4))
                                        data = data.replace('$production_capacity$', production_capacity)
                                        # new_date = datetime.now().strftime("%d-%m-%Y")
                                        terms_con = new_records[0].get('terms_and_conditions')

                                        if terms_con:
                                            data = data.replace('$Terms and Conditions:-$', 'Terms and Conditions :-')
                                            data = data.replace('$terms$', terms_con)
                                        else:
                                            data = data.replace('$Terms and Conditions:-$', ' ')
                                            data = data.replace('$terms$', ' ')
                                        data = data.replace('$DESIGNATION$', str(designation))
                                        pdf_name = f'{reference_no}_unsigned'
                                        if os.path.exists(
                                                os.path.join(dsign_html_template_dir, 'ulb_certificate.html')):
                                            os.remove(os.path.join(dsign_html_template_dir, 'ulb_certificate.html'))
                                        with open(os.path.join(dsign_html_template_dir, 'ulb_certificate.html'),
                                                  'w') as w:
                                            w.write(data)
                                        if os.path.exists(f'{digital_signature_files}/{pdf_name}.pdf'):
                                            os.remove(f'{digital_signature_files}/{pdf_name}.pdf')
                                        pdfkit.from_file(os.path.join(dsign_html_template_dir, 'ulb_certificate.html'),
                                                         f'{digital_signature_files}/{pdf_name}.pdf',
                                                         options=self.options)
                                        logger.info('certificate generated successfully')
                                        file_path = rf'{digital_signature_files}/{pdf_name}.pdf'
                                        pdf_path = f"{ds_minio_path}/ULB/{user_id}/unsigned/{pdf_name}.pdf"
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
                                        logger.info('certificate generated successfully')
                                        return ResponseMessage.final_json(status=Message.success,
                                                                          message="Get Summary List  Successful",
                                                                          data=final_json)

                                    else:
                                        logger.info('no data corresponding to pwp waste processing capacity')
                                else:
                                    logger.error('error while trying to perform processing query')
                        else:
                            logger.error('There is no path corresponding for pwp logo')

                    else:
                        logger.error('There is no such file or directory for pwp_new')

                else:
                    logger.info('no data corresponding to pwp certificate query')
            else:
                logger.error(f'error while trying to perform pwp certificate query')

        except Exception as e:
            logger.exception(f'error while trying to generate pwp certificate{str(e)}')
            traceback.print_exc()

    def fetch_selected_state(self, request_id):
        try:
            logger.info("Fetch selected state from the request")
            query = f"""select
    par.state_id
from
    pibo_epr_target pe
    left join pibo_application_requests par on pe.company_id = par.company_id
    and pe.application_id = par.application_id
    and pe.state_id = par.state_id
where
    par.request_id = '{request_id}'
"""
            status, resp = self.db_util.select_mysql_fetchone(query=query)
            if status and resp:
                return resp.get('state_id')
            else:
                raise Exception('Failed to fetch state_id')
        except Exception as e:
            logger.error(f"Error occurred while fetching selected state : {str(e)}")
            raise Exception("Failed to fetch selected state")
