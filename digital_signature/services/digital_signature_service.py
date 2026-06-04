from fastapi import APIRouter, Form, Depends
from starlette.requests import Request

from scripts.constants.app_constants import Routes, DigitalSignature
from scripts.core.digital_signature.handlers.digital_signature_handler import DigitalSignatureHandler
from scripts.core.digital_signature.handlers.digital_signature_pwp_handler import DigitalSignatureHandlerPWP
from scripts.core.digital_signature.models.digital_signature_model import SignDigitally
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.decorators import CookieAuthentication

ds_router = APIRouter(prefix=Routes.digital_signature_base_url, tags=[Routes.digital_signature_base_url])
auth = CookieAuthentication()


@ds_router.post(DigitalSignature.sign_digitally)
def sign_digitally(request: Request, input_json: SignDigitally, req_body=Depends(auth)):
    try:
        CommonUtils.user_activity(req_body['user_id'],req_body['role'],'DigitalSignature.sign_digitally')
        input_json = CommonUtils().getMyPayload(input_json,SignDigitally)

        if not CommonUtils.checkIsAdmin(req_body):
            return {"status":"failed","message":"Unauthorized access"}
        logger.info("Inside the Digital signature service")
        user_info = req_body
        #In the inner function user_id taken from Auth
        final_json = DigitalSignatureHandler().sign_digitally(input_json, user_info, request)
        return final_json
    except Exception as e:
        logger.info(f"Exception while Signing {e}")
        return str(e)


@ds_router.post(DigitalSignature.gateway_response)
def gateway_response(Returnvalue: str = Form(...),
                     ReturnStatus: str = Form(...),
                     Referencenumber: str = Form(...)):
    try:
        logger.info("Inside the Gateway Response Service")
        final_json = DigitalSignatureHandler().gate_way_response(Returnvalue, ReturnStatus,
                                                                 Referencenumber)
        return final_json
    except Exception as e:
        logger.info(f"Exception while Getting response Service {e}")
        return f"Exception while Getting response Service {e}"


@ds_router.post(DigitalSignature.sign_digitally_pwp)
def sign_digitally(request: Request, input_json: SignDigitally, req_body=Depends(auth)):
    try:
        CommonUtils.user_activity(req_body['user_id'],req_body['role'],'DigitalSignature.sign_digitally_pwp')
        input_json = CommonUtils().getMyPayload(input_json, SignDigitally)
        
        if not CommonUtils.checkIsAdmin(req_body):
            return {"status":"failed","message":"Unauthorized access"}
        
        if req_body['api_check'] :
            return {"status":"failed","message":"Unauthorized access"}
        logger.info("Inside the Digital signature service")
        user_info = req_body
        final_json = DigitalSignatureHandlerPWP().sign_digitally(input_json, user_info, request)
        return final_json
    except Exception as e:
        logger.info(f"Exception while Signing {e}")
        return str(e)


@ds_router.post(DigitalSignature.gateway_response_pwp)
def gateway_response(Returnvalue: str = Form(...),
                     ReturnStatus: str = Form(...),
                     Referencenumber: str = Form(...)):
    try:
        logger.info("Inside the Gateway Response Service")
        final_json = DigitalSignatureHandlerPWP().gate_way_response(Returnvalue, ReturnStatus,
                                                                    Referencenumber)
        return final_json
    except Exception as e:
        logger.info(f"Exception while Getting response Service {e}")
        return f"Exception while Getting response Service {e}"


@ds_router.post(DigitalSignature.sign_digitally_ulb)
def sign_digitally(request: Request, input_json: SignDigitally, req_body=Depends(auth)):
    try:
        CommonUtils.user_activity(req_body['user_id'],req_body['role'],'DigitalSignature.sign_digitally_ulb')
        input_json = CommonUtils().getMyPayload(input_json, SignDigitally)
        if not CommonUtils.checkIsAdmin(req_body):
            return {"status":"failed","message":"Unauthorized access"}
        
        if req_body['api_check'] :
            return {"status":"failed","message":"Unauthorized access"}
        logger.info("Inside the Digital signature service")
        user_info = req_body
        final_json = DigitalSignatureHandlerPWP().sign_digitally_ulb(input_json, user_info, request)
        return final_json
    except Exception as e:
        logger.info(f"Exception while Signing {e}")
        return str(e)


@ds_router.post(DigitalSignature.gateway_response_ulb)
def gateway_response(Returnvalue: str = Form(...),
                     ReturnStatus: str = Form(...),
                     Referencenumber: str = Form(...)):
    try:
        logger.info("Inside the Gateway Response Service")
        final_json = DigitalSignatureHandlerPWP().gate_way_response_ulb(Returnvalue, ReturnStatus, Referencenumber)
        return final_json
    except Exception as e:
        logger.info(f"Exception while Getting response Service {e}")
        return f"Exception while Getting response Service {e}"
